from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

def _parse_iso(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid ISO datetime: {s}")

def _range(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    if not start or not end:
        raise HTTPException(status_code=400, detail="Query params 'start' and 'end' are required (ISO).")
    return _parse_iso(start), _parse_iso(end)

# ---------- 1.x ----------
class BQ11Row(BaseModel):
    day: str
    category_id: str | None
    count: int

@router.get("/bq/1_1", response_model=list[BQ11Row])
async def bq_1_1(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_1_1_listings_per_day_by_category(start=s_dt, end=e_dt)
    return [BQ11Row(day=str(r[0]), category_id=r[1], count=int(r[2])) for r in rows]

class BQ12Row(BaseModel):
    step: str
    total: int
    cancelled: int
    pct_cancelled: float

@router.get("/bq/1_2", response_model=list[BQ12Row])
async def bq_1_2(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_1_2_escrow_cancel_rate(start=s_dt, end=e_dt)
    return [BQ12Row(step=r[0], total=int(r[1]), cancelled=int(r[2]), pct_cancelled=float(r[3])) for r in rows]

# ---------- 2.x ----------
class BQ21Row(BaseModel):
    day: str
    event_type: str | None
    count: int

@router.get("/bq/2_1", response_model=list[BQ21Row])
async def bq_2_1(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_2_1_events_per_type_by_day(start=s_dt, end=e_dt)
    return [BQ21Row(day=str(r[0]), event_type=r[1], count=int(r[2])) for r in rows]

class BQ22Row(BaseModel):
    day: str
    button: str | None
    count: int

@router.get("/bq/2_2", response_model=list[BQ22Row])
async def bq_2_2(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_2_2_clicks_by_button_by_day(start=s_dt, end=e_dt)
    return [BQ22Row(day=str(r[0]), button=r[1], count=int(r[2])) for r in rows]

class BQ24Row(BaseModel):
    screen: str | None
    total_seconds: int
    views: int
    avg_seconds: int

@router.get("/bq/2_4", response_model=list[BQ24Row])
async def bq_2_4(
    start: str = Query(..., description="ISO 8601 e.g. 2025-10-14T00:00:00Z"),
    end:   str = Query(..., description="ISO 8601 e.g. 2025-10-15T00:00:00Z"),
    max_idle_sec: int = Query(300, ge=30, le=3600, description="Cap para intervalos sin siguiente pantalla"),
    db: AsyncSession = Depends(get_db),
):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_2_4_time_by_screen(start=s_dt, end=e_dt, max_idle_sec=max_idle_sec)
    return [
        BQ24Row(screen=r[0], total_seconds=int(r[1]), views=int(r[2]), avg_seconds=int(r[3]))
        for r in rows
    ]

# ---------- 3.x ----------
class BQ31Row(BaseModel):
    day: str
    dau: int

@router.get("/bq/3_1", response_model=list[BQ31Row])
async def bq_3_1(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_3_1_dau(start=s_dt, end=e_dt)
    return [BQ31Row(day=str(r[0]), dau=int(r[1])) for r in rows]

class BQ32Row(BaseModel):
    day: str
    sessions: int

@router.get("/bq/3_2", response_model=list[BQ32Row])
async def bq_3_2(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_3_2_sessions_by_day(start=s_dt, end=e_dt)
    return [BQ32Row(day=str(r[0]), sessions=int(r[1])) for r in rows]

# ---------- 4.x ----------
class BQ41Row(BaseModel):
    day: str
    status: str
    count: int

@router.get("/bq/4_1", response_model=list[BQ41Row])
async def bq_4_1(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_4_1_orders_by_status_by_day(start=s_dt, end=e_dt)
    return [BQ41Row(day=str(r[0]), status=r[1], count=int(r[2])) for r in rows]

class BQ42Row(BaseModel):
    day: str
    gmv_cents: int
    orders_paid: int

@router.get("/bq/4_2", response_model=list[BQ42Row])
async def bq_4_2(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_4_2_gmv_by_day(start=s_dt, end=e_dt)
    return [BQ42Row(day=str(r[0]), gmv_cents=int(r[1]), orders_paid=int(r[2])) for r in rows]

# ---------- 5.x ----------
class BQ51Row(BaseModel):
    day: str
    category_id: str | None
    count: int

@router.get("/bq/5_1", response_model=list[BQ51Row])
async def bq_5_1(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)):
    s_dt, e_dt = _range(start, end)
    rows = await AnalyticsService(db).bq_5_1_quick_view_by_category_by_day(start=s_dt, end=e_dt)
    return [BQ51Row(day=str(r[0]), category_id=r[1], count=int(r[2])) for r in rows]
