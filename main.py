import asyncio
import logging
import sys
import socket
import os
import subprocess

# MONKEYPATCH: Force Windows to use IPv4 globally. 
# This bypasses the notorious 21-second IPv6 DNS timeout bug that freezes aiogram HTTP requests.
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

from loguru import logger

from app.services.price_service import PriceService
from app.services.alert_manager import AlertManager
from app.services.trade_manager import TradeManager
from app.bot.dispatcher import start_bot, bot
from app.bot.notification_handler import NotificationHandler

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

def run_preflight_checks():
    """
    Ensures the codebase adheres to the Digital Constitution and 
    Architectural standards before allowing the bot to boot.
    """
    logger.info("🔍 Running pre-flight architecture and constitution checks...")
    
    scripts_dir = os.path.join("app", "infrastructure", "checks")
    checks = [
        ("Architecture", "architecture_inspector.py"),
        ("Constitution", "dev_constitution.py")
    ]
    
    for name, script in checks:
        script_path = os.path.join(scripts_dir, script)
        if not os.path.exists(script_path):
            logger.warning(f"⚠️ {name} check skipped: {script_path} not found.")
            continue
            
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"❌ {name} Check Failed!")
            print("\n" + "="*50)
            print(f"VIOLATION DETECTED IN {script.upper()}")
            print("="*50)
            print(result.stdout)
            print(result.stderr)
            print("="*50 + "\n")
            logger.critical("System boot aborted due to rule violations.")
            sys.exit(1)
            
    logger.info("✅ Pre-flight checks passed. System is Senior-grade.")


async def main():
    # 0. Rule Enforcement (Fail Fast)
    run_preflight_checks()
    
    logger.info("🚀 Starting Mister Alert System...")

    # 1. Initialize Database Schema (Create missing tables)
    from app.data.database import init_models
    await init_models()
    logger.info("✅ Database schema initialized.")

    # 2. Seed default settings & payment methods (idempotent — safe on every restart)
    from app.data.seeder import seed_defaults
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
    from app.services.subscription_service import SubscriptionService
    sub_service = SubscriptionService()

    # 6. Initialize & Start Marketing Engine (Growth Layer)
    try:
        from app.services.userbot_client import userbot_client
        from app.services.marketing_engine import MarketingEngine
        from app.data.economy_repository import SettingsRepository
        
        mme = MarketingEngine(bot=bot) # Pass bot instance (DI)
        await mme.setup()

        # Load session string and credentials from DB if available, otherwise fallback to .env
        async with AsyncSessionLocal() as session:
            settings_repo = SettingsRepository(session)
            db_session = await settings_repo.get("telegram_session_string")
            db_api_id = await settings_repo.get("telegram_api_id")
            db_api_hash = await settings_repo.get("telegram_api_hash")
            
        # Convert db_api_id string to int if it exists
        api_id_int = int(db_api_id) if db_api_id and db_api_id.isdigit() else None
        
        # We start these as background tasks to keep the gather loop clean
        userbot_task = userbot_client.start(
            session_string=db_session,
            api_id=api_id_int,
            api_hash=db_api_hash
        )
        report_task = mme.start_reporting_logic()
        
        # Add to the gather list below if initialization was successful
        logger.success("🚀 Marketing Growth Layer initialized.")
    except Exception as e:
        logger.error(f"⚠️ Marketing Engine failed to start: {e}. Bot core still operational.")
        userbot_task = asyncio.sleep(0) # No-op
        report_task = asyncio.sleep(0) # No-op

    # 7. Connect all components and run concurrently
    logger.info("🧠 Nervous System, Brain, Eyes, and Marketing Engine connected.")
    
    try:
        # Run Bot Polling, Price Polling, and Subscription Checks concurrently
        await asyncio.gather(
            start_bot(),          # Telegram Interface (Long Polling)
            price_service.start(), # Price Provider (Background Loop)
            sub_service.start(),    # Subscription Monitor (Background Loop)
            userbot_task,          # UserBot (Background Listener)
            report_task            # Marketing Stats Scheduler
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
        logger.info("Bot manually stopped by user.")
