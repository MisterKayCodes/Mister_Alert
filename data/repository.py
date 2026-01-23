from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from .models import User, Alert, Trade


# =========================
# USER REPOSITORY (Memory: Identity)
# =========================

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: str, username: str | None) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            is_premium=False,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: str, username: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user
        return await self.create_user(telegram_id, username)

    async def set_premium(self, user_id: int, is_premium: bool):
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_premium=is_premium)
        )
        await self.session.commit()


# =========================
# ALERT REPOSITORY (Memory: Perception)
# =========================

class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        user_id: int,
        symbol: str,
        price_above: float | None,
        price_below: float | None,
    ) -> Alert:
        alert = Alert(
            user_id=user_id,
            symbol=symbol,
            price_above=price_above,
            price_below=price_below,
            is_active=True,
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_active_alerts(self) -> list[Alert]:
        result = await self.session.execute(
            select(Alert).where(Alert.is_active == True)
        )
        return list(result.scalars().all())

    async def get_user_alerts(self, user_id: int) -> list[Alert]:
        result = await self.session.execute(
            select(Alert).where(Alert.user_id == user_id)
        )
        return list(result.scalars().all())

    async def deactivate_alert(self, alert_id: int):
        await self.session.execute(
            update(Alert)
            .where(Alert.id == alert_id)
            .values(is_active=False)
        )
        await self.session.commit()


# =========================
# TRADE REPOSITORY (Memory: History)
# =========================

class TradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_trade(
        self,
        user_id: int,
        symbol: str,
        entry_price: float,
        stop_loss: float | None,
        take_profit: float | None,
        position_size: float | None,
    ) -> Trade:
        trade = Trade(
            user_id=user_id,
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            is_closed=False,
        )
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade

    async def get_open_trades(self) -> list[Trade]:
        result = await self.session.execute(
            select(Trade).where(Trade.is_closed == False)
        )
        return list(result.scalars().all())

    async def close_trade(self, trade_id: int, result_text: str):
        """Rule 5: Idempotent state change in the Vault."""
        try:
            await self.session.execute(
                update(Trade)
                .where(Trade.id == trade_id)
                .values(
                    is_closed=True,
                    closed_at=func.now(),  # ✅ Handled by SQL engine
                    result=result_text,
                )
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e