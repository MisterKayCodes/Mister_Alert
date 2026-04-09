from aiogram import Router, types, F
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from app.utils.fmt import section, success

router = Router()
SUPPORTED_CURRENCIES = ["USD", "NGN", "KES", "GBP", "EUR"]

@router.callback_query(F.data == "pick_currency")
async def pick_currency(callback: types.CallbackQuery):
    await callback.answer("⏳")
    buttons = [
        [types.InlineKeyboardButton(text=c, callback_data="set_currency:" + c)]
        for c in SUPPORTED_CURRENCIES
    ]
    await callback.message.edit_text(
        section("🌍", "Currency Selection", "Prices in the Shop will update instantly."),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("set_currency:"))
async def set_currency(callback: types.CallbackQuery):
    currency_code = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if user:
            await user_repo.update_currency(user.id, currency_code)
    await callback.message.edit_text(
        success(f"Currency set to {currency_code}!") + "\n\n"
        f"_Shop prices now show in {currency_code}._",
        parse_mode="Markdown"
    )
    await callback.answer()
