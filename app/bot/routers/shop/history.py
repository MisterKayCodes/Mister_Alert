from aiogram import Router, types, F
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from app.data.economy_repository import TransactionRepository
from app.utils.fmt import section

router = Router()

@router.callback_query(F.data == "my_transactions")
async def my_transactions(callback: types.CallbackQuery):
    await callback.answer("⏳")
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        tx_repo = TransactionRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user: return await callback.answer("User not found.")
        txs = await tx_repo.get_user_transactions(user.id)
    
    if not txs:
        return await callback.message.edit_text(section("📜", "My Transactions", "_No transactions yet._"), parse_mode="Markdown")
        
    lines = []
    for tx in txs[:10]:
        icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(tx.status, "❓")
        lines.append(f"{icon} #{tx.id} · {tx.tx_type} · `{tx.amount} {tx.currency}`")
        
    await callback.message.edit_text(section("📜", "My Transactions", "\n".join(lines)), parse_mode="Markdown")
