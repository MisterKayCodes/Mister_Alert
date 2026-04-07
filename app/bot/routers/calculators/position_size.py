import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.bot.states.calculator_states import PositionSizeStates
from app.core.calculators.position_size import get_position_size
from app.utils.fmt import header, DIVIDER, row, error

router = Router()
logger = logging.getLogger(__name__)

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
        await message.answer(error("Invalid number."), parse_mode="Markdown")

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
        await message.answer(error("Invalid number."), parse_mode="Markdown")

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
            row("💵", "Risk Amount", "$" + f"{risk_usd:,.2f}"),
            row("📏", "Distance", str(result["pips"]) + " pips"),
            row("💰", "Lot Size", f"`{result['lots']}` lots")
        ])
        
        await message.answer(
            f"📐 *Position Size Calculated*\n{DIVIDER}\n{body}",
            parse_mode="Markdown"
        )
        await state.clear()
    except ValueError:
        await message.answer(error("Invalid number."), parse_mode="Markdown")
