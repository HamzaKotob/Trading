"""In-memory simulated broker for demos, backtests, and tests."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from trading_agent.broker.base import BrokerClient
from trading_agent.models import Direction, Trade


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaperBroker(BrokerClient):
    """Simulates order execution entirely in memory; no real orders are
    ever sent anywhere. Use this for demos, backtests, and paper trading
    before connecting a real broker."""

    def __init__(self, starting_balance: float):
        self._balance = starting_balance
        self._open: dict[str, Trade] = {}
        self._closed: list[Trade] = []

    def get_account_balance(self) -> float:
        return self._balance

    def place_order(
        self,
        symbol: str,
        direction: Direction,
        size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        opened_at: datetime | None = None,
    ) -> Trade:
        trade = Trade(
            id=str(uuid.uuid4()),
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=opened_at or _utcnow(),
        )
        self._open[trade.id] = trade
        return trade

    def modify_stop_loss(self, trade_id: str, new_stop_loss: float) -> None:
        self._open[trade_id].stop_loss = new_stop_loss

    def close_trade(self, trade_id: str, exit_price: float, closed_at: datetime | None = None) -> Trade:
        trade = self._open.pop(trade_id)
        direction_sign = 1 if trade.direction is Direction.BUY else -1
        trade.exit_price = exit_price
        trade.closed_at = closed_at or _utcnow()
        trade.pnl = direction_sign * (exit_price - trade.entry_price) * trade.size
        risk = abs(trade.entry_price - trade.stop_loss)
        trade.r_multiple = (direction_sign * (exit_price - trade.entry_price) / risk) if risk else 0.0
        trade.status = "CLOSED"
        self._balance += trade.pnl
        self._closed.append(trade)
        return trade

    def get_open_trades(self) -> list[Trade]:
        return list(self._open.values())

    def get_closed_trades(self) -> list[Trade]:
        return list(self._closed)
