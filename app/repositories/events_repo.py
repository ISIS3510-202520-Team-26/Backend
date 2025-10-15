from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --------- Inserción robusta ----------
    async def insert_batch(self, events: Iterable[Mapping[str, Any]]) -> list[str]:
        sql = sa.text("""
            INSERT INTO event (
                event_type, user_id, session_id, listing_id, order_id, chat_id,
                step, properties, occurred_at
            )
            VALUES (
                :event_type, :user_id, :session_id, :listing_id, :order_id, :chat_id,
                :step, :properties, :occurred_at
            )
            RETURNING id
        """).bindparams(
            sa.bindparam("properties", type_=JSONB)
        )

        def _coerce_dt(v: Any) -> datetime:
            if isinstance(v, datetime):
                return v
            if isinstance(v, str):
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            return datetime.now(timezone.utc)

        ids: list[str] = []
        for e in events:
            ev = {
                "event_type": e["event_type"],
                "user_id": e.get("user_id"),
                "session_id": e.get("session_id", "srv"),
                "listing_id": e.get("listing_id"),
                "order_id": e.get("order_id"),
                "chat_id": e.get("chat_id"),
                "step": e.get("step"),
                "properties": e.get("properties", {}),
                "occurred_at": _coerce_dt(e.get("occurred_at")),
            }
            res = await self.session.execute(sql, ev)
            ids.append(res.scalar_one())
        return ids

    # ----------------------- BQ 1.x -----------------------
    async def bq_1_1_listings_per_day_by_category(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT occurred_at::date AS day, properties->>'category_id' AS category_id, COUNT(*) AS n
            FROM event
            WHERE event_type = 'listing.created'
              AND occurred_at >= :start AND occurred_at < :end
            GROUP BY day, category_id
            ORDER BY day, category_id
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    async def bq_1_2_escrow_cancel_rate(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            WITH base AS (
              SELECT step, (properties->>'result') AS result
              FROM event
              WHERE event_type = 'escrow.step'
                AND occurred_at >= :start AND occurred_at < :end
            ),
            per_step AS (
              SELECT step,
                     COUNT(*) AS total,
                     COUNT(*) FILTER (WHERE result = 'cancelled') AS cancelled
              FROM base GROUP BY step
            )
            SELECT step, total, cancelled,
                   CASE WHEN total=0 THEN 0 ELSE ROUND(cancelled::numeric*100/total, 2) END AS pct_cancelled
            FROM per_step
            ORDER BY step
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    # ----------------------- BQ 2.x -----------------------
    async def bq_2_1_events_per_type_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT occurred_at::date AS day, event_type, COUNT(*) AS n
            FROM event
            WHERE occurred_at >= :start AND occurred_at < :end
            GROUP BY day, event_type
            ORDER BY day, event_type
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    async def bq_2_2_clicks_by_button_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT occurred_at::date AS day, properties->>'button' AS button, COUNT(*) AS n
            FROM event
            WHERE event_type = 'ui.click'
              AND occurred_at >= :start AND occurred_at < :end
            GROUP BY day, button
            ORDER BY day, button
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    async def bq_2_4_time_by_screen(self, *, start: datetime, end: datetime, max_idle_sec: int = 300):
        """
        Calcula dwell time por pantalla usando eventos `screen.view`.
        - Usa LEAD() por session_id para tomar la siguiente vista como fin del intervalo.
        - Si no hay siguiente vista, capea a `max_idle_sec` (por defecto 5 min).
        Devuelve: [(screen, total_seconds, views, avg_seconds)]
        """
        stmt = sa.text("""
            WITH v AS (
              SELECT
                session_id,
                occurred_at,
                COALESCE(NULLIF(properties->>'screen',''), '(unknown)') AS screen
              FROM event
              WHERE event_type = 'screen.view'
                AND occurred_at >= :start AND occurred_at < :end
            ),
            o AS (
              SELECT
                session_id,
                screen,
                occurred_at,
                LEAD(occurred_at) OVER (PARTITION BY session_id ORDER BY occurred_at) AS next_time
              FROM v
            ),
            d AS (
              SELECT
                screen,
                LEAST(:max_idle, GREATEST(0, COALESCE(EXTRACT(EPOCH FROM (next_time - occurred_at)), :max_idle)))::bigint AS seconds
              FROM o
            )
            SELECT
              screen,
              SUM(seconds)::bigint AS total_seconds,
              COUNT(*)::bigint AS views,
              ROUND(AVG(seconds))::bigint AS avg_seconds
            FROM d
            GROUP BY screen
            ORDER BY total_seconds DESC
        """)
        res = await self.session.execute(stmt, {
            "start": start,
            "end": end,
            "max_idle": max_idle_sec,
        })
        return res.all()

    # ----------------------- BQ 3.x -----------------------
    async def bq_3_1_dau(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT occurred_at::date AS day,
                   COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) AS dau
            FROM event
            WHERE occurred_at >= :start AND occurred_at < :end
            GROUP BY day
            ORDER BY day
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    async def bq_3_2_sessions_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT occurred_at::date AS day,
                   COUNT(DISTINCT session_id) AS sessions
            FROM event
            WHERE occurred_at >= :start AND occurred_at < :end
            GROUP BY day
            ORDER BY day
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    # ----------------------- BQ 4.x -----------------------
    async def bq_4_1_orders_by_status_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT created_at::date AS day, status, COUNT(*) AS n
            FROM "order"
            WHERE created_at >= :start AND created_at < :end
            GROUP BY day, status
            ORDER BY day, status
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    async def bq_4_2_gmv_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT created_at::date AS day,
                   COALESCE(SUM(CASE WHEN status IN ('paid','completed') THEN total_cents END), 0) AS gmv_cents,
                   COUNT(*) FILTER (WHERE status IN ('paid','completed')) AS orders_paid
            FROM "order"
            WHERE created_at >= :start AND created_at < :end
            GROUP BY day
            ORDER BY day
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()

    # ----------------------- BQ 5.x -----------------------
    async def bq_5_1_quick_view_by_category_by_day(self, *, start: datetime, end: datetime):
        stmt = sa.text("""
            SELECT e.occurred_at::date AS day,
                   l.category_id::text AS category_id,
                   COUNT(*) AS n
            FROM event e
            JOIN listing l ON l.id = e.listing_id
            WHERE e.event_type = 'feature.used'
              AND e.properties->>'feature_key' = 'quick_view'
              AND e.occurred_at >= :start AND e.occurred_at < :end
            GROUP BY day, l.category_id
            ORDER BY day, l.category_id
        """)
        res = await self.session.execute(stmt, {"start": start, "end": end})
        return res.all()
