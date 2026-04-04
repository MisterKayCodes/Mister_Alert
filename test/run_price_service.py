import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

# Force project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from data.database import engine, AsyncSessionLocal
from data.models import Base
from data.repository import UserRepository, AlertRepository, TradeRepository
from core.events import PriceUpdateEvent
from services.event_bus import event_bus
from services.price_service import PriceService

async def setup_db():
    print("Resetting Test Database Meta...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def test_price_service_orchestration():
    print("Starting PriceService Orchestration Test")
    print("==========================================")
    await setup_db()

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        trade_repo = TradeRepository(session)

        # Create Test Data
        user = await user_repo.create_user(telegram_id="999", username="test_eye")
        
        # Crypto alert
        await alert_repo.create_alert(user.id, "BTC", price_above=60000, price_below=None)
        # Forex trade
        await trade_repo.create_trade(user_id=user.id, symbol="EURUSD", entry_price=1.08, take_profit=1.10, stop_loss=1.05, position_size=1000, direction="LONG")
        
        print("Created Active Symbols in DB: BTC (Alert), EURUSD (Trade)")

    # 1. Initialize PriceService
    price_service = PriceService(interval=5)
    
    # 2. Trap for PriceUpdateEvents
    received_events = []
    async def price_trap(event):
        print(f"TRAP CAUGHT: PriceUpdateEvent for {event.symbol} -> {event.price}")
        received_events.append(event)
        
    event_bus.subscribe(PriceUpdateEvent, price_trap)

    # 3. Mock Providers to avoid real API hits
    with patch.object(price_service.binance, 'get_prices', new_callable=AsyncMock) as mock_binance, \
         patch.object(price_service.twelve_data, 'get_prices', new_callable=AsyncMock) as mock_twelve:
        
        # Define mock returns
        mock_binance.return_value = {"BTC": 60500.0}
        mock_twelve.return_value = {"EURUSD": 1.09}
        
        print("\nFiring single refresh_once()...")
        await price_service.refresh_once()
        
        # Verifications
        print("\nVerifying results...")
        if len(received_events) == 2:
            print("✅ SUCCESS: Received 2 price updates.")
        else:
            print(f"❌ FAILURE: Expected 2 updates, got {len(received_events)}")
            sys.exit(1)

        # Verify symbols
        symbols = {e.symbol for e in received_events}
        if "BTC" in symbols and "EURUSD" in symbols:
            print("✅ SUCCESS: Correct symbols (BTC, EURUSD) captured.")
        else:
            print(f"❌ FAILURE: Missing or incorrect symbols: {symbols}")
            sys.exit(1)

        # Verify Provider calls
        mock_binance.assert_called_once_with(["BTC"])
        print("✅ SUCCESS: Binance provider called for BTC.")
        
        mock_twelve.assert_called_once_with(["EURUSD"])
        print("✅ SUCCESS: TwelveData provider called for EURUSD.")

    print("\n🎉 PRICE SERVICE ORCHESTRATION TEST PASSED 100%")

if __name__ == "__main__":
    try:
        asyncio.run(test_price_service_orchestration())
    except Exception as e:
        print(f"💥 TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
