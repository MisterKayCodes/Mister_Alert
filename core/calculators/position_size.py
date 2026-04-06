from typing import Dict

def get_position_size(pair: str, entry: float, sl: float, risk_usd: float) -> Dict[str, any]:
    pair = pair.upper()
    price_diff = abs(entry - sl)
    
    if price_diff == 0:
        return {"pips": 0.0, "lots": 0.0, "warning": None}

    # Standard Pip Sizes and Values (1.0 lot)
    if "XAUUSD" in pair or "GOLD" in pair:
        pip_size = 0.1
        pip_value_per_lot = 10.00 # $10 per 0.1 move for 1 lot
    elif any(k in pair for k in ["BTC", "ETH", "BNB"]):
        pip_size = 1.0  # 1.0 unit move
        pip_value_per_lot = 1.0 # $1 per $1 move for 1.0 lot (standard crypto sizing)
    elif "JPY" in pair:
        pip_size = 0.01
        pip_value_per_lot = 10.00 # Standard $10/pip approximated
    elif any(k in pair for k in ["US30", "NAS100", "GER30", "SPX500"]):
        pip_size = 1.0
        pip_value_per_lot = 1.0
    else:
        # Standard Forex (EURUSD, GBPUSD, etc.)
        pip_size = 0.0001
        pip_value_per_lot = 10.00 # $10/pip for 1.0 lot

    pips_at_risk = price_diff / pip_size
    
    # Lot Size = Risk / (Pips * PipValuePerLot)
    denominator = pips_at_risk * pip_value_per_lot
    if denominator == 0:
        return {"pips": round(pips_at_risk, 1), "lots": 0.0, "warning": None}

    lot_size = risk_usd / denominator

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
