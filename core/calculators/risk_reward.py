from .pips import calculate_pips

def calculate_risk_reward(pair: str, position: str, entry_price: float, stop_loss: float, take_profit: float) -> dict:
    position = position.upper()
    if position not in ("LONG", "SHORT"):
        raise ValueError("Position must be 'LONG' or 'SHORT'")
    
    # Calculate risk and reward in pips using calculate_pips
    risk_pips = calculate_pips(pair, entry_price, stop_loss)
    reward_pips = calculate_pips(pair, entry_price, take_profit)
    
    if risk_pips == 0:
        raise ValueError("Risk (distance between entry and stop loss) cannot be zero")
    
    rr_ratio = reward_pips / risk_pips
    
    def format_decimal(value: float) -> str:
        # Format with max 1 decimal place, no trailing zeros
        return f"{value:.1f}".rstrip('0').rstrip('.') if '.' in f"{value:.1f}" else f"{value:.1f}"
    
    return {
        "position": position,
        "risk_pips": format_decimal(risk_pips),
        "reward_pips": format_decimal(reward_pips),
        "risk_reward_ratio": format_decimal(rr_ratio),
        "formatted": f"R:R {format_decimal(rr_ratio)} (Risk: {format_decimal(risk_pips)} pips, Reward: {format_decimal(reward_pips)} pips)"
    }
