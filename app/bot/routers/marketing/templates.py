import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.data.database import AsyncSessionLocal
from app.data.repositories.marketing import MarketingRepository
from app.bot.routers.admin.dashboard import admin_only # Reuse admin check

router = Router()
logger = logging.getLogger(__name__)

class TemplateStates(StatesGroup):
    waiting_for_template_name = State()
    waiting_for_template_content = State()

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
    await state.set_state(TemplateStates.waiting_for_template_name)

@router.message(TemplateStates.waiting_for_template_name)
@admin_only
async def mkt_template_save_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Enter <b>Message Content</b> (supports {{handle}}):", parse_mode="HTML")
    await state.set_state(TemplateStates.waiting_for_template_content)

@router.message(TemplateStates.waiting_for_template_content)
@admin_only
async def mkt_template_save_content(message: types.Message, state: FSMContext):
    from app.bot.routers.marketing.dashboard import marketing_dashboard
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        repo = MarketingRepository(session)
        await repo.create_template(name=data['name'], content=message.text)
    await message.answer(f"✅ Template <b>{data['name']}</b> saved!")
    await marketing_dashboard(message, state)
