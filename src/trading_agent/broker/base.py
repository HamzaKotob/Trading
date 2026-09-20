"""Broker execution interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from trading_agent.models import Direction, Trade


class BrokerClient(ABC):
    """Executes and manages orders against a broker/exchange.

    Order placement always takes an explicit, pre-approved size, entry,
    stop loss and take profit: sizing and risk approval happen upstream in
    the deterministic risk engine, never inside the broker client.

    `opened_at`/`closed_at` default to the real current time (correct for
    live/paper trading) but can be overridden with a simulated timestamp,
    which a backtest must do to keep the journal's trade history aligned
    with the historical data being replayed rather than wall-clock time.
    """

    @abstractmethod
    def get_account_balance(self) -> float:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def modify_stop_loss(self, trade_id: str, new_stop_loss: float) -> None:
        ...

    @abstractmethod
    def close_trade(self, trade_id: str, exit_price: float, closed_at: datetime | None = None) -> Trade:
        ...

    @abstractmethod
    def get_open_trades(self) -> list[Trade]:
        ...
