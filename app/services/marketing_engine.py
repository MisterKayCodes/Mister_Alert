import asyncio
import random
from typing import List, Optional
from loguru import logger
from telethon import events
from datetime import datetime

from app.services.event_bus import event_bus
from app.data.database import AsyncSessionLocal
from app.data.repositories.marketing import MarketingRepository
from app.utils.template_engine import DynamicTemplateEngine
from app.services.event_bus import event_bus
from app.data.database import AsyncSessionLocal
from app.data.repositories.marketing import MarketingRepository
from app.utils.template_engine import DynamicTemplateEngine
from config import settings

class MarketingEngine:
    def __init__(self, bot=None):
        self.bot = bot # Dependency Injection (prevents illegal layer-to-layer imports)
        self.repo: Optional[MarketingRepository] = None
        self.active_keywords = ["signal", "alert", "indicator", "trade", "fomo", "gold", "xau", "premium"]
        self.bot_username: Optional[str] = None

    async def setup(self):
        """Initializes the engine and subscribes to events."""
        event_bus.subscribe(events.NewMessage.Event, self.handle_group_message)
        logger.info("Mister Marketing Engine initialized and subscribed to EventBus.")
        
        # Get bot username for {{handle}} placeholder
        try:
            me = await self.bot.get_me()
            self.bot_username = f"@{me.username}"
        except Exception as e:
            logger.warning(f"Could not fetch bot username: {e}")
            self.bot_username = "@MisterAlertBot"

    async def handle_group_message(self, event: events.NewMessage.Event):
        """Process incoming messages from target groups."""
        if not event.is_group:
            return

        chat_id = str(event.chat_id)
        text = event.message.message.lower() if event.message.message else ""

        async with AsyncSessionLocal() as session:
            repo = MarketingRepository(session)
            
            # 1. Check if the group is a monitored target
            targets = await repo.get_targets(monitored_only=True)
            target_ids = [t.chat_id for t in targets]
            
            if chat_id not in target_ids:
                return

            # 2. Check for keywords
            if not any(kw in text for kw in self.active_keywords):
                return

            # 3. Check Current Goals & Limits (Protection Layer)
            stats = await repo.get_stats_summary()
            current = stats.get('daily_replies', {}).get('current', 0)
            target = stats.get('daily_replies', {}).get('target', 15)

            if current >= target:
                logger.debug(f"Daily reply goal reached ({current}/{target}). Skipping.")
                return

            # 4. Pick a random active template
            templates = await repo.get_templates(active_only=True)
            if not templates:
                logger.warning("No active marketing templates found!")
                return

            template = random.choice(templates)
            
            # 5. Render Template
            context = {"handle": self.bot_username}
            reply_text = DynamicTemplateEngine.render(template.content, context)

            # 6. Safety Delay (Look Human)
            delay = random.randint(30, 90)
            logger.info(f"Keyword Hit in {chat_id}! Waiting {delay}s to reply...")
            await asyncio.sleep(delay)

            # 7. Send Reply via UserBot (The Event object belongs to Telethon client)
            try:
                await event.reply(reply_text)
                await repo.log_stat(type='reply', chat_id=chat_id, template_name=template.name)
                logger.success(f"Marketing reply sent to {chat_id} using template '{template.name}'")
            except Exception as e:
                logger.error(f"Failed to send marketing reply: {e}")

    async def start_reporting_logic(self):
        """Background loop for 11 PM reporting and goal resets."""
        while True:
            now = datetime.now()
            # Check if it's 11:00 PM (23:00)
            if now.hour == 23 and now.minute == 0:
                await self.send_daily_report()
                # Wait a minute to prevent double trigging
                await asyncio.sleep(65)
            
            # Deep sleep to save CPU, check every 30s
            await asyncio.sleep(30)

    async def send_daily_report(self):
        """Sends the 11 PM Marketing Summary to all admins."""
        async with AsyncSessionLocal() as session:
            repo = MarketingRepository(session)
            stats = await repo.get_stats_summary()
            
            report = (
                "🎯 <b>Mister Marketing Engine: Daily Report</b>\n\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                "───────────────────\n"
            )
            
            for g_type, data in stats.items():
                name = "Keyword Replies" if g_type == 'daily_replies' else "Group Posts"
                percentage = (data['current'] / data['target'] * 100) if data['target'] > 0 else 0
                report += f"🔹 {name}: <b>{data['current']}/{data['target']}</b> ({percentage:.1f}%)\n"

            report += "\n🚀 <i>Daily goals will be reset now. Keep building!</i>"

            for admin_id in settings.admin_ids:
                try:
                    await self.bot.send_message(admin_id, report, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to send report to admin {admin_id}: {e}")

            await repo.reset_daily_goals()
            logger.info("Daily marketing goals reset.")
