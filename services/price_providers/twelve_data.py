import httpx
import logging
from typing import List, Dict
from .base import PriceProvider
from config import settings

logger = logging.getLogger(__name__)

class TwelveDataProvider(PriceProvider):
    """
    Price provider for Twelve Data (Forex/Stocks).
    Docs: https://twelvedata.com/docs#price
    """
    BASE_URL = "https://api.twelvedata.com/price"

    def __init__(self):
        self.api_key = settings.twelve_data_api_key

    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        if not symbols or not self.api_key or self.api_key == "your_twelve_data_key":
            logger.warning(f"TwelveData: Symbols: {symbols}, API Key: {self.api_key}")
            return {}

        # Twelve Data supports multiple symbols in one request
        symbol_str = ",".join(symbols).upper()
        results = {}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.BASE_URL, 
                    params={"symbol": symbol_str, "apikey": self.api_key}
                )
                if response.status_code == 200:
                    data = response.json()
                    
                    # Log the structure to help debug if needed
                    logger.debug(f"TwelveData raw output: {data}")

                    # Handle single symbol response
                    if len(symbols) == 1:
                        symbol = symbols[0].upper()
                        if "price" in data:
                            results[symbols[0]] = float(data["price"])
                        elif "code" in data and data["code"] != 200:
                            logger.error(f"TwelveData Error: {data.get('message')}")
                    # Handle multiple symbol response
                    else:
                        for symbol, info in data.items():
                            if isinstance(info, dict) and "price" in info:
                                results[symbol] = float(info["price"])
                            elif isinstance(info, dict) and "code" in info and info["code"] != 200:
                                logger.warning(f"TwelveData: Symbol {symbol} fail: {info.get('message')}")
                                
                else:
                    logger.error(f"TwelveData Request Failed: Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"TwelveData Exception: {e}")
                pass

        return results
