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
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_support")]
    ])
    await message.answer(
        "💬 *Contact Support*\n\n"
        "Please send your message below. An admin will get back to you directly in this chat.\n\n"
        "_Tip: Tap 'Cancel' below if you didn't mean to contact us._",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "cancel_support")
async def cancel_support(callback: types.CallbackQuery, state: FSMContext):
    """User cancels support request."""
    await state.clear()
    await callback.message.edit_text("❌ Support request cancelled.")
    await callback.answer()

@router.message(SupportStates.waiting_for_message)
async def forward_to_admins(message: types.Message, state: FSMContext, bot: Bot):
    """Forward user message to all configured admins and save to DB."""
    user_id = message.from_user.id
    text = message.text.strip()
    
    from app.data.database import AsyncSessionLocal
    from app.data.repositories import UserRepository
    from app.data.support_repository import SupportTicketRepository

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        support_repo = SupportTicketRepository(session)
        
        user = await user_repo.get_by_telegram_id(str(user_id))
        if not user:
            await message.answer("❌ User account not found.")
            return
            
        # 1. Save to Database
        ticket = await support_repo.create(user.id, text)
        
        # 2. Prepare Admin Notification
        user_info = f"👤 *Support Ticket #{ticket.id}*\nFrom: {message.from_user.full_name} (@{message.from_user.username})\nID: `{user_id}`\n"
        forward_text = f"{user_info}\n💬 *Message:*\n{text}"
        
        # 3. Add Reply Button for Admin
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💬 Reply Now", callback_data=f"admin:reply_ticket:{ticket.id}")]
        ])
        
        success_count = 0
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=forward_text,
                    parse_mode="Markdown",
                    reply_markup=kb
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
    Relays the reply and DELETES the ticket to save storage.
    """
    if message.from_user.id not in settings.admin_ids:
        return

    reply_to = message.reply_to_message
    if not reply_to.text or "👤 *Support Ticket*" not in reply_to.text:
        return

    try:
        import re
        # Find Ticket ID and User ID
        ticket_match = re.search(r"Support Ticket #(\d+)", reply_to.text)
        user_match = re.search(r"ID: `(\d+)`", reply_to.text)
        
        if not ticket_match or not user_match:
            return
            
        ticket_id = int(ticket_match.group(1))
        target_user_id = int(user_match.group(1))
        
        # 1. Send admin's reply to the user
        await bot.send_message(
            chat_id=target_user_id,
            text=f"👨‍💻 *Support Reply:*\n\n{message.text}",
            parse_mode="Markdown"
        )
        
        # 2. DELETE the ticket from DB (Self-Cleaning)
        from app.data.database import AsyncSessionLocal
        from app.data.support_repository import SupportTicketRepository
        async with AsyncSessionLocal() as session:
            repo = SupportTicketRepository(session)
            await repo.delete(ticket_id)

        await message.reply("✅ Reply sent and ticket resolved (deleted from DB).")
        
    except Exception as e:
        await message.reply(f"❌ Failed to process reply: {e}")
        logger.error(f"Support reply error: {e}")
