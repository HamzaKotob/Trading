from trading_agent.risk.risk_manager import RiskManager


def test_blocks_trades_when_risk_reward_too_low():
    rm = RiskManager(account_balance=10_000, min_risk_reward=2.0)
    assert not rm.can_open_trade(risk_reward=1.5)
    assert rm.can_open_trade(risk_reward=2.0)


def test_stops_trading_after_daily_loss_limit():
    rm = RiskManager(account_balance=10_000, max_daily_loss_pct=2.0, min_risk_reward=1.0)
    assert rm.can_open_trade(risk_reward=2.0)
    rm.register_trade_result(-150.0)
    assert rm.can_open_trade(risk_reward=2.0)  # -150 > -200 threshold, still allowed
    rm.register_trade_result(-60.0)  # total -210 <= -200 threshold
    assert not rm.can_open_trade(risk_reward=2.0)


def test_reset_daily_clears_limit():
    rm = RiskManager(account_balance=10_000, max_daily_loss_pct=2.0, min_risk_reward=1.0)
    rm.register_trade_result(-300.0)
    assert not rm.can_open_trade(risk_reward=2.0)
    rm.reset_daily()
    assert rm.can_open_trade(risk_reward=2.0)


def test_weekly_loss_limit_independent_of_daily_reset():
    rm = RiskManager(account_balance=10_000, max_daily_loss_pct=50.0, max_weekly_loss_pct=5.0, min_risk_reward=1.0)
    rm.register_trade_result(-600.0)
    assert not rm.can_open_trade(risk_reward=2.0)
    rm.reset_daily()
    assert not rm.can_open_trade(risk_reward=2.0)
    rm.reset_weekly()
    assert rm.can_open_trade(risk_reward=2.0)
