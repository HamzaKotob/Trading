"""Best Opportunity Ranking across everything the scanner found."""
from __future__ import annotations

from trading_agent.models import Decision, Grade, TradeSetup

_GRADE_RANK = {Grade.A_PLUS: 4, Grade.A: 3, Grade.B: 2, Grade.C: 1, Grade.REJECT: 0}


def rank_opportunities(setups: list[TradeSetup]) -> list[TradeSetup]:
    """Rank setups best-first by grade, then confidence, then risk/reward."""
    return sorted(
        setups,
        key=lambda s: (_GRADE_RANK[s.grade], s.confidence_score, s.risk_reward),
        reverse=True,
    )


def best_opportunity(setups: list[TradeSetup]) -> TradeSetup | None:
    """Return the single best tradeable (A+/A grade, non-WAIT) setup, if any."""
    for setup in rank_opportunities(setups):
        if setup.grade in (Grade.A_PLUS, Grade.A) and setup.decision is not Decision.WAIT:
            return setup
    return None
