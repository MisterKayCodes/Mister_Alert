import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings

# 1. Initialize Bot & Dispatcher
bot = Bot(token=settings.telegram_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from .middlewares.permissions import SubscriptionMiddleware
from .middlewares.throttle import ThrottleMiddleware

# 2. Main Router Setup (Will be populated in next steps)
def setup_routers():
    from .routers import start, alerts, trades, calculators, admin, history, shop, support
    
    dp.include_router(admin.router)   # admin first — highest priority
    dp.include_router(support.router) # support high priority too
    dp.include_router(start.router)
    dp.include_router(alerts.router)
    dp.include_router(trades.router)
    dp.include_router(calculators.router)
    dp.include_router(history.router)
    dp.include_router(shop.router)
    
    # ThrottleMiddleware FIRST — drops duplicate taps before any DB call
    throttle = ThrottleMiddleware()
    dp.message.middleware(throttle)
    dp.callback_query.middleware(throttle)

    # SubscriptionMiddleware SECOND — gates alert creation
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

@dp.startup()
async def on_startup(bot: Bot):
    print("\n" + "="*55)
    print("🚀 THE BOT IS NOW FULLY RUNNING! YOU CAN CLICK /start")
    print("="*55 + "\n")

async def start_bot():
    """Entry point for polling."""
    setup_routers()
    logging.info("Bot logic initialized.")
    # Drop pending updates so offline button spam doesn't crowd SQLite on boot
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
