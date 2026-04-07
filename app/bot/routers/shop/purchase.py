import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from app.data.economy_repository import PaymentMethodRepository, TransactionRepository
from app.utils.fmt import header, DIVIDER, row, success, error

router = Router()
logger = logging.getLogger(__name__)

class ShopStates(StatesGroup):
    awaiting_amount = State()
    awaiting_evidence = State()

@router.callback_query(F.data.startswith("buy:"))
async def select_payment_method(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    tx_type = callback.data.split(":")[1]
    await state.update_data(tx_type=tx_type)
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        methods = await pm_repo.get_all_active()
    if not methods:
        return await callback.message.edit_text(error("No payment methods configured."), parse_mode="Markdown")
    buttons = [[types.InlineKeyboardButton(text=f"🏦 {m.name}", callback_data=f"pm:{m.id}")] for m in methods]
    await callback.message.edit_text(
        header("💳", "Select Payment Method") + "\n" + DIVIDER + "\nChoose how you'd like to pay:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("pm:"))
async def show_payment_details(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    pm_id = int(callback.data.split(":")[1])
    await state.update_data(pm_id=pm_id)
    async with AsyncSessionLocal() as session:
        pm_repo = PaymentMethodRepository(session)
        pm = await pm_repo.get_by_id(pm_id)
    if not pm: return await callback.answer("Method not found.")
    await callback.message.edit_text(
        pm.details + "\n\n" + DIVIDER + "\n_Submit reference after payment._",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="✅ I Have Paid", callback_data="have_paid")]]),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "have_paid")
async def request_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("⏳")
    await state.set_state(ShopStates.awaiting_amount)
    await callback.message.answer(header("💰", "Payment — Step 1 of 2") + "\n" + DIVIDER + "\nEnter amount paid:", parse_mode="Markdown")

@router.message(ShopStates.awaiting_amount)
async def receive_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        await state.update_data(amount=amount)
        await state.set_state(ShopStates.awaiting_evidence)
        await message.answer(header("🔖", "Payment — Step 2 of 2") + "\n" + DIVIDER + "\nSend Transaction Reference:", parse_mode="Markdown")
    except ValueError:
        await message.answer(error("Invalid amount."), parse_mode="Markdown")

@router.message(ShopStates.awaiting_evidence)
async def receive_evidence(message: types.Message, state: FSMContext):
    evidence = message.text.strip()
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        tx_repo = TransactionRepository(session)
        user = await user_repo.get_or_create(str(message.from_user.id), message.from_user.username)
        tx = await tx_repo.create(user_id=user.id, amount=data["amount"], currency=user.preferred_currency, tx_type=data["tx_type"], evidence=evidence, pm_id=data["pm_id"])
    body = "\n".join([row("🔖", "Ref", evidence), row("💰", "Amt", f"{data['amount']} {user.preferred_currency}"), row("🆔", "ID", f"#{tx.id}")])
    await message.answer(success("Payment Submitted!") + "\n" + DIVIDER + "\n" + body + "\n\n_Reviewing shortly._", parse_mode="Markdown")
    await state.clear()
