import sys
import os
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.trades.tracker import TradeTracker
from app.core.events import TakeProfitHitEvent, StopLossHitEvent

@dataclass
class MockTrade:
    id: int
    user_id: int
    symbol: str
    entry_price: Decimal
    take_profit: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    direction: str = "LONG"

def test_trade_tracker():
    tracker = TradeTracker()
    now = datetime.utcnow()
    
    trades = [
        # Long BTC: Entry 50,000, TP 55,000, SL 45,000
        MockTrade(id=1, user_id=1, symbol="BTCUSD", entry_price=Decimal("50000"), take_profit=Decimal("55000"), stop_loss=Decimal("45000"), direction="LONG"),
        # Short BTC: Entry 50,000, TP 45,000, SL 55,000
        MockTrade(id=2, user_id=1, symbol="BTCUSD", entry_price=Decimal("50000"), take_profit=Decimal("45000"), stop_loss=Decimal("55000"), direction="SHORT"),
    ]

    print("--- Running TradeTracker Tests ---")

    # Case 1: Long hits Take Profit
    results = tracker.evaluate(now=now, symbol="BTCUSD", price=Decimal("55100"), trades=trades)
    assert any(isinstance(r, TakeProfitHitEvent) and r.trade_id == 1 for r in results)
    print("✅ Case 1 Passed: Long BTC TP hit")

    # Case 2: Long hits Stop Loss
    results = tracker.evaluate(now=now, symbol="BTCUSD", price=Decimal("44900"), trades=trades)
    assert any(isinstance(r, StopLossHitEvent) and r.trade_id == 1 for r in results)
    print("✅ Case 2 Passed: Long BTC SL hit")

    # Case 3: Short hits Take Profit
    results = tracker.evaluate(now=now, symbol="BTCUSD", price=Decimal("44900"), trades=trades)
    assert any(isinstance(r, TakeProfitHitEvent) and r.trade_id == 2 for r in results)
    print("✅ Case 3 Passed: Short BTC TP hit")

    # Case 4: Short hits Stop Loss
    results = tracker.evaluate(now=now, symbol="BTCUSD", price=Decimal("55100"), trades=trades)
    assert any(isinstance(r, StopLossHitEvent) and r.trade_id == 2 for r in results)
    print("✅ Case 4 Passed: Short BTC SL hit")

    # Case 5: Between TP / SL
    results = tracker.evaluate(now=now, symbol="BTCUSD", price=Decimal("50100"), trades=trades)
    assert len(results) == 0
    print("✅ Case 5 Passed: No alerts for BTC trades in range")

    print("\n🎉 ALL TRADE TRACKER TESTS PASSED 100%")

if __name__ == "__main__":
    try:
        test_trade_tracker()
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"💥 ERROR: {e}")
        sys.exit(1)
