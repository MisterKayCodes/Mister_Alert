from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime, timezone, timedelta
from app.data.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: str, username: str | None) -> User:
        user = User(telegram_id=telegram_id, username=username, is_premium=False)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: str, username: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user: return user
        return await self.create_user(telegram_id, username)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def promote_to_premium(self, user_id: int, days: int = 30):
        await self.session.execute(
            update(User).where(User.id == user_id)
            .values(is_premium=True, premium_until=datetime.now(timezone.utc) + timedelta(days=days))
        )
        await self.session.commit()

    async def demote_from_premium(self, user_id: int):
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_premium=False, premium_until=None)
        )
        await self.session.commit()

    async def add_credits(self, user_id: int, amount: int):
        await self.session.execute(
            update(User).where(User.id == user_id).values(credits=User.credits + amount)
        )
        await self.session.commit()

    async def deduct_credits(self, user_id: int, amount: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user or (user.credits or 0) < amount: return False
        await self.session.execute(
            update(User).where(User.id == user_id).values(credits=User.credits - amount)
        )
        await self.session.commit()
        return True

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def count_premium(self) -> int:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_premium == True)
        )
        return result.scalar() or 0

    async def count_recent(self, days: int) -> int:
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            select(func.count(User.id)).where(User.created_at >= recent_cutoff)
        )
        return result.scalar() or 0

    async def get_all_ordered(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def get_expired_users(self) -> list[User]:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(User).where(
                User.is_premium == True,
                User.premium_until != None,
                User.premium_until < now
            )
        )
        return list(result.scalars().all())

    async def update_currency(self, user_id: int, currency: str):
        await self.session.execute(
            update(User).where(User.id == user_id).values(preferred_currency=currency)
        )
        await self.session.commit()

    async def update_timezone(self, user_id: int, tz: str):
        await self.session.execute(
            update(User).where(User.id == user_id).values(timezone=tz)
        )
        await self.session.commit()
