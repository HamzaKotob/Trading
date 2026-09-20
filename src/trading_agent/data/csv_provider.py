"""CSV-backed market data provider, for backtesting and demos."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from trading_agent.data.base import MarketDataProvider
from trading_agent.models import Candle, Timeframe


class CSVDataProvider(MarketDataProvider):
    """Reads historical OHLCV candles from local CSV files.

    Used for backtesting and for running the agent end-to-end without a
    live broker connection. Expects one file per symbol/timeframe named
    ``<symbol>_<timeframe>.csv`` with columns: time,open,high,low,close,volume.
    """

    def __init__(self, data_dir: str | Path):
        self._data_dir = Path(data_dir)
        self._cache: dict[tuple[str, Timeframe], list[Candle]] = {}

    def _load(self, symbol: str, timeframe: Timeframe) -> list[Candle]:
        key = (symbol, timeframe)
        if key in self._cache:
            return self._cache[key]

        path = self._data_dir / f"{symbol}_{timeframe.value}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No candle data for {symbol} {timeframe.value} at {path}")

        candles: list[Candle] = []
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                candles.append(
                    Candle(
                        time=datetime.fromisoformat(row["time"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0.0)),
                    )
                )
        candles.sort(key=lambda c: c.time)
        self._cache[key] = candles
        return candles

    def get_candles(self, symbol: str, timeframe: Timeframe, count: int) -> list[Candle]:
        candles = self._load(symbol, timeframe)
        return candles[-count:]

    def get_current_price(self, symbol: str) -> float:
        for timeframe in Timeframe:
            path = self._data_dir / f"{symbol}_{timeframe.value}.csv"
            if path.exists():
                return self._load(symbol, timeframe)[-1].close
        raise FileNotFoundError(f"No candle data available for {symbol}")

    def get_symbols(self) -> list[str]:
        symbols = set()
        for path in self._data_dir.glob("*_*.csv"):
            symbol = path.stem.rsplit("_", 1)[0]
            symbols.add(symbol)
        return sorted(symbols)
