import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.bot.states.calculator_states import RiskRewardStates
from app.core.calculators.risk_reward import calculate_risk_reward
from app.utils.fmt import header, DIVIDER, row, rr_report, error

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "calc_rr")
async def start_rr(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RiskRewardStates.waiting_for_pair)
    await callback.message.edit_text(
        header("⚖️", "R:R Calculator — Step 1 of 5") + "\n" + DIVIDER + "\n"
        "Enter the *pair* (e.g. `BTCUSD`, `EURUSD`):",
        parse_mode="Markdown"
    )

@router.message(RiskRewardStates.waiting_for_pair)
async def process_rr_pair(message: types.Message, state: FSMContext):
    await state.update_data(pair=message.text.upper())
    await state.set_state(RiskRewardStates.waiting_for_position)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="📈 LONG", callback_data="LONG"),
            types.InlineKeyboardButton(text="📉 SHORT", callback_data="SHORT"),
        ]
    ])
    await message.answer(
        header("⚖️", "R:R Calculator — Step 2 of 5") + "\n" + DIVIDER + "\n"
        "Is this a *LONG* or *SHORT* trade?",
        reply_markup=kb, parse_mode="Markdown"
    )

@router.callback_query(RiskRewardStates.waiting_for_position)
async def process_rr_position(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(position=callback.data)
    await state.set_state(RiskRewardStates.waiting_for_entry)
    await callback.message.edit_text(
        header("⚖️", "R:R Calculator — Step 3 of 5") + "\n" + DIVIDER + "\n"
        "Enter your *entry price*:",
        parse_mode="Markdown"
    )

@router.message(RiskRewardStates.waiting_for_entry)
async def process_rr_entry(message: types.Message, state: FSMContext):
    try:
        await state.update_data(entry=float(message.text))
        await state.set_state(RiskRewardStates.waiting_for_sl)
        await message.answer(
            header("⚖️", "R:R Calculator — Step 4 of 5") + "\n" + DIVIDER + "\n"
            "Enter your *stop loss price*:",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(error("Invalid number."), parse_mode="Markdown")

@router.message(RiskRewardStates.waiting_for_sl)
async def process_rr_sl(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sl=float(message.text))
        await state.set_state(RiskRewardStates.waiting_for_tp)
        await message.answer(
            header("⚖️", "R:R Calculator — Step 5 of 5") + "\n" + DIVIDER + "\n"
            "Enter your *take profit price*:",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(error("Invalid number."), parse_mode="Markdown")

@router.message(RiskRewardStates.waiting_for_tp)
async def process_rr_tp(message: types.Message, state: FSMContext):
    try:
        tp = float(message.text)
        data = await state.get_data()
        
        result = calculate_risk_reward(
            pair=data["pair"], position=data["position"],
            entry_price=data["entry"], stop_loss=data["sl"], take_profit=tp
        )
        
        rr_val = float(result["risk_reward_ratio"])
        report = rr_report(data["pair"], data["position"], result)
        if rr_val < 1.0:
            report += "\n\n⚠️ *Warning:* Bad R:R ratio!"
            
        await message.answer(report, parse_mode="Markdown")
        await state.clear()
    except Exception as e:
        await message.answer(error(f"Error: {e}"))
        await state.clear()
