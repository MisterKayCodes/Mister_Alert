import asyncio
import logging
from datetime import datetime, timezone
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from app.core.events import SubscriptionExpiredEvent
from app.services.event_bus import event_bus

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
                logger.debug("Subscription service task was safely cancelled.")
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
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            expired_users = await user_repo.get_expired_users()

            if not expired_users:
                return

            logger.info(f"SubscriptionService: Found {len(expired_users)} expired subscriptions.")

            for user in expired_users:
                # 1. Downgrade user
                await user_repo.demote_from_premium(user.id)
                
                # 2. Publish event for notification (decoupled)
                await event_bus.publish(SubscriptionExpiredEvent(
                    user_id=user.id,
                    telegram_id=user.telegram_id
                ))
