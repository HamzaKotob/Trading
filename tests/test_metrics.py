from datetime import datetime, timedelta, timezone

import pytest

from trading_agent.journal.metrics import average_return, max_drawdown, profit_factor, win_rate
from trading_agent.models import Direction, Trade


def _closed_trade(pnl: float, closed_at: datetime) -> Trade:
    return Trade(
        id=f"{pnl}-{closed_at.isoformat()}",
        symbol="EURUSD",
        direction=Direction.BUY,
        size=1.0,
        entry_price=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        opened_at=closed_at - timedelta(hours=1),
        exit_price=1.1 + pnl / 1000,
        closed_at=closed_at,
        pnl=pnl,
        status="CLOSED",
    )


def test_metrics_on_mixed_trades():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    trades = [
        _closed_trade(100, start),
        _closed_trade(-50, start + timedelta(days=1)),
        _closed_trade(200, start + timedelta(days=2)),
        _closed_trade(-300, start + timedelta(days=3)),
    ]

    assert win_rate(trades) == 50.0
    assert average_return(trades) == pytest.approx((100 - 50 + 200 - 300) / 4)
    assert profit_factor(trades) == pytest.approx(0.86)


def test_max_drawdown_tracks_peak_to_trough():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    trades = [
        _closed_trade(1000, start),
        _closed_trade(-500, start + timedelta(days=1)),
        _closed_trade(-300, start + timedelta(days=2)),
    ]
    dd = max_drawdown(trades, starting_balance=10_000)
    assert dd == pytest.approx((11000 - 10200) / 11000 * 100, rel=1e-3)


def test_empty_trades_returns_zero():
    assert win_rate([]) == 0.0
    assert average_return([]) == 0.0
    assert profit_factor([]) == 0.0
    assert max_drawdown([], starting_balance=10_000) == 0.0
