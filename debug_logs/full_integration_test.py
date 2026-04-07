import sys
import os
import asyncio
from datetime import datetime
from decimal import Decimal

from app.data.database import engine, AsyncSessionLocal
from app.data.models import Base
from app.data.repository import UserRepository, AlertRepository, TradeRepository
from app.core.events import PriceUpdateEvent, AlertTriggeredEvent, TakeProfitHitEvent
from app.services.event_bus import event_bus
from app.services.alert_manager import AlertManager
from app.services.trade_manager import TradeManager

async def setup_db():
    print("🛠️ Resetting Test Database Meta...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def test_full_cycle():
    print("🚀 Starting Full-Round System Integration Test")
    print("============================================")
    await setup_db()

    # 1. Setup Data in "Vault" (Memory Layer)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        trade_repo = TradeRepository(session)

        # Create Test User
        user = await user_repo.create_user(telegram_id="12345", username="tester")
        print(f"👤 Created User: {user.username} (ID: {user.id})")
        
        # Create an alert for BTC > 60,000
        await alert_repo.create_alert(user.id, "BTCUSD", price_above=60000, price_below=None)
        print("🔔 Created Alert: BTCUSD > 60,000")
        
        # Create a Long trade for ETH: Entry 2000, TP 2500, SL 1500
        await trade_repo.create_trade(user_id=user.id, symbol="ETHUSD", entry_price=2000, take_profit=2500, stop_loss=1500, position_size=1.0)
        print("📈 Created Trade: LONG ETHUSD (TP: 2500, SL: 1500)")

    # 2. Initialize "Nervous System" Managers (Service Layer)
    alert_mgr = AlertManager()
    alert_mgr.setup()
    trade_mgr = TradeManager()
    trade_mgr.setup()
    print("🧠 Managers initialized and subscribed to EventBus.")

    # 3. Traps for events (Verification Layer)
    triggered_alerts = []
    hit_trades = []

    async def alert_trap(event): 
        print(f"🎯 TRAP CAUGHT: AlertTriggeredEvent for {event.symbol} at {event.price}")
        triggered_alerts.append(event)
        
    async def trade_trap(event): 
        print(f"🎯 TRAP CAUGHT: TakeProfitHitEvent for {event.symbol} at {event.price}")
        hit_trades.append(event)

    event_bus.subscribe(AlertTriggeredEvent, alert_trap)
    event_bus.subscribe(TakeProfitHitEvent, trade_trap)

    # 4. Simulate Price Updates from "Eyes" (Provider Layer)
    print("\n📡 PUBLISHING: BTCUSD @ 60,100")
    await event_bus.publish(PriceUpdateEvent(symbol="BTCUSD", price=60100))
    
    print("📡 PUBLISHING: ETHUSD @ 2,550")
    await event_bus.publish(PriceUpdateEvent(symbol="ETHUSD", price=2550))

    # Give async tasks a moment to process everything
    await asyncio.sleep(1)

    # 5. Final Verifications
    print("\n🧪 Final Logic Verification")
    print("---------------------------")
    
    error_count = 0

    if len(triggered_alerts) == 1:
        print("✅ SUCCESS: AlertTriggeredEvent verified.")
    else:
        print(f"❌ FAILURE: Expected 1 alert hit, got {len(triggered_alerts)}")
        error_count += 1

    if len(hit_trades) == 1:
        print("✅ SUCCESS: TakeProfitHitEvent verified.")
    else:
        print(f"❌ FAILURE: Expected 1 trade hit, got {len(hit_trades)}")
        error_count += 1

    # Check Database state (Vault Persistence & Idempotency)
    async with AsyncSessionLocal() as session:
        alert_repo = AlertRepository(session)
        trade_repo = TradeRepository(session)
        
        active_alerts = await alert_repo.get_active_alerts()
        open_trades = await trade_repo.get_open_trades()
        
        if len(active_alerts) == 0:
            print("✅ SUCCESS: Alert correctly marked inactive in DB.")
        else:
            print(f"❌ FAILURE: Alert still active in DB! Count: {len(active_alerts)}")
            error_count += 1

        if len(open_trades) == 0:
            print("✅ SUCCESS: Trade correctly marked closed in DB.")
        else:
            print(f"❌ FAILURE: Trade still open in DB! Count: {len(open_trades)}")
            error_count += 1

    if error_count == 0:
        print("\n🎉 ALL ROUND SYSTEM INTEGRATION TEST PASSED 100%")
    else:
        print(f"\n🛑 TEST FAILED WITH {error_count} ERRORS")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_full_cycle())
    except Exception as e:
        print(f"💥 SYSTEM CRASHED DURING TEST: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
