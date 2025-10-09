from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.payment import PaymentCallbackIn
from app.api.deps import get_current_user
from app.db.session import get_db
from app.services.payment_service import capture_payment, refund_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/capture", status_code=status.HTTP_200_OK)
async def capture(cb: PaymentCallbackIn, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ok = await capture_payment(db, order_id=cb.order_id, provider_ref=cb.provider_ref)
    await db.commit()
    return {"captured": bool(ok)}

@router.post("/refund", status_code=status.HTTP_200_OK)
async def refund(cb: PaymentCallbackIn, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ok = await refund_payment(db, order_id=cb.order_id, provider_ref=cb.provider_ref)
    await db.commit()
    return {"refunded": bool(ok)}
