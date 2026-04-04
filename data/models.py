from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, func, Text
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime(timezone=True), nullable=True)
    credits = Column(Integer, default=0)
    preferred_currency = Column(String, default="USD")
    timezone = Column(String, default="UTC")       # IANA timezone string e.g. "Africa/Lagos"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    alerts = relationship("Alert", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
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
    position_size = Column(Numeric(precision=18, scale=8), nullable=True)
    direction = Column(String, nullable=False)  # 'LONG' or 'SHORT'
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_at_price = Column(Numeric(precision=18, scale=8), nullable=True)
    is_closed = Column(Boolean, default=False)
    result = Column(String, nullable=True)  # 'win', 'loss', 'break-even', 'manual'

    user = relationship("User", back_populates="trades")


# ─────────────────────────────────────────────────
# ECONOMY LAYER
# ─────────────────────────────────────────────────

class BotSetting(Base):
    """Dynamic key-value store for bot content & system parameters."""
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String, nullable=True)


class PaymentMethod(Base):
    """Manageable deposit accounts (Bank Transfer, Mpesa, etc.)."""
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # e.g. "Bank Transfer"
    details = Column(Text, nullable=False)               # Full instructions/account info
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="payment_method")


class Transaction(Base):
    """Tracks user deposit requests awaiting admin approval."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=True)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, default="USD")
    tx_type = Column(String, default="credits")  # 'credits' or 'subscription'
    evidence = Column(String, nullable=True)      # Transaction ID / reference
    status = Column(String, default="pending")    # 'pending', 'approved', 'rejected'
    admin_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
