from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from app.data.models import BotSetting, PaymentMethod, Transaction, User


# ─────────────────────────────────────────────────
# BOT SETTINGS REPOSITORY
# ─────────────────────────────────────────────────

class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def set(self, key: str, value: str, description: str = "") -> None:
        existing = await self.session.execute(
            select(BotSetting).where(BotSetting.key == key)
        )
        row = existing.scalar_one_or_none()
        if row:
            row.value = value
        else:
            self.session.add(BotSetting(key=key, value=value, description=description))
        await self.session.commit()

    async def get_all(self) -> list[BotSetting]:
        result = await self.session.execute(select(BotSetting).order_by(BotSetting.key))
        return list(result.scalars().all())


# ─────────────────────────────────────────────────
# PAYMENT METHODS REPOSITORY
# ─────────────────────────────────────────────────

class PaymentMethodRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> list[PaymentMethod]:
        result = await self.session.execute(
            select(PaymentMethod).where(PaymentMethod.is_active == True)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[PaymentMethod]:
        result = await self.session.execute(select(PaymentMethod))
        return list(result.scalars().all())

    async def get_by_id(self, pm_id: int) -> PaymentMethod | None:
        result = await self.session.execute(
            select(PaymentMethod).where(PaymentMethod.id == pm_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, details: str) -> PaymentMethod:
        pm = PaymentMethod(name=name, details=details, is_active=True)
        self.session.add(pm)
        await self.session.commit()
        await self.session.refresh(pm)
        return pm

    async def update(self, pm_id: int, name: str = None, details: str = None, is_active: bool = None):
        values = {}
        if name is not None: values["name"] = name
        if details is not None: values["details"] = details
        if is_active is not None: values["is_active"] = is_active
        if values:
            await self.session.execute(
                update(PaymentMethod).where(PaymentMethod.id == pm_id).values(**values)
            )
            await self.session.commit()

    async def delete(self, pm_id: int):
        await self.session.execute(
            delete(PaymentMethod).where(PaymentMethod.id == pm_id)
        )
        await self.session.commit()


# ─────────────────────────────────────────────────
# TRANSACTION REPOSITORY
# ─────────────────────────────────────────────────

class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, amount: float, currency: str,
                     tx_type: str, evidence: str, pm_id: int) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            payment_method_id=pm_id,
            amount=amount,
            currency=currency,
            tx_type=tx_type,
            evidence=evidence,
            status="pending"
        )
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    async def get_pending(self) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.status == "pending")
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_user_transactions(self, user_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve(self, tx_id: int, admin_note: str = "") -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == tx_id)
        )
        tx = result.scalar_one_or_none()
        if tx:
            tx.status = "approved"
            tx.admin_note = admin_note
            await self.session.commit()
            await self.session.refresh(tx)
        return tx

    async def reject(self, tx_id: int, admin_note: str = "") -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == tx_id)
        )
        tx = result.scalar_one_or_none()
        if tx:
            tx.status = "rejected"
            tx.admin_note = admin_note
            await self.session.commit()
            await self.session.refresh(tx)
        return tx

    async def count_pending(self) -> int:
        result = await self.session.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "pending")
        )
        return result.scalar() or 0

    async def approve_and_credit_user(self, tx_id: int, admin_note: str = "") -> Transaction | None:
        """Approve a transaction and credit the user appropriately."""
        from datetime import datetime, timezone, timedelta

        tx = await self.approve(tx_id, admin_note)
        if not tx:
            return None

        if tx.tx_type == "credits":
            # Use the actual transaction amount instead of hardcoded 10
            credit_amount = int(tx.amount)
            await self.session.execute(
                update(User).where(User.id == tx.user_id)
                .values(credits=User.credits + credit_amount)
            )
        elif tx.tx_type in ("weekly", "monthly", "yearly"):
            days_map = {"weekly": 7, "monthly": 30, "yearly": 365}
            days = days_map[tx.tx_type]
            await self.session.execute(
                update(User).where(User.id == tx.user_id)
                .values(
                    is_premium=True,
                    premium_until=datetime.now(timezone.utc) + timedelta(days=days)
                )
            )
        await self.session.commit()
        return tx
