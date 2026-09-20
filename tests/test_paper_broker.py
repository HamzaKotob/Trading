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
