import sys
import os
import asyncio

# Force project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from bot.dispatcher import setup_routers, dp
from bot.notification_handler import NotificationHandler
from bot.dispatcher import bot

async def test_bot_setup():
    print("Testing Bot Setup & Router Registration...")
    try:
        setup_routers()
        print("✅ SUCCESS: Routers registered.")
        
        notifier = NotificationHandler(bot)
        notifier.setup()
        print("✅ SUCCESS: NotificationHandler setup.")
        
        print("\nAll bot components initialized correctly (Imports Verified).")
    except Exception as e:
        print(f"❌ FAILURE: Bot setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_bot_setup())
