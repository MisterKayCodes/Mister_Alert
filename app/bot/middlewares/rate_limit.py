"""
rate_limit.py
Token-bucket based rate limiter to prevent users from spamming bot queries.
"""
from __future__ import annotations
import logging
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, window_seconds: int = 10) -> None:
        super().__init__()
        self.limit = limit
        self.window_seconds = window_seconds
        # Store lists of timestamps for each user
        self._user_requests = TTLCache(maxsize=10000, ttl=window_seconds)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Rate limit messages and callbacks ONLY
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        now = time.time()
        user_id = user.id

        # Get existing requests
        requests = self._user_requests.get(user_id, [])
        # Filter requests within the rolling window
        requests = [req_time for req_time in requests if now - req_time < self.window_seconds]

        if len(requests) >= self.limit:
            # Drop the request and notify sparingly
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("⏳ Too many requests. Please wait.", show_alert=True)
                except Exception as e:
                    logger.debug(f"Rate limit callback answer failed: {e}")
            elif isinstance(event, Message):
                # Don't spam them with rate limit messages if they are spamming
                pass
            return

        # Add the current request
        requests.append(now)
        self._user_requests[user_id] = requests

        return await handler(event, data)
