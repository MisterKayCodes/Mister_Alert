import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.data.database import AsyncSessionLocal
from app.data.repositories.marketing import MarketingRepository
from app.bot.routers.admin.dashboard import admin_only # Reuse admin check
from app.bot.routers.marketing.templates import router as templates_router
from app.bot.routers.marketing.rotation import router as rotation_router

router = Router()
router.include_router(templates_router)
router.include_router(rotation_router)

logger = logging.getLogger(__name__)

class DashboardStates(StatesGroup):
    waiting_for_group_id = State()
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

@router.callback_query(F.data == "mkt:back")
@admin_only
async def mkt_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🚀 <b>Mister Marketing Engine (MME)</b>\n\nChoose a category to manage:",
        reply_markup=_marketing_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "mkt:groups")
@admin_only
async def mkt_groups_list(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        targets = await repo.get_targets()
    text = "🌍 <b>Monitored Target Groups</b>\n\n"
    if not targets:
        text += "<i>No groups monitored yet.</i>"
    else:
        for t in targets:
            text += f"🟢 <b>ID:</b> <code>{t.chat_id}</code>\n"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Add New Group", callback_data="mkt:target_add")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "mkt:target_add")
@admin_only
async def mkt_target_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 Send the <b>Telegram Chat ID</b> of the target group:", parse_mode="HTML")
    await state.set_state(DashboardStates.waiting_for_group_id)

@router.message(DashboardStates.waiting_for_group_id)
@admin_only
async def mkt_target_save(message: types.Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.add_target(chat_id=message.text.strip(), is_monitored=True)
    await message.answer(f"✅ Group <code>{message.text}</code> added.")
    await marketing_dashboard(message, state)

@router.callback_query(F.data == "mkt:goals")
@admin_only
async def mkt_goals_panel(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        goals = await repo.get_stats_summary()
    text = "🎯 <b>Marketing Daily Goals</b>\n\n"
    kb_list = []
    for g_type, data in goals.items():
        text += f"🔹 {g_type}: <b>{data['target']}</b> per day\n"
        kb_list.append([types.InlineKeyboardButton(text=f"⚙️ Edit {g_type}", callback_data=f"mkt:goal_edit:{g_type}")])
    kb_list.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")])
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="HTML")

@router.callback_query(F.data.startswith("mkt:goal_edit:"))
@admin_only
async def mkt_goal_update_start(callback: types.CallbackQuery, state: FSMContext):
    goal_type = callback.data.split(":")[-1]
    await state.update_data(goal_type=goal_type)
    await callback.message.edit_text(f"🔢 Enter new daily target for <b>{goal_type}</b>:", parse_mode="HTML")
    await state.set_state(DashboardStates.waiting_for_goal_target)

@router.message(DashboardStates.waiting_for_goal_target)
@admin_only
async def mkt_goal_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.update_goal(type=data['goal_type'], target=int(message.text))
    await message.answer(f"✅ Goal updated.")
    await marketing_dashboard(message, state)

@router.callback_query(F.data == "mkt:stats")
@admin_only
async def mkt_stats(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        summary = await repo.get_stats_summary()
    text = "📊 <b>Performance</b>\n\n"
    for g_type, data in summary.items():
        text += f"🔹 {g_type}: {data['current']}/{data['target']}\n"
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="↩️ Back", callback_data="mkt:back")]]), parse_mode="HTML")

@router.callback_query(F.data == "mkt:manual_post")
@admin_only
async def mkt_manual_post(callback: types.CallbackQuery):
    await callback.answer("🚧 Manual posting coming soon!", show_alert=True)
