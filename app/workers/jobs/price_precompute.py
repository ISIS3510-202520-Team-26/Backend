from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from app.workers.celery_app import celery_app
from ._session import session_scope
from app.repositories.listing_repo import ListingRepository
from app.repositories.price_suggestion_repo import PriceSuggestionRepository
from app.services.price_suggestion import suggest_price_cents

@celery_app.task(name="jobs.price_precompute.precompute_recent_prices", max_retries=2, default_retry_delay=10)
def precompute_recent_prices() -> dict:
    """
    Recorre los listings recientes y genera una sugerencia de precio (mediana 90 días).
    """
    async def _run():
        async with session_scope() as db:
            repo = ListingRepository(db)
            items, _ = await repo.search(page=1, page_size=200)
            ps_repo = PriceSuggestionRepository(db)
            n = 0
            for l in items:
                suggested = await suggest_price_cents(db, category_id=l.category_id, brand_id=l.brand_id)
                if suggested is not None:
                    await ps_repo.create_for_listing(listing_id=l.id, suggested_price_cents=suggested, algorithm="p50")
                    n += 1
            return {"suggested_for": n}
    return asyncio.run(_run())
