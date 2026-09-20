from trading_agent.data.csv_provider import CSVDataProvider
from trading_agent.models import Timeframe


def test_csv_provider_reads_and_sorts_candles(tmp_path):
    csv_content = (
        "time,open,high,low,close,volume\n"
        "2026-01-01T01:00:00+00:00,1.10,1.12,1.09,1.11,100\n"
        "2026-01-01T00:00:00+00:00,1.09,1.11,1.08,1.10,90\n"
    )
    (tmp_path / "EURUSD_H1.csv").write_text(csv_content)

    provider = CSVDataProvider(tmp_path)
    candles = provider.get_candles("EURUSD", Timeframe.H1, count=10)

    assert len(candles) == 2
    assert candles[0].time < candles[1].time
    assert provider.get_current_price("EURUSD") == 1.11
    assert provider.get_symbols() == ["EURUSD"]


def test_csv_provider_missing_file_raises(tmp_path):
    provider = CSVDataProvider(tmp_path)
    try:
        provider.get_candles("GBPUSD", Timeframe.H1, count=5)
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
