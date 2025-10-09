from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.services.escrow_service import emit_escrow_step_event
from app.schemas.escrow import EscrowStepIn

router = APIRouter(prefix="/escrow", tags=["escrow"])


@router.post("/step", status_code=status.HTTP_202_ACCEPTED)
async def escrow_step(data: EscrowStepIn, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    await emit_escrow_step_event(db, escrow_id=data.escrow_id, step=data.step, result=data.result)
    await db.commit()
    return {"ok": True}
