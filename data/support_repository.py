from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from data.models import SupportTicket, User
from datetime import datetime, timezone

class SupportTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, message: str) -> SupportTicket:
        ticket = SupportTicket(user_id=user_id, message=message)
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def get_all_open(self) -> List[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.status == "open").order_by(SupportTicket.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, ticket_id: int) -> Optional[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def add_reply(self, ticket_id: int, reply_text: str) -> Optional[SupportTicket]:
        ticket = await self.get_by_id(ticket_id)
        if ticket:
            ticket.admin_reply = reply_text
            ticket.status = "replied"
            ticket.replied_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(ticket)
        return ticket

    async def get_user_tickets(self, user_id: int) -> List[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(SupportTicket.created_at.desc())
        )
        return result.scalars().all()
