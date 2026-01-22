from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BaseEvent:
    """Base class for all events. Automatically adds timestamp."""
    timestamp: datetime = field(default_factory=datetime.utcnow, init=False)


# ======================
# PRICE EVENTS
# ======================

@dataclass
class PriceUpdateEvent(BaseEvent):
    symbol: str
    price: float


# ======================
# ALERT EVENTS
# ======================

@dataclass
class AlertTriggeredEvent(BaseEvent):
    user_id: int
    alert_id: int
    symbol: str
    price: float
    target_price: float


@dataclass
class AlertExpiredEvent(BaseEvent):
    user_id: int
    alert_id: int
    symbol: str


# ======================
# TRADE EVENTS
# ======================

@dataclass
class TradeOpenedEvent(BaseEvent):
    user_id: int
    trade_id: int
    symbol: str
    entry: float
    tp: float
    sl: float
    direction: str  # "LONG" or "SHORT"


@dataclass
class TakeProfitHitEvent(BaseEvent):
    user_id: int
    trade_id: int
    symbol: str
    price: float


@dataclass
class StopLossHitEvent(BaseEvent):
    user_id: int
    trade_id: int
    symbol: str
    price: float


# ======================
# CSV EVENTS
# ======================

@dataclass
class CsvImportedEvent(BaseEvent):
    user_id: int
    trades_count: int
