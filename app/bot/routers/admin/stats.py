import logging
import csv
import io
from aiogram import Router, types, F
from datetime import datetime

from app.data.database import AsyncSessionLocal
from app.data.repositories.user import UserRepository
from app.data.repositories.trade import TradeRepository
from app.data.repositories.alert import AlertRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "admin:stats")
@admin_only
async def admin_stats_dashboard(callback: types.CallbackQuery):
    """Generate high-level production metrics."""
    await callback.answer("📊 Crunching data...", show_alert=False)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        trade_repo = TradeRepository(session)
        alert_repo = AlertRepository(session)
        
        total_users = await user_repo.count_all()
        premium_users = await user_repo.count_premium()
        new_users = await user_repo.count_recent(days=7)
        total_alerts = await alert_repo.count_active()
        total_trades = await trade_repo.count_active()
        
    text = (
        "📊 <b>Advanced System Analytics</b>\n\n"
        f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
        f"⭐ <b>Premium Members:</b> <code>{premium_users}</code>\n"
        f"📈 <b>Growth (7d):</b> +<code>{new_users}</code> users\n\n"
        f"🔔 <b>Active Alerts:</b> <code>{total_alerts}</code>\n"
        f"📉 <b>Active Trades:</b> <code>{total_trades}</code>\n\n"
        "<i>Use the Export button to download a full CSV of your userbase for marketing.</i>"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📥 Export Users (CSV)", callback_data="admin:stats_export")],
        [types.InlineKeyboardButton(text="↩️ Back to Panel", callback_data="admin:back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "admin:stats_export")
@admin_only
async def admin_export_csv(callback: types.CallbackQuery):
    """Generates and sends a CSV of all users for external marketing."""
    await callback.answer("Generating CSV...", show_alert=False)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_ordered()
        
    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Telegram ID", "Username", "Premium", "Credits", "Joined At"])
    
    for u in users:
        writer.writerow([
            u.id, 
            u.telegram_id, 
            u.username or "N/A", 
            "Yes" if u.is_premium else "No", 
            u.credits,
            u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "Unknown"
        ])
    
    output.seek(0)
    document = types.BufferedInputFile(
        output.getvalue().encode('utf-8'), 
        filename=f"mister_alert_users_{datetime.now().strftime('%Y%m%d')}.csv"
    )
    
    # Send document
    await callback.message.answer_document(
        document=document, 
        caption="📥 Here is your complete User Database export."
    )
    await callback.answer()
