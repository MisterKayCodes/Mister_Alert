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

    lines = [f"• `{s.key}` = `{s.value}`" for s in all_settings]
    text = "⚙️ *Bot Settings*\n\n" + "\n".join(lines) if lines else "No settings found."

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Edit a Setting", callback_data="admin:setting_edit")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")],
    ])
    await callback.message.edit_text(text, reply_markup=buttons, parse_mode="Markdown")
    await callback.answer()

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
