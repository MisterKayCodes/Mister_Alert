import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import (
    SettingsRepository, PaymentMethodRepository, TransactionRepository
)

router = Router()
logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = ["USD", "NGN", "KES", "GBP", "EUR"]


class ShopStates(StatesGroup):
    awaiting_amount = State()
    awaiting_evidence = State()
    awaiting_currency_pick = State()


# ──────────────────────────────────────────────────────────────
# SHOP MENU
# ──────────────────────────────────────────────────────────────

@router.message(F.text == "🛒 Shop")
async def shop_menu(message: types.Message):
    """Show the user their balance and purchase options."""
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await user_repo.get_or_create(telegram_id, message.from_user.username)

        currency = user.preferred_currency
        price_credits = await settings_repo.get("price_credits_10") or "500"
        price_monthly = await settings_repo.get("price_premium_monthly") or "2000"
        price_yearly = await settings_repo.get("price_premium_yearly") or "18000"

        status = "⭐ Premium" if user.is_premium else "🆓 Free"
        text = (
            f"🛒 *Mister Alert Shop*\n\n"
            f"👤 Tier: {status}\n"
            f"🪙 Credits: `{user.credits}`\n"
            f"🌍 Currency: `{currency}`\n\n"
            f"*Pricing ({currency})*:\n"
            f"  • 10 Credits — `{price_credits}`\n"
            f"  • 1 Month Premium — `{price_monthly}`\n"
            f"  • 1 Year Premium — `{price_yearly}`\n"
        )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🪙 Buy Credits (10)", callback_data="buy:credits")],
        [types.InlineKeyboardButton(text="⭐ Buy Monthly Premium", callback_data="buy:monthly")],
        [types.InlineKeyboardButton(text="👑 Buy Yearly Premium", callback_data="buy:yearly")],
        [types.InlineKeyboardButton(text="📜 My Transactions", callback_data="my_transactions")],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


# ──────────────────────────────────────────────────────────────
# BUY FLOW — Select payment method
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy:"))
async def select_payment_method(callback: types.CallbackQuery, state: FSMContext):
    tx_type = callback.data.split(":")[1]  # credits / monthly / yearly
    await state.update_data(tx_type=tx_type)

    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        methods = await pm_repo.get_all_active()

    if not methods:
        await callback.message.edit_text("❌ No payment methods configured yet. Contact admin.")
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"🏦 {m.name}", callback_data=f"pm:{m.id}")]
        for m in methods
    ]
    await callback.message.edit_text(
        "💳 *Select Payment Method*:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


# ──────────────────────────────────────────────────────────────
# BUY FLOW — Show account details & ask for amount
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pm:"))
async def show_payment_details(callback: types.CallbackQuery, state: FSMContext):
    pm_id = int(callback.data.split(":")[1])
    await state.update_data(pm_id=pm_id)

    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.get_by_id(pm_id)

    if not pm:
        await callback.answer("❌ Payment method not found.")
        return

    await callback.message.edit_text(
        f"{pm.details}\n\n"
        "📌 After payment, click the button below.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ I Have Paid", callback_data="have_paid")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "have_paid")
async def request_amount(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.awaiting_amount)
    await callback.message.answer("💰 Enter the *exact amount* you paid (numbers only):", parse_mode="Markdown")
    await callback.answer()


@router.message(ShopStates.awaiting_amount)
async def receive_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return
    await state.update_data(amount=amount)
    await state.set_state(ShopStates.awaiting_evidence)
    await message.answer("🔖 Send your *Transaction Reference / Reference Number*:", parse_mode="Markdown")


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

    await message.answer(
        f"✅ *Payment Submitted!*\n\n"
        f"Reference: `{evidence}`\n"
        f"Amount: `{data['amount']} {user.preferred_currency}`\n\n"
        f"🕐 An admin will review and approve within a few minutes.\n"
        f"Your Transaction ID: `#{tx.id}`",
        parse_mode="Markdown"
    )
    await state.clear()


# ──────────────────────────────────────────────────────────────
# MY TRANSACTIONS
# ──────────────────────────────────────────────────────────────

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
        await callback.message.edit_text("📜 No transactions yet.")
        return

    lines = []
    for tx in txs[:10]:
        icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(tx.status, "❓")
        lines.append(f"{icon} #{tx.id} | {tx.tx_type} | {tx.amount} {tx.currency}")

    await callback.message.edit_text(
        "📜 *Your Transactions*:\n\n" + "\n".join(lines),
        parse_mode="Markdown"
    )


# ──────────────────────────────────────────────────────────────
# CURRENCY PICKER (accessible from Settings)
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "pick_currency")
async def pick_currency(callback: types.CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(text=c, callback_data=f"set_currency:{c}")]
        for c in SUPPORTED_CURRENCIES
    ]
    await callback.message.edit_text(
        "🌍 *Select Your Preferred Currency*\n\nThis affects how prices are displayed in the shop.",
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
        f"✅ Currency set to *{currency}*! Prices in the shop will now show in {currency}.",
        parse_mode="Markdown"
    )
    await callback.answer()
