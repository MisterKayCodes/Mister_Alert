"""
utils/fmt.py - Mister Alert Universal Message Formatter

All bot messages must use these helpers so the UI is consistent,
premium-looking, and easy to change in one place.
"""

from __future__ import annotations

DIVIDER = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"


# ── Status pills ──────────────────────────────────────────────────────────────

def pill_status(is_active: bool) -> str:
    return "⏳ Watching" if is_active else "✅ Hit"


def pill_result(result: str | None) -> str:
    mapping = {
        "win": "🟢 Win",
        "loss": "🔴 Loss",
        "break-even": "⚪ Break-even",
        "manual": "🏁 Manual Close",
    }
    return mapping.get(result or "", "⚪ Unknown")


def pill_tx_status(status: str) -> str:
    mapping = {
        "pending": "⏳ Pending",
        "approved": "✅ Approved",
        "rejected": "❌ Rejected",
    }
    return mapping.get(status, status)


def pill_tier(is_premium: bool) -> str:
    return "⭐ Premium" if is_premium else "🆓 Free"


def pill_market(is_open: bool) -> str:
    return "🟢 Open" if is_open else "🔴 Closed"


# ── Building blocks ───────────────────────────────────────────────────────────

def header(emoji: str, title: str) -> str:
    return emoji + " *" + title + "*"


def section(emoji: str, title: str, body: str) -> str:
    return header(emoji, title) + "\n" + DIVIDER + "\n" + body


def row(label_emoji: str, label: str, value: object) -> str:
    return label_emoji + " *" + label + ":* `" + str(value) + "`"


def row_plain(label_emoji: str, label: str, value: object) -> str:
    return label_emoji + " *" + label + ":* " + str(value)


def success(text: str) -> str:
    return "✅ *" + text + "*"


def error(text: str) -> str:
    return "❌ *" + text + "*"


def warning(text: str) -> str:
    return "⚠️ *" + text + "*"


def info(text: str) -> str:
    return "ℹ️ " + text


# ── Composed screen templates ─────────────────────────────────────────────────

def alert_card(symbol: str, condition: str, is_active: bool, alert_id: int) -> str:
    direction = "📈 Above" if ">" in condition else "📉 Below"
    lines = [
        "📍 *" + symbol + "*",
        row("🎯", "Target", condition),
        row("🔀", "Direction", direction),
        row("📡", "Status", pill_status(is_active)),
    ]
    return "\n".join(lines)


def trade_card(symbol: str, direction: str, entry: str, sl: str, tp: str) -> str:
    dir_icon = "📈" if direction.upper() == "LONG" else "📉"
    sl_val = sl if sl and sl != "None" else "None"
    tp_val = tp if tp and tp != "None" else "None"
    lines = [
        dir_icon + " *" + symbol + "* — " + direction.upper(),
        row("💰", "Entry", entry),
        row("🛑", "Stop Loss", sl_val),
        row("🎯", "Take Profit", tp_val),
    ]
    return "\n".join(lines)


def performance_dashboard(stats: dict) -> str:
    win_icon = "🟢" if stats["win_rate"] >= 50 else "🔴"
    pip_icon = "🟢" if stats["total_pips"] >= 0 else "🔴"
    win_row = win_icon + " *Win Rate:* `" + str(stats["win_rate"]) + "%`"
    pip_row = pip_icon + " *Total Pips:* `" + str(stats["total_pips"]) + "`"
    body = "\n".join([
        row("🔢", "Total Trades", stats["total_trades"]),
        win_row,
        pip_row,
        row("📊", "Avg Pips/Trade", stats["avg_pips"]),
        "",
        "✅ Wins: `" + str(stats["wins"]) + "` · ❌ Losses: `" + str(stats["losses"]) + "`",
    ])
    return section("📈", "Performance Dashboard", body)


def trade_history_list(trades: list) -> str:
    if not trades:
        return section("📜", "Trade History", "_No closed trades yet._")
    icons = {"win": "🟢", "loss": "🔴", "manual": "🏁"}
    lines = []
    for t in trades:
        icon = icons.get(t.result or "", "⚪")
        date_str = t.closed_at.strftime("%d %b %y") if t.closed_at else "---"
        lines.append(icon + " `" + date_str + "` · *" + t.symbol + "* · " + t.direction)
    return section("📜", "Last 10 Trades", "\n".join(lines))


def rr_report(pair: str, position: str, result: dict) -> str:
    ratio = float(result["risk_reward_ratio"])
    label = result["ratio_label"]
    risk_pips = result["risk_pips"]
    reward_pips = result["reward_pips"]
    color = "🟢" if ratio >= 1.5 else ("🟡" if ratio >= 1 else "🔴")
    ratio_str = str(result["risk_reward_ratio"]) + "  (" + label + ")"
    body = "\n".join([
        row("📌", "Pair", pair) + " · " + position,
        row("🛑", "Risk", str(risk_pips) + " pips"),
        row("🎯", "Reward", str(reward_pips) + " pips"),
        color + " *Ratio:* `" + ratio_str + "`",
    ])
    return section("⚖️", "R:R Report", body)


def shop_menu_text(tier: str, credits: int, currency: str,
                   price_credits: str, price_weekly: str, price_monthly: str, price_yearly: str) -> str:
    body = "\n".join([
        row("👤", "Tier", tier),
        row("🪙", "Credits", credits),
        row("🌍", "Currency", currency),
        "",
        "ℹ️ *Free Tier:* 3 Active Alerts (Standard Queue)",
        "ℹ️ *Premium:* Unlimited Active Alerts + Priority Fast-Lane Queue",
        "ℹ️ *Credits:* Use 1 Credit to instantly boost any Free alert into the Fast-Lane",
        "",
        "*Pricing (" + currency + "):*",
        "  · 10 Credits — `" + price_credits + "`",
        "  · Weekly Premium — `" + price_weekly + "`",
        "  · Monthly Premium — `" + price_monthly + "`",
        "  · Yearly Premium — `" + price_yearly + "`",
    ])
    return section("🛒", "Mister Alert Shop", body)


def transaction_card(tx) -> str:
    amount_str = str(tx.amount) + " " + tx.currency
    lines = [
        "🧾 *Transaction #" + str(tx.id) + "*",
        row("📦", "Type", tx.tx_type),
        row("💰", "Amount", amount_str),
        row("🔖", "Reference", tx.evidence or "N/A"),
        row("📡", "Status", pill_tx_status(tx.status)),
    ]
    return "\n".join(lines)


def settings_list(settings_rows: list) -> str:
    if not settings_rows:
        return section("⚙️", "Bot Settings", "_No settings found._")
    lines = ["• `" + s.key + "` → `" + s.value + "`" for s in settings_rows]
    return section("⚙️", "Bot Settings", "\n".join(lines))


def payment_method_card(pm) -> str:
    status = "✅ Active" if pm.is_active else "💤 Disabled"
    return "💳 *" + pm.name + "* (ID: " + str(pm.id) + ") — " + status


def system_stats(total_users: int, premium: int, alerts: int, pending_txs: int) -> str:
    body = "\n".join([
        row("👥", "Total Users", total_users),
        row("⭐", "Premium Users", premium),
        row("🔔", "Active Alerts", alerts),
        row("⏳", "Pending Payments", pending_txs),
    ])
    return section("📊", "System Stats", body)


def format_forex_symbol(sym: str) -> str:
    """
    Normalizes a ticker symbol. If it's a 6-character forex/metal symbol 
    missing a slash (e.g., EURUSD, XAUUSD), it intelligently injects one (EUR/USD).
    Otherwise, it returns the symbol as-is.
    """
    s = sym.upper().replace("-", "").replace(" ", "")
    if len(s) == 6 and "/" not in s:
        return f"{s[:3]}/{s[3:]}"
    return s
