from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from .base import BaseRepository

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Category)

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create(self, *, slug: str, name: str) -> Category:
        cat = Category(slug=slug, name=name)
        return await self.add(cat)

    async def list_all(self) -> List[Category]:
        return await self.list()
