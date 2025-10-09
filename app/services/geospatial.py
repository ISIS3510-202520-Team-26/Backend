from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Tuple
from app.models.listing import Listing

async def listings_within_radius(
    db: AsyncSession, *, lat: float, lon: float, radius_km: float, limit: int = 50
) -> Sequence[Listing]:
    radius_m = radius_km * 1000.0
    dist = sa.func.ST_DistanceSphere(
        sa.func.ST_MakePoint(Listing.longitude, Listing.latitude),
        sa.func.ST_MakePoint(lon, lat),
    )
    stmt = (
        sa.select(Listing)
        .where(Listing.is_active.is_(True))
        .where(dist <= radius_m)
        .order_by(dist.asc(), Listing.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
