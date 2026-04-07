import logging
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
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        tickets = await support_repo.get_all_open()

    if not tickets:
        await callback.message.edit_text(
            "✅ *Support Tickets*\n\nAll caught up! No open tickets.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")]
            ]),
            parse_mode="Markdown"
        )
        return

    text = f"💬 *Open Support Tickets ({len(tickets)})*\n\n"
    buttons = []
    for t in tickets[:10]:
        text += f"🎫 #{t.id} - {t.message[:40]}...\n"
        buttons.append([types.InlineKeyboardButton(
            text=f"👁️ View Ticket #{t.id}", 
            callback_data=f"admin:view_ticket:{t.id}"
        )])

    buttons.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")])
    await callback.message.edit_text(
        text, 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin:view_ticket:"))
@admin_only
async def admin_view_ticket(callback: types.CallbackQuery):
    ticket_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        user_repo = UserRepository(session)
        ticket = await support_repo.get_by_id(ticket_id)
        if not ticket:
            await callback.answer("❌ Ticket not found.")
            return
        user = await user_repo.get_by_id(ticket.user_id)
        username = f"(@{user.username})" if user and user.username else ""

    text = (
        f"🎫 *Ticket #{ticket.id}*\n"
        f"👤 From: {user.full_name if user else 'Unknown'} {username}\n"
        f"🆔 User ID: `{user.telegram_id if user else 'N/A'}`\n"
        f"📅 Date: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"💬 *Message:*\n{ticket.message}"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💬 Reply", callback_data=f"admin:reply_ticket:{ticket.id}")],
        [types.InlineKeyboardButton(text="↩️ Back to List", callback_data="admin:support")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin:reply_ticket:"))
@admin_only
async def admin_start_reply(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminSupportStates.awaiting_reply_text)
    await callback.message.answer("📝 Type your reply to the user:")
    await callback.answer()

@router.message(AdminSupportStates.awaiting_reply_text)
async def admin_send_reply(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data["reply_ticket_id"]
    reply_text = message.text.strip()
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        user_repo = UserRepository(session)
        ticket = await support_repo.add_reply(ticket_id, reply_text)
        if not ticket:
            await message.answer("❌ Error: Ticket not found.")
            await state.clear()
            return
        user = await user_repo.get_by_id(ticket.user_id)
    try:
        user_msg = (
            "👩‍💻 *Support Reply*\n\n"
            f"Your message: _{ticket.message}_\n\n"
            f"✅ *Response:*\n{reply_text}"
        )
        await bot.send_message(user.telegram_id, user_msg, parse_mode="Markdown")
        await message.answer(f"✅ Reply sent to user {user.telegram_id}!")
    except Exception as e:
        await message.answer(f"⚠️ Reply saved in DB but failed to send via Telegram: {e}")
    await state.clear()
