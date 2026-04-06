import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from data.database import AsyncSessionLocal
from data.models import User
from bot.dispatcher import bot
from utils.fmt import warning

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Background worker that monitors premium expirations.
    Ensures that when a user's time is up, they are downgraded automatically.
    """
    def __init__(self, check_interval_seconds: int = 3600):
        self.check_interval = check_interval_seconds
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("SubscriptionService started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SubscriptionService stopped.")

    async def _run_loop(self):
        while self._running:
            try:
                await self.check_expirations()
            except Exception as e:
                logger.exception(f"SubscriptionService error during check: {e}")
            
            await asyncio.sleep(self.check_interval)

    async def check_expirations(self):
        """Find and downgrade users whose premium has expired."""
        now = datetime.now(timezone.utc)
        
        async with AsyncSessionLocal() as session:
            # 1. Find all premium users whose time has passed
            query = select(User).where(
                User.is_premium == True,
                User.premium_until != None,
                User.premium_until < now
            )
            result = await session.execute(query)
            expired_users = result.scalars().all()

            if not expired_users:
                return

            logger.info(f"SubscriptionService: Found {len(expired_users)} expired subscriptions.")

            for user in expired_users:
                # 2. Downgrade user
                user.is_premium = False
                # premium_until is kept for history but is_premium is the gatekeeper
                
                # 3. Notify user
                try:
                    msg = (
                        "🕒 *Subscription Expired*\n\n"
                        "Your Premium access has ended. Your alerts have been moved to the *Standard Queue* (turtle speed).\n\n"
                        "👉 Go to 🛒 *Shop* to renew and get back into the **Fast Lane**!"
                    )
                    await bot.send_message(user.telegram_id, msg, parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Could not notify user {user.telegram_id} of expiration: {e}")

            await session.commit()
