from typing import Dict

def get_position_size(pair: str, entry: float, sl: float, risk_usd: float) -> Dict[str, float]:
    pair = pair.upper()

    price_diff = abs(entry - sl)
    if price_diff == 0:
        return {"pips": 0.0, "lots": 0.0}

    if "XAUUSD" in pair:
        pip_size = 0.1
        pip_value_per_lot = 10.00  # Correct pip value for XAUUSD
    elif any(k in pair for k in ["BTC", "ETH", "BNB"]):
        pip_size = 0.1
        pip_value_per_lot = 0.10
    elif "JPY" in pair:
        pip_size = 0.01
        pip_value_per_lot = 10.00
    else:
        pip_size = 0.0001
        pip_value_per_lot = 10.00

    pips_at_risk = price_diff / pip_size
    denominator = pips_at_risk * pip_value_per_lot
    if denominator == 0:
        return {"pips": round(pips_at_risk, 1), "lots": 0.0}

    lot_size = risk_usd / denominator

    return {
        "pips": round(pips_at_risk, 1),
        "lots": round(lot_size, 4)
    }
