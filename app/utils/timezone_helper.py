"""
timezone_helper.py
Converts user-friendly timezone inputs to IANA strings and formats datetimes.
"""
from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ── Common alias map (user input → IANA) ──────────────────────────────────────
TIMEZONE_ALIASES: dict[str, str] = {
    # Africa
    "WAT":  "Africa/Lagos",       # West Africa Time (Nigeria, Cameroon)
    "CAT":  "Africa/Harare",      # Central Africa Time (Zimbabwe, Zambia)
    "EAT":  "Africa/Nairobi",     # East Africa Time (Kenya, Uganda, Tanzania)
    "SAST": "Africa/Johannesburg",# South Africa Standard Time
    "LAGOS":    "Africa/Lagos",
    "NAIROBI":  "Africa/Nairobi",
    "ACCRA":    "Africa/Accra",
    "CAIRO":    "Africa/Cairo",
    "JOHANNESBURG": "Africa/Johannesburg",

    # Europe
    "GMT":  "UTC",
    "UTC":  "UTC",
    "BST":  "Europe/London",      # British Summer Time
    "WET":  "Europe/Lisbon",
    "CET":  "Europe/Paris",
    "CEST": "Europe/Paris",
    "EET":  "Europe/Helsinki",
    "LONDON": "Europe/London",
    "PARIS":  "Europe/Paris",
    "BERLIN": "Europe/Berlin",
    "AMSTERDAM": "Europe/Amsterdam",
    "ROME":   "Europe/Rome",
    "MADRID": "Europe/Madrid",

    # Americas
    "EST":  "America/New_York",
    "EDT":  "America/New_York",
    "CST":  "America/Chicago",
    "CDT":  "America/Chicago",
    "MST":  "America/Denver",
    "PST":  "America/Los_Angeles",
    "PDT":  "America/Los_Angeles",
    "NEW YORK":  "America/New_York",
    "NEWYORK":   "America/New_York",
    "CHICAGO":   "America/Chicago",
    "LOS ANGELES":"America/Los_Angeles",
    "LA":        "America/Los_Angeles",
    "TORONTO":   "America/Toronto",
    "SAO PAULO": "America/Sao_Paulo",

    # Asia / Middle East
    "IST":  "Asia/Kolkata",       # India Standard Time
    "GST":  "Asia/Dubai",         # Gulf Standard Time
    "AST":  "Asia/Riyadh",        # Arabia Standard Time
    "MSK":  "Europe/Moscow",
    "DUBAI":  "Asia/Dubai",
    "RIYADH": "Asia/Riyadh",
    "DELHI":  "Asia/Kolkata",
    "MUMBAI": "Asia/Kolkata",
    "KOLKATA":"Asia/Kolkata",
    "SINGAPORE": "Asia/Singapore",
    "SGT":    "Asia/Singapore",
    "HKT":    "Asia/Hong_Kong",
    "HONG KONG": "Asia/Hong_Kong",
    "JST":    "Asia/Tokyo",
    "TOKYO":  "Asia/Tokyo",
    "KST":    "Asia/Seoul",
    "SEOUL":  "Asia/Seoul",
    "CST_ASIA":"Asia/Shanghai",
    "SHANGHAI":"Asia/Shanghai",
    "BEIJING": "Asia/Shanghai",

    # Oceania
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "ACST": "Australia/Darwin",
    "NZST": "Pacific/Auckland",
    "SYDNEY":   "Australia/Sydney",
    "MELBOURNE":"Australia/Melbourne",
    "PERTH":    "Australia/Perth",
    "AUCKLAND": "Pacific/Auckland",
}


def parse_timezone(user_input: str) -> str | None:
    """
    Convert a user's text into a valid IANA timezone string.
    Tries:
      1. Exact match in alias map
      2. Direct IANA validation (e.g. user typed 'Africa/Lagos')
    Returns None if unrecognised.
    """
    raw = user_input.strip()

    # 1. Try alias map (upper-cased key)
    alias_key = raw.upper().replace("_", " ").strip()
    if alias_key in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[alias_key]

    # Also try original casing for IANA
    iana_candidate = raw.replace(" ", "_")
    try:
        ZoneInfo(iana_candidate)
        return iana_candidate
    except (ZoneInfoNotFoundError, KeyError):
        _invalid = True

    # 2. Partial / city substring scan
    raw_lower = raw.lower()
    for alias, iana in TIMEZONE_ALIASES.items():
        if raw_lower in alias.lower():
            return iana

    return None


def format_time_for_user(dt: datetime, tz_string: str | None) -> str:
    """
    Format a UTC datetime into a human-readable string in the user's timezone.
    Falls back to UTC if tz_string is invalid or missing.
    Returns: '14:32:05 WAT (UTC+1)' style string.
    """
    iana = tz_string or "UTC"
    try:
        zone = ZoneInfo(iana)
    except (ZoneInfoNotFoundError, KeyError):
        zone = ZoneInfo("UTC")

    local_dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(zone)
    offset = local_dt.strftime("%z")
    # Format offset as UTC+1 / UTC-5 etc.
    if offset:
        sign = offset[0]
        h = int(offset[1:3])
        m = int(offset[3:5])
        utc_label = f"UTC{sign}{h}" if m == 0 else f"UTC{sign}{h}:{m:02d}"
    else:
        utc_label = "UTC"

    # Short zone abbreviation if available
    abbr = local_dt.strftime("%Z")
    time_str = local_dt.strftime("%H:%M:%S")
    date_str = local_dt.strftime("%d %b %Y")
    return f"{time_str} {abbr} ({utc_label}) · {date_str}"
