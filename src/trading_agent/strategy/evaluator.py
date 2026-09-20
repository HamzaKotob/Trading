"""Pure confluence-based trade setup evaluation.

This is the deterministic "Signal Engine": it takes candle history in and
returns a graded TradeSetup out, with no I/O and no side effects. Keeping
it pure means the exact same logic can run live (via Scanner, fed by a
MarketDataProvider) or in a backtest (fed historical slices bar-by-bar)
without risking lookahead bias.

The confluence rule set here (EMA trend alignment, MACD momentum, RSI,
structure break, liquidity sweep) is intentionally small and explicit — a
starting point to plug a fuller SMC/ICT engine into, not a finished one.
"""
from __future__ import annotations

from trading_agent.analysis.indicators import atr, candles_to_frame, ema, macd, rsi
from trading_agent.analysis.market_structure import detect_liquidity_sweep, detect_structure_break
from trading_agent.models import Candle, Direction, Grade, Timeframe, TradeSetup

_GRADE_BY_CONFLUENCE_COUNT: dict[int, tuple[Grade, float]] = {
    5: (Grade.A_PLUS, 90.0),
    4: (Grade.A, 82.0),
    3: (Grade.B, 65.0),
    2: (Grade.C, 50.0),
}


def evaluate_setup(
    symbol: str,
    trend_candles: list[Candle],
    entry_candles: list[Candle],
    entry_timeframe: Timeframe = Timeframe.M5,
) -> TradeSetup | None:
    """Evaluate one symbol's candle history into a graded TradeSetup, or
    None if no directional bias is found.

    Callers must pass exactly the candle history that should be visible at
    evaluation time (e.g. a historical slice during backtesting) to avoid
    lookahead bias — this function never fetches data itself.
    """
    if len(trend_candles) < 60 or len(entry_candles) < 10:
        return None

    direction, confluences, reasons = _evaluate_direction(trend_candles, entry_candles)
    if direction is None:
        return None

    current_price = entry_candles[-1].close
    atr_value = float(atr(candles_to_frame(entry_candles)).iloc[-1])
    if atr_value <= 0:
        return None

    stop_loss, tp1, tp2, tp3 = _levels(direction, current_price, atr_value)
    risk = abs(current_price - stop_loss)
    reward = abs(tp2 - current_price)
    risk_reward = round(reward / risk, 2) if risk else 0.0

    grade, confidence = _grade(confluences, risk_reward)

    return TradeSetup(
        symbol=symbol,
        direction=direction,
        current_price=current_price,
        entry_price=current_price,
        stop_loss=stop_loss,
        take_profit_1=tp1,
        take_profit_2=tp2,
        take_profit_3=tp3,
        risk_reward=risk_reward,
        probability=confidence,
        timeframe=entry_timeframe,
        duration_estimate="Intraday (hours), based on the entry timeframe",
        reason_entry="; ".join(reasons),
        reason_stop_loss=f"Beyond recent structure, ~{atr_value:.5f} (1x ATR) buffer",
        invalidation_level=stop_loss,
        market_bias=direction.value,
        confidence_score=confidence,
        grade=grade,
    )


def _evaluate_direction(
    trend_candles: list[Candle], entry_candles: list[Candle]
) -> tuple[Direction | None, int, list[str]]:
    trend_close = candles_to_frame(trend_candles)["close"]
    ema20, ema50, ema200 = (ema(trend_close, p).iloc[-1] for p in (20, 50, 200))

    if ema20 > ema50 > ema200:
        trend = Direction.BUY
    elif ema20 < ema50 < ema200:
        trend = Direction.SELL
    else:
        return None, 0, []

    entry_close = candles_to_frame(entry_candles)["close"]
    rsi_value = rsi(entry_close).iloc[-1]
    macd_hist = macd(entry_close)["histogram"].iloc[-1]
    structure = detect_structure_break(entry_candles)
    sweep = detect_liquidity_sweep(entry_candles)

    confluences = 1  # HTF EMA trend alignment
    reasons = [f"HTF EMA20/50/200 aligned {trend.value.lower()}"]

    momentum_ok = (trend is Direction.BUY and macd_hist > 0) or (trend is Direction.SELL and macd_hist < 0)
    if momentum_ok:
        confluences += 1
        reasons.append("MACD histogram confirms momentum")

    rsi_ok = (trend is Direction.BUY and 40 < rsi_value < 70) or (trend is Direction.SELL and 30 < rsi_value < 60)
    if rsi_ok:
        confluences += 1
        reasons.append(f"RSI at {rsi_value:.1f} supports continuation, not exhausted")

    if structure in ("BOS", "CHoCH"):
        confluences += 1
        reasons.append(f"Entry timeframe shows {structure}")

    if sweep is trend:
        confluences += 1
        reasons.append("Liquidity sweep in trend direction before continuation")

    return trend, confluences, reasons


def _levels(direction: Direction, price: float, atr_value: float) -> tuple[float, float, float, float]:
    sign = 1 if direction is Direction.BUY else -1
    stop_loss = price - sign * atr_value
    tp1 = price + sign * atr_value * 1.5
    tp2 = price + sign * atr_value * 2.5
    tp3 = price + sign * atr_value * 4.0
    return stop_loss, tp1, tp2, tp3


def _grade(confluences: int, risk_reward: float) -> tuple[Grade, float]:
    if risk_reward < 2.0:
        return Grade.REJECT, 0.0
    return _GRADE_BY_CONFLUENCE_COUNT.get(confluences, (Grade.REJECT, 0.0))
