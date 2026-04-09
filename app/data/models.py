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
    support_tickets = relationship("SupportTicket", back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    price_above = Column(Numeric(precision=18, scale=8), nullable=True)
    price_below = Column(Numeric(precision=18, scale=8), nullable=True)
    is_active = Column(Boolean, default=True)
    is_boosted = Column(Boolean, default=False)   # True = fast lane even on free tier
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


class SupportTicket(Base):
    """Stores support messages from users and admin replies."""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    status = Column(String, default="open")  # 'open', 'replied'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    replied_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="support_tickets")


class Voucher(Base):
    """Secure activation keys for the Voucher Economy (Premium/Credits)."""
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True, nullable=False)
    reward_type = Column(String, nullable=False) # e.g., 'premium_1_month', 'credits_500'
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", lazy="selectin")


# ─────────────────────────────────────────────────
# MARKETING ENGINE (MME) LAYER
# ─────────────────────────────────────────────────

class MarketingTemplate(Base):
    """Stores high-value 'Trojan Horse' message templates."""
    __tablename__ = "marketing_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Supports {{handle}} placeholder
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarketingTarget(Base):
    """Groups or channels where the UserBot is active."""
    __tablename__ = "marketing_targets"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True, index=True, nullable=False)
    chat_title = Column(String, nullable=True)
    is_monitored = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarketingStat(Base):
    """Tracks interaction history for analytics."""
    __tablename__ = "marketing_stats"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False) # 'reply' (keyword hit) or 'post' (timed drop)
    chat_id = Column(String, nullable=False)
    template_name = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class MarketingGoal(Base):
    """Stores daily/weekly outreach targets."""
    __tablename__ = "marketing_goals"

    id = Column(Integer, primary_key=True)
    goal_type = Column(String, default="daily_replies") # 'daily_replies', 'daily_posts'
    target_value = Column(Integer, default=15)
    current_value = Column(Integer, default=0)
    last_reset = Column(DateTime(timezone=True), server_default=func.now())
