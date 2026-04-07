import httpx
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import PriceProvider
from config import settings
from utils.fmt import format_forex_symbol

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
            logger.debug(f"TwelveData raw output: {data}")

            # Handle single symbol response
            if len(formatted_symbols) == 1:
                fsym = formatted_symbols[0]
                orig_sym = twelve_to_orig[fsym]
                if "price" in data:
                    results[orig_sym] = float(data["price"])
                elif "code" in data and data["code"] != 200:
                    logger.error(f"TwelveData Error: {data.get('message')}")
            # Handle multiple symbol response
            else:
                for fsym, info in data.items():
                    orig_sym = twelve_to_orig.get(fsym, fsym)
                    if isinstance(info, dict) and "price" in info:
                        results[orig_sym] = float(info["price"])
                    elif isinstance(info, dict) and "code" in info and info["code"] != 200:
                        logger.warning(f"TwelveData: Symbol {fsym} fail: {info.get('message')}")

        return results
