import asyncio
import logging
import sys
import socket

# MONKEYPATCH: Force Windows to use IPv4 globally. 
# This bypasses the notorious 21-second IPv6 DNS timeout bug that freezes aiogram HTTP requests.
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

from loguru import logger

from services.price_service import PriceService
from services.alert_manager import AlertManager
from services.trade_manager import TradeManager
from bot.dispatcher import start_bot, bot
from bot.notification_handler import NotificationHandler

# 1. Structured Logging Setup
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")
logger.add("logs/system.log", rotation="1 week", retention="1 month", level="INFO")
logger.add("logs/error.log", rotation="1 week", retention="1 month", level="ERROR")

async def main():
    logger.info("🚀 Starting Mister Alert System...")

    # 1. Initialize Database Schema (Create missing tables)
    from data.database import init_models
    await init_models()
    logger.info("✅ Database schema initialized.")

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

    # 5. Initialize & Start SubscriptionService (Revenue Protection Layer)
    from services.subscription_service import SubscriptionService
    sub_service = SubscriptionService()
    
    # 6. Connect all components and run concurrently
    logger.info("🧠 Nervous System, Brain, and Eyes connected.")
    
    try:
        # Run Bot Polling, Price Polling, and Subscription Checks concurrently
        await asyncio.gather(
            start_bot(),          # Telegram Interface (Long Polling)
            price_service.start(), # Price Provider (Background Loop)
            sub_service.start()    # Subscription Monitor (Background Loop)
        )
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Shutting down...")
        await price_service.stop()
        await sub_service.stop()
    except Exception as e:
        logger.exception(f"Critical system failure: {e}")
    finally:
        logger.info("System halted.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
