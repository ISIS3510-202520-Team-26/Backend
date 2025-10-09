from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.feature import Feature, FeatureFlag
from .base import BaseRepository

class FeatureRepository(BaseRepository[Feature]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Feature)

    async def get_flag(self, key: str) -> Feature | None:
        stmt = select(Feature).where(Feature.key == key)
        res = await self.session.execute(stmt)
        return res.scalars().first()

class FeatureFlagRepository(BaseRepository[FeatureFlag]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FeatureFlag)
