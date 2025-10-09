from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.price_suggestion import PriceSuggestionOut, ComputeIn
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user  # get_current_user si quieres exigir auth
from app.repositories.price_suggestion_repo import PriceSuggestionRepository
from app.services.price_suggestion import suggest_price_cents

router = APIRouter(prefix="/price-suggestions", tags=["price-suggestions"])


@router.get("/suggest", response_model=PriceSuggestionOut)
async def get_suggested_price(
    category_id: str | None = None,
    brand_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    value = await suggest_price_cents(db, category_id=category_id, brand_id=brand_id)
    if value is None:
        raise HTTPException(status_code=404, detail="No price suggestion available")
    return PriceSuggestionOut(suggested_price_cents=value, algorithm="p50")

@router.get("/{listing_id}/recent", response_model=list[PriceSuggestionOut])
async def recent_for_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    repo = PriceSuggestionRepository(db)
    rows = await repo.recent_for_listing(listing_id, limit=5)
    return [
        PriceSuggestionOut(
            id=r.id,
            listing_id=r.listing_id,
            suggested_price_cents=r.suggested_price_cents,
            algorithm=r.algorithm,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/{listing_id}/compute", response_model=PriceSuggestionOut, status_code=status.HTTP_201_CREATED)
async def compute_and_store(listing_id: str, body: ComputeIn, db: AsyncSession = Depends(get_db)):
    value = await suggest_price_cents(db, category_id=body.category_id, brand_id=body.brand_id)
    if value is None:
        raise HTTPException(status_code=404, detail="No price suggestion available")
    repo = PriceSuggestionRepository(db)
    rec = await repo.create_for_listing(listing_id=listing_id, suggested_price_cents=value, algorithm="p50")
    await db.commit()
    return PriceSuggestionOut(
        id=rec.id,
        listing_id=rec.listing_id,
        suggested_price_cents=rec.suggested_price_cents,
        algorithm=rec.algorithm,
        created_at=rec.created_at,
    )
