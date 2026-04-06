"""
Seeder — runs once at startup to populate default BotSettings and PaymentMethods
if they don't already exist in the database.
"""
import asyncio
import logging
from data.database import AsyncSessionLocal
from data.economy_repository import SettingsRepository, PaymentMethodRepository

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = [
    ("welcome_text",
     "👋 Welcome to *Mister Alert* — your personal trading companion!\n\n"
     "I'll monitor the markets 24/7 and notify you the instant your price targets are hit. "
     "Use the menu below to get started.",
     "Bot welcome message shown on /start"),
    ("alert_limit_free", "3", "Max alerts for free users"),
    ("alert_limit_premium", "50", "Max alerts for premium users"),
    ("credits_per_alert", "1", "Credits deducted per alert created"),
    ("price_credits_10", "5", "Base USD Price for 10 credits"),
    ("price_premium_monthly", "20", "Base USD Monthly subscription price"),
    ("price_premium_yearly", "180", "Base USD Yearly subscription price"),
    ("subscription_footer",
     "🚀 *Upgrade to Premium* — get real-time alerts & unlimited tracking!",
     "Footer shown on free-user notifications"),
]

DEFAULT_PAYMENT_METHODS = [
    ("Bank Transfer",
     "🏦 *Bank Transfer Details*\n\n"
     "Bank: Kuda Microfinance Bank\n"
     "Account Name: Donald Emeruwa\n"
     "Account Number: *2006539959*\n\n"
     "After payment, click _\"I Have Paid\"_ and enter your transaction reference."),
]


async def seed_defaults():
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        pm_repo = PaymentMethodRepository(session)

        for key, value, description in DEFAULT_SETTINGS:
            existing = await settings_repo.get(key)
            if existing is None:
                await settings_repo.set(key, value, description)
                logger.info(f"Seeded setting: {key}")

        for name, details in DEFAULT_PAYMENT_METHODS:
            all_pms = await pm_repo.get_all()
            names = [p.name for p in all_pms]
            if name not in names:
                await pm_repo.create(name, details)
                logger.info(f"Seeded payment method: {name}")

    logger.info("✅ Seeder complete.")


if __name__ == "__main__":
    asyncio.run(seed_defaults())
