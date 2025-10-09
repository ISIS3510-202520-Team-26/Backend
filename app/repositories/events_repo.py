from __future__ import annotations
from typing import Any, Dict, Iterable, List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_batch(self, items: Iterable[Dict[str, Any]]) -> List[str]:
        # items: dicts con claves acordes al modelo (incluye occurred_at: datetime aware)
        stmt = sa.insert(Event).returning(Event.id)
        res = await self.session.execute(stmt, list(items))
        return [row[0] for row in res.all()]

    async def bq_1_1_listings_per_day_by_category(self, *, start, end) -> List[Dict[str, Any]]:
        # start/end son datetime (aware)
        stmt = sa.text("""
            SELECT occurred_at::date AS day,
                   properties->>'category_id' AS category_id,
                   COUNT(*) AS n
            FROM event
            WHERE event_type = 'listing.created'
              AND occurred_at >= :start AND occurred_at < :end
            GROUP BY day, category_id
            ORDER BY day, category_id
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return [dict(r) for r in res.mappings().all()]

    async def bq_1_2_escrow_cancel_rate(self, *, start, end) -> List[Dict[str, Any]]:
        # Usamos la columna step y tomamos result desde properties (no existe columna 'result')
        stmt = sa.text("""
            WITH base AS (
              SELECT
                step AS step,
                properties->>'result' AS result
              FROM event
              WHERE event_type = 'escrow.step'
                AND occurred_at >= :start AND occurred_at < :end
            ),
            per_step AS (
              SELECT step,
                     COUNT(*) AS total,
                     COUNT(*) FILTER (WHERE result = 'cancelled') AS cancelled
              FROM base
              GROUP BY step
            )
            SELECT step, total, cancelled,
                   CASE WHEN total = 0 THEN 0
                        ELSE ROUND(cancelled::numeric * 100 / total, 2)
                   END AS pct_cancelled
            FROM per_step
            ORDER BY step
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return [dict(r) for r in res.mappings().all()]
