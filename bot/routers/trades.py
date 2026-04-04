from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.trade_states import TradeStates
from data.database import AsyncSessionLocal
from data.repository import UserRepository, TradeRepository

router = Router()

@router.message(F.text == "📈 Trades")
async def trades_menu(message: types.Message):
    """Present the Trades menu."""
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📜 View Open Trades", callback_data="view_trades")],
        ]
    )
    await message.answer("📈 **Trade Portfolio**\n\nManage your active positions:", reply_markup=kb)

@router.callback_query(F.data == "view_trades")
async def view_trades(callback: types.CallbackQuery):
    """Display user's open trades with action buttons."""
    telegram_id = str(callback.from_user.id)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("❌ User not found.")
            return
            
        trades = await trade_repo.get_open_trades()
        # Filter for current user (Repository currently doesn't filter by user for open trades)
        user_trades = [t for t in trades if t.user_id == user.id]
        
    if not user_trades:
        await callback.message.edit_text("📈 No open trades found.")
        return
        
    await callback.message.edit_text("🎯 **Open Trades**\nClick below to manage SL/TP or close a trade:")

    for t in user_trades:
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🎯 Edit SL/TP", callback_data=f"edit_trade:{t.id}"),
                 types.InlineKeyboardButton(text="❌ Close", callback_data=f"close_trade:{t.id}")],
                [types.InlineKeyboardButton(text="🗑️ Delete Record", callback_data=f"delete_trade:{t.id}")]
            ]
        )
        
        text = (
            f"📍 **{t.symbol}** | {t.direction}\n"
            f"💰 Entry: `{t.entry_price}`\n"
            f"🛑 SL: `{t.stop_loss or 'None'}`\n"
            f"🎯 TP: `{t.take_profit or 'None'}`"
        )
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("delete_trade:"))
async def delete_trade_handler(callback: types.CallbackQuery):
    """Permanently delete a trade record."""
    trade_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        trade_repo = TradeRepository(session)
        await trade_repo.delete_trade(trade_id)
    await callback.message.edit_text("🗑️ **Trade Record Deleted**", parse_mode="Markdown")
    await callback.answer("Deleted.")

@router.callback_query(F.data.startswith("close_trade:"))
async def close_trade_manual(callback: types.CallbackQuery):
    """Manually mark a trade as closed."""
    trade_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        trade_repo = TradeRepository(session)
        # Note: In a manual close, we don't have the current price easily
        # so we mark it as manual close. Result defaults to 'manual'
        await trade_repo.close_trade(trade_id, "manual")
    await callback.message.edit_text("🏁 **Trade Closed Manually**", parse_mode="Markdown")
    await callback.answer("Closed.")

@router.callback_query(F.data.startswith("edit_trade:"))
async def start_edit_trade(callback: types.CallbackQuery, state: FSMContext):
    """Start SL/TP edit flow."""
    trade_id = int(callback.data.split(":")[1])
    await state.update_data(edit_trade_id=trade_id)
    await state.set_state(TradeStates.waiting_for_new_sl)
    await callback.message.answer("🛑 **Editing Trade Targets**\n\nEnter NEW **Stop Loss** (or '0' for None):")
    await callback.answer()

@router.message(TradeStates.waiting_for_new_sl)
async def process_new_sl(message: types.Message, state: FSMContext):
    """Save SL and ask for TP."""
    try:
        sl = float(message.text)
        sl = None if sl == 0 else sl
        await state.update_data(new_sl=sl)
        await state.set_state(TradeStates.waiting_for_new_tp)
        await message.answer("🎯 Enter NEW **Take Profit** (or '0' for None):")
    except ValueError:
        await message.answer("❌ Invalid number. Enter SL or '0'.")

@router.message(TradeStates.waiting_for_new_tp)
async def process_new_tp(message: types.Message, state: FSMContext):
    """Finalize SL/TP update."""
    try:
        tp = float(message.text)
        tp = None if tp == 0 else tp
        user_data = await state.get_data()
        trade_id = user_data["edit_trade_id"]
        sl = user_data["new_sl"]
        
        async with AsyncSessionLocal() as session:
            trade_repo = TradeRepository(session)
            await trade_repo.update_trade_targets(trade_id, sl, tp)
            
        await message.answer(f"✅ **Trade Updated Successfully!**\nNew targets saved.", parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("❌ Invalid number. Enter TP or '0'.")
