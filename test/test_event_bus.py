import pytest
import asyncio
from services.event_bus import event_bus, EventBus
from core.events import PriceUpdateEvent

@pytest.fixture
def isolated_bus():
    return EventBus()

@pytest.mark.asyncio
async def test_event_bus_sync_handler(isolated_bus):
    received = []
    
    def handler(event):
        received.append(event)
        
    isolated_bus.subscribe(PriceUpdateEvent, handler)
    
    event = PriceUpdateEvent(symbol="BTC", price=50000.0)
    await isolated_bus.publish(event)
    
    assert len(received) == 1
    assert received[0].symbol == "BTC"
    assert received[0].price == 50000.0

@pytest.mark.asyncio
async def test_event_bus_async_handler(isolated_bus):
    received = []
    
    async def async_handler(event):
        await asyncio.sleep(0.01)
        received.append(event)
        
    isolated_bus.subscribe(PriceUpdateEvent, async_handler)
    
    event = PriceUpdateEvent(symbol="ETH", price=2000.0)
    await isolated_bus.publish(event)
    
    assert len(received) == 1
    assert received[0].symbol == "ETH"
    assert received[0].price == 2000.0
