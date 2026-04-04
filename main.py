import asyncio
import logging
import sys
from loguru import logger

from services.price_service import PriceService
from services.alert_manager import AlertManager
from services.trade_manager import TradeManager
from bot.dispatcher import start_bot, bot
from bot.notification_handler import NotificationHandler

# 1. Structured Logging Setup
logging.basicConfig(level=logging.INFO)
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")

async def main():
    logger.info("🚀 Starting Mister Alert System...")

    # 2. Seed default settings & payment methods (idempotent — safe on every restart)
    from data.seeder import seed_defaults
    await seed_defaults()
    logger.info("✅ Database seeded.")

    # 2. Initialize Core Managers (Service Layer)
    alert_mgr = AlertManager()
    alert_mgr.setup()
    
    trade_mgr = TradeManager()
    trade_mgr.setup()
    
    # 3. Initialize Notification Handler (Bridge Layer)
    notifier = NotificationHandler(bot)
    notifier.setup()

    # 4. Initialize & Start PriceService (Provider Layer)
    price_service = PriceService()
    
    # 5. Connect all components and run concurrently
    logger.info("🧠 Nervous System, Brain, and Eyes connected.")
    
    try:
        # Run Bot Polling and Price Polling concurrently
        await asyncio.gather(
            start_bot(),          # Telegram Interface (Long Polling)
            price_service.start() # Price Provider (Background Loop)
        )
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Shutting down...")
        await price_service.stop()
    except Exception as e:
        logger.exception(f"Critical system failure: {e}")
    finally:
        logger.info("System halted.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
