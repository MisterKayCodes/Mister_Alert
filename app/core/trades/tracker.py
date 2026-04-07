from datetime import datetime
from decimal import Decimal
from typing import List, Protocol, Optional

from app.core.events import TakeProfitHitEvent, StopLossHitEvent, BaseEvent


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
            if trade.symbol.upper() == symbol.upper():
                hit_event = self._evaluate_trade(trade, price)
                if hit_event:
                    events.append(hit_event)

        return events

    def _evaluate_trade(self, trade: OpenTradeProvider, price: Decimal) -> Optional[BaseEvent]:
        """Detect if a single trade has hit TP or SL."""
        direction = trade.direction.upper()
        
        if direction == "LONG":
            if trade.take_profit is not None and price >= trade.take_profit:
                return TakeProfitHitEvent(
                    user_id=trade.user_id, trade_id=trade.id, 
                    symbol=trade.symbol.upper(), price=float(price)
                )
            if trade.stop_loss is not None and price <= trade.stop_loss:
                return StopLossHitEvent(
                    user_id=trade.user_id, trade_id=trade.id, 
                    symbol=trade.symbol.upper(), price=float(price)
                )
                
        if direction == "SHORT":
            if trade.take_profit is not None and price <= trade.take_profit:
                return TakeProfitHitEvent(
                    user_id=trade.user_id, trade_id=trade.id, 
                    symbol=trade.symbol.upper(), price=float(price)
                )
            if trade.stop_loss is not None and price >= trade.stop_loss:
                return StopLossHitEvent(
                    user_id=trade.user_id, trade_id=trade.id, 
                    symbol=trade.symbol.upper(), price=float(price)
                )
        return None
