import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from app.data.database import AsyncSessionLocal
from app.data.repositories.marketing import MarketingRepository
from app.data.economy_repository import SettingsRepository
from app.bot.routers.admin.dashboard import admin_only # Reuse admin check

router = Router()
logger = logging.getLogger(__name__)

class MarketingStates(StatesGroup):
    waiting_for_template_name = State()
    waiting_for_template_content = State()
    waiting_for_group_id = State()
    waiting_for_session_string = State()
    waiting_for_api_id = State()
    waiting_for_api_hash = State()
    waiting_for_goal_target = State()

def _marketing_main_keyboard() -> types.InlineKeyboardMarkup:
    from app.services.userbot_client import userbot_client
    status_emoji = "✅" if userbot_client.is_active else "❌"
    
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="📝 Templates", callback_data="mkt:templates"),
            types.InlineKeyboardButton(text="🌍 Target Groups", callback_data="mkt:groups")
        ],
        [
            types.InlineKeyboardButton(text="📊 Live Stats", callback_data="mkt:stats"),
            types.InlineKeyboardButton(text="🎯 Set Goals", callback_data="mkt:goals")
        ],
        [
            types.InlineKeyboardButton(text=f"{status_emoji} Full Rotation / Session", callback_data="mkt:session")
        ],
        [
            types.InlineKeyboardButton(text="📢 Send Value Drop (Manual)", callback_data="mkt:manual_post")
        ]
    ])

# ─────────────────────────────────────────────────
# DASHBOARD COMMAND
# ─────────────────────────────────────────────────

@router.message(Command("marketing"))
@admin_only
async def marketing_dashboard(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "🚀 <b>Mister Marketing Engine (MME)</b>\n\n"
        "Welcome to the Growth Command Center. From here, you can manage your UserBot "
        "outreach, keyword triggers, and engagement goals.\n\n"
        "<i>All actions are non-spam compliant.</i>"
    )
    await message.answer(text, reply_markup=_marketing_main_keyboard(), parse_mode="HTML")

# ─────────────────────────────────────────────────
# TARGET GROUPS MANAGEMENT
# ─────────────────────────────────────────────────

@router.callback_query(F.data == "mkt:groups")
@admin_only
async def mkt_groups_list(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        targets = await repo.get_targets()

    text = "🌍 <b>Monitored Target Groups</b>\n\n"
    if not targets:
        text += "<i>No groups monitored yet. Add a group to start keyword-based outreach.</i>"
    else:
        for t in targets:
            status = "🟢" if t.is_monitored else "⚪"
            text += f"{status} <b>ID:</b> <code>{t.chat_id}</code>\n"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Add New Group", callback_data="mkt:target_add")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "mkt:target_add")
@admin_only
async def mkt_target_add_start(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "📥 <b>Send the Telegram Chat ID of the target group:</b>\n\n"
        "<i>Tip: You can get the chat ID by using a bot like @userinfobot or by forwarding a message from the group to yourself.</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_group_id)

@router.message(MarketingStates.waiting_for_group_id)
@admin_only
async def mkt_target_save(message: types.Message, state: FSMContext):
    chat_id = message.text.strip()
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.add_target(chat_id=chat_id, is_monitored=True)
    
    await message.answer(f"✅ Group <code>{chat_id}</code> added to monitoring.", parse_mode="HTML")
    await marketing_dashboard(message, state)

# ─────────────────────────────────────────────────
# GOALS MANAGEMENT
# ─────────────────────────────────────────────────

@router.callback_query(F.data == "mkt:goals")
@admin_only
async def mkt_goals_panel(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        goals = await repo.get_stats_summary()
    
    text = "🎯 <b>Marketing Daily Goals</b>\n\nConfigure your safety limits here:\n\n"
    kb_list = []
    
    for g_type, data in goals.items():
        name = "💬 Keyword Replies" if g_type == 'daily_replies' else "📢 Timed Posts"
        text += f"🔹 {name}: <b>{data['target']}</b> per day\n"
        kb_list.append([types.InlineKeyboardButton(text=f"⚙️ Edit {g_type}", callback_data=f"mkt:goal_edit:{g_type}")])

    kb_list.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")])
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="HTML")

@router.callback_query(F.data.startswith("mkt:goal_edit:"))
@admin_only
async def mkt_goal_update_start(callback: types.CallbackQuery, state: FSMContext):
    goal_type = callback.data.split(":")[-1]
    await state.update_data(goal_type=goal_type)
    await callback.message.edit_text(f"🔢 Enter new daily target for <b>{goal_type}</b>:", parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_goal_target)

@router.message(MarketingStates.waiting_for_goal_target)
@admin_only
async def mkt_goal_save(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Please enter a valid number.")
    
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.update_goal(type=data['goal_type'], target=int(message.text))
    
    await message.answer(f"✅ Daily target for <b>{data['goal_type']}</b> updated to {message.text}.", parse_mode="HTML")
    await marketing_dashboard(message, state)

# ─────────────────────────────────────────────────
# ACCOUNT ROTATION / SESSION
# ─────────────────────────────────────────────────

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
    await state.set_state(MarketingStates.waiting_for_api_id)

@router.message(MarketingStates.waiting_for_api_id)
@admin_only
async def mkt_api_id_save(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Invalid ID. Please send numbers only.")
    
    await _validate_and_save(message, state, "telegram_api_id", message.text)

@router.callback_query(F.data == "mkt:api_hash_update")
@admin_only
async def mkt_api_hash_update_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send the new <b>API HASH</b>:", parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_api_hash)

@router.message(MarketingStates.waiting_for_api_hash)
@admin_only
async def mkt_api_hash_save(message: types.Message, state: FSMContext):
    await _validate_and_save(message, state, "telegram_api_hash", message.text.strip())

@router.callback_query(F.data == "mkt:session_update")
@admin_only
async def mkt_session_update_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send your new <b>Telethon Session String</b>:", parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_session_string)

@router.message(MarketingStates.waiting_for_session_string)
@admin_only
async def mkt_session_save(message: types.Message, state: FSMContext):
    await _validate_and_save(message, state, "telegram_session_string", message.text.strip())

# --- REUSABLE VALIDATOR & HOT RELOAD HELPER ---

async def _validate_and_save(message: types.Message, state: FSMContext, key: str, value: str):
    from app.services.userbot_client import userbot_client
    
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

# ─────────────────────────────────────────────────
# STATS VIEW
# ─────────────────────────────────────────────────

@router.callback_query(F.data == "mkt:stats")
@admin_only
async def mkt_stats(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        summary = await repo.get_stats_summary()
    
    text = "📊 <b>Marketing Performance</b>\n\n"
    for g_type, data in summary.items():
        name = "Keyword Replies" if g_type == 'daily_replies' else "Timed Posts"
        progress = f"<code>{data['current']}/{data['target']}</code>"
        percent = (data['current'] / data['target'] * 100) if data['target'] > 0 else 0
        filled = int(percent / 100 * 10)
        bar = "🟢" * filled + "⚪" * (10 - filled)
        text += f"🔹 {name}:\n{bar} {progress} ({percent:.1f}%)\n\n"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "mkt:back")
@admin_only
async def mkt_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🚀 <b>Mister Marketing Engine (MME)</b>\n\nChoose a category to manage:",
        reply_markup=_marketing_main_keyboard(),
        parse_mode="HTML"
    )

# ─────────────────────────────────────────────────
# TEMPLATE MANAGEMENT
# ─────────────────────────────────────────────────

@router.callback_query(F.data == "mkt:templates")
@admin_only
async def mkt_templates_list(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        templates = await repo.get_templates()

    text = "📝 <b>Marketing Templates</b>\n\n"
    if not templates:
        text += "<i>No templates found.</i>"
    else:
        for t in templates:
            text += f"✅ <b>{t.name}</b>\n<code>{t.content[:50]}...</code>\n\n"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Add Template", callback_data="mkt:template_add")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "mkt:template_add")
@admin_only
async def mkt_template_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter <b>Name</b> for template:", parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_template_name)

@router.message(MarketingStates.waiting_for_template_name)
@admin_only
async def mkt_template_save_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Enter <b>Message Content</b> (supports {{handle}}):", parse_mode="HTML")
    await state.set_state(MarketingStates.waiting_for_template_content)

@router.message(MarketingStates.waiting_for_template_content)
@admin_only
async def mkt_template_save_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.create_template(name=data['name'], content=message.text)
    await message.answer(f"✅ Template <b>{data['name']}</b> saved!")
    await marketing_dashboard(message, state)

# ─────────────────────────────────────────────────
# MANUAL POST (PLACEHOLDER)
# ─────────────────────────────────────────────────

@router.callback_query(F.data == "mkt:manual_post")
@admin_only
async def mkt_manual_post(callback: types.CallbackQuery):
    await callback.answer("🚧 Manual posting flow is coming soon. Use keyword-based outreach for now!", show_alert=True)
