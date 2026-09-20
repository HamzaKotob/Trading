"""Performance analytics computed from the trade journal: win rate,
average return, max drawdown, profit factor."""
from __future__ import annotations

from trading_agent.models import Trade


def _closed_pnls(trades: list[Trade]) -> list[float]:
    return [t.pnl for t in trades if t.status == "CLOSED" and t.pnl is not None]


def win_rate(trades: list[Trade]) -> float:
    pnls = _closed_pnls(trades)
    if not pnls:
        return 0.0
    wins = sum(1 for p in pnls if p > 0)
    return round(100 * wins / len(pnls), 2)


def average_return(trades: list[Trade]) -> float:
    pnls = _closed_pnls(trades)
    return round(sum(pnls) / len(pnls), 2) if pnls else 0.0


def profit_factor(trades: list[Trade]) -> float:
    pnls = _closed_pnls(trades)
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return round(gross_profit / gross_loss, 2)


def max_drawdown(trades: list[Trade], starting_balance: float) -> float:
    """Maximum peak-to-trough drawdown (%) of the equity curve built by
    applying closed trades in chronological order."""
    closed = sorted((t for t in trades if t.status == "CLOSED"), key=lambda t: t.closed_at)
    equity = starting_balance
    peak = starting_balance
    max_dd = 0.0
    for pnl in _closed_pnls(closed):
        equity += pnl
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak * 100 if peak else 0.0
        max_dd = max(max_dd, drawdown)
    return round(max_dd, 2)
