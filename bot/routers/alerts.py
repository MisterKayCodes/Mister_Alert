from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states.alert_states import AlertStates
from data.database import AsyncSessionLocal
from data.repository import UserRepository, AlertRepository
from utils.market_hours import is_market_open, get_market_status_label

router = Router()

@router.message(F.text == "🔔 Alerts")
async def alerts_menu(message: types.Message, state: FSMContext):
    """Present the Alerts menu."""
    await state.clear()
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Add New Alert", callback_data="add_alert")],
            [types.InlineKeyboardButton(text="📜 View All Alerts", callback_data="view_alerts")],
        ]
    )
    await message.answer("🔔 Alerts Management\n\nChoose an option:", reply_markup=kb)

@router.callback_query(F.data == "add_alert")
async def start_add_alert(callback: types.CallbackQuery, state: FSMContext):
    """Start alert creation flow."""
    await state.set_state(AlertStates.waiting_for_symbol)
    await callback.message.edit_text("🔤 Enter Symbol (e.g., BTCUSD, EURUSD):")

@router.message(AlertStates.waiting_for_symbol)
async def process_symbol(message: types.Message, state: FSMContext):
    """Save symbol and ask for condition."""
    await state.update_data(symbol=message.text.upper())
    await state.set_state(AlertStates.waiting_for_condition)
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Price Above 📈", callback_data="above"),
             types.InlineKeyboardButton(text="Price Below 📉", callback_data="below")]
        ]
    )
    await message.answer(f"Symbol: {message.text.upper()}\nSelect condition:", reply_markup=kb)

@router.callback_query(AlertStates.waiting_for_condition)
async def process_condition(callback: types.CallbackQuery, state: FSMContext):
    """Save condition and ask for price."""
    condition = callback.data
    await state.update_data(condition=condition)
    await state.set_state(AlertStates.waiting_for_price)
    
    label = "Price Above" if condition == "above" else "Price Below"
    await callback.message.edit_text(f"🚀 {label}\n\nEnter Target Price:")

@router.message(AlertStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    """Finish alert creation."""
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ Invalid price. Please enter a number.")
        return
        
    user_data = await state.get_data()
    symbol = user_data["symbol"]
    condition = user_data["condition"]
    
    # Save to database
    telegram_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.answer("❌ Error: User not found. Try /start again.")
            await state.clear()
            return
            
        # Create alert matching the price criteria
        price_above = price if condition == "above" else None
        price_below = price if condition == "below" else None
        
        await alert_repo.create_alert(
            user_id=user.id,
            symbol=symbol,
            price_above=price_above,
            price_below=price_below
        )
        
    market_warning = ""
    if not is_market_open(symbol):
        market_warning = "\n\n⚠️ **Note**: Market is currently CLOSED for this asset. Monitoring will begin at next open."
        
    await message.answer(f"✅ Alert Created Successfully!\nTracking: {symbol} @ {price}{market_warning}", parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "view_alerts")
async def view_alerts(callback: types.CallbackQuery):
    """Display user's active alerts."""
    telegram_id = str(callback.from_user.id)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        alert_repo = AlertRepository(session)
        
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("❌ User not found.")
            return
            
        alerts = await alert_repo.get_user_alerts(user.id)
        
    if not alerts:
        await callback.message.edit_text("📜 You have no active alerts.")
        return
        
    await callback.message.edit_text("🚀 **Viewing Active Alerts**\nClick below to manage or delete an alert:")

    for a in alerts:
        condition = f"> {a.price_above}" if a.price_above else f"< {a.price_below}"
        status = "⏳" if a.is_active else "✅ (Hit)"
        
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=f"🗑️ Delete {a.symbol}", callback_data=f"delete_alert:{a.id}")]
            ]
        )
        await callback.message.answer(f"📍 **{a.symbol}**\nTarget: {condition}\nStatus: {status}", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("delete_alert:"))
async def delete_alert_handler(callback: types.CallbackQuery):
    """Handle alert deletion from inline button."""
    alert_id = int(callback.data.split(":")[1])
    
    async with AsyncSessionLocal() as session:
        alert_repo = AlertRepository(session)
        await alert_repo.delete_alert(alert_id)
        
    await callback.message.edit_text("🗑️ **Alert Deleted Successfully**", parse_mode="Markdown")
    await callback.answer("Deleted.")
