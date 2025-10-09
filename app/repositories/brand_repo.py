from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand import Brand
from .base import BaseRepository

class BrandRepository(BaseRepository[Brand]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Brand)

    async def get_by_slug(self, slug: str) -> Brand | None:
        stmt = select(Brand).where(Brand.slug == slug)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create(self, *, name: str, slug: str, category_id: str | None = None) -> Brand:
        brand = Brand(name=name, slug=slug, category_id=category_id)
        return await self.add(brand)

    async def list_by_category(self, category_id: str) -> List[Brand]:
        stmt = select(Brand).where(Brand.category_id == category_id).order_by(Brand.name)
        res = await self.session.execute(stmt)
        return res.scalars().all()
