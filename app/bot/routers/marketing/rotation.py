import logging
from typing import Optional
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository
from app.bot.routers.admin.dashboard import admin_only # Reuse admin check

router = Router()
logger = logging.getLogger(__name__)

class RotationStates(StatesGroup):
    waiting_for_session_string = State()
    waiting_for_api_id = State()
    waiting_for_api_hash = State()

@router.callback_query(F.data == "mkt:session")
@admin_only
async def mkt_session_status(callback: types.CallbackQuery):
    from app.services.userbot_client import userbot_client
    
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        current_session = await settings_repo.get("telegram_session_string") or "Env"
        current_id = await settings_repo.get("telegram_api_id") or "Env"
        current_hash = await settings_repo.get("telegram_api_hash") or "Env"

    status = "🟢 <b>ACTIVE</b>" if userbot_client.is_active else "🔴 <b>INACTIVE</b>"
    
    text = (
        "🔌 <b>Full Account Rotation Manager</b>\n\n"
        f"Status: {status}\n\n"
        f"🔹 <b>API ID:</b> <code>{current_id}</code>\n"
        f"🔹 <b>API HASH:</b> <code>{current_hash[:6]}...</code>\n"
        f"🔹 <b>SESSION:</b> <code>{current_session[:15]}...</code>\n\n"
        "Updating any of these will trigger a <b>Pre-flight Connection Test</b>."
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔑 Update API ID", callback_data="mkt:api_id_update")],
        [types.InlineKeyboardButton(text="🔐 Update API Hash", callback_data="mkt:api_hash_update")],
        [types.InlineKeyboardButton(text="🔄 Update Session String", callback_data="mkt:session_update")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "mkt:api_id_update")
@admin_only
async def mkt_api_id_update_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send the new <b>API ID</b> (numbers only):", parse_mode="HTML")
    await state.set_state(RotationStates.waiting_for_api_id)

@router.message(RotationStates.waiting_for_api_id)
@admin_only
async def mkt_api_id_save(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Invalid ID. Please send numbers only.")
    await _validate_and_save(message, state, "telegram_api_id", message.text)

@router.callback_query(F.data == "mkt:api_hash_update")
@admin_only
async def mkt_api_hash_update_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send the new <b>API HASH</b>:", parse_mode="HTML")
    await state.set_state(RotationStates.waiting_for_api_hash)

@router.message(RotationStates.waiting_for_api_hash)
@admin_only
async def mkt_api_hash_save(message: types.Message, state: FSMContext):
    await _validate_and_save(message, state, "telegram_api_hash", message.text.strip())

@router.callback_query(F.data == "mkt:session_update")
@admin_only
async def mkt_session_update_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send your new <b>Telethon Session String</b>:", parse_mode="HTML")
    await state.set_state(RotationStates.waiting_for_session_string)

@router.message(RotationStates.waiting_for_session_string)
@admin_only
async def mkt_session_save(message: types.Message, state: FSMContext):
    await _validate_and_save(message, state, "telegram_session_string", message.text.strip())

async def _validate_and_save(message: types.Message, state: FSMContext, key: str, value: str):
    from app.services.userbot_client import userbot_client
    from app.bot.routers.marketing.dashboard import marketing_dashboard
    
    await message.answer("🔍 <b>Performing Pre-flight Connection Test...</b>", parse_mode="HTML")
    
    async with AsyncSessionLocal() as session:
        sr = SettingsRepository(session)
        aid = await sr.get("telegram_api_id") or str(settings.telegram_api_id)
        ahash = await sr.get("telegram_api_hash") or settings.telegram_api_hash
        sess = await sr.get("telegram_session_string") or settings.telegram_session_string
        
        if key == "telegram_api_id": aid = value
        elif key == "telegram_api_hash": ahash = value
        elif key == "telegram_session_string": sess = value

    success, info = await userbot_client.validate_credentials(int(aid), ahash, sess)
    
    if not success:
        await message.answer(f"❌ <b>Validation Failed!</b>\n\n<code>{info}</code>", parse_mode="HTML")
        return

    async with AsyncSessionLocal() as session:
        sr = SettingsRepository(session)
        await sr.set(key, value, f"UserBot {key}")
    
    await message.answer(f"✅ <b>Validated!</b> {info}.\nSettings saved.")
    
    try:
        await userbot_client.reload(new_session_string=sess, new_api_id=int(aid), new_api_hash=ahash)
        await message.answer("♻️ <b>Engine Active.</b>")
    except Exception as e:
        await message.answer(f"⚠️ Reload failed: {e}")
    
    await marketing_dashboard(message, state)
