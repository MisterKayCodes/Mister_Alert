import logging
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.voucher_repository import VoucherRepository
from app.data.repositories import UserRepository
from datetime import datetime, timedelta, timezone

router = Router()
logger = logging.getLogger(__name__)

class RedeemStates(StatesGroup):
    waiting_for_code = State()

@router.callback_query(F.data == "redeem_code")
async def ask_for_code(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RedeemStates.waiting_for_code)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="user_home")]
    ])
    
    await callback.message.edit_text(
        "🎟️ <b>Redeem Activation Code</b>\n\n"
        "Please enter your unique 13-character activation code (e.g., <code>PREM-ABC123XY</code>).\n\n"
        "<i>Don't have a code? DM the creator to get one!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(RedeemStates.waiting_for_code)
async def process_code_redemption(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        voucher_repo = VoucherRepository(session)
        
        user = await user_repo.get_by_telegram_id(str(user_id))
        if not user:
            await message.answer("❌ Account not found. Please type /start first.")
            await state.clear()
            return
            
        result = await voucher_repo.redeem(code, user.id)
        
        if not result["success"]:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Cancel", callback_data="user_home")]
            ])
            await message.answer(f"{result['message']}\n\nPlease try again or tap Cancel.", reply_markup=kb)
            return
            
        # Code was valid and marked as used. Now apply the reward!
        reward = result["reward_type"]
        
        if reward == "premium_1_month":
            # Add 30 days of premium
            now = datetime.now(timezone.utc)
            current_expiry = user.premium_until if user.premium_until and user.premium_until > now else now
            new_expiry = current_expiry + timedelta(days=30)
            
            user.is_premium = True
            user.premium_until = new_expiry
            success_msg = f"🎉 <b>Premium Activated!</b>\n\nYou now have Premium access until <code>{new_expiry.strftime('%Y-%m-%d')}</code>."
            
        elif reward.startswith("credits_"):
            amount = int(reward.split("_")[1])
            user.credits = (user.credits or 0) + amount
            success_msg = f"🎉 <b>Credits Added!</b>\n\nYou received {amount} credits. Your new balance is <code>{user.credits}</code>."
            
        else:
            success_msg = "🎉 <b>Code Redeemed!</b> Reward applied."

        await session.commit()
    
    await message.answer(success_msg, parse_mode="HTML")
    await state.clear()
