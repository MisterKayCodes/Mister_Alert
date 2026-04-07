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
            # Flatten nesting by processing symbols sequentially (or can use gather here)
            for symbol in symbols:
                price = await self._fetch_single_price(client, symbol)
                if price is not None:
                    results[symbol] = price
        return results

    async def _format_symbol(self, symbol: str) -> str:
        """Helper to map user symbols to Binance-compatible strings."""
        s = symbol.upper().replace("/", "").replace("-", "")
        # Special cases: Common requested pairs vs Binance availability
        if s == "BTCUSD": return "BTCUSDT"
        if s == "ETHUSD": return "ETHUSDT"
        if len(s) <= 4: return s + "USDT"
        return s

    async def _fetch_single_price(self, client: httpx.AsyncClient, symbol: str) -> float | None:
        """Handles the request/response for a single symbol to reduce loop nesting."""
        formatted = await self._format_symbol(symbol)
        try:
            response = await client.get(self.BASE_URL, params={"symbol": formatted})
            if response.status_code == 200:
                data = response.json()
                val = float(data["price"])
                logger.debug(f"Binance: {symbol} -> {val}")
                return val
            elif response.status_code >= 500:
                response.raise_for_status()
            else:
                logger.warning(f"Binance: Failed to fetch {symbol} (Status {response.status_code})")
        except Exception as e:
            logger.error(f"Binance error fetching {symbol}: {e}")
        return None
