import pytest
from app.data.models import Voucher, User
from app.data.voucher_repository import VoucherRepository

# This is a unit test that acts as our CI/CD pipeline check.
# "Senior Devs" at Facebook write these to prove code works before deploying.

@pytest.mark.asyncio
async def test_voucher_generation_and_redemption(test_session):
    # 1. Setup: Create our repository and a dummy user
    repo = VoucherRepository(test_session)
    user = User(telegram_id="12345", username="testuser")
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    # 2. Test Minting (Generation)
    voucher = await repo.mint_voucher(reward_type="premium_1_month")
    
    assert voucher is not None
    assert voucher.code.startswith("PREM-")
    assert len(voucher.code) == 13 # PREM- + 8 chars
    assert voucher.is_used is False
    assert voucher.reward_type == "premium_1_month"

    # 3. Test Invalid Redemption
    bad_result = await repo.redeem(code="FAKE-CODE", user_id=user.id)
    assert bad_result["success"] is False
    assert "Invalid" in bad_result["message"]

    # 4. Test Valid Redemption
    good_result = await repo.redeem(code=voucher.code, user_id=user.id)
    assert good_result["success"] is True
    assert good_result["reward_type"] == "premium_1_month"

    # Verify DB State updated
    await test_session.refresh(voucher)
    assert voucher.is_used is True
    assert voucher.used_by == user.id

    # 5. Test Double Spend Prevention (Security)
    double_spend_result = await repo.redeem(code=voucher.code, user_id=user.id)
    assert double_spend_result["success"] is False
    assert "already been redeemed" in double_spend_result["message"]
