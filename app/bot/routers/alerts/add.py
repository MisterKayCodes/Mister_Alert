import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository, AlertRepository
from app.data.economy_repository import SettingsRepository
from app.utils.market_hours import is_market_open
from app.utils.fmt import (
    header, row, success, error, warning, DIVIDER
)
from app.bot.states.alert_states import AlertStates
from app.utils.symbol_validator import is_valid_symbol

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "add_alert")
async def start_add_alert(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    await state.set_state(AlertStates.waiting_for_symbol)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="user_home")]
    ])
    
    await callback.message.edit_text(
        f"{header('🔤', 'Add Alert — Step 1 of 3')}\n{DIVIDER}\n"
        "Enter the *symbol* you want to monitor:\n\n"
        "_Examples: `BTCUSD`, `EURUSD`, `XAUUSD`_",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.message(AlertStates.waiting_for_symbol)
async def process_symbol(message: types.Message, state: FSMContext):
    symbol = message.text.upper().strip()
    if not is_valid_symbol(symbol):
        return await message.answer(
            error("Invalid symbol format.") + "\n\n"
            "Please use a standard format like `BTCUSD`, `EURUSD`, or `NAS100`.\n",
            parse_mode="Markdown"
        )
    await state.update_data(symbol=symbol)
    await state.set_state(AlertStates.waiting_for_condition)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📈 Price Goes Above", callback_data="above"),
         types.InlineKeyboardButton(text="📉 Price Goes Below", callback_data="below")],
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="user_home")]
    ])
    await message.answer(
        f"{header('🔀', 'Add Alert — Step 2 of 3')}\n{DIVIDER}\n"
        f"Symbol: *{symbol}*\n\nWhich direction should trigger the alert?",
        reply_markup=kb, parse_mode="Markdown"
    )

@router.callback_query(AlertStates.waiting_for_condition)
async def process_condition(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    condition = callback.data
    await state.update_data(condition=condition)
    await state.set_state(AlertStates.waiting_for_price)
    label = "Above 📈" if condition == "above" else "Below 📉"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="user_home")]
    ])
    
    await callback.message.edit_text(
        f"{header('💰', 'Add Alert — Step 3 of 3')}\n{DIVIDER}\n"
        f"Direction: *{label}*\n\nEnter the *target price*:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.message(AlertStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer(error("Invalid price — enter a number."), parse_mode="Markdown")

    user_data = await state.get_data()
    symbol = user_data["symbol"]
    condition = user_data["condition"]
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        settings_repo = SettingsRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.answer(error("User not found."), parse_mode="Markdown")
            await state.clear()
            return
        
        # Enforce alert limits
        current_alerts = await alert_repo.get_user_alerts(user.id)
        active_count = len([a for a in current_alerts if a.is_active])
        
        if user.is_premium:
            limit = int(await settings_repo.get("alert_limit_premium") or "50")
        else:
            limit = int(await settings_repo.get("alert_limit_free") or "3")
        
        if active_count >= limit:
            tier = "Premium ⭐" if user.is_premium else "Free 🆓"
            await message.answer(
                f"{error('Alert Limit Reached!')}\n{DIVIDER}\n"
                f"Your *{tier}* plan allows *{limit}* active alerts.\n"
                f"You currently have *{active_count}*.\n\n"
                f"_Delete an old alert or upgrade to Premium for more!_",
                parse_mode="Markdown"
            )
            await state.clear()
            return
        
        await alert_repo.create_alert(user_id=user.id, symbol=symbol,
                                      price_above=(price if condition == "above" else None),
                                      price_below=(price if condition == "below" else None))
        is_premium = user.is_premium

    speed_note = "⚡ *Fast Lane*" if is_premium else "🐢 *Standard Mode*"
    await message.answer(
        f"{success('Alert Created!')}\n{DIVIDER}\n"
        f"{row('📌', 'Symbol', symbol)}\n"
        f"{row('🎯', 'Target', str(price))}\n"
        f"{speed_note}",
        parse_mode="Markdown"
    )
    await state.clear()

