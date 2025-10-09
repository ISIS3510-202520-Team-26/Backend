from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.dispute import DisputeCreate, DisputeOut, DisputeUpdate

from app.api.deps import get_db, get_current_user
from app.repositories.dispute_repo import DisputeRepository

router = APIRouter(prefix="/disputes", tags=["disputes"])

@router.post("", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    body: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    repo = DisputeRepository(db)
    rec = await repo.create(order_id=body.order_id, raised_by=user.id, reason=body.reason, status="open")
    await db.commit()
    return DisputeOut(
        id=rec.id, order_id=rec.order_id, raised_by=rec.raised_by, reason=rec.reason, status=rec.status, created_at=rec.created_at
    )

@router.patch("/{dispute_id}", response_model=DisputeOut)
async def update_dispute(dispute_id: str, body: DisputeUpdate, db: AsyncSession = Depends(get_db)):
    repo = DisputeRepository(db)
    rec = await repo.get(dispute_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Dispute not found")
    rec = await repo.set_status(rec, body.status)
    await db.commit()
    return DisputeOut(
        id=rec.id, order_id=rec.order_id, raised_by=rec.raised_by, reason=rec.reason, status=rec.status, created_at=rec.created_at
    )

@router.get("/open", response_model=list[DisputeOut])
async def list_open(db: AsyncSession = Depends(get_db)):
    repo = DisputeRepository(db)
    rows = await repo.list_open(limit=100)
    return [
        DisputeOut(
            id=r.id, order_id=r.order_id, raised_by=r.raised_by, reason=r.reason, status=r.status, created_at=r.created_at
        )
        for r in rows
    ]

@router.get("/orders/{order_id}", response_model=DisputeOut | None)
async def get_by_order(order_id: str, db: AsyncSession = Depends(get_db)):
    repo = DisputeRepository(db)
    r = await repo.get_by_order(order_id)
    if not r:
        return None
    return DisputeOut(
        id=r.id, order_id=r.order_id, raised_by=r.raised_by, reason=r.reason, status=r.status, created_at=r.created_at
    )
