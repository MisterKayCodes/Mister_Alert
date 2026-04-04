from typing import List, Dict, Protocol, runtime_checkable

@runtime_checkable
class PriceProvider(Protocol):
    """
    Interface for all price providers.
    """
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch current prices for a list of symbols.
        Returns a mapping of symbol -> price.
        """
        ...
