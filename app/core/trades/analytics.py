from typing import List

def calculate_trade_performance(trades: List[dict]) -> dict:
    """
    Calculates high-level performance metrics from a list of closed trade data.
    Expected dict keys: symbol, entry_price, closed_at_price, direction
    """
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pips": 0.0,
            "avg_pips": 0.0,
            "wins": 0,
            "losses": 0
        }

    total_pips = 0.0
    wins = 0
    losses = 0

    from app.core.calculators.pips import DEFAULT_PIP_MAP

    for trade in trades:
        symbol = str(trade.get("symbol", "UNKNOWN")).upper()
        pip_size = next((v for k, v in DEFAULT_PIP_MAP.items() if k in symbol), 0.0001)
        
        entry = float(trade.get("entry_price", 0))
        exit_p = float(trade.get("closed_at_price", 0))
        direction = str(trade.get("direction", "LONG")).upper()

        if direction == "LONG":
            diff = exit_p - entry
        else:
            diff = entry - exit_p
            
        trade_pips = diff / pip_size
        total_pips += trade_pips
        
        if trade_pips > 0:
            wins += 1
        else:
            losses += 1

    total_trades = len(trades)
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0.0
    avg_pips = total_pips / total_trades if total_trades > 0 else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_pips": round(total_pips, 2),
        "avg_pips": round(avg_pips, 2),
        "wins": wins,
        "losses": losses
    }
