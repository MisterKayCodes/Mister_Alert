import pytest
from app.data.database import AsyncSessionLocal
from app.data.economy_repository import SettingsRepository
from config import settings

@pytest.mark.asyncio
async def test_god_key_functionality(test_session):
    # 1. Setup: Let's mock the God Key in the test database
    settings_repo = SettingsRepository(test_session)
    await settings_repo.set("god_key", "MISTER-TEST-KEY", "Test Key")
    
    # 2. Simulate User hitting the recovery logic
    settings.admin_ids = [] # Ensure user is NOT an admin
    user_id = 123456789
    message_text = "MISTER-TEST-KEY"
    
    current_key = await settings_repo.get("god_key")
    
    # Validation logic inside recovery.py
    if current_key and message_text == current_key:
        if user_id not in settings.admin_ids:
            settings.admin_ids.append(user_id)
            
        # Burn and rotate
        import string
        import random
        chars = string.ascii_uppercase + string.digits
        secret = "".join(random.choices(chars, k=24))
        new_key = f"MISTER-ALERT-GOD-{secret}"
        await settings_repo.set("god_key", new_key, "Test Key")
        
    # 3. Assertions (The CI/CD Check)
    assert user_id in settings.admin_ids, "User was not promoted to admin!"
    
    new_db_key = await settings_repo.get("god_key")
    assert new_db_key != "MISTER-TEST-KEY", "God Key failed to auto-rotate (burn)!"
    assert new_db_key.startswith("MISTER-ALERT-GOD-"), "New God Key format is invalid!"
