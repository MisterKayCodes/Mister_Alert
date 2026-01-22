import asyncio
import logging
from typing import List, Dict, Optional
from core.events import PriceUpdateEvent, AlertTriggeredEvent
from services.event_bus import event_bus

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self):
        # Dict key = symbol, value = list of Alert objects
        self.active_alerts: Dict[str, List] = {}
        self._lock = asyncio.Lock()

    def add_alert(self, alert):
        """Add alert to active alerts cache"""
        symbol = alert.symbol.upper()
        if symbol not in self.active_alerts:
            self.active_alerts[symbol] = []
        self.active_alerts[symbol].append(alert)
        logger.info(f"Added alert {alert.id} for symbol {symbol}")

    def remove_alert(self, symbol: str, alert_id: int):
        symbol = symbol.upper()
        if symbol in self.active_alerts:
            self.active_alerts[symbol] = [a for a in self.active_alerts[symbol] if a.id != alert_id]
            if not self.active_alerts[symbol]:
                del self.active_alerts[symbol]

    async def on_price_update(self, event: PriceUpdateEvent):
        symbol = event.symbol.upper()
        price = float(event.price)  # Ensure float for comparisons

        async with self._lock:
            alerts = self.active_alerts.get(symbol, [])
            if not alerts:
                return

            to_remove = []

            for alert in alerts:
                triggered, target = self._check_alert_trigger(alert, price)

                if triggered:
                    try:
                        logger.info(f"Triggering alert {alert.id} for user {alert.user_id}")
                        await event_bus.publish(
                            AlertTriggeredEvent(
                                user_id=alert.user_id,
                                alert_id=alert.id,
                                symbol=alert.symbol,
                                price=price,
                                target_price=target
                            )
                        )
                        to_remove.append(alert.id)
                    except Exception as e:
                        logger.error(f"Failed to publish alert trigger {alert.id}: {e}")

            # Clean up triggered alerts from memory cache
            for alert_id in to_remove:
                self.remove_alert(alert_id)

    def _check_alert_trigger(self, alert, price: float) -> tuple[bool, Optional[float]]:
        """Return (triggered, target_price)"""
        if alert.price_above is not None and price >= float(alert.price_above):
            return True, float(alert.price_above)
        if alert.price_below is not None and price <= float(alert.price_below):
            return True, float(alert.price_below)
        return False, None
