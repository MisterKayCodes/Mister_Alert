import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings
from data.database import AsyncSessionLocal
from data.repository import UserRepository
from data.economy_repository import (
    SettingsRepository, PaymentMethodRepository, TransactionRepository
)

router = Router()
logger = logging.getLogger(__name__)


def admin_only(func):
    """Decorator to restrict handler to admin users."""
    import functools
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if user_id not in settings.admin_ids:
            if hasattr(event, 'answer'):
                await event.answer("⛔ Admin access only.")
            return
        return await func(event, *args, **kwargs)
    return wrapper


# ──────────────────────────────────────────────────────────────
# ADMIN MAIN PANEL
# ──────────────────────────────────────────────────────────────

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👥 User Management", callback_data="admin:users")],
        [types.InlineKeyboardButton(text="💳 Payment Methods", callback_data="admin:payments")],
        [types.InlineKeyboardButton(text="⏳ Pending Transactions", callback_data="admin:transactions")],
        [types.InlineKeyboardButton(text="💬 Support Tickets", callback_data="admin:support")],
        [types.InlineKeyboardButton(text="⚙️ Bot Settings & Captions", callback_data="admin:settings")],
        [types.InlineKeyboardButton(text="📊 System Stats", callback_data="admin:stats")],
    ])
    await message.answer(
        "🕹️ *Mister Alert Admin Panel*\n\nYou have full control. What would you like to manage?",
        reply_markup=kb,
        parse_mode="Markdown"
    )


# ──────────────────────────────────────────────────────────────
# PAYMENT METHODS MANAGEMENT
# ──────────────────────────────────────────────────────────────

class AdminPaymentStates(StatesGroup):
    awaiting_pm_name = State()
    awaiting_pm_details = State()
    awaiting_pm_edit_id = State()
    awaiting_pm_edit_field = State()
    awaiting_pm_edit_value = State()


class AdminSupportStates(StatesGroup):
    awaiting_reply_text = State()


@router.callback_query(F.data == "admin:payments")
async def admin_payments(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Access denied.")
        return

    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        methods = await pm_repo.get_all()

    text = "💳 *Payment Methods*\n\n"
    buttons = []
    for pm in methods:
        status = "✅" if pm.is_active else "💤"
        text += f"{status} *{pm.name}* (ID: {pm.id})\n"
        buttons.append([
            types.InlineKeyboardButton(text=f"✏️ {pm.name}", callback_data=f"admin:pm_edit:{pm.id}"),
            types.InlineKeyboardButton(text="🗑️", callback_data=f"admin:pm_delete:{pm.id}"),
        ])

    buttons.append([types.InlineKeyboardButton(text="➕ Add New Method", callback_data="admin:pm_add")])
    buttons.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")])

    await callback.message.edit_text(
        text or "No payment methods yet.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:pm_add")
async def admin_pm_add(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Access denied.")
        return
    await state.set_state(AdminPaymentStates.awaiting_pm_name)
    await callback.message.answer("📝 Enter the *name* for the new payment method (e.g. 'Mpesa'):", parse_mode="Markdown")
    await callback.answer()


@router.message(AdminPaymentStates.awaiting_pm_name)
async def admin_pm_name_received(message: types.Message, state: FSMContext):
    await state.update_data(pm_name=message.text.strip())
    await state.set_state(AdminPaymentStates.awaiting_pm_details)
    await message.answer(
        "📋 Enter the *full payment details* (this is shown to users).\n\n"
        "Tip: Use Markdown for formatting, e.g.:\n"
        "`Bank: Kuda\nAccount: 2006539959\nName: Donald Emeruwa`",
        parse_mode="Markdown"
    )


@router.message(AdminPaymentStates.awaiting_pm_details)
async def admin_pm_details_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.create(data["pm_name"], message.text.strip())
    await message.answer(f"✅ Payment method *{pm.name}* created successfully!", parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("admin:pm_edit:"))
async def admin_pm_edit(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔ Access denied.")
        return
    pm_id = int(callback.data.split(":")[2])
    await state.update_data(pm_id=pm_id)

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Edit Name", callback_data=f"admin:pm_field:name:{pm_id}")],
        [types.InlineKeyboardButton(text="📋 Edit Details", callback_data=f"admin:pm_field:details:{pm_id}")],
        [types.InlineKeyboardButton(text="🔀 Toggle Active", callback_data=f"admin:pm_toggle:{pm_id}")],
    ])
    await callback.message.edit_text("What would you like to edit?", reply_markup=buttons)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pm_field:"))
async def admin_pm_field(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    _, _, field, pm_id = callback.data.split(":")
    await state.update_data(pm_edit_field=field, pm_id=int(pm_id))
    await state.set_state(AdminPaymentStates.awaiting_pm_edit_value)
    await callback.message.answer(f"📝 Enter the new *{field}*:", parse_mode="Markdown")
    await callback.answer()


@router.message(AdminPaymentStates.awaiting_pm_edit_value)
async def admin_pm_edit_value_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data["pm_edit_field"]
    pm_id = data["pm_id"]
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        await pm_repo.update(pm_id, **{field: message.text.strip()})
    await message.answer(f"✅ Payment method *{field}* updated!", parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("admin:pm_toggle:"))
async def admin_pm_toggle(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    pm_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.get_by_id(pm_id)
        if pm:
            await pm_repo.update(pm_id, is_active=(not pm.is_active))
            status = "✅ Active" if not pm.is_active else "💤 Disabled"
            await callback.answer(f"Payment method is now {status}")
    await callback.message.edit_text(f"✅ Status toggled for method ID {pm_id}.")


@router.callback_query(F.data.startswith("admin:pm_delete:"))
async def admin_pm_delete(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    pm_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        await pm_repo.delete(pm_id)
    await callback.message.edit_text(f"🗑️ Payment method deleted.")
    await callback.answer("Deleted.")


# ──────────────────────────────────────────────────────────────
# BOT SETTINGS MANAGEMENT
# ──────────────────────────────────────────────────────────────

class AdminSettingsStates(StatesGroup):
    awaiting_setting_key = State()
    awaiting_setting_value = State()


@router.callback_query(F.data == "admin:settings")
async def admin_settings(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return

    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        all_settings = await settings_repo.get_all()

    lines = [f"• `{s.key}` = `{s.value}`" for s in all_settings]
    text = "⚙️ *Bot Settings*\n\n" + "\n".join(lines) if lines else "No settings found."

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Edit a Setting", callback_data="admin:setting_edit")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")],
    ])
    await callback.message.edit_text(text, reply_markup=buttons, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin:setting_edit")
async def admin_setting_edit(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    await state.set_state(AdminSettingsStates.awaiting_setting_key)
    await callback.message.answer(
        "🔑 Enter the *key* of the setting to edit (e.g. `welcome_text`, `alert_limit_free`):",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AdminSettingsStates.awaiting_setting_key)
async def admin_setting_key_received(message: types.Message, state: FSMContext):
    await state.update_data(setting_key=message.text.strip())
    await state.set_state(AdminSettingsStates.awaiting_setting_value)
    await message.answer("📝 Enter the *new value*:", parse_mode="Markdown")


@router.message(AdminSettingsStates.awaiting_setting_value)
async def admin_setting_value_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data["setting_key"]
    value = message.text.strip()
    async with AsyncSessionLocal() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set(key, value)
    await message.answer(f"✅ Setting `{key}` updated to:\n`{value}`", parse_mode="Markdown")
    await state.clear()


# ──────────────────────────────────────────────────────────────
# TRANSACTION APPROVAL QUEUE
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:transactions")
async def admin_transactions(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return

    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        pending = await tx_repo.get_pending()

    if not pending:
        await callback.message.edit_text("✅ No pending transactions! All clear.", parse_mode="Markdown")
        return

    for tx in pending[:5]:  # Show 5 at a time to avoid spam
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


@router.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve_tx(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    tx_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        tx = await tx_repo.approve(tx_id, admin_note="Approved by admin")

        if tx:
            # Credit the user
            from sqlalchemy import update
            from data.models import User
            settings_repo = SettingsRepository(session)

            if tx.tx_type == "credits":
                credits_per_pack = 10  # Default pack size
                await session.execute(
                    update(User).where(User.id == tx.user_id)
                    .values(credits=User.credits + credits_per_pack)
                )
            elif tx.tx_type in ("monthly", "yearly"):
                from datetime import datetime, timezone, timedelta
                duration = timedelta(days=30 if tx.tx_type == "monthly" else 365)
                await session.execute(
                    update(User).where(User.id == tx.user_id)
                    .values(is_premium=True, premium_until=datetime.now(timezone.utc) + duration)
                )
            await session.commit()

    await callback.message.edit_text(
        f"✅ Transaction #{tx_id} *approved* and user credited!",
        parse_mode="Markdown"
    )
    await callback.answer("Approved!")


@router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject_tx(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    tx_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        await tx_repo.reject(tx_id, admin_note="Rejected by admin")

    await callback.message.edit_text(f"❌ Transaction #{tx_id} *rejected*.", parse_mode="Markdown")
    await callback.answer("Rejected.")


# ──────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ──────────────────────────────────────────────────────────────

class AdminUserStates(StatesGroup):
    awaiting_target_id = State()
    awaiting_credits_amount = State()


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬆️ Promote User to Premium", callback_data="admin:promote")],
        [types.InlineKeyboardButton(text="⬇️ Demote User", callback_data="admin:demote")],
        [types.InlineKeyboardButton(text="🪙 Add Credits to User", callback_data="admin:add_credits")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")],
    ])
    await callback.message.edit_text("👥 *User Management*", reply_markup=buttons, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.in_({"admin:promote", "admin:demote", "admin:add_credits"}))
async def admin_user_action(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    action = callback.data.split(":")[1]
    await state.update_data(admin_action=action)
    await state.set_state(AdminUserStates.awaiting_target_id)
    await callback.message.answer("🔍 Enter the *Telegram ID* of the user:", parse_mode="Markdown")
    await callback.answer()


@router.message(AdminUserStates.awaiting_target_id)
async def admin_user_id_received(message: types.Message, state: FSMContext):
    telegram_id = message.text.strip()
    data = await state.get_data()
    action = data["admin_action"]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)

        if not user:
            await message.answer(f"❌ No user found with Telegram ID `{telegram_id}`.", parse_mode="Markdown")
            await state.clear()
            return

        if action == "add_credits":
            await state.update_data(target_user_id=user.id)
            await state.set_state(AdminUserStates.awaiting_credits_amount)
            await message.answer("🪙 How many credits to add?")
            return

        from sqlalchemy import update
        from data.models import User as UserModel
        from datetime import datetime, timezone, timedelta

        if action == "promote":
            await session.execute(
                update(UserModel).where(UserModel.id == user.id)
                .values(is_premium=True, premium_until=datetime.now(timezone.utc) + timedelta(days=30))
            )
            msg = f"⬆️ User `{telegram_id}` promoted to *Premium* for 30 days!"
        else:
            await session.execute(
                update(UserModel).where(UserModel.id == user.id)
                .values(is_premium=False, premium_until=None)
            )
            msg = f"⬇️ User `{telegram_id}` demoted to Free tier."

        await session.commit()

    await message.answer(msg, parse_mode="Markdown")
    await state.clear()


@router.message(AdminUserStates.awaiting_credits_amount)
async def admin_credits_received(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Enter a valid number.")
        return

    data = await state.get_data()
    from sqlalchemy import update
    from data.models import User as UserModel

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserModel).where(UserModel.id == data["target_user_id"])
            .values(credits=UserModel.credits + amount)
        )
        await session.commit()

    await message.answer(f"✅ Added *{amount}* credits to user!", parse_mode="Markdown")
    await state.clear()


# ──────────────────────────────────────────────────────────────
# STATS
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return

    from sqlalchemy import select, func as sqlfunc
    from data.models import User as UserModel, Alert, Trade, Transaction as TxModel

    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(sqlfunc.count(UserModel.id)))).scalar()
        premium_users = (await session.execute(
            select(sqlfunc.count(UserModel.id)).where(UserModel.is_premium == True)
        )).scalar()
        total_alerts = (await session.execute(select(sqlfunc.count(Alert.id)))).scalar()
        pending_txs = (await session.execute(
            select(sqlfunc.count(TxModel.id)).where(TxModel.status == "pending")
        )).scalar()

    await callback.message.edit_text(
        f"📊 *System Stats*\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"⭐ Premium Users: `{premium_users}`\n"
        f"🔔 Active Alerts: `{total_alerts}`\n"
        f"⏳ Pending Payments: `{pending_txs}`",
        parse_mode="Markdown"
    )
    await callback.answer()


# ──────────────────────────────────────────────────────────────
# SUPPORT TICKET MANAGEMENT
# ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:support")
async def admin_support_tickets(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return

    from data.support_repository import SupportTicketRepository
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        tickets = await support_repo.get_all_open()

    if not tickets:
        await callback.message.edit_text(
            "✅ *Support Tickets*\n\nAll caught up! No open tickets.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")]
            ]),
            parse_mode="Markdown"
        )
        return

    text = f"💬 *Open Support Tickets ({len(tickets)})*\n\n"
    buttons = []
    for t in tickets[:10]: # Show first 10
        text += f"🎫 #{t.id} - {t.message[:40]}...\n"
        buttons.append([types.InlineKeyboardButton(
            text=f"👁️ View Ticket #{t.id}", 
            callback_data=f"admin:view_ticket:{t.id}"
        )])

    buttons.append([types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")])
    await callback.message.edit_text(
        text, 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin:view_ticket:"))
async def admin_view_ticket(callback: types.CallbackQuery):
    ticket_id = int(callback.data.split(":")[2])
    
    from data.support_repository import SupportTicketRepository
    from data.repository import UserRepository
    
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        user_repo = UserRepository(session)
        ticket = await support_repo.get_by_id(ticket_id)
        
        if not ticket:
            await callback.answer("❌ Ticket not found.")
            return
            
        user = await user_repo.get_by_id(ticket.user_id)
        username = f"(@{user.username})" if user and user.username else ""

    text = (
        f"🎫 *Ticket #{ticket.id}*\n"
        f"👤 From: {user.full_name if user else 'Unknown'} {username}\n"
        f"🆔 User ID: `{user.telegram_id if user else 'N/A'}`\n"
        f"📅 Date: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"💬 *Message:*\n{ticket.message}"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💬 Reply", callback_data=f"admin:reply_ticket:{ticket.id}")],
        [types.InlineKeyboardButton(text="↩️ Back to List", callback_data="admin:support")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin:reply_ticket:"))
async def admin_start_reply(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminSupportStates.awaiting_reply_text)
    
    await callback.message.answer("📝 Type your reply to the user:")
    await callback.answer()

@router.message(AdminSupportStates.awaiting_reply_text)
async def admin_send_reply(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data["reply_ticket_id"]
    reply_text = message.text.strip()
    
    from data.support_repository import SupportTicketRepository
    from data.repository import UserRepository
    
    async with AsyncSessionLocal() as session:
        support_repo = SupportTicketRepository(session)
        user_repo = UserRepository(session)
        
        ticket = await support_repo.add_reply(ticket_id, reply_text)
        if not ticket:
            await message.answer("❌ Error: Ticket not found.")
            await state.clear()
            return
            
        user = await user_repo.get_by_id(ticket.user_id)
        
    # Send reply to user
    try:
        user_msg = (
            "👩‍💻 *Support Reply*\n\n"
            f"Your message: _{ticket.message}_\n\n"
            f"✅ *Response:*\n{reply_text}"
        )
        await bot.send_message(user.telegram_id, user_msg, parse_mode="Markdown")
        await message.answer(f"✅ Reply sent to user {user.telegram_id}!")
    except Exception as e:
        await message.answer(f"⚠️ Reply saved in DB but failed to send via Telegram: {e}")
        
    await state.clear()


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: types.CallbackQuery):
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("⛔")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👥 User Management", callback_data="admin:users")],
        [types.InlineKeyboardButton(text="💳 Payment Methods", callback_data="admin:payments")],
        [types.InlineKeyboardButton(text="⏳ Pending Transactions", callback_data="admin:transactions")],
        [types.InlineKeyboardButton(text="💬 Support Tickets", callback_data="admin:support")],
        [types.InlineKeyboardButton(text="⚙️ Bot Settings & Captions", callback_data="admin:settings")],
        [types.InlineKeyboardButton(text="📊 System Stats", callback_data="admin:stats")],
    ])
    await callback.message.edit_text(
        "🕹️ *Mister Alert Admin Panel*",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await callback.answer()
