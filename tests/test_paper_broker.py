from datetime import datetime, timezone

import pytest

from trading_agent.broker.paper_broker import PaperBroker
from trading_agent.models import Direction


def test_paper_broker_round_trip():
    broker = PaperBroker(starting_balance=10_000)
    trade = broker.place_order(
        "EURUSD", Direction.BUY, size=10_000, entry_price=1.1000, stop_loss=1.0950, take_profit=1.1100
    )
    assert trade in broker.get_open_trades()

    closed = broker.close_trade(trade.id, exit_price=1.1050)
    assert closed.status == "CLOSED"
    assert closed.pnl == pytest.approx((1.1050 - 1.1000) * 10_000)
    assert broker.get_account_balance() == pytest.approx(10_000 + closed.pnl)
    assert broker.get_open_trades() == []


def test_paper_broker_uses_supplied_simulated_timestamps():
    """A backtest must be able to stamp trades with the historical candle
    time being replayed, not wall-clock time, or the journal misrepresents
    when trades actually happened in the simulation."""
    broker = PaperBroker(starting_balance=10_000)
    opened_at = datetime(2020, 1, 1, 9, 0, tzinfo=timezone.utc)
    closed_at = datetime(2020, 1, 1, 15, 0, tzinfo=timezone.utc)

    trade = broker.place_order(
        "EURUSD",
        Direction.BUY,
        size=10_000,
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        opened_at=opened_at,
    )
    assert trade.opened_at == opened_at

    closed = broker.close_trade(trade.id, exit_price=1.1050, closed_at=closed_at)
    assert closed.closed_at == closed_at


def test_paper_broker_defaults_to_wall_clock_when_no_timestamp_given():
    broker = PaperBroker(starting_balance=10_000)
    before = datetime.now(timezone.utc)
    trade = broker.place_order(
        "EURUSD", Direction.BUY, size=10_000, entry_price=1.1000, stop_loss=1.0950, take_profit=1.1100
    )
    after = datetime.now(timezone.utc)
    assert before <= trade.opened_at <= after
