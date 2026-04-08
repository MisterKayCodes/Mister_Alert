import logging
import html
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.support_repository import SupportTicketRepository
from app.data.repositories import UserRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

class AdminSupportStates(StatesGroup):
    awaiting_reply_text = State()

@router.callback_query(F.data == "admin:support")
@admin_only
async def admin_support_tickets(callback: types.CallbackQuery):
    logger.info(f"Admin {callback.from_user.id} requested support tickets list")
    try:
        async with AsyncSessionLocal() as session:
            support_repo = SupportTicketRepository(session)
            tickets = await support_repo.get_all_open()

        if not tickets:
            await callback.message.edit_text(
                "✅ <b>Support Tickets</b>\n\nAll caught up! No open tickets.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")]
                ]),
                parse_mode="HTML"
            )
            return

        text = f"💬 <b>Open Support Tickets ({len(tickets)})</b>\n\n"
        buttons = []
        for t in tickets[:10]:
            safe_preview = html.escape(t.message[:40])
            text += f"🎫 #{t.id} - {safe_preview}...\n"
            buttons.append([types.InlineKeyboardButton(
                text=f"👁️ View Ticket #{t.id}", 
                callback_data=f"admin:view_ticket:{t.id}"
            )])

        buttons.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")])
        await callback.message.edit_text(
            text, 
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error loading support tickets: {e}", exc_info=True)
        await callback.answer("❌ Error: Check bot.log", show_alert=True)
    await callback.answer()

@router.callback_query(F.data.startswith("admin:view_ticket:"))
@admin_only
async def admin_view_ticket(callback: types.CallbackQuery):
    ticket_id = int(callback.data.split(":")[2])
    logger.info(f"Admin {callback.from_user.id} viewing ticket #{ticket_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            support_repo = SupportTicketRepository(session)
            user_repo = UserRepository(session)
            ticket = await support_repo.get_by_id(ticket_id)
            if not ticket:
                await callback.answer("❌ Ticket not found.")
                return
            user = await user_repo.get_by_id(ticket.user_id)
            username = f"(@{user.username})" if user and user.username else ""

        safe_msg = html.escape(ticket.message)
        user_name = "User" if user else "Unknown"
        
        text = (
            f"🎫 <b>Ticket #{ticket.id}</b>\n"
            f"👤 From: {user_name} {username}\n"
            f"🆔 User ID: <code>{user.telegram_id if user else 'N/A'}</code>\n"
            f"📅 Date: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"💬 <b>Message:</b>\n{safe_msg}"
        )
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💬 Reply", callback_data=f"admin:reply_ticket:{ticket.id}")],
            [types.InlineKeyboardButton(text="↩️ Back to List", callback_data="admin:support")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to view ticket #{ticket_id}: {e}", exc_info=True)
        await callback.answer("❌ Render Error: Check bot.log", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin:reply_ticket:"))
@admin_only
async def admin_start_reply(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminSupportStates.awaiting_reply_text)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="admin:support")]
    ])
    await callback.message.answer("📝 Type your reply to the user:", reply_markup=kb)
    await callback.answer()

@router.message(AdminSupportStates.awaiting_reply_text)
@admin_only
async def admin_send_reply(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data["reply_ticket_id"]
    reply_text = message.text.strip()
    logger.info(f"Admin {message.from_user.id} sending reply to ticket #{ticket_id}")
    
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        user_repo = UserRepository(session)
        
        ticket = await support_repo.get_by_id(ticket_id)
        if not ticket:
            await message.answer("❌ Error: Ticket not found.")
            await state.clear()
            return
        user = await user_repo.get_by_id(ticket.user_id)
        
        try:
            user_msg = (
                "👩‍💻 <b>Support Reply</b>\n\n"
                f"Your message: <i>{html.escape(ticket.message)}</i>\n\n"
                f"✅ <b>Response:</b>\n{html.escape(reply_text)}"
            )
            await bot.send_message(user.telegram_id, user_msg, parse_mode="HTML")
            
            await support_repo.delete(ticket_id)
            await message.answer(f"✅ Reply sent to user and ticket #{ticket_id} resolved.")
            logger.info(f"Ticket #{ticket_id} resolved and deleted.")
        except Exception as e:
            logger.error(f"Failed to send reply to user {user.telegram_id}: {e}")
            await message.answer(f"❌ Failed to reach user: {e}")
            
    await state.clear()
