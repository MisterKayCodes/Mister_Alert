import logging
from aiogram import Router, types, F
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository, AlertRepository
from app.utils.fmt import (
    header, row, success, error, warning, DIVIDER, alert_card
)

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "view_alerts")
async def view_alerts(callback: types.CallbackQuery):
    await callback.answer("⏳")
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
            "🔔 *My Alerts*\n\nYou have no alerts yet.",
            parse_mode="Markdown"
        )
        return

    speed_label = "⚡ Fast Lane" if is_premium else "🐢 Standard"
    await callback.message.edit_text(
        f"{header('📋', 'My Alerts')}\n{DIVIDER}\n"
        f"Polling speed: *{speed_label}*",
        parse_mode="Markdown"
    )
    for a in alerts:
        cond_str = f"> {a.price_above}" if a.price_above else f"< {a.price_below}"
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
    await callback.answer("⏳")
    alert_id = int(callback.data.split(":")[1])
    telegram_id = str(callback.from_user.id)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user or (user.credits or 0) < 1:
            await callback.message.answer(
                warning("⚡ *No Credits!*"),
                parse_mode="Markdown"
            )
            return

        success_deduct = await user_repo.deduct_credits(user.id, 1)
        if success_deduct:
            await alert_repo.boost_alert(alert_id)
            await callback.message.edit_text(
                success("⚡ Alert Boosted!"),
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
