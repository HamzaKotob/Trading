import pytest

from trading_agent.risk.position_sizing import calculate_position_size, units_to_lots


def test_calculate_position_size_basic():
    units = calculate_position_size(
        account_balance=10_000, risk_percent=1, entry_price=1.1000, stop_loss_price=1.0950
    )
    assert units == pytest.approx(20_000.0)


def test_calculate_position_size_rejects_zero_distance():
    with pytest.raises(ValueError):
        calculate_position_size(10_000, 1, 1.1000, 1.1000)


def test_calculate_position_size_rejects_non_positive_risk():
    with pytest.raises(ValueError):
        calculate_position_size(10_000, 0, 1.1000, 1.0950)


def test_units_to_lots():
    assert units_to_lots(50_000) == 0.5
