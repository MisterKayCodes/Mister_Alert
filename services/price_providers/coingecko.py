import httpx
import logging
import asyncio
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import PriceProvider

logger = logging.getLogger(__name__)

class CoinGeckoProvider(PriceProvider):
    """
    Price provider for CoinGecko (Crypto Backup).
    Uses the /simple/price endpoint.
    """
    BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
    
    # Mapping for common symbols to CoinGecko IDs
    # (In a real system, this would be more dynamic)
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "XRP": "ripple",
        "DOT": "polkadot",
        "MATIC": "polygon",
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        if not symbols:
            return {}

        results = {}
        # 1. Map symbols to CG IDs
        cg_ids = []
        symbol_to_id = {}
        for s in symbols:
            # BTCUSD -> BTC
            base = s.upper().replace("USDT", "").replace("USD", "").replace("/", "")
            cg_id = self.SYMBOL_MAP.get(base)
            if cg_id:
                cg_ids.append(cg_id)
                symbol_to_id[s] = cg_id

        if not cg_ids:
            return {}

        async with httpx.AsyncClient() as client:
            params = {
                "ids": ",".join(cg_ids),
                "vs_currencies": "usd"
            }
            response = await client.get(self.BASE_URL, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            for s, cg_id in symbol_to_id.items():
                if cg_id in data:
                    results[s] = float(data[cg_id]["usd"])
            logger.info(f"CoinGecko (Backup): Fetched {len(results)} symbols.")
            
        return results
