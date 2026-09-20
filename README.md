# Trading Agent

A modular, multi-timeframe trading analysis system implementing the
institutional analyst behavior described in [`SYSTEM_PROMPT.md`](./SYSTEM_PROMPT.md).

The core design principle: **the AI analyzes, deterministic code decides.**
A signal/strategy layer can propose a setup; a separate, non-AI risk engine
has final authority over whether any order is allowed, sized, or modified.
Nothing here lets a language model directly move money or a stop loss.

This is a scaffold, not a finished live-trading system — see
[Scope](#scope) and [Roadmap](#roadmap) below.

## How this maps to a full trading-system architecture

```
LIVE MARKET DATA
      ↓
MarketDataProvider (data/)          — pluggable: CSVDataProvider (done), MT5DataProvider (guarded stub)
      ↓
Scanner + evaluator (strategy/)     — "Market Scanner" + "Strategy Agent": multi-timeframe
      ↓                               confluence scoring (trend, momentum, structure, liquidity)
Ranking (strategy/ranking.py)       — Best Opportunity Ranking across every symbol scanned
      ↓
RiskManager (risk/)                 — "Risk Management Engine": deterministic, not AI.
      ↓                               Enforces min R:R, daily/weekly loss limits, position sizing
TRADE DECISION: BUY / SELL / WAIT
      ↓
BrokerClient (broker/)              — "Execution Engine": pluggable, PaperBroker (done) or MT5Broker
      ↓
TradeManager (execution/)           — "Position Manager": rule-based break-even + ATR trailing stop
      ↓
TradeJournal + metrics (journal/)   — "Trade Journal" + "Performance Agent": SQLite log,
                                       win rate / avg return / max drawdown / profit factor
```

An LLM (or a human analyst) fits above this diagram, reading the scanner's
output and journal's history to explain setups and post-trade patterns —
never inside the risk/execution path.

## Project layout

```
src/trading_agent/
├── models.py                # Candle, TradeSetup, Trade, enums
├── config.py                 # YAML-backed AppConfig / RiskConfig
├── data/
│   ├── base.py                #   MarketDataProvider interface
│   ├── csv_provider.py        #   Reads OHLCV from local CSV (backtest/demo)
│   └── mt5_provider.py        #   Live/historical data via MetaTrader 5
├── broker/
│   ├── base.py                #   BrokerClient interface
│   ├── paper_broker.py        #   In-memory simulated broker
│   └── mt5_broker.py          #   Real execution via MetaTrader 5
├── analysis/
│   ├── indicators.py           # EMA, RSI, MACD, ATR
│   └── market_structure.py     # Swings, BOS/CHoCH, FVG, order blocks, liquidity sweeps
├── strategy/
│   ├── evaluator.py             # Pure confluence-based setup evaluation (no I/O)
│   ├── scanner.py                # Fetches candles + runs the evaluator per symbol
│   └── ranking.py                # Ranks setups, picks the single best opportunity
├── risk/
│   ├── position_sizing.py        # Risk-% based position sizing
│   └── risk_manager.py            # Deterministic per-trade / daily / weekly loss limits
├── execution/
│   └── trade_manager.py           # Rule-based break-even + ATR trailing stop
├── news/
│   └── economic_calendar.py       # High-impact news avoidance interface
├── journal/
│   ├── trade_journal.py            # SQLite-backed trade log
│   └── metrics.py                   # Win rate, avg return, drawdown, profit factor
├── alerts/
│   └── notifier.py                  # Alert interface (console notifier included)
├── backtest/
│   └── engine.py                     # Single-symbol walk-forward backtest loop
└── main.py                            # CLI entry point (`scan` command)

tests/                          # pytest suite covering every module above
data/samples/                    # Synthetic demo OHLCV data (not real market data)
scripts/generate_sample_data.py  # Regenerates the synthetic demo data
config/settings.example.yaml     # Example AppConfig
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the demo scanner

Uses the bundled synthetic sample data in `data/samples/` (not real market
data — see `scripts/generate_sample_data.py`):

```bash
python -m trading_agent.main scan --csv-dir data/samples --symbols EURUSD \
    --trend-timeframe H4 --entry-timeframe M15
```

This prints every candidate setup found (per the Trade Output fields in
`SYSTEM_PROMPT.md`) ranked best-first, followed by a final `BUY`/`SELL`/`WAIT`
decision for the single best opportunity.

## Run the tests

```bash
pip install -e ".[dev]"
pytest
```

## Connecting to MetaTrader (MT4/MT5)

`MT5DataProvider` and `MT5Broker` (in `data/mt5_provider.py` and
`broker/mt5_broker.py`) wrap the official `MetaTrader5` Python package. That
package only ships for Windows and requires a running, logged-in MT5
terminal, so it's an optional extra:

```bash
pip install -e ".[mt5]"   # Windows only
```

Once installed, swap `CSVDataProvider`/`PaperBroker` for
`MT5DataProvider`/`MT5Broker` when wiring up `main.py` or your own script.

## Scope

What's implemented and tested here:

- ✅ Multi-timeframe trend/momentum/structure confluence scoring
- ✅ Risk-% based position sizing and daily/weekly loss limit enforcement
  (deterministic, separate from the scanner/AI layer)
- ✅ Rule-based break-even + ATR trailing stop management
- ✅ Trade journal (SQLite) and performance metrics (win rate, average
  return, max drawdown, profit factor)
- ✅ Pluggable data/broker interfaces, with a safe `PaperBroker` for demos
  and a guarded MetaTrader 5 adapter for later live use
- ✅ Best-opportunity ranking across multiple scanned symbols
- ✅ A single-symbol walk-forward backtest engine with no lookahead bias

Deliberately simplified / left for follow-up work:

- The confluence scanner (`strategy/evaluator.py`) uses a small, explicit
  rule set (EMA alignment, MACD, RSI, structure break, liquidity sweep) —
  not a full SMC/ICT engine, and not fundamental/news-sentiment analysis.
- `NullEconomicCalendar` is a no-op placeholder; wire in a real economic
  calendar feed before trading live.
- `BacktestEngine` is a single-symbol, single-timeframe walk-forward loop
  with no slippage/spread/partial-fill modeling.
- No live alert channel (Telegram/Slack/email) is wired up — only
  `ConsoleNotifier`.
- No LLM integration yet: today, `strategy/evaluator.py` is the entire
  "intelligence" layer. An LLM would sit alongside it for narrative
  analysis/news interpretation, never inside the risk or execution path.

## Roadmap

Following a backtest → paper trading → live progression, in this order:

1. **Backtesting** — extend `backtest/engine.py` to multi-symbol,
   multi-timeframe, with slippage/spread modeling; validate on an
   out-of-sample period before trusting any result.
2. **Paper trading** — run the scanner + risk engine + `PaperBroker`
   continuously against live data for weeks, comparing expected vs. actual
   performance via `journal/metrics.py`.
3. **AI analyst layer** — add an LLM-backed module that explains setups,
   interprets incoming news, and summarizes patterns across the trade
   journal — read-only with respect to risk/execution.
4. **Real broker integration** — MetaTrader first (`mt5_provider.py` /
   `mt5_broker.py` are already stubbed for this); only after step 2 has
   validated the strategy.
5. **Service + dashboard** — if/when this needs to run as a hosted system
   with a UI (a FastAPI backend over this package, a Postgres store for
   `trades`/`signals`/`agent_decisions`, and a Next.js dashboard), that's a
   separate, larger project layered on top of this package — not a
   rewrite of it.

Only after backtesting and a real paper-trading track record should live
capital be considered, and only in small size initially.
