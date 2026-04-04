from typing import List, Dict, Union
from decimal import Decimal


def analyze_trades(trades: List[Union[dict, object]]) -> Dict[str, Union[int, float]]:
   
    total_trades = len(trades)
    open_trades = 0
    closed_trades = 0
    wins = 0
    losses = 0
    break_even = 0
    total_position_size = Decimal('0')
    total_pnl = Decimal('0')

    def get_attr_or_key(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    for trade in trades:
        is_closed = get_attr_or_key(trade, 'is_closed', False)
        result = get_attr_or_key(trade, 'result', None)
        position_size = get_attr_or_key(trade, 'position_size', None)
        entry_price = get_attr_or_key(trade, 'entry_price', None)
        take_profit = get_attr_or_key(trade, 'take_profit', None)
        stop_loss = get_attr_or_key(trade, 'stop_loss', None)
        direction = get_attr_or_key(trade, 'direction', None)

        if is_closed:
            closed_trades += 1
        else:
            open_trades += 1

        if position_size is not None:
            total_position_size += Decimal(str(position_size))

        if is_closed:
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1
            elif result == 'break-even':
                break_even += 1

            exit_price = None
            if result == 'win' and take_profit is not None:
                exit_price = Decimal(str(take_profit))
            elif result == 'loss' and stop_loss is not None:
                exit_price = Decimal(str(stop_loss))
            elif result == 'break-even' and entry_price is not None:
                exit_price = Decimal(str(entry_price))

            if exit_price is not None and position_size is not None and entry_price is not None and direction is not None:
                entry = Decimal(str(entry_price))
                pos_size = Decimal(str(position_size))
                if direction.upper() == 'LONG':
                    pnl = (exit_price - entry) * pos_size
                elif direction.upper() == 'SHORT':
                    pnl = (entry - exit_price) * pos_size
                else:
                    pnl = Decimal('0')
                total_pnl += pnl

    win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0.0
    avg_position_size = float(total_position_size / total_trades) if total_trades > 0 else 0.0
    avg_pnl = float(total_pnl / closed_trades) if closed_trades > 0 else 0.0

    return {
        'total_trades': total_trades,
        'open_trades': open_trades,
        'closed_trades': closed_trades,
        'wins': wins,
        'losses': losses,
        'break_even': break_even,
        'win_rate_percent': round(win_rate, 2),
        'avg_position_size': round(avg_position_size, 8),
        'avg_profit_loss': round(avg_pnl, 8),
    }
