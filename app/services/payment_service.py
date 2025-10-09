from __future__ import annotations
import uuid
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.payment_repo import PaymentRepository

PROVIDER = "mock"

async def authorize_payment(db: AsyncSession, *, order_id: str, amount_cents: int) -> Tuple[str, str]:
    """
    Mock: autoriza y crea Payment en estado 'authorized'
    Devuelve (provider, provider_ref)
    """
    provider_ref = str(uuid.uuid4())
    repo = PaymentRepository(db)
    await repo.create(order_id=order_id, provider=PROVIDER, amount_cents=amount_cents, provider_ref=provider_ref, status="authorized")
    await db.flush()
    return PROVIDER, provider_ref

async def capture_payment(db: AsyncSession, *, order_id: str, provider_ref: str) -> bool:
    """
    Mock: marca el último pago como 'captured' para el order_id
    """
    repo = PaymentRepository(db)
    pays = await repo.get_by_order(order_id)
    for p in pays:
        if p.provider_ref == provider_ref:
            p.status = "captured"
            await db.flush()
            return True
    return False

async def refund_payment(db: AsyncSession, *, order_id: str, provider_ref: str) -> bool:
    repo = PaymentRepository(db)
    pays = await repo.get_by_order(order_id)
    for p in pays:
        if p.provider_ref == provider_ref:
            p.status = "refunded"
            await db.flush()
            return True
    return False
