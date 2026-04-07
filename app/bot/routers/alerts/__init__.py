from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.utils.fmt import section

from . import add, manage

router = Router()
router.include_router(add.router)
router.include_router(manage.router)

@router.message(F.text == "🔔 Alerts")
async def alerts_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ New Alert", callback_data="add_alert")],
        [types.InlineKeyboardButton(text="📋 My Alerts", callback_data="view_alerts")],
    ])
    await message.answer(
        section("🔔", "Alert Manager", "Monitor any asset. Get notified the instant your target is hit."),
        reply_markup=kb, parse_mode="Markdown"
    )
