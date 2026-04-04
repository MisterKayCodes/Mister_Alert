import logging
from aiogram import Bot
from core.events import AlertTriggeredEvent, TakeProfitHitEvent
from services.event_bus import event_bus
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import SettingsRepository
from utils.fmt import DIVIDER, row
from utils.timezone_helper import format_time_for_user

logger = logging.getLogger(__name__)


class NotificationHandler:
    """
    Bridge between system events and Telegram notifications.
    Listens to EventBus and sends messages to users.
    """
    def __init__(self, bot: Bot):
        self.bot = bot

    def setup(self):
        event_bus.subscribe(AlertTriggeredEvent, self.handle_alert_hit)
        event_bus.subscribe(TakeProfitHitEvent, self.handle_tp_hit)
        logger.info("NotificationHandler subscribed to Alert and Trade events.")

    async def handle_alert_hit(self, event: AlertTriggeredEvent):
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            settings_repo = SettingsRepository(session)

            user = await user_repo.get_by_id(event.user_id)
            if not user:
                logger.error("User %s not found for alert %s", event.user_id, event.alert_id)
                return

            telegram_id = user.telegram_id
            sub_footer = await settings_repo.get("subscription_footer") or ""
            user_tz = user.timezone or "UTC"

        # Format time in user's local timezone
        ts = format_time_for_user(event.timestamp, user_tz)

        body = "\n".join([
            row("📌", "Symbol", event.symbol),
            row("🎯", "Target", event.target_price),
            row("💹", "Current", event.price),
            row("🕒", "Time", ts),
        ])
        message = "🔔 *ALERT TRIGGERED!*\n" + DIVIDER + "\n" + body

        if not user.is_premium and sub_footer:
            message += "\n\n" + DIVIDER + "\n_" + sub_footer + "_"

        try:
            await self.bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
            logger.info("Alert notification sent to %s", telegram_id)
        except Exception as e:
            logger.error("Failed to send alert notification to %s: %s", telegram_id, e)

    async def handle_tp_hit(self, event: TakeProfitHitEvent):
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(event.user_id)
            if not user:
                return
            telegram_id = user.telegram_id

        ts = event.timestamp.strftime("%H:%M:%S")
        body = "\n".join([
            row("📌", "Symbol", event.symbol),
            row("💰", "Exit Price", event.price),
            row("🔑", "Trade ID", event.trade_id),
            row("🕒", "Time", ts),
        ])
        message = "📈 *TAKE PROFIT HIT!* 💰\n" + DIVIDER + "\n" + body

        try:
            await self.bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
            logger.info("TP notification sent to %s", telegram_id)
        except Exception as e:
            logger.error("Failed to send TP notification to %s: %s", telegram_id, e)
