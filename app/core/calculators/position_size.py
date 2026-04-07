from typing import Dict

def get_position_size(pair: str, entry: float, sl: float, risk_usd: float) -> Dict[str, any]:
    pair = pair.upper()
    diff = abs(entry - sl)
    if diff == 0: return {"pips": 0.0, "lots": 0.0, "warning": None}

    # Mapping keywords to (pip_size, pip_value_per_lot)
    # Priority: Specific name -> Major classes -> Default
    ASSET_MAP = {
        "XAUUSD": (0.1, 10.0), "GOLD": (0.1, 10.0),
        "BTC": (1.0, 1.0), "ETH": (1.0, 1.0), "BNB": (1.0, 1.0),
        "JPY": (0.01, 10.0),
        "US30": (1.0, 1.0), "NAS100": (1.0, 1.0), "GER30": (1.0, 1.0), "SPX500": (1.0, 1.0)
    }
    
    # Simple lookup logic with default to standard Forex
    config = (0.0001, 10.0)
    for key, val in ASSET_MAP.items():
        if key in pair:
            config = val
            break

    psize, pval = config
    pips_at_risk = diff / psize
    lot_size = risk_usd / (pips_at_risk * pval) if (pips_at_risk * pval) > 0 else 0.0

    # "Dumb User" Protection / Careless Trader Warnings
    warning_msg = None
    if pips_at_risk > 1000:
        warning_msg = "Extremely wide Stop Loss"
    elif pips_at_risk > 150 and not any(k in pair for k in ["BTC", "ETH", "XAUUSD"]):
        warning_msg = "Unusually wide Stop Loss"

    return {
        "pips": round(pips_at_risk, 1),
        "lots": round(lot_size, 4),
        "warning": warning_msg
    }
