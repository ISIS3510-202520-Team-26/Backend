from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.models.order_status import OrderStatusHistory
from app.models.enums import OrderStatus
from .base import BaseRepository

class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    async def create(
        self, *, buyer_id: str, seller_id: str, listing_id: str, total_cents: int, currency: str = "COP"
    ) -> Order:
        order = Order(
            buyer_id=buyer_id,
            seller_id=seller_id,
            listing_id=listing_id,
            total_cents=total_cents,
            currency=currency,
            status=OrderStatus.created,
        )
        self.session.add(order)
        await self.session.flush()
        self.session.add(OrderStatusHistory(order_id=order.id, from_status=None, to_status=OrderStatus.created.value))
        await self.session.flush()
        return order

    async def set_status(self, order: Order, to_status: OrderStatus, reason: str | None = None) -> Order:
        prev = order.status
        order.status = to_status
        self.session.add(OrderStatusHistory(order_id=order.id, from_status=prev.value, to_status=to_status.value, reason=reason))
        await self.session.flush()
        return order

    async def get_with_relations(self, id_: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == id_)
            .options(
                sa.orm.selectinload(Order.status_history),
                sa.orm.selectinload(Order.payments),
                sa.orm.selectinload(Order.escrow),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()
