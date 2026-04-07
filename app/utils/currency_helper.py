import httpx
import time
import logging

logger = logging.getLogger(__name__)

# Fallback rates if API fails
EXCHANGE_RATES = {
    "USD": 1.0,
    "NGN": 1200.0,
    "KES": 130.0,
    "GBP": 0.8,
    "EUR": 0.92
}

_cache_time = 0
_cache_ttl = 3600  # 1 hour cache

async def fetch_live_rates():
    global _cache_time
    # Only fetch once per hour to stay fast and avoid rate limits
    if time.time() - _cache_time < _cache_ttl:
        return
        
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://open.er-api.com/v6/latest/USD", timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                rates = data.get("rates", {})
                for c in ["NGN", "KES", "GBP", "EUR"]:
                    if c in rates:
                        EXCHANGE_RATES[c] = float(rates[c])
                _cache_time = time.time()
                logger.info("Live exchange rates updated.")
    except Exception as e:
        logger.warning(f"Failed to fetch live exchange rates: {e}")

async def convert_currency(usd_amount: float, target_currency: str) -> str:
    """Takes a base USD amount, fetches live rate, and returns formatted string for target currency."""
    await fetch_live_rates()
    
    rate = EXCHANGE_RATES.get(target_currency, 1.0)
    converted = usd_amount * rate
    
    if converted >= 100:
        return f"{converted:,.0f}"  # e.g. 12,000 NGN
    else:
        return f"{converted:,.2f}"  # e.g. 5.00 USD
