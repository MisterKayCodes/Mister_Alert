import logging
from aiogram import Router, types, F, Bot
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import TransactionRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "admin:transactions")
@admin_only
async def admin_transactions(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        pending = await tx_repo.get_pending()

    if not pending:
        await callback.message.edit_text(
            "✅ No pending transactions! All clear.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")]
            ]),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    for tx in pending[:5]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Approve", callback_data=f"admin:approve:{tx.id}"),
                types.InlineKeyboardButton(text="❌ Reject", callback_data=f"admin:reject:{tx.id}"),
            ]
        ])
        await callback.message.answer(
            f"⏳ *Transaction #{tx.id}*\n"
            f"User ID: `{tx.user_id}`\n"
            f"Type: `{tx.tx_type}`\n"
            f"Amount: `{tx.amount} {tx.currency}`\n"
            f"Reference: `{tx.evidence}`",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    await callback.answer(f"{len(pending)} pending transaction(s).")


async def _notify_user(bot: Bot, telegram_id: str, text: str):
    """Helper to DM a user with error handling."""
    try:
        await bot.send_message(chat_id=int(telegram_id), text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {telegram_id}: {e}")


@router.callback_query(F.data.startswith("admin:approve:"))
@admin_only
async def admin_approve_tx(callback: types.CallbackQuery, bot: Bot):
    tx_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        tx = await tx_repo.approve_and_credit_user(tx_id, admin_note="Approved by admin")

        if tx:
            from app.data.repositories import UserRepository
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(tx.user_id)
            if user:
                await _notify_user(bot, user.telegram_id, (
                    f"✅ <b>Payment Approved!</b>\n\n"
                    f"Your {tx.tx_type} transaction of <code>{tx.amount} {tx.currency}</code> has been approved.\n\n"
                    f"<i>Your account has been credited. Enjoy!</i>"
                ))

    await callback.message.edit_text(
        f"✅ Transaction #{tx_id} *approved* and user credited!",
        parse_mode="Markdown"
    )
    await callback.answer("Approved!")


@router.callback_query(F.data.startswith("admin:reject:"))
@admin_only
async def admin_reject_tx(callback: types.CallbackQuery, bot: Bot):
    tx_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        tx = await tx_repo.reject(tx_id, admin_note="Rejected by admin")

        if tx:
            from app.data.repositories import UserRepository
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(tx.user_id)
            if user:
                await _notify_user(bot, user.telegram_id, (
                    f"❌ <b>Payment Rejected</b>\n\n"
                    f"Your {tx.tx_type} transaction of <code>{tx.amount} {tx.currency}</code> was not approved.\n\n"
                    f"<i>If you believe this is an error, please contact Support.</i>"
                ))

    await callback.message.edit_text(
        f"❌ Transaction #{tx_id} *rejected*.",
        parse_mode="Markdown"
    )
    await callback.answer("Rejected.")
