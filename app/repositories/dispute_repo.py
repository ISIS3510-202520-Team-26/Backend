from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dispute import Dispute
from .base import BaseRepository

class DisputeRepository(BaseRepository[Dispute]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Dispute)

    async def create(self, *, order_id: str, raised_by: str, reason: str | None = None, status: str = "open") -> Dispute:
        d = Dispute(order_id=order_id, raised_by=raised_by, reason=reason, status=status)
        return await self.add(d)

    async def get_by_order(self, order_id: str) -> Dispute | None:
        stmt = select(Dispute).where(Dispute.order_id == order_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def set_status(self, dispute: Dispute, status: str) -> Dispute:
        dispute.status = status
        await self.session.flush()
        return dispute

    async def list_open(self, limit: int = 50):
        stmt = select(Dispute).where(Dispute.status == "open").order_by(Dispute.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()
