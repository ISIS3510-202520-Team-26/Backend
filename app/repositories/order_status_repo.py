from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order_status import OrderStatusHistory
from .base import BaseRepository

class OrderStatusRepository(BaseRepository[OrderStatusHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderStatusHistory)

    async def add_history(self, *, order_id: str, from_status: str | None, to_status: str, reason: str | None = None) -> OrderStatusHistory:
        rec = OrderStatusHistory(order_id=order_id, from_status=from_status, to_status=to_status, reason=reason)
        return await self.add(rec)

    async def list_for_order(self, order_id: str) -> List[OrderStatusHistory]:
        stmt = select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.created_at.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()
