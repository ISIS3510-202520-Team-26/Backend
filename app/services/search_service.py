from __future__ import annotations
import time
from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.listing_repo import ListingRepository
from app.repositories.events_repo import EventRepository

async def search_with_telemetry(
    db: AsyncSession,
    *,
    user_id: str | None,
    session_id: str,
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
) -> Tuple[list, int]:
    """Busca y registra telemetría: search.performed + search.filter.used (para BQ 2.2 y 5.1)."""
    repo = ListingRepository(db)
    t0 = time.monotonic()
    items, total = await repo.search(
        q=q, category_id=category_id, brand_id=brand_id,
        min_price=min_price, max_price=max_price,
        near_lat=near_lat, near_lon=near_lon, radius_km=radius_km,
        page=page, page_size=page_size,
    )
    duration_ms = int((time.monotonic() - t0) * 1000)

    ev_repo = EventRepository(db)
    events: List[Dict[str, Any]] = [{
        "event_type": "search.performed",
        "user_id": user_id, "session_id": session_id,
        "properties": {"q": q or "", "duration_ms": duration_ms, "page": page, "page_size": page_size, "total": total},
    }]

    if category_id: events.append({"event_type": "search.filter.used","user_id": user_id,"session_id": session_id,
                                   "properties": {"filter_type":"category","value":category_id}})
    if brand_id:    events.append({"event_type": "search.filter.used","user_id": user_id,"session_id": session_id,
                                   "properties": {"filter_type":"brand","value":brand_id}})
    if min_price is not None or max_price is not None:
        events.append({"event_type":"search.filter.used","user_id":user_id,"session_id":session_id,
                       "properties":{"filter_type":"price","min":min_price,"max":max_price}})
    if near_lat is not None and near_lon is not None and radius_km is not None:
        events.append({"event_type":"search.filter.used","user_id":user_id,"session_id":session_id,
                       "properties":{"filter_type":"availability","near":[near_lat,near_lon],"radius_km":radius_km}})

    await ev_repo.insert_batch(events)
    await db.commit()
    return items, total
