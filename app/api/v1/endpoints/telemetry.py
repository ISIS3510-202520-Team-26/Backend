from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.schemas.telemetry import TelemetryBatchIn
from app.services.telemetry_sink import ingest_batch

router = APIRouter(prefix="/events", tags=["telemetry"])

@router.post("", status_code=202)
async def ingest_events(batch: TelemetryBatchIn, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    ids = await ingest_batch(db, [e.model_dump() for e in batch.events])
    return {"inserted": len(ids), "ids": ids[:5]}  
