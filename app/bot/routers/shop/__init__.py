from aiogram import Router, types, F
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from app.data.economy_repository import SettingsRepository
from app.utils.fmt import shop_menu_text, pill_tier
from . import currency, purchase, history, redeem

router = Router()
router.include_router(currency.router)
router.include_router(purchase.router)
router.include_router(history.router)
router.include_router(redeem.router)

async def _send_shop_menu(message: types.Message):
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        settings_repo = SettingsRepository(session)
        user = await user_repo.get_or_create(telegram_id, message.from_user.username)
        curr = user.preferred_currency or "USD"
        
        base_credits = float(await settings_repo.get("price_credits_10") or "5")
        base_weekly = float(await settings_repo.get("price_premium_weekly") or "7")
        base_monthly = float(await settings_repo.get("price_premium_monthly") or "20")
        base_yearly = float(await settings_repo.get("price_premium_yearly") or "180")
        
        from app.utils.currency_helper import convert_currency
        p_credits = await convert_currency(base_credits, curr)
        p_weekly = await convert_currency(base_weekly, curr)
        p_monthly = await convert_currency(base_monthly, curr)
        p_yearly = await convert_currency(base_yearly, curr)
        
        tier = pill_tier(user.is_premium)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎟️ Redeem Activation Code", callback_data="redeem_code")],
        [types.InlineKeyboardButton(text="🪙 Buy Credits (10)", callback_data="buy:credits")],
        [types.InlineKeyboardButton(text="⚡ Weekly Premium", callback_data="buy:weekly")],
        [types.InlineKeyboardButton(text="⭐ Monthly Premium", callback_data="buy:monthly")],
        [types.InlineKeyboardButton(text="👑 Yearly Premium", callback_data="buy:yearly")],
        [types.InlineKeyboardButton(text="📜 My Transactions", callback_data="my_transactions")],
    ])
    await message.answer(
        shop_menu_text(tier, user.credits or 0, curr, p_credits, p_weekly, p_monthly, p_yearly),
        reply_markup=kb, parse_mode="Markdown"
    )

@router.message(F.text == "🛒 Shop")
async def shop_menu_msg(message: types.Message):
    await _send_shop_menu(message)

@router.callback_query(F.data == "go_shop")
async def shop_menu_cb(callback: types.CallbackQuery):
    await _send_shop_menu(callback.message)
    await callback.answer()
