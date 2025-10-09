from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.events_repo import EventRepository

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _ensure_dt_aware(dt: datetime | None) -> datetime:
    if dt is None:
        return _now_utc()
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _normalize_event(ev: Mapping[str, Any]) -> Dict[str, Any]:
    d: Dict[str, Any] = dict(ev)
    d.setdefault("properties", {})
    d["occurred_at"] = _ensure_dt_aware(d.get("occurred_at"))
    return d

async def ingest_batch(db: AsyncSession, events: Iterable[Mapping[str, Any]]) -> list[str]:
    repo = EventRepository(db)
    norm = [_normalize_event(e) for e in events]
    ids = await repo.insert_batch(norm)
    await db.commit()
    return ids
