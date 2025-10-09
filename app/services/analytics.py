from __future__ import annotations
from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.events_repo import EventRepository

class AnalyticsService:
    """
    Fachada sobre EventRepository para responder BQs clave.
    Agrega métodos declarativos y deja el SQL en el repo cuando aplique.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.events = EventRepository(db)

    async def bq_1_1_listings_per_day_by_category(self, *, start: str, end: str) -> List[Tuple]:
        return await self.events.bq_1_1_listings_per_day_by_category(start=start, end=end)

    async def bq_1_2_escrow_cancel_rate(self, *, start: str, end: str) -> List[Tuple]:
        return await self.events.bq_1_2_escrow_cancel_rate(start=start, end=end)
