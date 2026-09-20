"""Deterministic risk approval engine.

Deliberately not AI: this is the module with final authority over whether
a trade is allowed, per the core prompt's risk rules (max 1% per trade,
min 1:2 RR, 2% daily / 5% weekly loss limits, stop trading once hit). A
scanner/strategy module may propose a setup; only RiskManager approves it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskManager:
    """Tracks running daily/weekly P&L against the starting balance and
    blocks new trades once configured limits are breached."""

    account_balance: float
    risk_per_trade_pct: float = 0.5
    max_risk_per_trade_pct: float = 1.0
    min_risk_reward: float = 2.0
    max_daily_loss_pct: float = 2.0
    max_weekly_loss_pct: float = 5.0

    _daily_pnl: float = field(default=0.0, init=False)
    _weekly_pnl: float = field(default=0.0, init=False)

    def can_open_trade(self, risk_reward: float) -> bool:
        if risk_reward < self.min_risk_reward:
            return False
        if self._daily_pnl <= -self.account_balance * (self.max_daily_loss_pct / 100):
            return False
        if self._weekly_pnl <= -self.account_balance * (self.max_weekly_loss_pct / 100):
            return False
        return True

    def register_trade_result(self, pnl: float) -> None:
        self._daily_pnl += pnl
        self._weekly_pnl += pnl

    def reset_daily(self) -> None:
        self._daily_pnl = 0.0

    def reset_weekly(self) -> None:
        self._weekly_pnl = 0.0

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    @property
    def weekly_pnl(self) -> float:
        return self._weekly_pnl
