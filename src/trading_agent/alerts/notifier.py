"""Instant alerting interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from trading_agent.models import TradeSetup


class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        ...

    def notify_setup(self, setup: TradeSetup) -> None:
        self.send(
            f"[{setup.grade.value}] {setup.decision.value} {setup.symbol} @ {setup.entry_price} "
            f"| SL {setup.stop_loss} | TP1 {setup.take_profit_1} | R:R {setup.risk_reward} "
            f"| Confidence {setup.confidence_score}%"
        )


class ConsoleNotifier(Notifier):
    """Prints alerts to stdout. Swap in a Telegram/Slack/email notifier
    for real instant alerts."""

    def send(self, message: str) -> None:
        print(message)
