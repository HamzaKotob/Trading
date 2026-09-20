"""CLI entry point.

Wires together: CSVDataProvider (data) -> Scanner (signal engine) ->
RiskManager (approval) -> NullEconomicCalendar (news gate) -> ranking ->
ConsoleNotifier (alerts). Swap CSVDataProvider for MT5DataProvider and add
a broker + journal wiring for live/paper trading.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from trading_agent.alerts.notifier import ConsoleNotifier
from trading_agent.config import AppConfig
from trading_agent.data.csv_provider import CSVDataProvider
from trading_agent.models import Decision, Timeframe
from trading_agent.news.economic_calendar import NullEconomicCalendar
from trading_agent.risk.risk_manager import RiskManager
from trading_agent.strategy.ranking import best_opportunity, rank_opportunities
from trading_agent.strategy.scanner import Scanner


def scan_command(args: argparse.Namespace) -> None:
    config = AppConfig.from_yaml(args.config) if args.config else AppConfig()
    data_provider = CSVDataProvider(args.csv_dir)
    symbols = args.symbols or data_provider.get_symbols() or config.symbols

    scanner = Scanner(
        data_provider,
        entry_timeframe=Timeframe(args.entry_timeframe),
        trend_timeframe=Timeframe(args.trend_timeframe),
    )
    risk_manager = RiskManager(
        account_balance=config.account_balance,
        risk_per_trade_pct=config.risk.risk_per_trade_pct,
        max_risk_per_trade_pct=config.risk.max_risk_per_trade_pct,
        min_risk_reward=config.risk.min_risk_reward,
        max_daily_loss_pct=config.risk.max_daily_loss_pct,
        max_weekly_loss_pct=config.risk.max_weekly_loss_pct,
    )
    calendar = NullEconomicCalendar()
    notifier = ConsoleNotifier()

    setups = scanner.scan(symbols)
    ranked = rank_opportunities(setups)

    print(f"Scanned {len(symbols)} symbol(s), {len(setups)} candidate setup(s):\n")
    for setup in ranked:
        news_blocked = calendar.has_high_impact_event_within(
            setup.symbol, config.news_lookahead_minutes, datetime.now(timezone.utc)
        )
        risk_ok = risk_manager.can_open_trade(setup.risk_reward)
        decision = setup.decision if (risk_ok and not news_blocked) else Decision.WAIT

        print(f"Symbol: {setup.symbol}")
        print(f"Direction: {setup.direction.value}")
        print(f"Current Price: {setup.current_price}")
        print(f"Entry Price: {setup.entry_price}")
        print(f"Stop Loss: {setup.stop_loss}")
        print(f"Take Profit 1: {setup.take_profit_1}")
        print(f"Take Profit 2: {setup.take_profit_2}")
        print(f"Take Profit 3: {setup.take_profit_3}")
        print(f"Risk Reward: {setup.risk_reward}")
        print(f"Probability: {setup.probability}%")
        print(f"Timeframe: {setup.timeframe.value}")
        print(f"Trade Duration Estimate: {setup.duration_estimate}")
        print(f"Reason for Entry: {setup.reason_entry}")
        print(f"Reason for Stop Loss: {setup.reason_stop_loss}")
        print(f"Invalidation Level: {setup.invalidation_level}")
        print(f"Market Bias: {setup.market_bias}")
        print(f"Confidence Score: {setup.confidence_score}")
        print(f"Grade: {setup.grade.value}")
        print(f"Decision: {decision.value}\n")
        if decision is not Decision.WAIT:
            notifier.notify_setup(setup)

    best = best_opportunity(ranked)
    if best is None:
        print("Final Decision: WAIT")
    else:
        print(f"Best Opportunity: {best.symbol} -> Final Decision: {best.decision.value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-agent")
    subparsers = parser.add_subparsers(required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan symbols and report ranked trade setups")
    scan_parser.add_argument("--config", help="Path to a YAML config file (see config/settings.example.yaml)")
    scan_parser.add_argument("--csv-dir", default="data/samples", help="Directory of <symbol>_<timeframe>.csv files")
    scan_parser.add_argument(
        "--symbols", nargs="*", help="Symbols to scan (defaults to config or CSV directory contents)"
    )
    scan_parser.add_argument("--entry-timeframe", default="M15")
    scan_parser.add_argument("--trend-timeframe", default="H4")
    scan_parser.set_defaults(func=scan_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
