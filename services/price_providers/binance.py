import httpx
import logging
from typing import List, Dict
from .base import PriceProvider

logger = logging.getLogger(__name__)

class BinanceProvider(PriceProvider):
    """
    Price provider for Binance (Crypto).
    Docs: https://binance-docs.github.io/apidocs/spot/en/#symbol-price-ticker
    """
    BASE_URL = "https://api.binance.com/api/v3/ticker/price"

    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        if not symbols:
            return {}

        results = {}
        async with httpx.AsyncClient() as client:
            for symbol in symbols:
                # Binance expects symbols like BTCUSDT
                formatted_symbol = symbol.upper().replace("/", "").replace("-", "")
                
                # Special cases: Common requested pairs vs Binance availability
                if formatted_symbol == "BTCUSD":
                    formatted_symbol = "BTCUSDT"
                elif formatted_symbol == "ETHUSD":
                    formatted_symbol = "ETHUSDT"
                elif len(formatted_symbol) <= 4:
                    formatted_symbol += "USDT"

                try:
                    response = await client.get(self.BASE_URL, params={"symbol": formatted_symbol})
                    if response.status_code == 200:
                        data = response.json()
                        results[symbol] = float(data["price"])
                        logger.debug(f"Binance: {symbol} -> {results[symbol]}")
                    else:
                        logger.warning(f"Binance: Failed to fetch {symbol} (Status {response.status_code})")
                except Exception as e:
                    logger.error(f"Binance: Error fetching {symbol}: {e}")
                    continue
        return results
