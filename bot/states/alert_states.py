from aiogram.fsm.state import State, StatesGroup

class AlertStates(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_condition = State()  # Above or Below
    waiting_for_price = State()
