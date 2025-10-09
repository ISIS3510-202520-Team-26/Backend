from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from .base import BaseRepository

class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Payment)

    async def create(self, *, order_id: str, provider: str, amount_cents: int, provider_ref: str | None = None, status: str = "authorized") -> Payment:
        p = Payment(order_id=order_id, provider=provider, provider_ref=provider_ref, amount_cents=amount_cents, status=status)
        return await self.add(p)

    async def get_by_order(self, order_id: str) -> List[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_by_provider(self, provider: str, limit: int = 50) -> List[Payment]:
        stmt = select(Payment).where(Payment.provider == provider).order_by(Payment.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()
