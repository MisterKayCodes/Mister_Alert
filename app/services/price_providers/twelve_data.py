import httpx
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import PriceProvider
from config import settings
from app.utils.fmt import format_forex_symbol

logger = logging.getLogger(__name__)

class TwelveDataProvider(PriceProvider):
    """
    Price provider for Twelve Data (Forex/Stocks).
    Docs: https://twelvedata.com/docs#price
    """
    BASE_URL = "https://api.twelvedata.com/price"

    def __init__(self):
        self.api_key = settings.twelve_data_api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        if not symbols or not self.api_key or self.api_key == "your_twelve_data_key":
            logger.warning(f"TwelveData: Symbols: {symbols}, API Key: {self.api_key}")
            return {}

        # TwelveData expects forex pairs as EUR/USD, but users often provide EURUSD.
        formatted_symbols = []
        twelve_to_orig = {}
        for sym in symbols:
            formatted = format_forex_symbol(sym)
            formatted_symbols.append(formatted)
            twelve_to_orig[formatted] = sym

        symbol_str = ",".join(formatted_symbols)
        results = {}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL, 
                params={"symbol": symbol_str, "apikey": self.api_key}
            )
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_response(data, formatted_symbols, twelve_to_orig)

        return results

    def _parse_response(self, data, formatted_symbols, twelve_to_orig) -> Dict[str, float]:
        """Flattened parsing logic for Twelve Data API response."""
        results = {}
        # Single symbol response
        if len(formatted_symbols) == 1:
            return self._parse_single(data, formatted_symbols[0], twelve_to_orig)
        
        # Multiple symbols response
        for fsym, info in data.items():
            if not isinstance(info, dict):
                continue
            
            orig_sym = twelve_to_orig.get(fsym, fsym)
            if "price" in info:
                results[orig_sym] = float(info["price"])
            elif info.get("code") != 200:
                logger.warning(f"TwelveData: Symbol {fsym} fail: {info.get('message')}")
        return results

    def _parse_single(self, data, fsym, twelve_to_orig) -> Dict[str, float]:
        orig_sym = twelve_to_orig.get(fsym, fsym)
        if "price" in data:
            return {orig_sym: float(data["price"])}
        if data.get("code") != 200:
            logger.error(f"TwelveData Error: {data.get('message')}")
        return {}
