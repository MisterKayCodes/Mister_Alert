import logging
from aiogram import Router, types, F
from data.database import AsyncSessionLocal
from data.repository import UserRepository, TradeRepository
from core.trades.analytics import calculate_trade_performance

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📜 History")
async def history_menu(message: types.Message):
    """Present the History options."""
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Performance Stats", callback_data="stats_performance")],
            [types.InlineKeyboardButton(text="📜 Last 10 Trades", callback_data="stats_history")],
        ]
    )
    await message.answer("📜 **Trade Historian**\n\nAnalyze your past performance:", reply_markup=kb)

@router.callback_query(F.data == "stats_performance")
async def view_performance(callback: types.CallbackQuery):
    """Calculate and display user performance stats."""
    telegram_id = str(callback.from_user.id)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("❌ User not found.")
            return
            
        trades = await trade_repo.get_all_closed_trades(user.id)
        stats = calculate_trade_performance(trades)
        
    if stats["total_trades"] == 0:
        await callback.message.edit_text("📈 **Performance Dashboard**\n\nNo closed trades found yet. Start trading to see stats!")
        return
        
    win_color = "🟢" if stats["win_rate"] >= 50 else "🔴"
    pip_color = "🟢" if stats["total_pips"] >= 0 else "🔴"
    
    text = (
        "📈 **Performance Dashboard**\n"
        "----------------------------\n"
        f"🔢 **Total Trades**: `{stats['total_trades']}`\n"
        f"{win_color} **Win Rate**: `{stats['win_rate']}%`\n"
        f"{pip_color} **Total Pips**: `{stats['total_pips']}`\n"
        f"📊 **Avg Pips/Trade**: `{stats['avg_pips']}`\n\n"
        f"✅ Wins: `{stats['wins']}` | ❌ Losses: `{stats['losses']}`"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")

@router.callback_query(F.data == "stats_history")
async def view_trade_history(callback: types.CallbackQuery):
    """List the last 10 closed trades."""
    telegram_id = str(callback.from_user.id)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("❌ User not found.")
            return
            
        trades = await trade_repo.get_user_trade_history(user.id, limit=10)
        
    if not trades:
        await callback.message.edit_text("📜 **Trade History**\n\nNo closed trades found.")
        return
        
    text = "📜 **Last 10 Trades**:\n\n"
    for t in trades:
        # Determine win/loss icon
        # We need to re-calc pips briefly for the icon or use the 'result' field if set
        # For now, we'll check the 'result' field in the model
        icon = "🟢" if t.result == "win" else "🔴" if t.result == "loss" else "⚪"
        
        date_str = t.closed_at.strftime("%y-%m-%d") if t.closed_at else "---"
        text += f"{icon} {date_str} | {t.symbol} | {t.direction}\n"
        
    await callback.message.edit_text(text, parse_mode="Markdown")
