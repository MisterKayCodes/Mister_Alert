import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import SettingsRepository
from bot.keyboards.reply import get_main_menu
from utils.timezone_helper import parse_timezone, TIMEZONE_ALIASES

router = Router()
logger = logging.getLogger(__name__)


# ── Timezone FSM ──────────────────────────────────────────────────────────────
class SettingsStates(StatesGroup):
    waiting_for_timezone = State()


# ── /start ────────────────────────────────────────────────────────────────────

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


# ── Settings menu ─────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Settings")
async def settings_menu(message: types.Message, state: FSMContext):
    await state.clear()
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)

    currency = user.preferred_currency if user else "USD"
    tz = user.timezone if user else "UTC"
    tier = "⭐ Premium" if (user and user.is_premium) else "🆓 Free"

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🌍 Currency: {currency}", callback_data="pick_currency")],
        [types.InlineKeyboardButton(text=f"🕐 Timezone: {tz}", callback_data="set_timezone")],
        [types.InlineKeyboardButton(text="🪙 My Credits & Status", callback_data="my_balance")],
        [types.InlineKeyboardButton(text="📜 Transaction History", callback_data="my_transactions")],
    ])
    await message.answer(
        f"⚙️ *Settings*\n\nTier: {tier}\nCurrency: `{currency}`\nTimezone: `{tz}`",
        reply_markup=kb,
        parse_mode="Markdown"
    )


# ── Timezone setting ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_timezone")
async def prompt_timezone(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    await state.set_state(SettingsStates.waiting_for_timezone)

    examples = (
        "🌍 *Africa*\n`WAT` · `CAT` · `EAT` · `Africa/Lagos`\n\n"
        "🇪🇺 *Europe*\n`GMT` · `BST` · `Europe/London`\n\n"
        "🗽 *Americas*\n`EST` · `PST` · `America/New_York`\n\n"
        "🕌 *Middle East & Asia*\n`GST` · `IST` · `Asia/Dubai`"
    )
    await callback.message.edit_text(
        "🕐 *Set Your Timezone*\n\n"
        "Reply with your timezone. Here are some examples:\n\n"
        f"{examples}\n\n"
        "_Alert times will automatically convert to your local time._",
        parse_mode="Markdown"
    )


@router.message(SettingsStates.waiting_for_timezone)
async def receive_timezone(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    iana = parse_timezone(user_input)

    if not iana:
        await message.answer(
            "❌ *Timezone not recognised.*\n\n"
            "Try something like: `WAT`, `GMT`, `Africa/Lagos`, `London`, `New York`, `IST`",
            parse_mode="Markdown"
        )
        return  # Stay in state so user can try again

    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        if user:
            from sqlalchemy import update
            from data.models import User as UserModel
            await session.execute(
                update(UserModel).where(UserModel.id == user.id).values(timezone=iana)
            )
            await session.commit()

    await message.answer(
        f"✅ *Timezone saved!*\n\n"
        f"Set to: `{iana}`\n\n"
        "_All alert notifications will now show your local time._",
        parse_mode="Markdown"
    )
    await state.clear()


# ── Balance / status ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "my_balance")
async def my_balance(callback: types.CallbackQuery):
    await callback.answer("⏳")
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        price_credits = await settings_repo.get("price_credits_10") or "500"
        price_monthly = await settings_repo.get("price_premium_monthly") or "2000"

    tier = "⭐ Premium" if (user and user.is_premium) else "🆓 Free"
    credits = (user.credits or 0) if user else 0
    currency = user.preferred_currency if user else "USD"
    tz = user.timezone if user else "UTC"

    text = (
        f"💼 *Your Account*\n\n"
        f"Tier: {tier}\n"
        f"🪙 Credits: `{credits}`\n"
        f"🌍 Currency: `{currency}`\n"
        f"🕐 Timezone: `{tz}`\n\n"
        f"_10 Credits = {price_credits} {currency}_\n"
        f"_1 Month Premium = {price_monthly} {currency}_"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Go to Shop", callback_data="go_shop")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
