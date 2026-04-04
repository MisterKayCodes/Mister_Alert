import logging
from typing import List
from data.models import Trade
from core.calculators.pips import calculate_pips

logger = logging.getLogger(__name__)

def calculate_trade_performance(trades: List[Trade]) -> dict:
    """
    Calculates high-level performance metrics from a list of closed trades.
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

    for trade in trades:
        # Calculate signed pips
        # pips calculation is usually abs(price2 - price1) / pip_size
        # For profit/loss, we need:
        # LONG: (exit - entry) / pip_size
        # SHORT: (entry - exit) / pip_size
        
        # We'll use a local helper to get the pip_size logic from calculate_pips
        from core.calculators.pips import DEFAULT_PIP_MAP
        pip_size = next((v for k, v in DEFAULT_PIP_MAP.items() if k in trade.symbol.upper()), 0.0001)
        
        if trade.direction.upper() == "LONG":
            diff = float(trade.closed_at_price or 0) - float(trade.entry_price)
        else:
            diff = float(trade.entry_price) - float(trade.closed_at_price or 0)
            
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
