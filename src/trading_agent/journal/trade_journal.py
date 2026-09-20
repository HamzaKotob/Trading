"""SQLite-backed trade journal."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trading_agent.models import Direction, Trade

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    size REAL NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    opened_at TEXT NOT NULL,
    exit_price REAL,
    closed_at TEXT,
    pnl REAL,
    r_multiple REAL,
    status TEXT NOT NULL
)
"""


class TradeJournal:
    """Persists trades to a local SQLite database for later review and
    performance analytics (win rate, drawdown, profit factor, ...)."""

    def __init__(self, db_path: str | Path = "trade_journal.sqlite3"):
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def record_trade(self, trade: Trade) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO trades
                (id, symbol, direction, size, entry_price, stop_loss, take_profit,
                 opened_at, exit_price, closed_at, pnl, r_multiple, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.id,
                trade.symbol,
                trade.direction.value,
                trade.size,
                trade.entry_price,
                trade.stop_loss,
                trade.take_profit,
                trade.opened_at.isoformat(),
                trade.exit_price,
                trade.closed_at.isoformat() if trade.closed_at else None,
                trade.pnl,
                trade.r_multiple,
                trade.status,
            ),
        )
        self._conn.commit()

    def get_all_trades(self) -> list[Trade]:
        cursor = self._conn.execute("SELECT * FROM trades ORDER BY opened_at")
        columns = [d[0] for d in cursor.description]
        trades = []
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            trades.append(
                Trade(
                    id=data["id"],
                    symbol=data["symbol"],
                    direction=Direction(data["direction"]),
                    size=data["size"],
                    entry_price=data["entry_price"],
                    stop_loss=data["stop_loss"],
                    take_profit=data["take_profit"],
                    opened_at=datetime.fromisoformat(data["opened_at"]),
                    exit_price=data["exit_price"],
                    closed_at=datetime.fromisoformat(data["closed_at"]) if data["closed_at"] else None,
                    pnl=data["pnl"],
                    r_multiple=data["r_multiple"],
                    status=data["status"],
                )
            )
        return trades

    def close(self) -> None:
        self._conn.close()
