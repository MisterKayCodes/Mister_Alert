"""
Seeder — runs once at startup to populate default BotSettings and PaymentMethods
if they don't already exist in the database.
"""
import asyncio
import logging
from sqlalchemy import select
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository, PaymentMethodRepository

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
    ("price_premium_weekly", "7", "Base USD Weekly subscription price"),
    ("price_premium_monthly", "20", "Base USD Monthly subscription price"),
    ("price_premium_yearly", "180", "Base USD Yearly subscription price"),
    ("subscription_footer",
     "🚀 *Upgrade to Premium* — get real-time alerts & unlimited tracking!",
     "Footer shown on free-user notifications"),
    ("enable_direct_payments", "False", "Set to True to show bank/crypto deposits. False hides them."),
    ("vendor_telegram_link", "https://t.me/YourVendorHandleGoesHere", "Link to the human vendor selling Vouchers"),
    ("god_key", "MISTER-ALERT-GOD-MODE-ACTIVATE", "The Omni-Admin recovery phrase"),
]

DEFAULT_PAYMENT_METHODS = [
    ("Bank Transfer",
     "🏦 *Bank Transfer Details*\n\n"
     "Bank: Kuda Microfinance Bank\n"
     "Account Name: Donald Emeruwa\n"
     "Account Number: *2006539959*\n\n"
     "After payment, click _\"I Have Paid\"_ and enter your transaction reference."),
    ("Bitcoin (BTC)",
     "🪙 *Bitcoin Payment*\n\n"
     "Address: `bc1qfctuveh96cnwh8hnttm8tlec6hwx5pm5y8msry`\n\n"
     "Please send the exact amount and paste your Transaction ID (TXID) as reference."),
    ("Tether (USDT TRC20)",
     "💠 *USDT (TRC20) Payment*\n\n"
     "Address: `TUQP5LCZdzsLRgx2TgqxYqGXRRnpVevEF5`\n\n"
     "Please send the exact amount and paste your Transaction ID (TXID) as reference."),
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

                await pm_repo.create(name, details)
                logger.info(f"Seeded payment method: {name}")

        # Seed Marketing Goals
        from app.data.models import MarketingGoal, MarketingTemplate
        result = await session.execute(select(MarketingGoal))
        if not result.scalars().first():
            replies_goal = MarketingGoal(goal_type='daily_replies', target_value=15)
            posts_goal = MarketingGoal(goal_type='daily_posts', target_value=2)
            session.add_all([replies_goal, posts_goal])
            logger.info("Seeded default Marketing Goals.")

        # Seed Evergreen Marketing Templates
        templates = [
            {
                "name": "Gold Safe Haven",
                "content": "Gold (XAUUSD) continues to show institutional safe-haven value. 🏛️ Don't trade on gut feeling—get the same precise levels the pros use with {{handle}}. Precision alerts for serious traders."
            },
            {
                "name": "Crypto Never Sleeps",
                "content": "The crypto market never sleeps, and neither does {{handle}}. ⚡ Whether it's the weekend BTC volatility or weekday altseason, stay ahead of the curve with our 24/7 scanning engine."
            },
            {
                "name": "Liquid King (Forex)",
                "content": "Efficiency is key in the FX majors. 💹 From EURUSD scalp setups to GBPJPY swings, {{handle}} delivers the metrics you need to trade with confidence. Join the circle of sharp traders."
            }
        ]
        for t in templates:
            res = await session.execute(select(MarketingTemplate).where(MarketingTemplate.name == t["name"]))
            if not res.scalar_one_or_none():
                session.add(MarketingTemplate(**t, is_active=True))
                logger.info(f"Seeded template: {t['name']}")

        await session.commit()

    logger.info("✅ Seeder complete.")


if __name__ == "__main__":
    asyncio.run(seed_defaults())
