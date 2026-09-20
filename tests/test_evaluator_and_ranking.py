from trading_agent.data.csv_provider import CSVDataProvider
from trading_agent.models import Grade, Timeframe
from trading_agent.strategy.evaluator import evaluate_setup
from trading_agent.strategy.ranking import rank_opportunities


def test_evaluate_setup_returns_none_on_too_little_history():
    assert evaluate_setup("EURUSD", [], []) is None


def test_evaluate_setup_finds_bullish_setup_on_sample_data():
    provider = CSVDataProvider("data/samples")
    trend_candles = provider.get_candles("EURUSD", Timeframe.H4, 220)
    entry_candles = provider.get_candles("EURUSD", Timeframe.M15, 220)

    setup = evaluate_setup("EURUSD", trend_candles, entry_candles, Timeframe.M15)

    assert setup is not None
    assert setup.risk_reward >= 2.0
    assert setup.grade != Grade.REJECT


def test_rank_opportunities_orders_best_first():
    provider = CSVDataProvider("data/samples")
    trend_candles = provider.get_candles("EURUSD", Timeframe.H4, 220)
    entry_candles = provider.get_candles("EURUSD", Timeframe.M15, 220)
    setup = evaluate_setup("EURUSD", trend_candles, entry_candles, Timeframe.M15)

    ranked = rank_opportunities([setup])
    assert ranked[0] is setup
