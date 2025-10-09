from __future__ import annotations
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.repositories.events_repo import EventRepository

router = APIRouter(prefix="/analytics/bq", tags=["analytics"])

def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class BQ11Row(BaseModel):
    day: str
    category_id: str | None
    count: int

@router.get("/1_1", response_model=List[BQ11Row])
async def bq_1_1(
    start: datetime = Query(..., description="ISO-8601 e.g. 2025-10-02T00:00:00Z"),
    end: datetime   = Query(..., description="ISO-8601 e.g. 2025-10-09T23:59:59Z"),
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    repo = EventRepository(db)
    rows = await repo.bq_1_1_listings_per_day_by_category(start=_to_utc(start), end=_to_utc(end))
    return [
        BQ11Row(day=str(r["day"]), category_id=r["category_id"], count=int(r["n"]))
        for r in rows
    ]

class BQ12Row(BaseModel):
    step: str | None
    total: int
    cancelled: int
    pct_cancelled: float

@router.get("/1_2", response_model=List[BQ12Row])
async def bq_1_2(
    start: datetime = Query(..., description="ISO-8601 e.g. 2025-10-02T00:00:00Z"),
    end: datetime   = Query(..., description="ISO-8601 e.g. 2025-10-09T23:59:59Z"),
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    repo = EventRepository(db)
    rows = await repo.bq_1_2_escrow_cancel_rate(start=_to_utc(start), end=_to_utc(end))
    return [
        BQ12Row(
            step=r["step"],
            total=int(r["total"]),
            cancelled=int(r["cancelled"]),
            pct_cancelled=float(r["pct_cancelled"]),
        )
        for r in rows
    ]
