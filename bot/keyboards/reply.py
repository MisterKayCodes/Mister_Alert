from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Main Menu keyboard for quick access."""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔔 Alerts"), KeyboardButton(text="📈 Trades")],
            [KeyboardButton(text="🧮 Calculators"), KeyboardButton(text="📜 History")],
            [KeyboardButton(text="🛒 Shop"), KeyboardButton(text="⚙️ Settings")],
            [KeyboardButton(text="💬 Support")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Select an option"
    )
    return kb
