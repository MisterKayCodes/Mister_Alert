from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.data.models import Alert

class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(self, user_id: int, symbol: str, price_above: float | None, price_below: float | None) -> Alert:
        alert = Alert(user_id=user_id, symbol=symbol, price_above=price_above, price_below=price_below, is_active=True)
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_active_alerts(self) -> list[Alert]:
        result = await self.session.execute(select(Alert).where(Alert.is_active == True))
        return list(result.scalars().all())

    async def get_tiered_symbols_data(self):
        """Returns (symbol, is_premium, is_boosted) for all active alerts."""
        from app.data.models import User
        result = await self.session.execute(
            select(Alert.symbol, User.is_premium, Alert.is_boosted)
            .join(User, Alert.user_id == User.id)
            .where(Alert.is_active == True)
        )
        return result.all()

    async def get_user_alerts(self, user_id: int) -> list[Alert]:
        result = await self.session.execute(select(Alert).where(Alert.user_id == user_id))
        return list(result.scalars().all())

    async def deactivate_alert(self, alert_id: int):
        await self.session.execute(update(Alert).where(Alert.id == alert_id).values(is_active=False))
        await self.session.commit()

    async def boost_alert(self, alert_id: int):
        await self.session.execute(update(Alert).where(Alert.id == alert_id).values(is_boosted=True))
        await self.session.commit()

    async def count_active(self) -> int:
        result = await self.session.execute(select(func.count(Alert.id)).where(Alert.is_active == True))
        return result.scalar() or 0

    async def delete_alert(self, alert_id: int):
        await self.session.execute(delete(Alert).where(Alert.id == alert_id))
        await self.session.commit()
