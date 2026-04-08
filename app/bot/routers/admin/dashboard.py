import logging
import functools
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import settings
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository, AlertRepository
from app.data.economy_repository import TransactionRepository

router = Router()
logger = logging.getLogger(__name__)

def admin_only(func):
    """Decorator to restrict handler to admin users."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if user_id not in settings.admin_ids:
            if hasattr(event, 'answer'):
                await event.answer("⛔ Admin access only.")
            return
        return await func(event, *args, **kwargs)
    return wrapper

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👥 User Management", callback_data="admin:users")],
        [types.InlineKeyboardButton(text="🎟️ Mint Vouchers", callback_data="admin:mint_vouchers")],
        [types.InlineKeyboardButton(text="💳 Payment Methods", callback_data="admin:payments")],
        [types.InlineKeyboardButton(text="⏳ Pending Transactions", callback_data="admin:transactions")],
        [types.InlineKeyboardButton(text="💬 Support Tickets", callback_data="admin:support")],
        [types.InlineKeyboardButton(text="⚙️ Bot Settings & Captions", callback_data="admin:settings")],
        [types.InlineKeyboardButton(text="📊 System Stats", callback_data="admin:stats")],
    ])
    await message.answer(
        "🕹️ *Mister Alert Admin Panel*\n\nYou have full control. What would you like to manage?",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin:stats")
@admin_only
async def admin_stats(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        tx_repo = TransactionRepository(session)

        total_users = await user_repo.count_all()
        premium_users = await user_repo.count_premium()
        total_alerts = await alert_repo.count_active()
        pending_txs = await tx_repo.count_pending()

    await callback.message.edit_text(
        f"📊 *System Stats*\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"⭐ Premium Users: `{premium_users}`\n"
        f"🔔 Active Alerts: `{total_alerts}`\n"
        f"⏳ Pending Payments: `{pending_txs}`",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin:back")
@admin_only
async def admin_back(callback: types.CallbackQuery, state: FSMContext):
    await admin_panel(callback.message, state)
    await callback.answer()
