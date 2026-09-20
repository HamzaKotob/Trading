"""Risk-percent based position sizing. Pure math, no I/O."""
from __future__ import annotations


def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
    contract_size: float = 1.0,
) -> float:
    """Calculate position size (units) so a stop-loss hit loses exactly
    `risk_percent` of `account_balance`.

    `contract_size` converts price units into account-currency risk per
    unit (e.g. 100_000 for a standard forex lot quoted directly in the
    account currency, or 1 for stocks/crypto priced directly in account
    currency). Returns raw units/shares/contracts, not lots — see
    `units_to_lots` to convert.
    """
    if risk_percent <= 0:
        raise ValueError("risk_percent must be positive")
    price_risk = abs(entry_price - stop_loss_price)
    if price_risk <= 0:
        raise ValueError("entry_price and stop_loss_price must differ")

    risk_amount = account_balance * (risk_percent / 100)
    return risk_amount / (price_risk * contract_size)


def units_to_lots(units: float, units_per_lot: float = 100_000.0) -> float:
    """Convert raw units into standard forex lots, rounded to 2 decimals
    (the typical minimum lot step)."""
    return round(units / units_per_lot, 2)
