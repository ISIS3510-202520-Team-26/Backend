from __future__ import annotations
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing import Listing

async def suggest_price_cents(
    db: AsyncSession, *, category_id: str, brand_id: str | None = None
) -> Optional[int]:

    where = [Listing.is_active.is_(True), Listing.category_id == category_id,
             Listing.created_at >= sa.text("now() - interval '90 days'")]
    if brand_id:
        where.append(Listing.brand_id == brand_id)

    stmt = sa.select(
        sa.func.percentile_disc(0.5)
          .within_group(Listing.price_cents.asc())
          .label("median")
    ).where(*where)
    res = await db.execute(stmt)
    median = res.scalar()
    return int(median) if median is not None else None
