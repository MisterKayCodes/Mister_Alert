import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings

# 1. Initialize Bot & Dispatcher
# Bot Token will be loaded from settings (via .env)
bot = Bot(token=settings.telegram_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from .middlewares.permissions import SubscriptionMiddleware

# 2. Main Router Setup (Will be populated in next steps)
def setup_routers():
    from .routers import start, alerts, trades, calculators, admin, history, shop
    
    dp.include_router(admin.router)   # admin first — highest priority
    dp.include_router(start.router)
    dp.include_router(alerts.router)
    dp.include_router(trades.router)
    dp.include_router(calculators.router)
    dp.include_router(history.router)
    dp.include_router(shop.router)
    
    # Register Middlewares
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

async def start_bot():
    """Entry point for polling."""
    setup_routers()
    logging.info("Bot logic initialized.")
    await dp.start_polling(bot)
