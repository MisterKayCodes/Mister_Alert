from datetime import datetime
from decimal import Decimal
from typing import List, Protocol, Optional

from app.core.events import AlertTriggeredEvent, AlertExpiredEvent, BaseEvent


class PriceAlertProvider(Protocol):
    """Protocol for alert objects the engine can process."""
    id: int
    user_id: int
    symbol: str
    price_above: Optional[Decimal]
    price_below: Optional[Decimal]


class AlertEngine:
    def evaluate(
        self,
        *,
        now: datetime,
        symbol: str,
        price: Decimal,
        alerts: List[PriceAlertProvider],
    ) -> List[BaseEvent]:
        """
        Evaluate a list of alerts against the current price.
        Returns a list of events to be published.
        """
        events = []

        for alert in alerts:
            if alert.symbol.upper() != symbol.upper():
                continue

            # Check Price Above
            if alert.price_above is not None and price >= alert.price_above:
                events.append(AlertTriggeredEvent(
                    user_id=alert.user_id,
                    alert_id=alert.id,
                    symbol=symbol.upper(),
                    price=float(price),
                    target_price=float(alert.price_above)
                ))

            # Check Price Below
            elif alert.price_below is not None and price <= alert.price_below:
                events.append(AlertTriggeredEvent(
                    user_id=alert.user_id,
                    alert_id=alert.id,
                    symbol=symbol.upper(),
                    price=float(price),
                    target_price=float(alert.price_below)
                ))

        return events
