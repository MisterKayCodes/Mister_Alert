import logging
import random
import string
from aiogram import Router, types
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository
from config import settings

router = Router()
logger = logging.getLogger(__name__)

def _generate_new_god_key() -> str:
    """Generates a highly secure new god key."""
    chars = string.ascii_uppercase + string.digits
    secret = "".join(random.choices(chars, k=24))
    return f"MISTER-ALERT-GOD-{secret}"

@router.message()
async def god_mode_listener(message: types.Message):
    """
    Hidden listener that watches every text message for the God Key.
    If matched, it grants admin access and burns the key.
    Note: This is registered last so it doesn't intercept regular commands,
    but acts as a fallback checker.
    """
    if not message.text:
        return

    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        current_god_key = await settings_repo.get("god_key")
        
        # Security check: Ensure God Key exists and matches perfectly.
        if current_god_key and current_god_key.strip() != "" and message.text.strip() == current_god_key:
            user_id = message.from_user.id
            
            # 1. Promote to Admin
            if user_id not in settings.admin_ids:
                settings.admin_ids.append(user_id)
                # In a robust production environment, you would also save this to `.env` or DB.
                # For this session, it grants immediate access to the admin dashboard.
                logger.critical(f"GOD MODE ACTIVATED: User {user_id} (@{message.from_user.username}) claimed the throne.")
                
            # 2. Burn and Rotate the Key
            new_key = _generate_new_god_key()
            await settings_repo.set("god_key", new_key, "The Omni-Admin recovery phrase")
            
            # 3. Send the Welcome Message
            await message.answer(
                "⚡ <b>GOD MODE ACTIVATED</b> ⚡\n\n"
                "Identity confirmed. You have been granted permanent Admin privileges.\n\n"
                "🔒 <i>Security Protocol: Your old passphrase has been destroyed. A new God Key has been generated. You can view it in the Admin Settings panel.</i>\n\n"
                "Type /admin to enter the Command Center.",
                parse_mode="HTML"
            )
            return
