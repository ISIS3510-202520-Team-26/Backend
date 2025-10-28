from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.price_suggestion import PriceSuggestionOut, ComputeIn
from app.api.deps import get_db  # , get_current_user
from app.repositories.price_suggestion_repo import PriceSuggestionRepository
from app.services.price_suggestion import suggest_price_cents

router = APIRouter(prefix="/price-suggestions", tags=["price-suggestions"])

@router.get("/suggest", response_model=PriceSuggestionOut)
async def get_suggested_price(
    category_id: str = Query(...),
    brand_id: str | None = Query(None),
    condition: str | None = Query(None, regex="^(new|like_new|good|fair|poor)$"),
    msrp_cents: int | None = Query(None, ge=0),
    months_since_release: int | None = Query(None, ge=0),
    rounding_quantum: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    payload = await suggest_price_cents(
        db,
        category_id=category_id,
        brand_id=brand_id,
        condition=condition,
        msrp_cents=msrp_cents,
        months_since_release=months_since_release,
        rounding_quantum=rounding_quantum,
    )
    if not payload:
        raise HTTPException(status_code=404, detail="No price suggestion available")

    # Devolvemos suggested + metadatos (p25/p50/p75/n/source) para la UI
    return PriceSuggestionOut(
        suggested_price_cents=payload["suggested"],
        algorithm=payload.get("source", "local_median"),
        p25=payload.get("p25"),
        p50=payload.get("p50"),
        p75=payload.get("p75"),
        n=payload.get("n"),
        source=payload.get("source"),
    )

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
            # Si tu repo/tabla no guardan p25/p50/p75/n/source, estos vendrán como None (OK)
        )
        for r in rows
    ]

@router.post("/{listing_id}/compute", response_model=PriceSuggestionOut, status_code=status.HTTP_201_CREATED)
async def compute_and_store(
    listing_id: str,
    body: ComputeIn,
    db: AsyncSession = Depends(get_db),
):
    payload = await suggest_price_cents(
        db,
        category_id=body.category_id,
        brand_id=body.brand_id,
        condition=body.condition,
        msrp_cents=body.msrp_cents,
        months_since_release=body.months_since_release,
        rounding_quantum=body.rounding_quantum or 100,
    )
    if not payload:
        raise HTTPException(status_code=404, detail="No price suggestion available")

    repo = PriceSuggestionRepository(db)
    rec = await repo.create_for_listing(
        listing_id=listing_id,
        suggested_price_cents=payload["suggested"],
        algorithm=payload.get("source", "local_median"),
    )
    await db.commit()

    return PriceSuggestionOut(
        id=rec.id,
        listing_id=rec.listing_id,
        suggested_price_cents=rec.suggested_price_cents,
        algorithm=rec.algorithm,
        created_at=rec.created_at,
        p25=payload.get("p25"),
        p50=payload.get("p50"),
        p75=payload.get("p75"),
        n=payload.get("n"),
        source=payload.get("source"),
    )
