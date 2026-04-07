import pytest
from datetime import datetime
from decimal import Decimal
from app.core.alerts.engine import AlertEngine
from dataclasses import dataclass

@dataclass
class MockAlert:
    id: int
    user_id: int
    symbol: str
    price_above: Decimal = None
    price_below: Decimal = None

def test_alert_engine_triggers_above():
    engine = AlertEngine()
    now = datetime.utcnow()
    
    alerts = [
        MockAlert(id=1, user_id=10, symbol="BTC", price_above=Decimal("50000"))
    ]
    
    # Should not trigger
    events = engine.evaluate(now=now, symbol="BTC", price=Decimal("49000"), alerts=alerts)
    assert len(events) == 0
    
    # Should trigger
    events = engine.evaluate(now=now, symbol="BTC", price=Decimal("50000"), alerts=alerts)
    assert len(events) == 1
    assert events[0].alert_id == 1
    assert events[0].symbol == "BTC"
    
def test_alert_engine_triggers_below():
    engine = AlertEngine()
    now = datetime.utcnow()
    
    alerts = [
        MockAlert(id=2, user_id=20, symbol="ETH", price_below=Decimal("2000"))
    ]
    
    # Should not trigger
    events = engine.evaluate(now=now, symbol="ETH", price=Decimal("2100"), alerts=alerts)
    assert len(events) == 0
    
    # Should trigger
    events = engine.evaluate(now=now, symbol="ETH", price=Decimal("1999"), alerts=alerts)
    assert len(events) == 1
    assert events[0].alert_id == 2
    assert events[0].symbol == "ETH"
