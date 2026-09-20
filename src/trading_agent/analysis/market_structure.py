"""Smart-money/ICT style structure detection: swings, BOS/CHoCH, fair value
gaps, order blocks, and liquidity sweeps.

These are deliberately simplified, mechanical heuristics over OHLC data —
a starting point to refine or replace, not a definitive SMC/ICT engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from trading_agent.models import Candle, Direction


@dataclass(frozen=True)
class FairValueGap:
    direction: Direction
    top: float
    bottom: float
    index: int


@dataclass(frozen=True)
class OrderBlock:
    direction: Direction
    high: float
    low: float
    index: int


def find_swings(candles: list[Candle], lookback: int = 2) -> tuple[list[int], list[int]]:
    """Return indices of local swing highs and swing lows.

    A swing high/low is a candle whose high/low is the most extreme within
    `lookback` candles on either side.
    """
    highs, lows = [], []
    for i in range(lookback, len(candles) - lookback):
        window = candles[i - lookback : i + lookback + 1]
        if candles[i].high == max(c.high for c in window):
            highs.append(i)
        if candles[i].low == min(c.low for c in window):
            lows.append(i)
    return highs, lows


def detect_structure_break(candles: list[Candle], lookback: int = 2) -> str | None:
    """Classify the most recent structural event as BOS, CHoCH, or None.

    Compares the last two swing highs and last two swing lows to establish
    the prevailing trend, then checks whether the latest close breaks
    beyond the prior swing: a break in the trend's direction is a Break of
    Structure (BOS); a break against it is a Change of Character (CHoCH).
    """
    highs, lows = find_swings(candles, lookback)
    if len(highs) < 2 or len(lows) < 2:
        return None

    last_close = candles[-1].close
    prior_high = candles[highs[-2]].high
    prior_low = candles[lows[-2]].low
    uptrend = candles[highs[-1]].high > prior_high and candles[lows[-1]].low > prior_low

    if last_close > prior_high:
        return "BOS" if uptrend else "CHoCH"
    if last_close < prior_low:
        return "CHoCH" if uptrend else "BOS"
    return None


def detect_fair_value_gaps(candles: list[Candle]) -> list[FairValueGap]:
    """Detect 3-candle imbalances (Fair Value Gaps): a gap between candle
    i-2's high/low and candle i's low/high that candle i-1 didn't fill."""
    gaps: list[FairValueGap] = []
    for i in range(2, len(candles)):
        first, third = candles[i - 2], candles[i]
        if first.high < third.low:
            gaps.append(FairValueGap(Direction.BUY, top=third.low, bottom=first.high, index=i))
        elif first.low > third.high:
            gaps.append(FairValueGap(Direction.SELL, top=first.low, bottom=third.high, index=i))
    return gaps


def detect_order_blocks(candles: list[Candle]) -> list[OrderBlock]:
    """Detect simple order blocks: the last opposite-direction candle
    before a strong impulsive move that breaks the prior candle's range."""
    blocks: list[OrderBlock] = []
    for i in range(1, len(candles) - 1):
        prev, curr = candles[i - 1], candles[i]
        bullish_impulse = curr.close > curr.open and curr.close > prev.high
        bearish_impulse = curr.close < curr.open and curr.close < prev.low
        if bullish_impulse and prev.close < prev.open:
            blocks.append(OrderBlock(Direction.BUY, high=prev.high, low=prev.low, index=i - 1))
        elif bearish_impulse and prev.close > prev.open:
            blocks.append(OrderBlock(Direction.SELL, high=prev.high, low=prev.low, index=i - 1))
    return blocks


def detect_liquidity_sweep(candles: list[Candle], lookback: int = 2) -> Direction | None:
    """Detect whether the latest candle swept a recent swing high/low and
    closed back inside the range (a classic liquidity grab).

    Returns Direction.SELL for a swept swing high (bearish reversal signal)
    or Direction.BUY for a swept swing low (bullish reversal signal).
    """
    if len(candles) < lookback * 2 + 2:
        return None
    highs, lows = find_swings(candles[:-1], lookback)
    latest = candles[-1]
    if highs and latest.high > candles[highs[-1]].high and latest.close < candles[highs[-1]].high:
        return Direction.SELL
    if lows and latest.low < candles[lows[-1]].low and latest.close > candles[lows[-1]].low:
        return Direction.BUY
    return None
