from __future__ import annotations
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.feature import Feature, FeatureFlag
from app.repositories.feature_repo import FeatureRepository, FeatureFlagRepository
from app.repositories.events_repo import EventRepository

async def get_feature_flags(db: AsyncSession) -> Dict[str, bool]:
    fr = FeatureRepository(db)
    flags = (await db.execute(select(Feature))).scalars().all()
    out: Dict[str, bool] = {}
    for f in flags:
        q = select(FeatureFlag).where(FeatureFlag.feature_id == f.id, FeatureFlag.scope == "global", FeatureFlag.enabled.is_(True))
        enabled = (await db.execute(q)).scalars().first() is not None
        out[f.key] = enabled
    return out

async def register_feature_use(db: AsyncSession, *, user_id: str | None, feature_key: str) -> None:
    ev = EventRepository(db)
    await ev.insert_batch([{
        "event_type": "feature.used",
        "session_id": "srv",
        "user_id": user_id,
        "properties": {"feature_key": feature_key},
    }])
    await db.flush()
