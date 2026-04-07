from aiogram.fsm.state import State, StatesGroup

class TradeStates(StatesGroup):
    waiting_for_trade_selection = State()
    waiting_for_new_sl = State()
    waiting_for_new_tp = State()
