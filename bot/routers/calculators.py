import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.calculator_states import PositionSizeStates, RiskRewardStates
from bot.keyboards.reply import get_main_menu
from core.calculators.position_size import get_position_size
from core.calculators.risk_reward import calculate_risk_reward

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "🧮 Calculators")
async def calculators_menu(message: types.Message, state: FSMContext):
    """Present the Calculators menu."""
    await state.clear()
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📐 Position Sizer", callback_data="calc_pos_size")],
            [types.InlineKeyboardButton(text="⚖️ Risk/Reward", callback_data="calc_rr")],
        ]
    )
    await message.answer("🧮 **Trading Strategist**\n\nChoose your calculation tool:", reply_markup=kb)

# ==========================================
# POSITION SIZER FLOW
# ==========================================

@router.callback_query(F.data == "calc_pos_size")
async def start_pos_size(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PositionSizeStates.waiting_for_pair)
    await callback.message.edit_text("📐 **Position Sizer**\n\nStep 1: Enter Pair (e.g., BTCUSD, XAUUSD, EURUSD):")

@router.message(PositionSizeStates.waiting_for_pair)
async def process_pos_pair(message: types.Message, state: FSMContext):
    await state.update_data(pair=message.text.upper())
    await state.set_state(PositionSizeStates.waiting_for_entry)
    await message.answer("Step 2: Enter Entry Price:")

@router.message(PositionSizeStates.waiting_for_entry)
async def process_pos_entry(message: types.Message, state: FSMContext):
    try:
        await state.update_data(entry=float(message.text))
        await state.set_state(PositionSizeStates.waiting_for_sl)
        await message.answer("Step 3: Enter Stop Loss (SL) Price:")
    except ValueError:
        await message.answer("❌ Invalid number. Enter Entry Price again:")

@router.message(PositionSizeStates.waiting_for_sl)
async def process_pos_sl(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sl=float(message.text))
        await state.set_state(PositionSizeStates.waiting_for_risk)
        await message.answer("Step 4: Enter Total Risk Amount in USD (e.g., 100):")
    except ValueError:
        await message.answer("❌ Invalid number. Enter SL Price again:")

@router.message(PositionSizeStates.waiting_for_risk)
async def process_pos_risk(message: types.Message, state: FSMContext):
    try:
        risk_usd = float(message.text)
        data = await state.get_data()
        
        result = get_position_size(
            pair=data["pair"],
            entry=data["entry"],
            sl=data["sl"],
            risk_usd=risk_usd
        )
        
        response = (
            f"🎯 **Position Size Result**\n"
            f"--------------------------\n"
            f"Pair: `{data['pair']}`\n"
            f"Risk: `${risk_usd}`\n\n"
            f"📏 **Distance**: {result['pips']} pips\n"
            f"💰 **Lot Size**: `{result['lots']}` units/lots\n\n"
            f"_Always manage your risk properly!_"
        )
        await message.answer(response, parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("❌ Invalid number. Enter Risk USD again:")

# ==========================================
# RISK/REWARD FLOW
# ==========================================

@router.callback_query(F.data == "calc_rr")
async def start_rr(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RiskRewardStates.waiting_for_pair)
    await callback.message.edit_text("⚖️ **Risk/Reward Calculator**\n\nStep 1: Enter Pair (e.g., BTCUSD, EURUSD):")

@router.message(RiskRewardStates.waiting_for_pair)
async def process_rr_pair(message: types.Message, state: FSMContext):
    await state.update_data(pair=message.text.upper())
    await state.set_state(RiskRewardStates.waiting_for_position)
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="LONG 📈", callback_data="LONG"),
             types.InlineKeyboardButton(text="SHORT 📉", callback_data="SHORT")]
        ]
    )
    await message.answer("Step 2: Is this a LONG or SHORT trade?", reply_markup=kb)

@router.callback_query(RiskRewardStates.waiting_for_position)
async def process_rr_position(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(position=callback.data)
    await state.set_state(RiskRewardStates.waiting_for_entry)
    await callback.message.edit_text(f"Position: {callback.data}\n\nStep 3: Enter Entry Price:")

@router.message(RiskRewardStates.waiting_for_entry)
async def process_rr_entry(message: types.Message, state: FSMContext):
    try:
        await state.update_data(entry=float(message.text))
        await state.set_state(RiskRewardStates.waiting_for_sl)
        await message.answer("Step 4: Enter Stop Loss (SL) Price:")
    except ValueError:
        await message.answer("❌ Invalid number. Enter Entry Price again:")

@router.message(RiskRewardStates.waiting_for_sl)
async def process_rr_sl(message: types.Message, state: FSMContext):
    try:
        await state.update_data(sl=float(message.text))
        await state.set_state(RiskRewardStates.waiting_for_tp)
        await message.answer("Step 5: Enter Take Profit (TP) Price:")
    except ValueError:
        await message.answer("❌ Invalid number. Enter SL Price again:")

@router.message(RiskRewardStates.waiting_for_tp)
async def process_rr_tp(message: types.Message, state: FSMContext):
    try:
        tp = float(message.text)
        data = await state.get_data()
        
        result = calculate_risk_reward(
            pair=data["pair"],
            position=data["position"],
            entry_price=data["entry"],
            stop_loss=data["sl"],
            take_profit=tp
        )
        
        color = "🟢" if float(result["risk_reward_ratio"]) >= 2 else "🟡"
        response = (
            f"⚖️ **R:R Calculation Report**\n"
            f"----------------------------\n"
            f"Pair: `{data['pair']}` | {data['position']}\n\n"
            f"🛑 **Risk**: {result['risk_pips']} pips\n"
            f"🎯 **Reward**: {result['reward_pips']} pips\n"
            f"{color} **Ratio**: `{result['risk_reward_ratio']}` (`{result['ratio_label']}`)\n\n"
            f"_Trade Recommendation: {result['formatted']}_"
        )
        await message.answer(response, parse_mode="Markdown")
        await state.clear()
    except (ValueError, ZeroDivisionError) as e:
        await message.answer(f"❌ Calculation Error: {e}. Start over.")
        await state.clear()
