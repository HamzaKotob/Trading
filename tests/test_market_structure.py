from datetime import datetime, timedelta, timezone

from trading_agent.analysis.market_structure import (
    detect_fair_value_gaps,
    detect_liquidity_sweep,
    detect_order_blocks,
    detect_structure_break,
    find_swings,
)
from trading_agent.models import Candle, Direction


def _candle(i: int, o: float, h: float, l: float, c: float) -> Candle:
    return Candle(time=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i), open=o, high=h, low=l, close=c)


def _c(i: int, close: float) -> Candle:
    return _candle(i, close - 0.005, close + 0.01, close - 0.01, close)


def test_detect_fair_value_gaps_bullish():
    candles = [
        _candle(0, 1.0, 1.05, 0.98, 1.02),
        _candle(1, 1.10, 1.15, 1.08, 1.12),
        _candle(2, 1.20, 1.25, 1.18, 1.22),
    ]
    gaps = detect_fair_value_gaps(candles)
    assert len(gaps) == 1
    assert gaps[0].direction is Direction.BUY


def test_detect_order_blocks_bullish():
    candles = [
        _candle(0, 1.05, 1.06, 1.00, 1.01),  # bearish candle -> potential OB
        _candle(1, 1.01, 1.20, 1.00, 1.19),  # strong bullish impulse breaking prev high
        _candle(2, 1.19, 1.21, 1.15, 1.20),
    ]
    blocks = detect_order_blocks(candles)
    assert any(b.direction is Direction.BUY for b in blocks)


def test_find_swings_detects_local_extremes():
    closes = [1.00, 1.05, 1.02, 1.08, 1.04, 1.12, 1.07, 1.15]
    candles = [_c(i, c) for i, c in enumerate(closes)]
    highs, lows = find_swings(candles, lookback=1)
    assert highs == [1, 3, 5]
    assert lows == [2, 4, 6]


def test_detect_structure_break_identifies_bos_in_uptrend():
    closes = [1.00, 1.05, 1.02, 1.08, 1.04, 1.12, 1.07, 1.15]
    candles = [_c(i, c) for i, c in enumerate(closes)]
    result = detect_structure_break(candles, lookback=1)
    assert result == "BOS"


def test_detect_liquidity_sweep_returns_none_with_insufficient_data():
    candles = [_candle(0, 1.0, 1.01, 0.99, 1.0)]
    assert detect_liquidity_sweep(candles) is None
