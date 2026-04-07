import sys
import os
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.alerts.engine import AlertEngine
from app.core.events import AlertTriggeredEvent

@dataclass
class MockAlert:
    id: int
    user_id: int
    symbol: str
    price_above: Optional[Decimal] = None
    price_below: Optional[Decimal] = None

def test_alert_engine():
    engine = AlertEngine()
    now = datetime.utcnow()
    
    alerts = [
        MockAlert(id=1, user_id=101, symbol="BTCUSD", price_above=Decimal("65000")),
        MockAlert(id=2, user_id=101, symbol="BTCUSD", price_below=Decimal("60000")),
        MockAlert(id=3, user_id=102, symbol="ETHUSD", price_above=Decimal("3500")),
    ]

    print("--- Running AlertEngine Tests ---")

    # Case 1: BTC Price hits price_above
    results = engine.evaluate(now=now, symbol="BTCUSD", price=Decimal("65100"), alerts=alerts)
    assert len(results) == 1
    assert isinstance(results[0], AlertTriggeredEvent)
    assert results[0].alert_id == 1
    assert results[0].target_price == 65000.0
    print("✅ Case 1 Passed: BTC Price Above triggered")

    # Case 2: BTC Price hits price_below
    results = engine.evaluate(now=now, symbol="BTCUSD", price=Decimal("59900"), alerts=alerts)
    assert len(results) == 1
    assert isinstance(results[0], AlertTriggeredEvent)
    assert results[0].alert_id == 2
    assert results[0].target_price == 60000.0
    print("✅ Case 2 Passed: BTC Price Below triggered")

    # Case 3: BTC Price between alerts
    results = engine.evaluate(now=now, symbol="BTCUSD", price=Decimal("62000"), alerts=alerts)
    assert len(results) == 0
    print("✅ Case 3 Passed: No alerts triggered for BTC in range")

    # Case 4: ETH Price hits price_above
    results = engine.evaluate(now=now, symbol="ETHUSD", price=Decimal("3600"), alerts=alerts)
    assert len(results) == 1
    assert results[0].alert_id == 3
    print("✅ Case 4 Passed: ETH alert triggered")

    # Case 5: Symbol mismatch
    results = engine.evaluate(now=now, symbol="SOLUSD", price=Decimal("150"), alerts=alerts)
    assert len(results) == 0
    print("✅ Case 5 Passed: No alerts for unknown symbol")

    print("\n🎉 ALL ALERT ENGINE TESTS PASSED 100%")

if __name__ == "__main__":
    try:
        test_alert_engine()
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"💥 ERROR: {e}")
        sys.exit(1)
