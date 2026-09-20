"""Rule-based position management: break-even + ATR trailing stop.

Deliberately not AI: an LLM should never be given the freedom to move a
live stop loss on a whim. This module is pure, deterministic math.
"""
from __future__ import annotations

from trading_agent.models import Direction, Trade


def update_stop_loss(
    trade: Trade,
    current_price: float,
    breakeven_trigger_r: float = 1.0,
    trailing_atr_multiple: float | None = None,
    atr_value: float | None = None,
) -> float:
    """Return the stop loss `trade` should be moved to, given current price.

    Once profit reaches `breakeven_trigger_r` R (multiples of the original
    stop distance), the stop moves to entry. Beyond that, if an ATR value
    and trailing multiple are supplied, the stop trails `trailing_atr_multiple`
    ATRs behind price. Never moves the stop against the trade's favor.
    """
    sign = 1 if trade.direction is Direction.BUY else -1
    initial_risk = abs(trade.entry_price - trade.stop_loss)
    if initial_risk == 0:
        return trade.stop_loss

    profit_r = sign * (current_price - trade.entry_price) / initial_risk
    new_stop = trade.stop_loss

    if profit_r >= breakeven_trigger_r:
        new_stop = trade.entry_price

    if trailing_atr_multiple is not None and atr_value is not None and profit_r >= breakeven_trigger_r:
        trailing_stop = current_price - sign * atr_value * trailing_atr_multiple
        if sign * (trailing_stop - new_stop) > 0:
            new_stop = trailing_stop

    return new_stop
