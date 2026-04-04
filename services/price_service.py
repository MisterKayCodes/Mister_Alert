import asyncio
import logging
from typing import Set, Dict, List
from data.database import AsyncSessionLocal
from data.repository import AlertRepository, TradeRepository
from core.events import PriceUpdateEvent
from services.event_bus import event_bus
from .price_providers.binance import BinanceProvider
from .price_providers.twelve_data import TwelveDataProvider
from .price_providers.coingecko import CoinGeckoProvider
from config import settings

logger = logging.getLogger(__name__)

class PriceService:
    """
    Orchestrator for price feeds with Tiered Latency & Backup Failover.
    - Primary Crypto: Binance
    - Backup Crypto: CoinGecko
    - Forex: TwelveData
    """
    def __init__(self):
        self.binance = BinanceProvider()
        self.twelve_data = TwelveDataProvider()
        self.coingecko = CoinGeckoProvider()
        self._running = False
        self._task = None
        self._tick_counter = 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PriceService (Tiered) started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        logger.info("PriceService stopped.")

    async def _run_loop(self):
        """
        Main loop running every 10 seconds.
        """
        while self._running:
            try:
                await self.refresh_tiered()
            except Exception as e:
                logger.exception(f"PriceService error: {e}")
            
            # Tick every 10 seconds (the Premium interval)
            await asyncio.sleep(10)
            self._tick_counter += 1

    async def refresh_tiered(self):
        """
        Splits symbols into Fast and Slow lanes.
        """
        fast_symbols, slow_symbols = await self._get_tiered_symbols()
        
        symbols_to_refresh = set(fast_symbols)
        
        # Every 12 ticks (120s), we add the slow lane symbols
        if self._tick_counter % 12 == 11 or not slow_symbols: # Tick 11 is 120s if loop starts at 0
             symbols_to_refresh.update(slow_symbols)
             if slow_symbols:
                logger.debug(f"Slow Lane Refresh Triggered for {len(slow_symbols)} symbols")

        if not symbols_to_refresh:
            return

        # Categorize for providers
        crypto_symbols = []
        forex_symbols = []
        for symbol in symbols_to_refresh:
            s = symbol.upper()
            if any(x in s for x in ["USDT", "BTC", "ETH", "BNB"]) or len(s) <= 5:
                crypto_symbols.append(symbol)
            else:
                forex_symbols.append(symbol)

        # Fetch Primary
        tasks = []
        if crypto_symbols:
            tasks.append(self.binance.get_prices(crypto_symbols))
        if forex_symbols:
            tasks.append(self.twelve_data.get_prices(forex_symbols))

        results = await asyncio.gather(*tasks)
        all_prices: Dict[str, float] = {}
        for res in results:
            all_prices.update(res)

        # 🚀 Failover Logic for Crypto
        missing_crypto = [s for s in crypto_symbols if s not in all_prices]
        if missing_crypto:
            logger.warning(f"Failover Triggered: Fetching {len(missing_crypto)} crypto symbols from CoinGecko...")
            backup_prices = await self.coingecko.get_prices(missing_crypto)
            all_prices.update(backup_prices)

        # Publish
        for symbol, price in all_prices.items():
            await event_bus.publish(PriceUpdateEvent(symbol=symbol, price=price))

    async def _get_tiered_symbols(self) -> tuple[Set[str], Set[str]]:
        """
        Logic: If a symbol is tracked by ANY premium user, it's Fast Lane.
        Otherwise, it's Slow Lane.
        """
        fast = set()
        slow = set()
        
        async with AsyncSessionLocal() as session:
            # We need to join with User to check is_premium
            from sqlalchemy import select
            from data.models import Alert, Trade, User
            
            # 1. Check Alerts — fast if user is premium OR alert is individually boosted
            alert_query = await session.execute(
                select(Alert.symbol, User.is_premium, Alert.is_boosted)
                .join(User, Alert.user_id == User.id)
                .where(Alert.is_active == True)
            )
            for symbol, is_premium, is_boosted in alert_query.all():
                if is_premium or is_boosted:
                    fast.add(symbol)
                else:
                    slow.add(symbol)

            # 2. Check Trades
            trade_query = await session.execute(
                select(Trade.symbol, User.is_premium)
                .join(User, Trade.user_id == User.id)
                .where(Trade.is_closed == False)
            )
            for symbol, is_premium in trade_query.all():
                if is_premium:
                    fast.add(symbol)
                else:
                    slow.add(symbol)

        # Cleanup: If a symbol is in both, remove from slow
        slow = slow - fast
        return fast, slow
