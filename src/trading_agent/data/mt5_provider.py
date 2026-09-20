"""Live/historical market data via MetaTrader 5.

Requires the `MetaTrader5` package, which only ships for Windows and needs
a running, logged-in MT5 terminal. Install with `pip install -e ".[mt5]"`
on a Windows host. On any other platform, importing this module still works
but instantiating `MT5DataProvider` raises `ImportError`.
"""
from __future__ import annotations

from datetime import datetime

from trading_agent.data.base import MarketDataProvider
from trading_agent.models import Candle, Timeframe

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - MetaTrader5 only ships for Windows
    mt5 = None

_TIMEFRAME_MAP: dict[Timeframe, int] = {}
if mt5 is not None:  # pragma: no cover
    _TIMEFRAME_MAP = {
        Timeframe.MN1: mt5.TIMEFRAME_MN1,
        Timeframe.W1: mt5.TIMEFRAME_W1,
        Timeframe.D1: mt5.TIMEFRAME_D1,
        Timeframe.H4: mt5.TIMEFRAME_H4,
        Timeframe.H1: mt5.TIMEFRAME_H1,
        Timeframe.M15: mt5.TIMEFRAME_M15,
        Timeframe.M5: mt5.TIMEFRAME_M5,
    }


class MT5DataProvider(MarketDataProvider):
    """Live/historical market data sourced from a running MetaTrader 5 terminal."""

    def __init__(self, login: int | None = None, password: str | None = None, server: str | None = None):
        if mt5 is None:
            raise ImportError(
                "MetaTrader5 package is not installed or not available on this "
                "platform (Windows + MT5 terminal required). Install it with "
                "`pip install -e \".[mt5]\"` on a Windows host."
            )
        if not mt5.initialize(login=login, password=password, server=server):
            raise RuntimeError(f"MetaTrader5 initialize() failed: {mt5.last_error()}")

    def shutdown(self) -> None:
        mt5.shutdown()

    def get_candles(self, symbol: str, timeframe: Timeframe, count: int) -> list[Candle]:
        rates = mt5.copy_rates_from_pos(symbol, _TIMEFRAME_MAP[timeframe], 0, count)
        if rates is None:
            raise RuntimeError(f"Failed to fetch candles for {symbol} {timeframe.value}: {mt5.last_error()}")
        return [
            Candle(
                time=datetime.fromtimestamp(r["time"]),
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r["tick_volume"]),
            )
            for r in rates
        ]

    def get_current_price(self, symbol: str) -> float:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Failed to fetch tick for {symbol}: {mt5.last_error()}")
        return float(tick.bid)

    def get_symbols(self) -> list[str]:
        symbols = mt5.symbols_get()
        return [s.name for s in symbols] if symbols else []
