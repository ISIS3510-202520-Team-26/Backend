from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.category import Category
from app.models.brand import Brand
from app.models.listing import Listing

ISO8601 = "%Y-%m-%dT%H:%M:%S.%fZ"

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

async def _max_updated_at(db: AsyncSession) -> Optional[datetime]:
    cat_max = func.max(func.coalesce(getattr(Category, "updated_at", None) or func.now(), func.now()))
    br_max  = func.max(func.coalesce(getattr(Brand, "updated_at", None) or func.now(), func.now()))
    li_max  = func.max(Listing.updated_at)
    stmt = select(func.greatest(cat_max, br_max, li_max))
    res = await db.execute(stmt)
    val = res.scalar()
    return val if isinstance(val, datetime) else None

def _etag_from_payload(payload: Dict[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(repr(payload).encode("utf-8"))
    return h.hexdigest()

async def get_catalog_delta(
    db: AsyncSession,
    *,
    since: Optional[datetime] = None,
    limit: int = 200,
) -> Tuple[Dict[str, Any], str, datetime]:
    
    data: Dict[str, Any] = {}

    cats = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    data["categories"] = [{"id": c.id, "slug": c.slug, "name": c.name} for c in cats]


    brands = (await db.execute(select(Brand).order_by(Brand.name))).scalars().all()
    data["brands"] = [{"id": b.id, "name": b.name, "slug": b.slug, "category_id": b.category_id} for b in brands]

    q = select(Listing).order_by(Listing.updated_at.desc()).limit(limit)
    if since:
        q = q.where(Listing.updated_at >= since)
    listings = (await db.execute(q)).scalars().all()
    data["listings"] = [{
        "id": l.id,
        "seller_id": l.seller_id,
        "title": l.title,
        "description": l.description,
        "category_id": l.category_id,
        "brand_id": l.brand_id,
        "price_cents": l.price_cents,
        "currency": l.currency,
        "condition": l.condition,
        "quantity": l.quantity,
        "is_active": l.is_active,
        "latitude": l.latitude,
        "longitude": l.longitude,
        "price_suggestion_used": l.price_suggestion_used,
        "quick_view_enabled": l.quick_view_enabled,
        "created_at": l.created_at.isoformat() if hasattr(l, "created_at") else None,
        "updated_at": l.updated_at.isoformat() if hasattr(l, "updated_at") else None,
    } for l in listings]

    last_modified = await _max_updated_at(db) or _utcnow()
    etag = _etag_from_payload({
        "counts": {
            "categories": len(data["categories"]),
            "brands": len(data["brands"]),
            "listings": len(data["listings"]),
        },
        "last_modified": last_modified.isoformat(),
    })
    return data, etag, last_modified

def not_modified(etag_client: Optional[str], etag_server: str) -> bool:
    return bool(etag_client) and etag_client == etag_server
