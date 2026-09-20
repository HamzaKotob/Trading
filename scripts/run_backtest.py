"""Run the walk-forward backtest engine over the bundled sample data.

Historical Data -> Strategy -> Backtest -> Results. Uses the synthetic
EURUSD M15 sample data (not real market data) with a fresh PaperBroker and
TradeJournal each run.
"""
from __future__ import annotations

from pathlib import Path

from trading_agent.backtest.engine import BacktestEngine
from trading_agent.broker.paper_broker import PaperBroker
from trading_agent.data.csv_provider import CSVDataProvider
from trading_agent.journal.metrics import average_return, max_drawdown, profit_factor, win_rate
from trading_agent.journal.trade_journal import TradeJournal
from trading_agent.models import Timeframe
from trading_agent.risk.risk_manager import RiskManager

STARTING_BALANCE = 10_000.0


def main() -> None:
    provider = CSVDataProvider("data/samples")
    symbol = "EURUSD"
    candles = provider.get_candles(symbol, Timeframe.M15, count=10_000)

    risk_manager = RiskManager(account_balance=STARTING_BALANCE, min_risk_reward=2.0)

    db_path = Path("backtest_journal.sqlite3")
    if db_path.exists():
        db_path.unlink()
    journal = TradeJournal(db_path)
    broker = PaperBroker(starting_balance=STARTING_BALANCE)

    engine = BacktestEngine(risk_manager, journal, broker)
    result = engine.run(symbol, candles, min_history=60)

    trades = journal.get_all_trades()

    print(f"Symbol: {symbol}")
    print(f"Candles walked: {len(candles)}")
    print(f"Trades taken: {result.trades_taken}")
    print(f"Starting balance: {STARTING_BALANCE:.2f}")
    print(f"Ending balance: {result.ending_balance:.2f}")
    print(f"Net P&L: {result.ending_balance - STARTING_BALANCE:.2f}")

    if trades:
        print(f"Win rate: {win_rate(trades)}%")
        print(f"Average return per trade: {average_return(trades):.5f}")
        print(f"Profit factor: {profit_factor(trades)}")
        print(f"Max drawdown: {max_drawdown(trades, STARTING_BALANCE)}%")
        print()
        for t in trades:
            print(
                f"  {t.opened_at.isoformat()} {t.direction.value} @ {t.entry_price:.5f} "
                f"-> {t.exit_price:.5f} ({t.closed_at.isoformat()}) "
                f"pnl={t.pnl:.2f} R={t.r_multiple:.2f} status={t.status}"
            )
    else:
        print("No A+/A setups were both found and risk-approved during this window.")

    journal.close()
    db_path.unlink()


if __name__ == "__main__":
    main()
