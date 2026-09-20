"""Core data structures shared across the trading agent."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Timeframe(str, Enum):
    MN1 = "MN1"
    W1 = "W1"
    D1 = "D1"
    H4 = "H4"
    H1 = "H1"
    M15 = "M15"
    M5 = "M5"


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Grade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    REJECT = "Reject"


class Decision(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


@dataclass(frozen=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class TradeSetup:
    """A candidate trade produced by the strategy scanner/evaluator."""

    symbol: str
    direction: Direction
    current_price: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    probability: float
    timeframe: Timeframe
    duration_estimate: str
    reason_entry: str
    reason_stop_loss: str
    invalidation_level: float
    market_bias: str
    confidence_score: float
    grade: Grade = Grade.REJECT

    @property
    def decision(self) -> Decision:
        """Final BUY/SELL/WAIT decision per the core prompt's rule: only
        A+/A grade setups with confidence >= 80 are ever actionable."""
        if self.grade not in (Grade.A_PLUS, Grade.A) or self.confidence_score < 80:
            return Decision.WAIT
        return Decision.BUY if self.direction is Direction.BUY else Decision.SELL


@dataclass
class Trade:
    """A trade that has been (paper or live) executed, for journaling."""

    id: str
    symbol: str
    direction: Direction
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    opened_at: datetime
    exit_price: float | None = None
    closed_at: datetime | None = None
    pnl: float | None = None
    r_multiple: float | None = None
    status: str = "OPEN"
