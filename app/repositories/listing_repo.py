from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing import Listing
from .base import BaseRepository

class ListingRepository(BaseRepository[Listing]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Listing)

    async def create(
        self,
        *,
        seller_id: str,
        title: str,
        description: str | None,
        category_id: str,
        brand_id: str | None,
        price_cents: int,
        currency: str = "COP",
        condition: str | None = None,
        quantity: int = 1,
        latitude: float | None = None,
        longitude: float | None = None,
        price_suggestion_used: bool = False,
        quick_view_enabled: bool = True,
    ) -> Listing:
        obj = Listing(
            seller_id=seller_id,
            title=title,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            price_cents=price_cents,
            currency=currency,
            condition=condition,
            quantity=quantity,
            latitude=latitude,
            longitude=longitude,
            price_suggestion_used=price_suggestion_used,
            quick_view_enabled=quick_view_enabled,
        )
        return await self.add(obj)

    async def update(
        self,
        listing: Listing,
        **fields,
    ) -> Listing:
        for k, v in fields.items():
            if hasattr(listing, k) and v is not None:
                setattr(listing, k, v)
        await self.session.flush()
        return listing

    async def search(
        self,
        *,
        q: str | None = None,
        category_id: str | None = None,
        brand_id: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        near_lat: float | None = None,
        near_lon: float | None = None,
        radius_km: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Listing], int]:
        where = [Listing.is_active.is_(True)]
        if category_id:
            where.append(Listing.category_id == category_id)
        if brand_id:
            where.append(Listing.brand_id == brand_id)
        if min_price is not None:
            where.append(Listing.price_cents >= min_price)
        if max_price is not None:
            where.append(Listing.price_cents <= max_price)
        if q:
            like = f"%{q.strip()}%"
            where.append(or_(Listing.title.ilike(like), Listing.description.ilike(like)))

        stmt = select(Listing)
        if where:
            for cond in where:
                stmt = stmt.where(cond)

        if near_lat is not None and near_lon is not None and radius_km:
            radius_m = radius_km * 1000.0
            dist_expr = sa.func.ST_DistanceSphere(
                sa.func.ST_MakePoint(Listing.longitude, Listing.latitude),
                sa.func.ST_MakePoint(near_lon, near_lat),
            )
            stmt = stmt.where(dist_expr <= radius_m).order_by(dist_expr.asc(), Listing.created_at.desc())
        else:
            stmt = stmt.order_by(Listing.created_at.desc())

        subq = stmt.subquery()
        total_q = select(func.count()).select_from(subq)
        total = int((await self.session.execute(total_q)).scalar_one())

        stmt = stmt.limit(page_size).offset((page - 1) * page_size)
        res = await self.session.execute(stmt)
        items = res.scalars().all()
        return items, total
