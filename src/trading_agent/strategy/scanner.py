"""Market scanner: fetches candles for many symbols and grades each one.

This is the "Market Scanner" agent from the target architecture — it owns
no risk or execution logic, only data fetching + delegating to the pure
evaluator.
"""
from __future__ import annotations

from trading_agent.data.base import MarketDataProvider
from trading_agent.models import Timeframe, TradeSetup
from trading_agent.strategy.evaluator import evaluate_setup


class Scanner:
    """Fetches trend + entry timeframe candles for a list of symbols from a
    MarketDataProvider and evaluates each into a graded TradeSetup."""

    def __init__(
        self,
        data_provider: MarketDataProvider,
        entry_timeframe: Timeframe = Timeframe.M5,
        trend_timeframe: Timeframe = Timeframe.H4,
        candle_count: int = 200,
    ):
        self._data = data_provider
        self._entry_timeframe = entry_timeframe
        self._trend_timeframe = trend_timeframe
        self._candle_count = candle_count

    def scan(self, symbols: list[str]) -> list[TradeSetup]:
        """Scan every symbol and return the setups with a directional bias
        (i.e. skip symbols the evaluator rejects outright)."""
        setups = []
        for symbol in symbols:
            trend_candles = self._data.get_candles(symbol, self._trend_timeframe, self._candle_count)
            entry_candles = self._data.get_candles(symbol, self._entry_timeframe, self._candle_count)
            setup = evaluate_setup(symbol, trend_candles, entry_candles, self._entry_timeframe)
            if setup is not None:
                setups.append(setup)
        return setups
