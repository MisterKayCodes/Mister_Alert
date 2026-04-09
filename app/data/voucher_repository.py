import random
import string
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.data.models import Voucher
from datetime import datetime, timezone

class VoucherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _generate_code(self, prefix: str) -> str:
        """Generates a secure 8-character random code with a given prefix."""
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}-{random_part}"

    async def mint_voucher(self, reward_type: str) -> Voucher:
        """Creates a new unique voucher code in the database."""
        prefix = "PREM" if "premium" in reward_type.lower() else "CRED"
        
        while True:
            # Generate a code and ensure it's unique
            code = self._generate_code(prefix)
            existing = await self.get_by_code(code)
            if not existing:
                break
                
        voucher = Voucher(code=code, reward_type=reward_type)
        self.session.add(voucher)
        await self.session.commit()
        await self.session.refresh(voucher)
        return voucher

    async def get_by_code(self, code: str) -> Voucher | None:
        """Looks up a voucher by its activation code."""
        result = await self.session.execute(
            select(Voucher).where(Voucher.code == code)
        )
        return result.scalar_one_or_none()

    async def redeem(self, code: str, user_id: int) -> dict:
        """
        Attempts to redeem a code for a specific user.
        Returns a dict: {"success": bool, "message": str, "reward_type": str}
        """
        voucher = await self.get_by_code(code)
        
        if not voucher:
            return {"success": False, "message": "❌ Invalid activation code."}
            
        if voucher.is_used:
            return {"success": False, "message": "❌ This code has already been redeemed."}
            
        # Mark as used (Atomic-like in the current session context)
        voucher.is_used = True
        voucher.used_by = user_id
        voucher.used_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        
        return {
            "success": True, 
            "message": "✅ Code redeemed successfully!",
            "reward_type": voucher.reward_type
        }

    async def get_stats(self) -> dict:
        """Returns voucher economy statistics for the admin dashboard."""
        total_result = await self.session.execute(select(func.count(Voucher.id)))
        total = total_result.scalar() or 0
        
        redeemed_result = await self.session.execute(
            select(func.count(Voucher.id)).where(Voucher.is_used == True)
        )
        redeemed = redeemed_result.scalar() or 0
        
        return {"total": total, "redeemed": redeemed, "unused": total - redeemed}
