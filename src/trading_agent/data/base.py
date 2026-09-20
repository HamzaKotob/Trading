"""Market data provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from trading_agent.models import Candle, Timeframe


class MarketDataProvider(ABC):
    """Source of OHLCV candles and live prices for one or more instruments."""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: Timeframe, count: int) -> list[Candle]:
        """Return the most recent `count` candles, oldest first."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Return the latest tradable price for `symbol`."""

    @abstractmethod
    def get_symbols(self) -> list[str]:
        """Return the list of instruments this provider can serve."""
