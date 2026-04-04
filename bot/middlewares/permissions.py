import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from data.database import AsyncSessionLocal
from data.repository import UserRepository, AlertRepository
from data.economy_repository import SettingsRepository

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware to enforce usage limits based on subscription tier & credits.
    
    Gating Logic:
      - Premium users: no limit (up to alert_limit_premium from settings)
      - Users with credits: credits act as bonus slots
      - Free users: limited to alert_limit_free from settings DB
    
    Psychological Trap: When limit is hit → show the 'Value Gap'.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Only intercept the "add_alert" action trigger
        if not (isinstance(event, CallbackQuery) and event.data == "add_alert"):
            return await handler(event, data)

        user_id = data.get("event_from_user").id

        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            alert_repo = AlertRepository(session)
            settings_repo = SettingsRepository(session)

            user = await user_repo.get_by_telegram_id(str(user_id))
            if not user:
                return await handler(event, data)

            active_alerts = await alert_repo.get_user_alerts(user.id)
            active_count = len([a for a in active_alerts if a.is_active])

            # Fetch dynamic limits from DB (admin-editable)
            limit_free = int(await settings_repo.get("alert_limit_free") or "3")
            limit_premium = int(await settings_repo.get("alert_limit_premium") or "50")
            credits_per_alert = int(await settings_repo.get("credits_per_alert") or "1")

        if user.is_premium:
            # Premium users — check against premium limit
            if active_count >= limit_premium:
                await event.answer("⛔ Premium limit reached.", show_alert=True)
                return
        elif user.credits > 0:
            # Has credits — allow but consume a credit
            if active_count >= (limit_free + user.credits):
                await event.answer("🚫 Credit limit reached.", show_alert=True)
                return await event.message.answer(
                    "🚫 *All Credit Slots Used!*\n\n"
                    "You've used up your free slots AND credits.\n\n"
                    "💡 Top up credits or upgrade to *Premium* for unlimited tracking!\n\n"
                    "👉 Go to 🛒 *Shop* to recharge.",
                    parse_mode="Markdown"
                )
        else:
            # Free tier — hard limit
            if active_count >= limit_free:
                await event.answer("🚫 ALERT LIMIT REACHED", show_alert=True)
                return await event.message.answer(
                    "🚫 *Free Slots Full!*\n\n"
                    f"You're using all `{limit_free}` free alert slots.\n\n"
                    "📈 There are *2,400+ potential pips* moving in the markets "
                    "right now that you aren't tracking.\n\n"
                    "🪙 Buy *Credits* for extra slots or upgrade to "
                    "*Premium* for unlimited, real-time tracking!\n\n"
                    "👉 Go to 🛒 *Shop* to upgrade.",
                    parse_mode="Markdown"
                )

        return await handler(event, data)
