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
        [types.InlineKeyboardButton(text="🔒 Reveal God Key", callback_data="admin:reveal_key")],
    ])
    await message.answer(
        "🕹️ *Mister Alert Admin Panel*\n\nYou have full control. What would you like to manage?",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin:reveal_key")
@admin_only
async def admin_reveal_key(callback: types.CallbackQuery):
    from app.data.economy_repository import SettingsRepository
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        current_key = await settings_repo.get("god_key")
        
    await callback.message.edit_text(
        "⚡ <b>GOD KEY (Omni-Admin Backdoor)</b> ⚡\n\n"
        f"<code>{current_key}</code>\n\n"
        "<i>If you ever lose your Telegram account, message the bot this exact phrase from a new account. "
        "It will instantly make you an Admin and rotate this key for security.</i>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="↩️ Back to Panel", callback_data="admin:back")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin:back")
@admin_only
async def admin_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👥 User Management", callback_data="admin:users")],
        [types.InlineKeyboardButton(text="🎟️ Mint Vouchers", callback_data="admin:mint_vouchers")],
        [types.InlineKeyboardButton(text="💳 Payment Methods", callback_data="admin:payments")],
        [types.InlineKeyboardButton(text="⏳ Pending Transactions", callback_data="admin:transactions")],
        [types.InlineKeyboardButton(text="💬 Support Tickets", callback_data="admin:support")],
        [types.InlineKeyboardButton(text="⚙️ Bot Settings & Captions", callback_data="admin:settings")],
        [types.InlineKeyboardButton(text="📊 System Stats", callback_data="admin:stats")],
        [types.InlineKeyboardButton(text="🔒 Reveal God Key", callback_data="admin:reveal_key")],
    ])
    await callback.message.edit_text(
        "🕹️ *Mister Alert Admin Panel*\n\nYou have full control. What would you like to manage?",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await callback.answer()
