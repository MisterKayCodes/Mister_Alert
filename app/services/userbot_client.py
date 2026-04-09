import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from loguru import logger
from typing import Optional

from config import settings
from app.services.event_bus import event_bus

class UserBotClient:
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.session_string = None
        self.client: Optional[TelegramClient] = None
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    async def start(self, session_string: Optional[str] = None, api_id: Optional[int] = None, api_hash: Optional[str] = None):
        """Starts the UserBot client with dynamic credentials."""
        self.session_string = session_string or settings.telegram_session_string
        self.api_id = api_id or settings.telegram_api_id
        self.api_hash = api_hash or settings.telegram_api_hash
        
        if not all([self.api_id, self.api_hash, self.session_string]):
            logger.warning("UserBot credentials or Session String missing. Marketing engine inactive.")
            return

        if self._is_running:
            await self.stop()

        self._loop_task = asyncio.create_task(self._run())
        return True

    async def _run(self):
        try:
            logger.info("Connecting UserBot...")
            self.client = TelegramClient(
                StringSession(self.session_string),
                self.api_id,
                self.api_hash,
                connection_retries=5,
                retry_delay=10
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("UserBot session is invalid!")
                return

            me = await self.client.get_me()
            logger.success(f"UserBot active as {me.first_name}")
            
            @self.client.on(events.NewMessage)
            async def handle_new_message(event):
                await event_bus.publish(event)

            self._is_running = True
            await self.client.run_until_disconnected()

        except Exception as e:
            logger.error(f"UserBot Error: {e}")
        finally:
            self._is_running = False

    async def stop(self):
        if self.client:
            await self.client.disconnect()
        if self._loop_task:
            self._loop_task.cancel()
        self._is_running = False
        logger.info("UserBot stopped.")

    async def validate_credentials(self, api_id: int, api_hash: str, session_string: str) -> tuple[bool, str]:
        """Performs a pre-flight connection test to verify credentials."""
        temp_client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash,
            connection_retries=1,
            retry_delay=1
        )
        try:
            logger.info("Performing pre-flight credential check...")
            await temp_client.connect()
            if not await temp_client.is_user_authorized():
                return False, "Session string is invalid or expired."
            
            me = await temp_client.get_me()
            return True, f"Successfully authorized as {me.first_name}"
        except Exception as e:
            return False, str(e)
        finally:
            await temp_client.disconnect()

    async def reload(self, new_session_string: str, new_api_id: Optional[int] = None, new_api_hash: Optional[str] = None):
        """Hot reload with a new session string and/or API credentials."""
        logger.info("Hot reloading UserBot session and credentials...")
        await self.stop()
        await self.start(session_string=new_session_string, api_id=new_api_id, api_hash=new_api_hash)

    @property
    def is_active(self) -> bool:
        return self._is_running and self.client and self.client.is_connected()

# Global Singleton Instance
userbot_client = UserBotClient()
