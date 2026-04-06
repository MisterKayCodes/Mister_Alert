from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.database import AsyncSessionLocal
from data.repository import UserRepository, AlertRepository
from data.economy_repository import SettingsRepository
from utils.market_hours import is_market_open
from utils.fmt import (
    header, section, row, success, error, warning,
    alert_card, pill_status, DIVIDER
)

router = Router()


# ── FSM States ────────────────────────────────────────────────────────────────
from bot.states.alert_states import AlertStates


# ── Alert menu ────────────────────────────────────────────────────────────────

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


# ── Add alert flow ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "add_alert")
async def start_add_alert(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    await state.set_state(AlertStates.waiting_for_symbol)
    await callback.message.edit_text(
        f"{header('🔤', 'Add Alert — Step 1 of 3')}\n{DIVIDER}\n"
        "Enter the *symbol* you want to monitor:\n\n"
        "_Examples: `BTCUSD`, `EURUSD`, `XAUUSD`_",
        parse_mode="Markdown"
    )


@router.message(AlertStates.waiting_for_symbol)
async def process_symbol(message: types.Message, state: FSMContext):
    from utils.symbol_validator import is_valid_symbol
    symbol = message.text.upper().strip()
    
    if not is_valid_symbol(symbol):
        return await message.answer(
            error("Invalid symbol format.") + "\n\n"
            "Please use a standard format like `BTCUSD`, `EURUSD`, or `NAS100`.\n"
            "Symbols should be alphanumeric and 2-15 characters long.",
            parse_mode="Markdown"
        )

    await state.update_data(symbol=symbol)
    await state.set_state(AlertStates.waiting_for_condition)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📈 Price Goes Above", callback_data="above"),
         types.InlineKeyboardButton(text="📉 Price Goes Below", callback_data="below")]
    ])
    await message.answer(
        f"{header('🔀', 'Add Alert — Step 2 of 3')}\n{DIVIDER}\n"
        f"Symbol: *{symbol}*\n\nWhich direction should trigger the alert?",
        reply_markup=kb, parse_mode="Markdown"
    )


@router.callback_query(AlertStates.waiting_for_condition)
async def process_condition(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    condition = callback.data
    await state.update_data(condition=condition)
    await state.set_state(AlertStates.waiting_for_price)
    label = "Above 📈" if condition == "above" else "Below 📉"
    await callback.message.edit_text(
        f"{header('💰', 'Add Alert — Step 3 of 3')}\n{DIVIDER}\n"
        f"Direction: *{label}*\n\nEnter the *target price*:",
        parse_mode="Markdown"
    )


@router.message(AlertStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer(error("Invalid price — enter a number."), parse_mode="Markdown")
        return

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
            await message.answer(error("User not found. Try /start again."), parse_mode="Markdown")
            await state.clear()
            return

        price_above = price if condition == "above" else None
        price_below = price if condition == "below" else None
        await alert_repo.create_alert(user_id=user.id, symbol=symbol,
                                      price_above=price_above, price_below=price_below)

        # Determine polling speed for this user
        is_premium = user.is_premium

    market_note = ""
    if not is_market_open(symbol):
        market_note = f"\n\n{warning('Market is CLOSED for this asset — alert will activate at next open.')}"

    # ── Speed tier notice ──────────────────────────────────────────────────────
    if is_premium:
        speed_note = "\n\n⚡ *Fast Lane* — Price checked every ~10 seconds."
    else:
        speed_note = (
            "\n\n🐢 *Standard Mode* — Price checked every ~2 minutes on the free tier.\n"
            "👉 Upgrade to *Premium* or use 🪙 *Credits* for real-time, 10-second alerts.\n"
            "Go to 🛒 *Shop* to upgrade."
        )

    cond_str = f"> {price}" if condition == "above" else f"< {price}"
    body = (
        f"{row('📌', 'Symbol', symbol)}\n"
        f"{row('🎯', 'Target', cond_str)}\n"
        f"{row('📡', 'Status', '⏳ Watching')}"
        f"{market_note}"
        f"{speed_note}"
    )
    await message.answer(
        f"{success('Alert Created!')}\n{DIVIDER}\n{body}",
        parse_mode="Markdown"
    )
    await state.clear()


# ── View / delete alerts ──────────────────────────────────────────────────────

@router.callback_query(F.data == "view_alerts")
async def view_alerts(callback: types.CallbackQuery):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.message.edit_text(error("User not found."), parse_mode="Markdown")
            return
        alerts = await alert_repo.get_user_alerts(user.id)
        is_premium = user.is_premium

    if not alerts:
        await callback.message.edit_text(
            section("🔔", "My Alerts", "_You have no alerts yet. Tap ➕ New Alert to get started._"),
            parse_mode="Markdown"
        )
        return

    speed_label = "⚡ Fast Lane (10s)" if is_premium else "🐢 Standard (2 min)"
    await callback.message.edit_text(
        f"{header('📋', 'My Alerts')}\n{DIVIDER}\n"
        f"Polling speed: *{speed_label}*\n"
        "_Tap Delete to remove an alert._",
        parse_mode="Markdown"
    )
    for a in alerts:
        cond_str = f"> {a.price_above}" if a.price_above else f"< {a.price_below}"

        # Build button row — add Boost button for free-tier active alerts
        buttons = [
            [types.InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete_alert:{a.id}")]
        ]
        if a.is_active and not is_premium:
            buttons[0].insert(0, types.InlineKeyboardButton(
                text="⚡ Boost (1 Credit)", callback_data=f"boost_alert:{a.id}"
            ))

        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer(
            alert_card(a.symbol, cond_str, a.is_active, a.id),
            reply_markup=kb, parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("boost_alert:"))
async def boost_alert_handler(callback: types.CallbackQuery):
    """Spend 1 credit to move a free-tier alert to the fast lane (mark premium-equivalent)."""
    await callback.answer("⏳")
    alert_id = int(callback.data.split(":")[1])
    telegram_id = str(callback.from_user.id)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            await callback.message.edit_text(error("User not found."), parse_mode="Markdown")
            return

        if (user.credits or 0) < 1:
            await callback.message.answer(
                warning(
                    "⚡ *No Credits!*\n\n"
                    "You need at least *1 credit* to boost an alert to the fast lane (10s checks).\n\n"
                    "👉 Go to 🛒 *Shop* to buy credits."
                ),
                parse_mode="Markdown"
            )
            return

        # Deduct 1 credit and set is_boosted on the alert
        from sqlalchemy import update
        from data.models import User as UserModel, Alert as AlertModel
        await session.execute(
            update(UserModel).where(UserModel.id == user.id)
            .values(credits=UserModel.credits - 1)
        )
        await session.execute(
            update(AlertModel).where(AlertModel.id == alert_id)
            .values(is_boosted=True)
        )
        await session.commit()

        remaining = user.credits - 1

    await callback.message.edit_text(
        success("⚡ Alert Boosted!") + "\n" + DIVIDER + "\n"
        f"{row('🪙', 'Credits Used', '1')}\n"
        f"{row('🪙', 'Remaining', str(remaining))}\n\n"
        "_This alert is now on the* fast lane* — price checked every ~10 seconds._",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("delete_alert:"))
async def delete_alert_handler(callback: types.CallbackQuery):
    await callback.answer("⏳")
    alert_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        alert_repo = AlertRepository(session)
        await alert_repo.delete_alert(alert_id)
    await callback.message.edit_text(success("Alert deleted."), parse_mode="Markdown")
