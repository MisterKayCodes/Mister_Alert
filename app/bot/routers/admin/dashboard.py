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


def _admin_panel_keyboard() -> types.InlineKeyboardMarkup:
    """Shared keyboard for the admin panel — single source of truth."""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👥 Users", callback_data="admin:users"),
            types.InlineKeyboardButton(text="🎟️ Mint Vouchers", callback_data="admin:mint_vouchers")
        ],
        [
            types.InlineKeyboardButton(text="💳 Payment Methods", callback_data="admin:payments"),
            types.InlineKeyboardButton(text="⏳ Transactions", callback_data="admin:transactions")
        ],
        [
            types.InlineKeyboardButton(text="💬 Tickets", callback_data="admin:support"),
            types.InlineKeyboardButton(text="⚙️ Settings", callback_data="admin:settings")
        ],
        [
            types.InlineKeyboardButton(text="📊 Stats", callback_data="admin:stats"),
            types.InlineKeyboardButton(text="🔒 God Key", callback_data="admin:reveal_key")
        ],
        [
            types.InlineKeyboardButton(text="🚀 Server Update", callback_data="admin:update_system")
        ]
    ])


ADMIN_PANEL_TEXT = "🕹️ *Mister Alert Admin Panel*\n\nYou have full control. What would you like to manage?"


@router.message(Command("admin"))
@admin_only
async def admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=_admin_panel_keyboard(), parse_mode="Markdown")

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
    await callback.message.edit_text(ADMIN_PANEL_TEXT, reply_markup=_admin_panel_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin:update_system")
@admin_only
async def admin_update_system(callback: types.CallbackQuery):
    import asyncio
    import os
    import sys
    
    # 1. Notify we are starting
    await callback.message.edit_text("🔄 <b>Initiating Deployment...</b>\n\n<i>Pulling latest code from GitHub...</i>", parse_mode="HTML")
    await callback.answer()
    
    # 2. Run Git Pull
    process = await asyncio.create_subprocess_shell(
        "git pull",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    output = stdout.decode('utf-8').strip()
    error_out = stderr.decode('utf-8').strip()
    
    full_output = []
    if output: full_output.append(output)
    if error_out: full_output.append(error_out)
    
    log_text = "\n".join(full_output)[:3000] # Telegram limit safety
    
    # 3. Inform user of git status and restart warning
    await callback.message.answer(
        f"✅ <b>Git Pull Complete</b>\n\n<pre>{log_text}</pre>\n\n🚀 <i>Restarting bot process now. Changes will be live in ~10 seconds.</i>",
        parse_mode="HTML"
    )
    
    # 4. Perform the hard reboot (Replace current process)
    # This inherits the environment (including virtualenv) and doesn't change the PID.
    os.execv(sys.executable, [sys.executable] + sys.argv)


