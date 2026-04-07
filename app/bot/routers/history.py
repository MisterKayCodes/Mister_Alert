import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository, TradeRepository
from app.core.trades.analytics import calculate_trade_performance
from app.utils.fmt import (
    section, header, DIVIDER,
    performance_dashboard, trade_history_list, error
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "📜 History")
async def history_menu(message: types.Message):
    await message.answer(
        section("📜", "Trade Historian", 
                "Analyze your past performance and trading edge.\n\n"
                "🚧 *Coming Soon*\n"
                "We are finishing the analytics engine to help you find your peak performance. Hang tight!"),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "stats_performance")
async def view_performance(callback: types.CallbackQuery):
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("User not found.")
            return
        trades = await trade_repo.get_all_closed_trades(user.id)
        
        # Convert models to dicts for the 'Pure' Core Analytics engine
        trade_dicts = [
            {
                "symbol": t.symbol,
                "entry_price": t.entry_price,
                "closed_at_price": t.closed_at_price,
                "direction": t.direction
            } for t in trades
        ]
        stats = calculate_trade_performance(trade_dicts)

    if stats["total_trades"] == 0:
        await callback.message.edit_text(
            section("📈", "Performance Dashboard",
                    "_No closed trades yet. Close your first trade to see stats here!_"),
            parse_mode="Markdown"
        )
        return

    await callback.message.edit_text(performance_dashboard(stats), parse_mode="Markdown")


@router.callback_query(F.data == "stats_history")
async def view_trade_history(callback: types.CallbackQuery):
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("User not found.")
            return
        trades = await trade_repo.get_user_trade_history(user.id, limit=10)

    await callback.message.edit_text(trade_history_list(trades), parse_mode="Markdown")
