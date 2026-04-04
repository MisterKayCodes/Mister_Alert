from datetime import datetime
from decimal import Decimal
from typing import List, Protocol, Optional

from core.events import TakeProfitHitEvent, StopLossHitEvent, BaseEvent


class OpenTradeProvider(Protocol):
    """Protocol for trade objects the tracker can process."""
    id: int
    user_id: int
    symbol: str
    entry_price: Decimal
    take_profit: Optional[Decimal]
    stop_loss: Optional[Decimal]
    direction: str  # "LONG" or "SHORT"


class TradeTracker:
    def evaluate(
        self,
        *,
        now: datetime,
        symbol: str,
        price: Decimal,
        trades: List[OpenTradeProvider],
    ) -> List[BaseEvent]:
        """
        Evaluate a list of open trades against the current price.
        Returns a list of events to be published.
        """
        events = []

        for trade in trades:
            if trade.symbol.upper() != symbol.upper():
                continue

            direction = trade.direction.upper()

            if direction == "LONG":
                # Check Take Profit for LONG
                if trade.take_profit is not None and price >= trade.take_profit:
                    events.append(TakeProfitHitEvent(
                        user_id=trade.user_id,
                        trade_id=trade.id,
                        symbol=symbol.upper(),
                        price=float(price)
                    ))
                # Check Stop Loss for LONG
                elif trade.stop_loss is not None and price <= trade.stop_loss:
                    events.append(StopLossHitEvent(
                        user_id=trade.user_id,
                        trade_id=trade.id,
                        symbol=symbol.upper(),
                        price=float(price)
                    ))

            elif direction == "SHORT":
                # Check Take Profit for SHORT
                if trade.take_profit is not None and price <= trade.take_profit:
                    events.append(TakeProfitHitEvent(
                        user_id=trade.user_id,
                        trade_id=trade.id,
                        symbol=symbol.upper(),
                        price=float(price)
                    ))
                # Check Stop Loss for SHORT
                elif trade.stop_loss is not None and price >= trade.stop_loss:
                    events.append(StopLossHitEvent(
                        user_id=trade.user_id,
                        trade_id=trade.id,
                        symbol=symbol.upper(),
                        price=float(price)
                    ))

        return events
