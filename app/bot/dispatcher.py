import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings

# 1. Initialize Bot & Dispatcher
bot = Bot(token=settings.telegram_token)

storage = MemoryStorage()
if settings.redis_url:
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis
        import asyncio

        redis_instance = Redis.from_url(settings.redis_url, socket_timeout=5)
        storage = RedisStorage(redis_instance)
        logging.info(f"Using Redis storage: {settings.redis_url}")
    except ImportError:
        logging.warning("Redis storage requested but 'redis' package not found. Falling back to Memory.")
    except Exception as e:
        logging.warning(f"Failed to initialize Redis ({e}). Falling back to Memory storage.")
else:
    logging.info("Using Memory storage (no redis_url provided).")

dp = Dispatcher(storage=storage)

from .middlewares.permissions import SubscriptionMiddleware
from .middlewares.throttle import ThrottleMiddleware
from .middlewares.idempotency import IdempotencyMiddleware
from .middlewares.rate_limit import RateLimitMiddleware

# 2. Main Router Setup (Will be populated in next steps)
def setup_routers():
    from .routers import start, alerts, trades, calculators, history, shop, support, recovery
    from .routers.admin import dashboard_router, users_router, economy_router, settings_router, support_router as admin_support_router, vouchers_router, stats_router
    from .routers.marketing.dashboard import router as marketing_router
    
    dp.include_router(marketing_router)
    dp.include_router(dashboard_router)
    dp.include_router(users_router)
    dp.include_router(economy_router)
    dp.include_router(settings_router)
    dp.include_router(admin_support_router)
    dp.include_router(vouchers_router)
    dp.include_router(stats_router)
    dp.include_router(support.router) # support high priority too
    dp.include_router(start.router)
    dp.include_router(alerts.router)
    dp.include_router(trades.router)
    dp.include_router(calculators.router)
    dp.include_router(history.router)
    dp.include_router(shop.router)
    dp.include_router(recovery.router) # God Mode fallback listener
    
    # 1. Idempotency (Outer-most layer for the update event)
    idemp = IdempotencyMiddleware()
    dp.update.middleware(idemp)

    # 2. Rate Limit
    rate_limiter = RateLimitMiddleware(limit=5, window_seconds=5)
    dp.message.middleware(rate_limiter)
    dp.callback_query.middleware(rate_limiter)

    # 3. ThrottleMiddleware — drops duplicate taps before any DB call
    throttle = ThrottleMiddleware()
    dp.message.middleware(throttle)
    dp.callback_query.middleware(throttle)

    # 4. SubscriptionMiddleware — gates alert creation
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
