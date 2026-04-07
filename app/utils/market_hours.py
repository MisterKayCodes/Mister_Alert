from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

def is_market_open(symbol: str) -> bool:
    """
    Checks if the market for a given symbol is currently open.
    - Crypto: Always open (24/7)
    - Forex: Sun 22:00 UTC to Fri 22:00 UTC
    """
    symbol = symbol.upper()
    
    # Heuristic for Crypto: Common pairs or length
    is_crypto = any(x in symbol for x in ["USDT", "BTC", "ETH", "BNB", "DOGE", "SOL"]) or len(symbol) <= 5
    
    if is_crypto:
        return True
        
    # Forex Logic
    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()  # Monday is 0, Sunday is 6
    hour = now_utc.hour
    
    # Market Closes Friday 22:00 UTC
    if weekday == 4 and hour >= 22:
        return False
    
    # Market Closed Saturday
    if weekday == 5:
        return False
        
    # Market Opens Sunday 22:00 UTC
    if weekday == 6 and hour < 22:
        return False
        
    return True

def get_market_status_label(symbol: str) -> str:
    """Returns a friendly label for UI."""
    if is_market_open(symbol):
        return "🟢 Open"
    return "🔴 Closed (Forex Weekend)"
