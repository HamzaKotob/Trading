"""YAML-backed application configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 0.5
    max_risk_per_trade_pct: float = 1.0
    min_risk_reward: float = 2.0
    max_daily_loss_pct: float = 2.0
    max_weekly_loss_pct: float = 5.0


@dataclass
class AppConfig:
    account_balance: float = 10_000.0
    symbols: list[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: list[str] = field(default_factory=lambda: ["D1", "H4", "H1", "M15"])
    risk: RiskConfig = field(default_factory=RiskConfig)
    min_confidence: float = 80.0
    news_lookahead_minutes: int = 30

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        data: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
        risk_data = data.pop("risk", {})
        return cls(risk=RiskConfig(**risk_data), **data)
