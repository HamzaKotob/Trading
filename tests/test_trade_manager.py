from datetime import datetime, timezone

import pytest

from trading_agent.execution.trade_manager import update_stop_loss
from trading_agent.models import Direction, Trade


def _trade(direction: Direction, entry: float, stop: float) -> Trade:
    return Trade(
        id="t1",
        symbol="EURUSD",
        direction=direction,
        size=1.0,
        entry_price=entry,
        stop_loss=stop,
        take_profit=entry + 0.01 if direction is Direction.BUY else entry - 0.01,
        opened_at=datetime.now(timezone.utc),
    )


def test_moves_stop_to_breakeven_after_trigger():
    trade = _trade(Direction.BUY, entry=1.1000, stop=1.0950)
    new_stop = update_stop_loss(trade, current_price=1.1080, breakeven_trigger_r=1.0)
    assert new_stop == pytest.approx(1.1000)


def test_does_not_move_stop_before_trigger():
    trade = _trade(Direction.BUY, entry=1.1000, stop=1.0950)
    new_stop = update_stop_loss(trade, current_price=1.1020, breakeven_trigger_r=1.0)
    assert new_stop == pytest.approx(1.0950)


def test_trails_stop_with_atr_after_breakeven():
    trade = _trade(Direction.BUY, entry=1.1000, stop=1.0950)
    new_stop = update_stop_loss(
        trade, current_price=1.1200, breakeven_trigger_r=1.0, trailing_atr_multiple=1.0, atr_value=0.0050
    )
    assert new_stop == pytest.approx(1.1200 - 0.0050)


def test_sell_side_breakeven():
    trade = _trade(Direction.SELL, entry=1.1000, stop=1.1050)
    new_stop = update_stop_loss(trade, current_price=1.0920, breakeven_trigger_r=1.0)
    assert new_stop == pytest.approx(1.1000)
