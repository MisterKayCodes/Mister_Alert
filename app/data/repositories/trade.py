from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.data.models import Trade

class TradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_trade(self, user_id: int, symbol: str, entry_price: float, stop_loss: float | None, take_profit: float | None, position_size: float | None, direction: str = "LONG") -> Trade:
        trade = Trade(user_id=user_id, symbol=symbol, entry_price=entry_price, stop_loss=stop_loss, take_profit=take_profit, position_size=position_size, direction=direction, is_closed=False)
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade

    async def get_open_trades(self) -> list[Trade]:
        result = await self.session.execute(select(Trade).where(Trade.is_closed == False))
        return list(result.scalars().all())

    async def count_active(self) -> int:
        result = await self.session.execute(select(func.count(Trade.id)).where(Trade.is_closed == False))
        return result.scalar() or 0

    async def update_trade_targets(self, trade_id: int, stop_loss: float | None, take_profit: float | None):
        await self.session.execute(
            update(Trade).where(Trade.id == trade_id)
            .values(stop_loss=stop_loss, take_profit=take_profit)
        )
        await self.session.commit()

    async def get_tiered_symbols_data(self):
        """Returns (symbol, is_premium) for all open trades."""
        from app.data.models import User
        result = await self.session.execute(
            select(Trade.symbol, User.is_premium)
            .join(User, Trade.user_id == User.id)
            .where(Trade.is_closed == False)
        )
        return result.all()

    async def close_trade(self, trade_id: int, result_text: str, closed_at_price: float | None = None):
        await self.session.execute(
            update(Trade).where(Trade.id == trade_id)
            .values(is_closed=True, closed_at=func.now(), closed_at_price=closed_at_price, result=result_text)
        )
        await self.session.commit()

    async def get_all_closed_trades(self, user_id: int) -> list[Trade]:
        result = await self.session.execute(
            select(Trade).where(Trade.user_id == user_id, Trade.is_closed == True)
            .order_by(Trade.closed_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_trade_history(self, user_id: int, limit: int = 10) -> list[Trade]:
        result = await self.session.execute(select(Trade).where(Trade.user_id == user_id, Trade.is_closed == True).order_by(Trade.closed_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def delete_trade(self, trade_id: int):
        await self.session.execute(delete(Trade).where(Trade.id == trade_id))
        await self.session.commit()
