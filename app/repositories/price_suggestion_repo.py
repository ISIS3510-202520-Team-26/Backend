from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.price_suggestion import PriceSuggestion
from .base import BaseRepository

class PriceSuggestionRepository(BaseRepository[PriceSuggestion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PriceSuggestion)

    async def create_for_listing(self, *, listing_id: str, suggested_price_cents: int, algorithm: str = "p50") -> PriceSuggestion:
        ps = PriceSuggestion(listing_id=listing_id, suggested_price_cents=suggested_price_cents, algorithm=algorithm)
        return await self.add(ps)

    async def recent_for_listing(self, listing_id: str, limit: int = 5) -> List[PriceSuggestion]:
        stmt = select(PriceSuggestion).where(PriceSuggestion.listing_id == listing_id).order_by(PriceSuggestion.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()
