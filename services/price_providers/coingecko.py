import httpx
import logging
import asyncio
from typing import List, Dict
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

        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "ids": ",".join(cg_ids),
                    "vs_currencies": "usd"
                }
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    for s, cg_id in symbol_to_id.items():
                        if cg_id in data:
                            results[s] = float(data[cg_id]["usd"])
                    logger.info(f"CoinGecko (Backup): Fetched {len(results)} symbols.")
                else:
                    logger.warning(f"CoinGecko: Failed (Status {response.status_code})")
        except Exception as e:
            logger.error(f"CoinGecko Error: {e}")
            
        return results
