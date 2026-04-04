from datetime import datetime
from decimal import Decimal
from typing import List

from data.database import AsyncSessionLocal
from data.repository import AlertRepository
from core.alerts.engine import AlertEngine
from core.events import PriceUpdateEvent
from services.event_bus import event_bus


class AlertManager:
    """
    Orchestrator for Price Alerts.
    Listens to PriceUpdateEvent, fetches active alerts, and publishes hits.
    """
    def __init__(self):
        self.engine = AlertEngine()

    def setup(self):
        """Register with the event bus."""
        event_bus.subscribe(PriceUpdateEvent, self.handle_price_update)

    async def handle_price_update(self, event: PriceUpdateEvent):
        """
        When a new price comes in, evaluate all active alerts for that symbol.
        """
        async with AsyncSessionLocal() as session:
            repo = AlertRepository(session)
            
            # 1. Fetch active alerts from the "Vault"
            alerts = await repo.get_active_alerts()
            
            # 2. Filter for the symbol of the current event
            symbol_alerts = [a for a in alerts if a.symbol.upper() == event.symbol.upper()]
            
            if not symbol_alerts:
                return

            # 3. Use the "Brain" to evaluate
            # repo.Alert objects have Numeric->Decimal fields, so they are compatible with engine.
            new_events = self.engine.evaluate(
                now=datetime.utcnow(),
                symbol=event.symbol,
                price=Decimal(str(event.price)),
                alerts=symbol_alerts
            )
            
            # 4. Use the "Nervous System" to publish triggers
            for triggered_event in new_events:
                await event_bus.publish(triggered_event)
                
                # Deactivate the alert once triggered to prevent duplicate hits
                await repo.deactivate_alert(triggered_event.alert_id)
