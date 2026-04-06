import re

def is_valid_symbol(symbol: str) -> bool:
    """
    Checks if a symbol follows a standard format (e.g. BTCUSD, EUR/USD, XAUUSD).
    Prevents junk or 'dumb' inputs from cluttering the price provider.
    """
    if not symbol:
        return False
        
    # Standard format: Alphanumeric, slash, or dash, 3-20 characters
    # e.g. BTCUSD, EUR-USD, NAS100, etc.
    pattern = r'^[A-Z0-9/\-]{2,15}$'
    if not re.match(pattern, symbol.upper()):
        return False
        
    # Check if it contains at least some letters (usually)
    if not any(c.isalpha() for c in symbol):
        # Allow pure numeric for some indices if needed, but usually nas100 has NAS
        pass
        
    return True
