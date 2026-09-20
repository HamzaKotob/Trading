"""Minimal single-symbol, single-timeframe walk-forward backtest.

Historical data -> Strategy -> Backtest -> Results, run before any paper
or live trading. Walks forward bar-by-bar through `candles`, evaluating
only the history visible up to each bar (no lookahead), opens a paper
trade on A/A+ setups approved by the risk engine, and closes it on the
first bar that touches stop loss or take_profit_1.

Uses the same candle series for both the trend and entry evaluation
windows, which is a simplification of the real multi-timeframe strategy.
Not a production-grade backtester: no slippage, spread, or partial fills
are modeled.
"""
from __future__ import annotations

from dataclasses import dataclass

from trading_agent.broker.paper_broker import PaperBroker
from trading_agent.journal.trade_journal import TradeJournal
from trading_agent.models import Candle, Direction, Grade
from trading_agent.risk.position_sizing import calculate_position_size
from trading_agent.risk.risk_manager import RiskManager
from trading_agent.strategy.evaluator import evaluate_setup


@dataclass
class BacktestResult:
    trades_taken: int
    ending_balance: float


class BacktestEngine:
    def __init__(self, risk_manager: RiskManager, journal: TradeJournal, broker: PaperBroker):
        self._risk = risk_manager
        self._journal = journal
        self._broker = broker

    def run(self, symbol: str, candles: list[Candle], min_history: int = 60) -> BacktestResult:
        trades_taken = 0
        open_trade_id: str | None = None

        for i in range(min_history, len(candles)):
            visible = candles[: i + 1]
            candle = candles[i]

            if open_trade_id is not None:
                trade = next(t for t in self._broker.get_open_trades() if t.id == open_trade_id)
                hit_sl = (trade.direction is Direction.BUY and candle.low <= trade.stop_loss) or (
                    trade.direction is Direction.SELL and candle.high >= trade.stop_loss
                )
                hit_tp = (trade.direction is Direction.BUY and candle.high >= trade.take_profit) or (
                    trade.direction is Direction.SELL and candle.low <= trade.take_profit
                )
                if hit_sl or hit_tp:
                    exit_price = trade.stop_loss if hit_sl else trade.take_profit
                    closed = self._broker.close_trade(open_trade_id, exit_price, closed_at=candle.time)
                    self._risk.register_trade_result(closed.pnl)
                    self._journal.record_trade(closed)
                    open_trade_id = None
                continue

            setup = evaluate_setup(symbol, visible, visible)
            if setup is None or setup.grade not in (Grade.A_PLUS, Grade.A):
                continue
            if not self._risk.can_open_trade(setup.risk_reward):
                continue

            size = calculate_position_size(
                self._broker.get_account_balance(),
                self._risk.risk_per_trade_pct,
                setup.entry_price,
                setup.stop_loss,
            )
            trade = self._broker.place_order(
                symbol,
                setup.direction,
                size,
                setup.entry_price,
                setup.stop_loss,
                setup.take_profit_1,
                opened_at=candle.time,
            )
            self._journal.record_trade(trade)
            open_trade_id = trade.id
            trades_taken += 1

        return BacktestResult(trades_taken=trades_taken, ending_balance=self._broker.get_account_balance())
