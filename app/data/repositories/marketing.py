from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.data.models import MarketingTemplate, MarketingTarget, MarketingStat, MarketingGoal

class MarketingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ─────────────────────────────────────────────────
    # TEMPLATES
    # ─────────────────────────────────────────────────

    async def get_templates(self, active_only: bool = False) -> List[MarketingTemplate]:
        query = select(MarketingTemplate)
        if active_only:
            query = query.where(MarketingTemplate.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_template(self, name: str, content: str) -> MarketingTemplate:
        template = MarketingTemplate(name=name, content=content)
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete_template(self, template_id: int):
        await self.session.execute(delete(MarketingTemplate).where(MarketingTemplate.id == template_id))
        await self.session.commit()

    # ─────────────────────────────────────────────────
    # TARGETS
    # ─────────────────────────────────────────────────

    async def get_targets(self, monitored_only: bool = False) -> List[MarketingTarget]:
        query = select(MarketingTarget)
        if monitored_only:
            query = query.where(MarketingTarget.is_monitored == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_target(self, chat_id: str, chat_title: Optional[str] = None) -> MarketingTarget:
        target = MarketingTarget(chat_id=str(chat_id), chat_title=chat_title)
        self.session.add(target)
        await self.session.commit()
        await self.session.refresh(target)
        return target

    # ─────────────────────────────────────────────────
    # STATS & GOALS
    # ─────────────────────────────────────────────────

    async def log_stat(self, type: str, chat_id: str, template_name: Optional[str] = None):
        stat = MarketingStat(type=type, chat_id=str(chat_id), template_name=template_name)
        self.session.add(stat)
        
        # Update current goal progress
        goal_type = 'daily_replies' if type == 'reply' else 'daily_posts'
        await self.session.execute(
            update(MarketingGoal)
            .where(MarketingGoal.goal_type == goal_type)
            .values(current_value=MarketingGoal.current_value + 1)
        )
        await self.session.commit()

    async def get_stats_summary(self):
        # Implementation for 11 PM report
        result = await self.session.execute(select(MarketingGoal))
        goals = result.scalars().all()
        return {g.goal_type: {"current": g.current_value, "target": g.target_value} for g in goals}

    async def reset_daily_goals(self):
        await self.session.execute(update(MarketingGoal).values(current_value=0, last_reset=func.now()))
        await self.session.commit()
