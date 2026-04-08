import logging
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.data.database import AsyncSessionLocal
from app.data.voucher_repository import VoucherRepository
from .dashboard import admin_only

router = Router()
logger = logging.getLogger(__name__)

class AdminVoucherStates(StatesGroup):
    waiting_for_type = State()

@router.callback_query(F.data == "admin:mint_vouchers")
@admin_only
async def admin_mint_vouchers_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💎 Mint 1 Month Premium", callback_data="admin:mint:premium_1_month")],
        [types.InlineKeyboardButton(text="🪙 Mint 500 Credits", callback_data="admin:mint:credits_500")],
        [types.InlineKeyboardButton(text="🪙 Mint 1000 Credits", callback_data="admin:mint:credits_1000")],
        [types.InlineKeyboardButton(text="↩️ Back to Panel", callback_data="admin:back")]
    ])
    await callback.message.edit_text(
        "🎟️ <b>The Mint (Voucher Generator)</b>\n\n"
        "Generate single-use activation codes to sell to users. What would you like to mint?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin:mint:"))
@admin_only
async def execute_mint(callback: types.CallbackQuery):
    reward_type = callback.data.split(":")[2]
    
    async with AsyncSessionLocal() as session:
        repo = VoucherRepository(session)
        voucher = await repo.mint_voucher(reward_type)
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔄 Mint Another", callback_data="admin:mint_vouchers")],
        [types.InlineKeyboardButton(text="↩️ Back to Panel", callback_data="admin:back")]
    ])
    
    await callback.message.edit_text(
        f"✅ <b>Voucher Minted Successfully!</b>\n\n"
        f"<b>Type:</b> <code>{reward_type}</code>\n"
        f"<b>Code:</b> <code>{voucher.code}</code>\n\n"
        f"<i>Copy the code above and send it to your buyer. It can only be used once.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer("Voucher Generated!")
