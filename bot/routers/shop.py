import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import (
    SettingsRepository, PaymentMethodRepository, TransactionRepository
)
from utils.fmt import (
    section, header, DIVIDER, row, success, error,
    shop_menu_text, transaction_card, pill_tx_status
)

router = Router()
logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = ["USD", "NGN", "KES", "GBP", "EUR"]


class ShopStates(StatesGroup):
    awaiting_amount = State()
    awaiting_evidence = State()


# ── Shop menu ─────────────────────────────────────────────────────────────────

@router.message(F.text == "🛒 Shop")
async def shop_menu(message: types.Message):
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await user_repo.get_or_create(telegram_id, message.from_user.username)
        currency = user.preferred_currency
        price_credits = await settings_repo.get("price_credits_10") or "500"
        price_monthly = await settings_repo.get("price_premium_monthly") or "2000"
        price_yearly = await settings_repo.get("price_premium_yearly") or "18000"
        from utils.fmt import pill_tier
        tier = pill_tier(user.is_premium)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🪙 Buy Credits (10)", callback_data="buy:credits")],
        [types.InlineKeyboardButton(text="⭐ Monthly Premium", callback_data="buy:monthly")],
        [types.InlineKeyboardButton(text="👑 Yearly Premium", callback_data="buy:yearly")],
        [types.InlineKeyboardButton(text="📜 My Transactions", callback_data="my_transactions")],
    ])
    await message.answer(
        shop_menu_text(tier, user.credits, currency, price_credits, price_monthly, price_yearly),
        reply_markup=kb, parse_mode="Markdown"
    )


# ── Buy flow ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy:"))
async def select_payment_method(callback: types.CallbackQuery, state: FSMContext):
    tx_type = callback.data.split(":")[1]
    await state.update_data(tx_type=tx_type)

    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        methods = await pm_repo.get_all_active()

    if not methods:
        await callback.message.edit_text(
            error("No payment methods configured yet. Contact admin."),
            parse_mode="Markdown"
        )
        return

    buttons = [
        [types.InlineKeyboardButton(text="🏦 " + m.name, callback_data="pm:" + str(m.id))]
        for m in methods
    ]
    await callback.message.edit_text(
        header("💳", "Select Payment Method") + "\n" + DIVIDER + "\n"
        "Choose how you'd like to pay:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pm:"))
async def show_payment_details(callback: types.CallbackQuery, state: FSMContext):
    pm_id = int(callback.data.split(":")[1])
    await state.update_data(pm_id=pm_id)

    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.get_by_id(pm_id)

    if not pm:
        await callback.answer("Payment method not found.")
        return

    await callback.message.edit_text(
        pm.details + "\n\n" + DIVIDER + "\n"
        "_After payment, tap the button below to submit your reference._",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ I Have Paid", callback_data="have_paid")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "have_paid")
async def request_amount(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.awaiting_amount)
    await callback.message.answer(
        header("💰", "Payment Confirmation — Step 1 of 2") + "\n" + DIVIDER + "\n"
        "Enter the *exact amount* you paid (numbers only):",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(ShopStates.awaiting_amount)
async def receive_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer(error("Invalid amount. Enter a number."), parse_mode="Markdown")
        return
    await state.update_data(amount=amount)
    await state.set_state(ShopStates.awaiting_evidence)
    await message.answer(
        header("🔖", "Payment Confirmation — Step 2 of 2") + "\n" + DIVIDER + "\n"
        "Send your *Transaction Reference / ID*:",
        parse_mode="Markdown"
    )


@router.message(ShopStates.awaiting_evidence)
async def receive_evidence(message: types.Message, state: FSMContext):
    evidence = message.text.strip()
    data = await state.get_data()
    telegram_id = str(message.from_user.id)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        tx_repo = TransactionRepository(session)
        user = await user_repo.get_or_create(telegram_id, message.from_user.username)
        tx = await tx_repo.create(
            user_id=user.id,
            amount=data["amount"],
            currency=user.preferred_currency,
            tx_type=data["tx_type"],
            evidence=evidence,
            pm_id=data["pm_id"]
        )

    body = "\n".join([
        row("🔖", "Reference", evidence),
        row("💰", "Amount", str(data["amount"]) + " " + user.preferred_currency),
        row("📦", "Type", data["tx_type"]),
        row("🆔", "Transaction ID", "#" + str(tx.id)),
        "",
        "_An admin will review and approve this shortly._",
    ])
    await message.answer(
        success("Payment Submitted!") + "\n" + DIVIDER + "\n" + body,
        parse_mode="Markdown"
    )
    await state.clear()


# ── Transaction history ───────────────────────────────────────────────────────

@router.callback_query(F.data == "my_transactions")
async def my_transactions(callback: types.CallbackQuery):
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        tx_repo = TransactionRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("User not found.")
            return
        txs = await tx_repo.get_user_transactions(user.id)

    if not txs:
        await callback.message.edit_text(
            section("📜", "My Transactions", "_No transactions yet._"),
            parse_mode="Markdown"
        )
        return

    lines = []
    for tx in txs[:10]:
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(tx.status, "❓")
        lines.append(
            status_icon + " #" + str(tx.id) + " · " + tx.tx_type +
            " · `" + str(tx.amount) + " " + tx.currency + "`"
        )
    await callback.message.edit_text(
        section("📜", "My Transactions", "\n".join(lines)),
        parse_mode="Markdown"
    )


# ── Currency picker ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "pick_currency")
async def pick_currency(callback: types.CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(text=c, callback_data="set_currency:" + c)]
        for c in SUPPORTED_CURRENCIES
    ]
    await callback.message.edit_text(
        section("🌍", "Currency Selection",
                "Choose your preferred currency.\nPrices in the Shop will update instantly."),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_currency:"))
async def set_currency(callback: types.CallbackQuery):
    currency = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if user:
            from sqlalchemy import update
            from data.models import User
            await session.execute(
                update(User).where(User.id == user.id).values(preferred_currency=currency)
            )
            await session.commit()
    await callback.message.edit_text(
        success("Currency set to " + currency + "!") + "\n\n"
        "_Shop prices now show in " + currency + "._",
        parse_mode="Markdown"
    )
    await callback.answer()
