from aiogram.fsm.state import State, StatesGroup

class PositionSizeStates(StatesGroup):
    waiting_for_pair = State()
    waiting_for_entry = State()
    waiting_for_sl = State()
    waiting_for_risk = State()

class RiskRewardStates(StatesGroup):
    waiting_for_pair = State()
    waiting_for_position = State()
    waiting_for_entry = State()
    waiting_for_sl = State()
    waiting_for_tp = State()
