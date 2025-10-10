# app/services/telemetry.py  (o donde tengas ingest_batch)
from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.events_repo import EventRepository

def _normalize_event(ev: Mapping[str, Any]) -> dict:
    d = dict(ev)
    d.setdefault("properties", {})
    occ = d.get("occurred_at")
    if isinstance(occ, str):
        d["occurred_at"] = datetime.fromisoformat(occ.replace("Z", "+00:00"))
    elif occ is None:
        d["occurred_at"] = datetime.now(timezone.utc)
    return d

async def ingest_batch(db: AsyncSession, events: Iterable[Mapping[str, Any]]) -> list[str]:
    repo = EventRepository(db)
    norm = [_normalize_event(e) for e in events]
    ids = await repo.insert_batch(norm)
    await db.commit()
    return ids
