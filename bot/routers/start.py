import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import SettingsRepository
from bot.keyboards.reply import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command. Registers user and shows dynamic welcome text."""
    await state.clear()

    telegram_id = str(message.from_user.id)
    username = message.from_user.username

    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await repo.get_or_create(telegram_id=telegram_id, username=username)
        welcome_text = await settings_repo.get("welcome_text")

    # Fallback if DB not seeded yet
    if not welcome_text:
        welcome_text = (
            f"Hi {message.from_user.full_name}! 🚨\n\n"
            "Welcome to *Mister Alert* — your trading companion.\n\n"
            "Use the menu below to set alerts, track trades, or use our calculators."
        )
    else:
        welcome_text = f"👋 Hi {message.from_user.first_name}!\n\n{welcome_text}"

    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")
    logger.info(f"User {telegram_id} ({username}) started the bot.")


# ──────────────────────────────────────────────────────────────
# SETTINGS MENU (from main keyboard)
# ──────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Settings")
async def settings_menu(message: types.Message):
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)

    currency = user.preferred_currency if user else "USD"
    tier = "⭐ Premium" if (user and user.is_premium) else "🆓 Free"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🌍 Currency: {currency}", callback_data="pick_currency")],
        [types.InlineKeyboardButton(text="🪙 My Credits & Status", callback_data="my_balance")],
        [types.InlineKeyboardButton(text="📜 Transaction History", callback_data="my_transactions")],
    ])
    await message.answer(
        f"⚙️ *Settings*\n\nTier: {tier}\nCurrency: `{currency}`",
        reply_markup=kb,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "my_balance")
async def my_balance(callback: types.CallbackQuery):
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        price_credits = await settings_repo.get("price_credits_10") or "500"
        price_monthly = await settings_repo.get("price_premium_monthly") or "2000"

    tier = "⭐ Premium" if (user and user.is_premium) else "🆓 Free"
    credits = user.credits if user else 0
    currency = user.preferred_currency if user else "USD"

    text = (
        f"💼 *Your Account*\n\n"
        f"Tier: {tier}\n"
        f"🪙 Credits: `{credits}`\n"
        f"🌍 Currency: `{currency}`\n\n"
        f"_10 Credits = {price_credits} {currency}_\n"
        f"_1 Month Premium = {price_monthly} {currency}_"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Go to Shop", callback_data="go_shop")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
