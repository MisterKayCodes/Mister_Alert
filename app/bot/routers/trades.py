from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.bot.states.trade_states import TradeStates
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository, TradeRepository
from app.utils.fmt import (
    section, header, DIVIDER, row,
    trade_card, success, error, warning
)

router = Router()


@router.message(F.text == "📈 Trades")
async def trades_menu(message: types.Message):
    await message.answer(
        section("📈", "Trade Portfolio", 
                "Track and manage your active positions.\n\n"
                "🚧 *Coming Soon*\n"
                "We are currently polishing the dashboard to give you a pro-level experience. Stay tuned!"),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "view_trades")
async def view_trades(callback: types.CallbackQuery):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    telegram_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("User not found.")
            return
        all_open = await trade_repo.get_open_trades()
        user_trades = [t for t in all_open if t.user_id == user.id]

    if not user_trades:
        await callback.message.edit_text(
            section("📈", "Open Trades", "_No open trades. Log a trade to start tracking._"),
            parse_mode="Markdown"
        )
        return

    await callback.message.edit_text(
        header("📋", "Open Trades — tap to manage:"),
        parse_mode="Markdown"
    )
    for t in user_trades:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🎯 Edit SL/TP", callback_data="edit_trade:" + str(t.id)),
                types.InlineKeyboardButton(text="❌ Close", callback_data="close_trade:" + str(t.id)),
            ],
            [types.InlineKeyboardButton(text="🗑️ Delete Record", callback_data="delete_trade:" + str(t.id))],
        ])
        await callback.message.answer(
            trade_card(t.symbol, t.direction, str(t.entry_price),
                       str(t.stop_loss), str(t.take_profit)),
            reply_markup=kb, parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("delete_trade:"))
async def delete_trade_handler(callback: types.CallbackQuery):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    trade_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        trade_repo = TradeRepository(session)
        await trade_repo.delete_trade(trade_id)
    await callback.message.edit_text(success("Trade record deleted."), parse_mode="Markdown")
    await callback.answer("Deleted.")


@router.callback_query(F.data.startswith("close_trade:"))
async def close_trade_manual(callback: types.CallbackQuery):
    await callback.answer("⏳")  # Clear Telegram spinner instantly
    trade_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        trade_repo = TradeRepository(session)
        await trade_repo.close_trade(trade_id, "manual")
    await callback.message.edit_text(success("Trade closed manually."), parse_mode="Markdown")
    await callback.answer("Closed.")


@router.callback_query(F.data.startswith("edit_trade:"))
async def start_edit_trade(callback: types.CallbackQuery, state: FSMContext):
    trade_id = int(callback.data.split(":")[1])
    await state.update_data(edit_trade_id=trade_id)
    await state.set_state(TradeStates.waiting_for_new_sl)
    await callback.message.answer(
        header("✏️", "Edit Trade Targets") + "\n" + DIVIDER + "\n"
        "Enter new *Stop Loss* (or `0` to remove):",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(TradeStates.waiting_for_new_sl)
async def process_new_sl(message: types.Message, state: FSMContext):
    try:
        sl = float(message.text)
        sl = None if sl == 0 else sl
        await state.update_data(new_sl=sl)
        await state.set_state(TradeStates.waiting_for_new_tp)
        await message.answer(
            "Enter new *Take Profit* (or `0` to remove):",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(error("Invalid number. Enter SL or 0."), parse_mode="Markdown")


@router.message(TradeStates.waiting_for_new_tp)
async def process_new_tp(message: types.Message, state: FSMContext):
    try:
        tp = float(message.text)
        tp = None if tp == 0 else tp
        data = await state.get_data()
        trade_id = data["edit_trade_id"]
        sl = data["new_sl"]
        async with AsyncSessionLocal() as session:
            trade_repo = TradeRepository(session)
            await trade_repo.update_trade_targets(trade_id, sl, tp)
        await message.answer(
            success("Trade targets updated!") + "\n" +
            row("🛑", "New SL", str(sl) if sl else "Removed") + "\n" +
            row("🎯", "New TP", str(tp) if tp else "Removed"),
            parse_mode="Markdown"
        )
        await state.clear()
    except ValueError:
        await message.answer(error("Invalid number. Enter TP or 0."), parse_mode="Markdown")
