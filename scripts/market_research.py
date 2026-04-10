import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from loguru import logger

# Add root to sys.path to allow absolute imports
sys.path.append(os.getcwd())

from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository

async def run_research(group_name: str, limit: int = 200):
    logger.info(f"🕵️ Starting Market Research on Group: '{group_name}'")
    
    # 1. Fetch Credentials from Database
    async with AsyncSessionLocal() as session:
        sr = SettingsRepository(session)
        sess_str = await sr.get("telegram_session_string")
        aid = await sr.get("telegram_api_id")
        ahash = await sr.get("telegram_api_hash")

    if not all([sess_str, aid, ahash]):
        logger.error("Missing UserBot credentials in DB. Please set them up in the /marketing dashboard first.")
        return

    # 2. Initialize Client
    client = TelegramClient(StringSession(sess_str), int(aid), ahash)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("Session string is invalid or expired.")
            return

        # 3. Find the Group
        target_chat = None
        async for dialog in client.iter_dialogs():
            if dialog.name == group_name:
                target_chat = dialog
                break

        if not target_chat:
            logger.error(f"Could not find group named '{group_name}' in your dialogs.")
            return

        logger.success(f"Found Group: {target_chat.name} (ID: {target_chat.id})")
        
        # 4. Scrape Messages
        messages = await client.get_messages(target_chat, limit=limit)
        
        output_dir = "marketing"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "research_drbills.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"=== MARKET RESEARCH: {group_name} ===\n")
            f.write(f"Extracted: {len(messages)} messages\n")
            f.write(f"Timestamp: {asyncio.get_event_loop().time()}\n\n")
            
            for msg in reversed(messages):
                sender = await msg.get_sender()
                sender_name = getattr(sender, 'first_name', 'Unknown')
                if not sender_name: sender_name = "System/Channel"
                
                timestamp = msg.date.strftime("%Y-%m-%d %H:%M")
                text = msg.text or "[No Text]"
                media_tag = " [🖼️ MEDIA]" if msg.media else ""
                
                f.write(f"[{timestamp}] {sender_name}: {text}{media_tag}\n")
        
        logger.success(f"Successfully scraped {len(messages)} messages to {output_file}")
        print(f"\n--- RESEARCH COMPLETE ---\nFile saved to: {output_file}\n")

    except Exception as e:
        logger.error(f"Scraper Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        target = "DrBillsFx Academy"
    else:
        target = sys.argv[1]
        
    asyncio.run(run_research(target))
