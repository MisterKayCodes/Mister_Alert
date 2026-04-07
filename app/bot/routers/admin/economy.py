import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import (
    PaymentMethodRepository, TransactionRepository, SettingsRepository
)
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

class AdminPaymentStates(StatesGroup):
    awaiting_pm_name = State()
    awaiting_pm_details = State()
    awaiting_pm_edit_id = State()
    awaiting_pm_edit_field = State()
    awaiting_pm_edit_value = State()

@router.callback_query(F.data == "admin:payments")
@admin_only
async def admin_payments(callback: types.CallbackQuery):
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
@admin_only
async def admin_pm_add(callback: types.CallbackQuery, state: FSMContext):
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
@admin_only
async def admin_pm_edit(callback: types.CallbackQuery, state: FSMContext):
    pm_id = int(callback.data.split(":")[2])
    await state.update_data(pm_id=pm_id)

    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Edit Name", callback_data=f"admin:pm_field:name:{pm_id}")],
        [types.InlineKeyboardButton(text="📋 Edit Details", callback_data=f"admin:pm_field:details:{pm_id}")],
        [types.InlineKeyboardButton(text="🔀 Toggle Active", callback_data=f"admin:pm_toggle:{pm_id}")],
    ])
    await callback.message.edit_text("What would you like to edit?", reply_markup=buttons)
    await callback.answer()

@router.callback_query(F.data.startswith("admin:pm_toggle:"))
@admin_only
async def admin_pm_toggle(callback: types.CallbackQuery):
    pm_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.get_by_id(pm_id)
        if pm:
            await pm_repo.update(pm_id, is_active=(not pm.is_active))
            status = "✅ Active" if not pm.is_active else "💤 Disabled"
            await callback.answer(f"Payment method is now {status}")
    await callback.message.edit_text(f"✅ Status toggled for method ID {pm_id}.")

@router.callback_query(F.data == "admin:transactions")
@admin_only
async def admin_transactions(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        pending = await tx_repo.get_pending()

    if not pending:
        await callback.message.edit_text("✅ No pending transactions! All clear.", parse_mode="Markdown")
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

@router.callback_query(F.data.startswith("admin:approve:"))
@admin_only
async def admin_approve_tx(callback: types.CallbackQuery):
    tx_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        tx_repo = TransactionRepository(session)
        tx = await tx_repo.approve_and_credit_user(tx_id, admin_note="Approved by admin")

    await callback.message.edit_text(
        f"✅ Transaction #{tx_id} *approved* and user credited!",
        parse_mode="Markdown"
    )
    await callback.answer("Approved!")
