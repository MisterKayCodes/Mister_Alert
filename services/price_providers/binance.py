import httpx
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import PriceProvider

logger = logging.getLogger(__name__)

class BinanceProvider(PriceProvider):
    """
    Price provider for Binance (Crypto).
    Docs: https://binance-docs.github.io/apidocs/spot/en/#symbol-price-ticker
    """
    BASE_URL = "https://api.binance.com/api/v3/ticker/price"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
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

                response = await client.get(self.BASE_URL, params={"symbol": formatted_symbol})
                if response.status_code == 200:
                    data = response.json()
                    results[symbol] = float(data["price"])
                    logger.debug(f"Binance: {symbol} -> {results[symbol]}")
                elif response.status_code >= 500:
                    response.raise_for_status() # Trigger retry for server errors
                else:
                    logger.warning(f"Binance: Failed to fetch {symbol} (Status {response.status_code})")
        return results
