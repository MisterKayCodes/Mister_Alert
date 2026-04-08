import logging
import csv
import io
from aiogram import Router, types, F
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta, timezone

from app.data.database import AsyncSessionLocal
from app.data.models import User, Trade, Alert
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "admin:stats")
@admin_only
async def admin_stats_dashboard(callback: types.CallbackQuery):
    """Generate high-level production metrics."""
    await callback.answer("📊 Crunching data...", show_alert=False)
    
    async with AsyncSessionLocal() as session:
        # 1. Total Users
        total_users = await session.scalar(select(func.count()).select_from(User))
        
        # 2. Premium Users
        premium_users = await session.scalar(
            select(func.count()).select_from(User).where(User.is_premium == True)
        )
        
        # 3. New Users (Last 7 Days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        new_users = await session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= seven_days_ago)
        )
        
        # 4. Total Active Alerts & Trades
        total_alerts = await session.scalar(select(func.count()).select_from(Alert).where(Alert.is_active == True))
        total_trades = await session.scalar(select(func.count()).select_from(Trade).where(Trade.is_closed == False))
        
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
        result = await session.execute(
            select(User).order_by(desc(User.created_at))
        )
        users = result.scalars().all()
        
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
