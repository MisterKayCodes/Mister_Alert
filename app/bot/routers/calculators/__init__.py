from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.utils.fmt import section

from . import position_size, risk_reward

router = Router()
router.include_router(position_size.router)
router.include_router(risk_reward.router)

@router.message(F.text == "🧮 Calculators")
async def calculators_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📐 Position Sizer", callback_data="calc_pos_size")],
        [types.InlineKeyboardButton(text="⚖️ Risk / Reward", callback_data="calc_rr")],
    ])
    await message.answer(
        section("🧮", "Trading Strategist", "Professional calculators to plan every trade."),
        reply_markup=kb, parse_mode="Markdown"
    )
