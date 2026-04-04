import logging
from aiogram import Bot
from core.events import AlertTriggeredEvent, TakeProfitHitEvent
from services.event_bus import event_bus
from data.database import AsyncSessionLocal
from data.repository import UserRepository

logger = logging.getLogger(__name__)

class NotificationHandler:
    """
    Bridge between system events and Telegram notifications.
    Listens to EventBus and sends messages to users.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

    def setup(self):
        """Subscribe to events."""
        event_bus.subscribe(AlertTriggeredEvent, self.handle_alert_hit)
        event_bus.subscribe(TakeProfitHitEvent, self.handle_tp_hit)
        logger.info("NotificationHandler subscribed to Alert and Trade events.")

    async def handle_alert_hit(self, event: AlertTriggeredEvent):
        """Send notification when an alert is hit."""
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.session.get(UserRepository.User, event.user_id)
            if not user:
                logger.error(f"User {event.user_id} not found for alert {event.alert_id}")
                return
            
            telegram_id = user.telegram_id
            
        message = (
            f"🔔 **ALERT TRIGGERED!** 🚨\n\n"
            f"Symbol: {event.symbol}\n"
            f"Target: {event.target_price}\n"
            f"Current: {event.price}\n\n"
            f"Time: {event.timestamp.strftime('%H:%M:%S')}"
        )
        
        if not user.is_premium:
            message += (
                f"\n\n---\n"
                f"⚡ **Premium users caught this 110s faster.**\n"
                f"Don't leave your entry to chance. Upgrade now!"
            )
        
        try:
            await self.bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
            logger.info(f"Notification sent to {telegram_id} for alert {event.alert_id}")
        except Exception as e:
            logger.error(f"Failed to send alert notification to {telegram_id}: {e}")

    async def handle_tp_hit(self, event: TakeProfitHitEvent):
        """Send notification when a take profit is hit."""
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.session.get(UserRepository.User, event.user_id)
            if not user:
                return
            
            telegram_id = user.telegram_id

        message = (
            f"📈 **TAKE PROFIT HIT!** 💰\n\n"
            f"Symbol: {event.symbol}\n"
            f"Price: {event.price}\n"
            f"Trade ID: {event.trade_id}\n\n"
            f"Time: {event.timestamp.strftime('%H:%M:%S')}"
        )

        try:
            await self.bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
            logger.info(f"TP notification sent to {telegram_id} for trade {event.trade_id}")
        except Exception as e:
            logger.error(f"Failed to send TP notification to {telegram_id}: {e}")
