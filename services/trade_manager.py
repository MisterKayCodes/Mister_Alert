from datetime import datetime
from decimal import Decimal
from typing import List

from data.database import AsyncSessionLocal
from data.repository import TradeRepository
from core.trades.tracker import TradeTracker
from core.events import PriceUpdateEvent, TakeProfitHitEvent, StopLossHitEvent
from services.event_bus import event_bus


class TradeManager:
    """
    Orchestrator for Open Trades.
    Listens to PriceUpdateEvent, fetches open trades, and publishes hits.
    """
    def __init__(self):
        self.tracker = TradeTracker()

    def setup(self):
        """Register with the event bus."""
        event_bus.subscribe(PriceUpdateEvent, self.handle_price_update)

    async def handle_price_update(self, event: PriceUpdateEvent):
        """
        When a new price comes in, evaluate all open trades for that symbol.
        """
        async with AsyncSessionLocal() as session:
            repo = TradeRepository(session)
            
            # 1. Fetch open trades from the "Vault"
            trades = await repo.get_open_trades()
            
            # 2. Filter for symbol
            symbol_trades = [t for t in trades if t.symbol.upper() == event.symbol.upper()]
            
            if not symbol_trades:
                return

            # 3. Use the "Brain" to evaluate
            new_events = self.tracker.evaluate(
                now=datetime.utcnow(),
                symbol=event.symbol,
                price=Decimal(str(event.price)),
                trades=symbol_trades
            )
            
            # 4. Use the "Nervous System" to publish triggers
            for hit_event in new_events:
                await event_bus.publish(hit_event)
                
                # Record result and close the trade in the Vault
                if isinstance(hit_event, TakeProfitHitEvent):
                    await repo.close_trade(hit_event.trade_id, "TAKE PROFIT HIT")
                elif isinstance(hit_event, StopLossHitEvent):
                    await repo.close_trade(hit_event.trade_id, "STOP LOSS HIT")
