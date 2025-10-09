from __future__ import annotations
from typing import List
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.listing_repo import ListingRepository
from app.repositories.events_repo import EventRepository
from app.schemas.listing import ListingCreate, ListingUpdate, ListingOut
from app.schemas.common import Page
from app.services.search_service import search_with_telemetry

router = APIRouter(prefix="/listings", tags=["listings"])

@router.post("", response_model=ListingOut, status_code=201)
async def create_listing(
    data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    repo = ListingRepository(db)
    lat = data.location.latitude if data.location else None
    lon = data.location.longitude if data.location else None

    obj = await repo.create(
        seller_id=current.id,
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        brand_id=data.brand_id,
        price_cents=data.price_cents,
        currency=data.currency,
        condition=data.condition,
        quantity=data.quantity,
        latitude=lat,
        longitude=lon,
        price_suggestion_used=data.price_suggestion_used,
        quick_view_enabled=data.quick_view_enabled,
    )
    ev = EventRepository(db)
    await ev.insert_batch([{
        "event_type":"listing.created",
        "user_id": current.id,
        "session_id": "srv",
        "listing_id": obj.id,
        "properties": {"category_id": obj.category_id, "brand_id": obj.brand_id},
    }])
    await db.commit()

    stmt = sa.select(type(obj)).where(type(obj).id == obj.id).options(selectinload(type(obj).photos))
    out = (await db.execute(stmt)).scalars().first()
    return ListingOut.model_validate(out)

@router.get("", response_model=Page[ListingOut])
async def list_listings(
    q: str | None = None,
    category_id: str | None = None,
    brand_id: str | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    near_lat: float | None = None,
    near_lon: float | None = None,
    radius_km: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    items, total = await search_with_telemetry(
        db, user_id=current.id, session_id="srv",
        q=q, category_id=category_id, brand_id=brand_id,
        min_price=min_price, max_price=max_price,
        near_lat=near_lat, near_lon=near_lon, radius_km=radius_km,
        page=page, page_size=page_size,
    )
    ids = [i.id for i in items]
    if ids:
        stmt = sa.select(type(items[0])).where(type(items[0]).id.in_(ids)).options(selectinload(type(items[0]).photos))
        items = (await db.execute(stmt)).scalars().all()

    return Page[ListingOut](
        items=[ListingOut.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size, has_next=(page*page_size < total)
    )

@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    from app.models.listing import Listing
    stmt = sa.select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    obj = (await db.execute(stmt)).scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingOut.model_validate(obj)

@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: str, data: ListingUpdate, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)
):
    repo = ListingRepository(db)
    obj = await repo.get(listing_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Listing not found")

    fields = data.model_dump(exclude_unset=True)
    loc = fields.pop("location", None)
    if loc:
        fields["latitude"] = loc["latitude"]
        fields["longitude"] = loc["longitude"]

    obj = await repo.update(obj, **fields)
    await db.commit()
    from app.models.listing import Listing
    stmt = sa.select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    obj = (await db.execute(stmt)).scalars().first()
    return ListingOut.model_validate(obj)

@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = ListingRepository(db)
    affected = await repo.delete(listing_id)
    await db.commit()
    if not affected:
        raise HTTPException(status_code=404, detail="Listing not found")
