import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings

router = Router()
logger = logging.getLogger(__name__)

class SupportStates(StatesGroup):
    waiting_for_message = State()

@router.message(F.text == "💬 Support")
async def support_request(message: types.Message, state: FSMContext):
    """User clicks Support button."""
    await state.set_state(SupportStates.waiting_for_message)
    await message.answer(
        "💬 *Contact Support*\n\n"
        "Please send your message below. You can include text, or questions about your account.\n\n"
        "An admin will get back to you directly in this chat.",
        parse_mode="Markdown"
    )

@router.message(SupportStates.waiting_for_message)
async def forward_to_admins(message: types.Message, state: FSMContext, bot: Bot):
    """Forward user message to all configured admins."""
    user = message.from_user
    user_info = f"👤 *Support Ticket*\nFrom: {user.full_name} (@{user.username})\nID: `{user.id}`\n"
    
    forward_text = f"{user_info}\n💬 *Message:*\n{message.text}"
    
    success_count = 0
    for admin_id in settings.admin_ids:
        try:
            # We don't use built-in forward because we want to format it with the user ID for easy reply parsing
            await bot.send_message(
                chat_id=admin_id,
                text=forward_text,
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to forward support message to admin {admin_id}: {e}")

    if success_count > 0:
        await message.answer("✅ Your message has been sent to support. Please wait for a reply.")
        await state.clear()
    else:
        await message.answer("❌ Sorry, there was an error connecting to support. Please try again later.")

@router.message(F.reply_to_message)
async def admin_reply_handler(message: types.Message, bot: Bot):
    """
    Handle admin replies. 
    If an admin replies to a support ticket message, relay it back to the user.
    """
    # Only admins can reply
    if message.from_user.id not in settings.admin_ids:
        return

    # Check if the message being replied to has our Support Ticket header
    reply_to = message.reply_to_message
    if not reply_to.text or "👤 *Support Ticket*" not in reply_to.text:
        return

    try:
        # Extract user ID from the ticket header
        # Header format: ID: `user_id`
        import re
        match = re.search(r"ID: `(\d+)`", reply_to.text)
        if not match:
            return
            
        target_user_id = int(match.group(1))
        
        # Send admin's reply to the user
        await bot.send_message(
            chat_id=target_user_id,
            text=f"👨‍💻 *Support Reply:*\n\n{message.text}",
            parse_mode="Markdown"
        )
        await message.reply("✅ Reply sent to user.")
        logger.info(f"Admin {message.from_user.id} replied to support ticket for user {target_user_id}")
        
    except Exception as e:
        await message.reply(f"❌ Failed to send reply: {e}")
        logger.error(f"Support reply error: {e}")
