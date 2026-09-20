"""High-impact news avoidance interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class EconomicCalendarProvider(ABC):
    """Source of upcoming high-impact economic events."""

    @abstractmethod
    def has_high_impact_event_within(self, symbol: str, minutes: int, as_of: datetime) -> bool:
        """Return True if a high-impact event affecting `symbol` falls
        within `minutes` of `as_of`."""


class NullEconomicCalendar(EconomicCalendarProvider):
    """Default placeholder that reports no upcoming news.

    Swap in a real provider (e.g. backed by a ForexFactory/Investing.com-
    style economic calendar feed) before trading live: the core prompt's
    "no major news within next 30 minutes" entry rule depends on it.
    """

    def has_high_impact_event_within(self, symbol: str, minutes: int, as_of: datetime) -> bool:
        return False
