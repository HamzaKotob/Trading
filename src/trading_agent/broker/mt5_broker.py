"""Real order execution via MetaTrader 5.

Requires the `MetaTrader5` package (Windows + a running, logged-in MT5
terminal). See README for setup. On any other platform, importing this
module still works but instantiating `MT5Broker` raises `ImportError`.
"""
from __future__ import annotations

from datetime import datetime, timezone

from trading_agent.broker.base import BrokerClient
from trading_agent.models import Direction, Trade

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None


class MT5Broker(BrokerClient):
    """Places and manages real orders through a running MetaTrader 5 terminal."""

    def __init__(self, magic_number: int = 20260101):
        if mt5 is None:
            raise ImportError(
                "MetaTrader5 package is not installed or not available on this "
                "platform. Install it with `pip install -e \".[mt5]\"` on Windows."
            )
        self._magic = magic_number

    def get_account_balance(self) -> float:
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"Failed to fetch account info: {mt5.last_error()}")
        return float(info.balance)

    def place_order(
        self,
        symbol: str,
        direction: Direction,
        size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> Trade:
        order_type = mt5.ORDER_TYPE_BUY if direction is Direction.BUY else mt5.ORDER_TYPE_SELL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": size,
            "type": order_type,
            "price": entry_price,
            "sl": stop_loss,
            "tp": take_profit,
            "magic": self._magic,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_send failed for {symbol}: {result}")
        return Trade(
            id=str(result.order),
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=datetime.now(timezone.utc),
        )

    def modify_stop_loss(self, trade_id: str, new_stop_loss: float) -> None:
        position = self._get_position(trade_id)
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": position.symbol,
            "sl": new_stop_loss,
            "tp": position.tp,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Failed to modify stop loss for {trade_id}: {result}")

    def close_trade(self, trade_id: str, exit_price: float) -> Trade:
        position = self._get_position(trade_id)
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": exit_price,
            "magic": self._magic,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Failed to close trade {trade_id}: {result}")
        direction = Direction.BUY if position.type == mt5.ORDER_TYPE_BUY else Direction.SELL
        direction_sign = 1 if direction is Direction.BUY else -1
        pnl = direction_sign * (exit_price - position.price_open) * position.volume
        return Trade(
            id=trade_id,
            symbol=position.symbol,
            direction=direction,
            size=position.volume,
            entry_price=position.price_open,
            stop_loss=position.sl,
            take_profit=position.tp,
            opened_at=datetime.fromtimestamp(position.time, tz=timezone.utc),
            exit_price=exit_price,
            closed_at=datetime.now(timezone.utc),
            pnl=pnl,
            status="CLOSED",
        )

    def get_open_trades(self) -> list[Trade]:
        positions = mt5.positions_get()
        if not positions:
            return []
        trades = []
        for p in positions:
            direction = Direction.BUY if p.type == mt5.ORDER_TYPE_BUY else Direction.SELL
            trades.append(
                Trade(
                    id=str(p.ticket),
                    symbol=p.symbol,
                    direction=direction,
                    size=p.volume,
                    entry_price=p.price_open,
                    stop_loss=p.sl,
                    take_profit=p.tp,
                    opened_at=datetime.fromtimestamp(p.time, tz=timezone.utc),
                )
            )
        return trades

    def _get_position(self, trade_id: str):
        positions = mt5.positions_get(ticket=int(trade_id))
        if not positions:
            raise RuntimeError(f"No open position found for trade {trade_id}")
        return positions[0]
