from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)

    alerts = relationship("Alert", back_populates="user")
    trades = relationship("Trade", back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)  # e.g., BTCUSD, EURUSD
    price_above = Column(Numeric(precision=18, scale=8), nullable=True)
    price_below = Column(Numeric(precision=18, scale=8), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    entry_price = Column(Numeric(precision=18, scale=8), nullable=False)
    stop_loss = Column(Numeric(precision=18, scale=8), nullable=True)
    take_profit = Column(Numeric(precision=18, scale=8), nullable=True)
    position_size = Column(Numeric(precision=18, scale=8), nullable=True)  # lot size or amount
    direction = Column(String, nullable=False)  # 'LONG' or 'SHORT'
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    is_closed = Column(Boolean, default=False)
    result = Column(String, nullable=True)  # e.g., 'win', 'loss', 'break-even'

    user = relationship("User", back_populates="trades")
