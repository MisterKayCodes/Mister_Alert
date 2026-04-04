import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from bot.states.calculator_states import PositionSizeStates, RiskRewardStates
from core.calculators.position_size import get_position_size
from core.calculators.risk_reward import calculate_risk_reward
from utils.fmt import section, header, DIVIDER, row, rr_report, success, error

router = Router()
logger = logging.getLogger(__name__)


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


# ── Position Sizer ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "calc_pos_size")
async def start_pos_size(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PositionSizeStates.waiting_for_pair)
    await callback.message.edit_text(
        header("📐", "Position Sizer — Step 1 of 4") + "\n" + DIVIDER + "\n"
        "Enter the *pair* (e.g. `BTCUSD`, `EURUSD`, `XAUUSD`):",
        parse_mode="Markdown"
    )


@router.message(PositionSizeStates.waiting_for_pair)
async def process_pos_pair(message: types.Message, state: FSMContext):
    await state.update_data(pair=message.text.upper())
    await state.set_state(PositionSizeStates.waiting_for_entry)
    await message.answer(
        header("📐", "Position Sizer — Step 2 of 4") + "\n" + DIVIDER + "\n"
        "Enter your *entry price*:",
        parse_mode="Markdown"
    )


@router.message(PositionSizeStates.waiting_for_entry)
async def process_pos_entry(message: types.Message, state: FSMContext):
    try:
        await state.update_data(entry=float(message.text))
        await state.set_state(PositionSizeStates.waiting_for_sl)
        await message.answer(
            header("📐", "Position Sizer — Step 3 of 4") + "\n" + DIVIDER + "\n"
            "Enter your *stop loss price*:",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(error("Invalid number — enter entry price again."), parse_mode="Markdown")


@router.message(PositionSizeStates.waiting_for_sl)
async def process_pos_sl(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sl=float(message.text))
        await state.set_state(PositionSizeStates.waiting_for_risk)
        await message.answer(
            header("📐", "Position Sizer — Step 4 of 4") + "\n" + DIVIDER + "\n"
            "Enter your *risk amount in USD* (e.g. `100`):",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(error("Invalid number — enter stop loss price again."), parse_mode="Markdown")


@router.message(PositionSizeStates.waiting_for_risk)
async def process_pos_risk(message: types.Message, state: FSMContext):
    try:
        risk_usd = float(message.text)
        data = await state.get_data()
        result = get_position_size(
            pair=data["pair"], entry=data["entry"],
            sl=data["sl"], risk_usd=risk_usd
        )
        body = "\n".join([
            row("📌", "Pair", data["pair"]),
            row("💵", "Risk Amount", "$" + str(risk_usd)),
            row("📏", "Distance", str(result["pips"]) + " pips"),
            row("💰", "Lot Size", str(result["lots"]) + " lots"),
            "",
            "_Always manage your risk properly!_",
        ])
        await message.answer(
            success("Position Size Calculated") + "\n" + DIVIDER + "\n" + body,
            parse_mode="Markdown"
        )
        await state.clear()
    except ValueError:
        await message.answer(error("Invalid number — enter risk amount again."), parse_mode="Markdown")


# ── Risk / Reward ─────────────────────────────────────────────────────────────

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
        await message.answer(error("Invalid number — enter entry price again."), parse_mode="Markdown")


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
        await message.answer(error("Invalid number — enter stop loss again."), parse_mode="Markdown")


@router.message(RiskRewardStates.waiting_for_tp)
async def process_rr_tp(message: types.Message, state: FSMContext):
    try:
        tp = float(message.text)
        data = await state.get_data()
        result = calculate_risk_reward(
            pair=data["pair"], position=data["position"],
            entry_price=data["entry"], stop_loss=data["sl"], take_profit=tp
        )
        await message.answer(rr_report(data["pair"], data["position"], result), parse_mode="Markdown")
        await state.clear()
    except (ValueError, ZeroDivisionError) as e:
        await message.answer(error("Calculation error: " + str(e) + ". Starting over."), parse_mode="Markdown")
        await state.clear()
