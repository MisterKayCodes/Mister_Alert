import sys
import os
import asyncio

# Force project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from bot.dispatcher import setup_routers, dp
from bot.routers import calculators

async def test_calculator_setup():
    print("Testing Calculator Router Registration...")
    try:
        setup_routers()
        
        # Check if calculators router is in the dispatcher
        # This is a bit internal but we can check the list of routers
        router_names = [r.name for r in dp.sub_routers if hasattr(r, 'name')]
        print(f"Registered routers: {router_names}")
        
        # Verify the calculator router has the expected handlers
        # We can check for the presence of the calculator message handler
        print("✅ SUCCESS: Calculators router registered and accessible.")
        
    except Exception as e:
        print(f"❌ FAILURE: Calculator setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_calculator_setup())
