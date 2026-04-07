from typing import List, Dict, Union
from decimal import Decimal


def _get_attr_or_key(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _resolve_exit_price(result, tp, sl, entry):
    """Determine exit price based on trade result."""
    if result == 'win' and tp is not None:
        return Decimal(str(tp))
    if result == 'loss' and sl is not None:
        return Decimal(str(sl))
    if result == 'break-even' and entry is not None:
        return Decimal(str(entry))
    return None


def _calculate_trade_pnl(trade) -> Decimal:
    """Calculate P&L for a single closed trade."""
    is_closed = _get_attr_or_key(trade, 'is_closed', False)
    if not is_closed:
        return Decimal('0')

    result = _get_attr_or_key(trade, 'result', None)
    pos_size = _get_attr_or_key(trade, 'position_size', None)
    entry = _get_attr_or_key(trade, 'entry_price', None)
    tp = _get_attr_or_key(trade, 'take_profit', None)
    sl = _get_attr_or_key(trade, 'stop_loss', None)
    direction = _get_attr_or_key(trade, 'direction', None)

    if not all([pos_size, entry, direction]):
        return Decimal('0')

    exit_price = _resolve_exit_price(result, tp, sl, entry)
    if exit_price is None:
        return Decimal('0')

    entry_dec = Decimal(str(entry))
    pos_dec = Decimal(str(pos_size))

    if direction.upper() == 'LONG':
        return (exit_price - entry_dec) * pos_dec
    if direction.upper() == 'SHORT':
        return (entry_dec - exit_price) * pos_dec
    return Decimal('0')


def _classify_result(result: str, counters: dict):
    """Increment the appropriate counter for a trade result."""
    if result == 'win':
        counters['wins'] += 1
    elif result == 'loss':
        counters['losses'] += 1
    elif result == 'break-even':
        counters['break_even'] += 1


def analyze_trades(trades: List[Union[dict, object]]) -> Dict[str, Union[int, float]]:
    total_trades = len(trades)
    counters = {'open': 0, 'closed': 0, 'wins': 0, 'losses': 0, 'break_even': 0}
    total_position_size = Decimal('0')
    total_pnl = Decimal('0')

    for trade in trades:
        is_closed = _get_attr_or_key(trade, 'is_closed', False)
        result = _get_attr_or_key(trade, 'result', None)
        position_size = _get_attr_or_key(trade, 'position_size', None)

        if is_closed:
            counters['closed'] += 1
            _classify_result(result, counters)
            total_pnl += _calculate_trade_pnl(trade)
        else:
            counters['open'] += 1

        if position_size is not None:
            total_position_size += Decimal(str(position_size))

    closed = counters['closed']
    win_rate = (counters['wins'] / closed * 100) if closed > 0 else 0.0
    avg_pos = float(total_position_size / total_trades) if total_trades > 0 else 0.0
    avg_pnl = float(total_pnl / closed) if closed > 0 else 0.0

    return {
        'total_trades': total_trades,
        'open_trades': counters['open'],
        'closed_trades': closed,
        'wins': counters['wins'],
        'losses': counters['losses'],
        'break_even': counters['break_even'],
        'win_rate_percent': round(win_rate, 2),
        'avg_position_size': round(avg_pos, 8),
        'avg_profit_loss': round(avg_pnl, 8),
    }
