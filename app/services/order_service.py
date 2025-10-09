from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.repositories.order_repo import OrderRepository
from app.models.enums import OrderStatus, EscrowStatus
from app.services.payment_service import authorize_payment, capture_payment, refund_payment
from app.services.escrow_service import create_escrow, set_status as escrow_set_status, emit_escrow_step_event

async def create_order(
    session: AsyncSession,
    *,
    buyer_id: str,
    seller_id: str,
    listing_id: str,
    total_cents: int,
    currency: str,
) -> str:
    order = Order(
        buyer_id=buyer_id,
        seller_id=seller_id,
        listing_id=listing_id,
        total_cents=total_cents,
        currency=currency,
    )
    session.add(order)
    await session.flush()  # asegura PK
    return str(order.id)

async def pay_order(db: AsyncSession, *, order_id: str) -> bool:
    repo = OrderRepository(db)
    order = await repo.get(order_id)
    if not order or order.status != OrderStatus.created:
        return False
    provider, ref = await authorize_payment(db, order_id=order_id, amount_cents=order.total_cents)
    await repo.set_status(order, OrderStatus.paid, reason="authorized")
    ok = await capture_payment(db, order_id=order_id, provider_ref=ref)
    if ok:
        escrow_id = await create_escrow(db, order_id=order_id, provider="mock")
        await escrow_set_status(db, escrow_id=escrow_id, status=EscrowStatus.funded, step="payment_made", result="success")
        await db.flush()
        return True
    return False

async def complete_order(db: AsyncSession, *, order_id: str) -> bool:
    repo = OrderRepository(db)
    order = await repo.get(order_id)
    if not order:
        return False
    await repo.set_status(order, OrderStatus.completed, reason="delivered")
    return True

async def cancel_order(db: AsyncSession, *, order_id: str, reason: Optional[str] = None) -> bool:
    repo = OrderRepository(db)
    order = await repo.get(order_id)
    if not order:
        return False
    await repo.set_status(order, OrderStatus.cancelled, reason=reason or "cancelled_by_user")
    await refund_payment(db, order_id=order_id, provider_ref="*")
    return True
