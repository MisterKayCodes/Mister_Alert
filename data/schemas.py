from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# =========================
# USER SCHEMAS
# =========================

class UserCreate(BaseModel):
    telegram_id: str
    username: Optional[str] = None


class UserRead(BaseModel):
    id: int
    telegram_id: str
    username: Optional[str]
    is_premium: bool

    class Config:
        from_attributes = True


# =========================
# ALERT SCHEMAS
# =========================

class AlertCreate(BaseModel):
    symbol: str
    price_above: Optional[float] = None
    price_below: Optional[float] = None


class AlertRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    price_above: Optional[float]
    price_below: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


# =========================
# TRADE SCHEMAS
# =========================

class TradeCreate(BaseModel):
    symbol: str
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


class TradeRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: Optional[float]
    is_closed: bool
    created_at: datetime
    closed_at: Optional[datetime]
    result: Optional[str]

    class Config:
        from_attributes = True
