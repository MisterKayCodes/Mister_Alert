import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

class AdminSettingsStates(StatesGroup):
    awaiting_setting_key = State()
    awaiting_setting_value = State()

@router.callback_query(F.data == "admin:settings")
@admin_only
async def admin_settings(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        all_settings = await settings_repo.get_all()

    is_direct_enabled = "False"
    vendor_link = "Not Set"
    
    for s in all_settings:
        if s.key == "enable_direct_payments": is_direct_enabled = s.value
        elif s.key == "vendor_telegram_link": vendor_link = s.value

    status = "🟢 ON" if is_direct_enabled == "True" else "🔴 OFF"
    text = (
        "⚙️ *Bot Settings & Economy Controls*\n\n"
        f"🏦 *Direct Bank/Crypto Payments*: {status}\n"
        f"🧑‍💼 *Current Vendor Link*: `{vendor_link}`\n\n"
        "_Toggle payments below. If OFF, users must buy vouchers from your Vendor._" 
    )

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🔀 Toggle Direct Payments", callback_data="admin:toggle_direct")],
        [types.InlineKeyboardButton(text="🧑‍💼 Set Vendor username/link", callback_data="admin:set_vendor")],
        [types.InlineKeyboardButton(text="✏️ Edit Advanced Setting", callback_data="admin:setting_edit")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")],
    ])
    await callback.message.edit_text(text, reply_markup=buttons, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin:toggle_direct")
@admin_only
async def admin_toggle_direct(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        current = await settings_repo.get("enable_direct_payments")
        new_val = "False" if current == "True" else "True"
        await settings_repo.set("enable_direct_payments", new_val)
    # Reload menu
    await admin_settings(callback)

class AdminVendorState(StatesGroup):
    awaiting_vendor_link = State()

@router.callback_query(F.data == "admin:set_vendor")
@admin_only
async def admin_set_vendor(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminVendorState.awaiting_vendor_link)
    await callback.message.edit_text(
        "🔗 *Set Vendor Link*\n\nEnter the full Telegram link for the voucher vendor (e.g., `https://t.me/Kaycris`):",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="admin:settings")]])
    )
    await callback.answer()

@router.message(AdminVendorState.awaiting_vendor_link)
async def admin_save_vendor(message: types.Message, state: FSMContext):
    link = message.text.strip()
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set("vendor_telegram_link", link)
    await message.answer(f"✅ Vendor link updated to: {link}\n\nType /admin to return to panel.")
    await state.clear()

@router.callback_query(F.data == "admin:setting_edit")
@admin_only
async def admin_setting_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminSettingsStates.awaiting_setting_key)
    await callback.message.answer(
        "🔑 Enter the *key* of the setting to edit (e.g. `welcome_text`, `alert_limit_free`):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminSettingsStates.awaiting_setting_key)
async def admin_setting_key_received(message: types.Message, state: FSMContext):
    await state.update_data(setting_key=message.text.strip())
    await state.set_state(AdminSettingsStates.awaiting_setting_value)
    await message.answer("📝 Enter the *new value*:", parse_mode="Markdown")

@router.message(AdminSettingsStates.awaiting_setting_value)
async def admin_setting_value_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data["setting_key"]
    value = message.text.strip()
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set(key, value)
    await message.answer(f"✅ Setting `{key}` updated to:\n`{value}`", parse_mode="Markdown")
    await state.clear()
