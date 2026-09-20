from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from trading_agent.analysis.indicators import atr, candles_to_frame, ema, macd, rsi
from trading_agent.models import Candle


def _make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            time=start + timedelta(hours=i),
            open=c - 0.1,
            high=c + 0.2,
            low=c - 0.2,
            close=c,
            volume=100,
        )
        for i, c in enumerate(closes)
    ]


def test_ema_converges_to_constant_series():
    series = pd.Series([10.0] * 50)
    result = ema(series, 20)
    assert result.iloc[-1] == pytest.approx(10.0)


def test_rsi_is_100_for_pure_uptrend():
    series = pd.Series(range(1, 30))
    result = rsi(series, period=14)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_macd_histogram_positive_in_uptrend():
    series = pd.Series([float(i) for i in range(1, 60)])
    result = macd(series)
    assert result["histogram"].iloc[-1] > 0


def test_atr_positive_for_volatile_series():
    candles = _make_candles([100 + i * 0.5 for i in range(30)])
    df = candles_to_frame(candles)
    result = atr(df, period=14)
    assert result.iloc[-1] > 0
