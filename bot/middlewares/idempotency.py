"""
idempotency.py
Prevents processing the same Telegram update twice by caching the update_id.
"""
from __future__ import annotations
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class IdempotencyMiddleware(BaseMiddleware):
    def __init__(self, ttl: int = 300) -> None:
        super().__init__()
        # Cache processed update IDs. 10000 items, 5 minute TTL
        self._processed = TTLCache(maxsize=10000, ttl=ttl)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # aiogram's base event in dispatcher layers is often an Update
        # If it's an Update, we can extract update_id
        if isinstance(event, Update):
            update_id = event.update_id
            if update_id in self._processed:
                logger.warning(f"Duplicate update_id {update_id} detected. Skipping.")
                return None
            
            # Mark as seen
            self._processed[update_id] = True

        return await handler(event, data)
