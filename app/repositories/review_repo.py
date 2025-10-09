from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review import Review
from .base import BaseRepository

class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Review)

    async def create(self, *, order_id: str, rater_id: str, ratee_id: str, rating: int, comment: str | None = None) -> Review:
        rev = Review(order_id=order_id, rater_id=rater_id, ratee_id=ratee_id, rating=rating, comment=comment)
        return await self.add(rev)

    async def get_by_order(self, order_id: str) -> Review | None:
        stmt = select(Review).where(Review.order_id == order_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_for_user(self, user_id: str, limit: int = 50) -> List[Review]:
        stmt = select(Review).where(Review.ratee_id == user_id).order_by(Review.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()
