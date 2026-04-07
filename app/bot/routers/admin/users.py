import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.repositories import UserRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

class AdminUserStates(StatesGroup):
    awaiting_target_id = State()
    awaiting_credits_amount = State()

@router.callback_query(F.data == "admin:users")
@admin_only
async def admin_users(callback: types.CallbackQuery):
    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬆️ Promote User to Premium", callback_data="admin:promote")],
        [types.InlineKeyboardButton(text="⬇️ Demote User", callback_data="admin:demote")],
        [types.InlineKeyboardButton(text="🪙 Add Credits to User", callback_data="admin:add_credits")],
        [types.InlineKeyboardButton(text="↩️ Back", callback_data="admin:back")],
    ])
    await callback.message.edit_text("👥 *User Management*", reply_markup=buttons, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.in_({"admin:promote", "admin:demote", "admin:add_credits"}))
@admin_only
async def admin_user_action(callback: types.CallbackQuery, state: FSMContext):
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

        if action == "promote":
            await user_repo.promote_to_premium(user.id, days=30)
            msg = f"⬆️ User `{telegram_id}` promoted to *Premium* for 30 days!"
        else:
            await user_repo.demote_from_premium(user.id)
            msg = f"⬇️ User `{telegram_id}` demoted to Free tier."

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

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        await user_repo.add_credits(data["target_user_id"], amount)

    await message.answer(f"✅ Added *{amount}* credits to user!", parse_mode="Markdown")
    await state.clear()
