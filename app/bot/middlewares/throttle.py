"""
throttle.py
Prevents double-tap and button-spam by holding a per-user asyncio lock.
If a user's request is already in-flight, the duplicate is silently dropped
with an instant callback answer so Telegram's spinner clears immediately.
"""
from __future__ import annotations
import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message


class ThrottleMiddleware(BaseMiddleware):
    """
    In-memory per-user lock.
    Works for both messages and callback queries.
    """
    def __init__(self) -> None:
        super().__init__()
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Identify the user
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        lock = self._get_lock(user.id)

        if lock.locked():
            # Duplicate tap — drop silently, clear Telegram spinner
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("⏳ Processing...", show_alert=False)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Throttle callback answer failed: {e}")
            return  # Drop the duplicate

        async with lock:
            return await handler(event, data)
