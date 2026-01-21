DEFAULT_PIP_MAP = {
    "JPY": 0.01,
    "XAUUSD": 0.1,
    "BTC": 0.1,
    "ETH": 0.1,
    "BNB": 0.1,
}

def calculate_pips(pair: str, price1: float, price2: float, pip_map=None) -> float:
    pip_map = pip_map or DEFAULT_PIP_MAP
    pair = pair.upper()
    pip_size = next((v for k, v in pip_map.items() if k in pair), 0.0001)
    return round(abs(price2 - price1) / pip_size, 4)
