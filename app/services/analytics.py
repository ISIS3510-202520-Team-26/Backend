from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.events_repo import EventRepository


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.events = EventRepository(db)

    # 1.x
    async def bq_1_1_listings_per_day_by_category(self, *, start: datetime, end: datetime):
        return await self.events.bq_1_1_listings_per_day_by_category(start=start, end=end)

    async def bq_1_2_escrow_cancel_rate(self, *, start: datetime, end: datetime):
        return await self.events.bq_1_2_escrow_cancel_rate(start=start, end=end)

    # 2.x
    async def bq_2_1_events_per_type_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_2_1_events_per_type_by_day(start=start, end=end)

    async def bq_2_2_clicks_by_button_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_2_2_clicks_by_button_by_day(start=start, end=end)

    # 3.x
    async def bq_3_1_dau(self, *, start: datetime, end: datetime):
        return await self.events.bq_3_1_dau(start=start, end=end)

    async def bq_3_2_sessions_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_3_2_sessions_by_day(start=start, end=end)

    # 4.x
    async def bq_4_1_orders_by_status_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_4_1_orders_by_status_by_day(start=start, end=end)

    async def bq_4_2_gmv_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_4_2_gmv_by_day(start=start, end=end)

    # 5.x
    async def bq_5_1_quick_view_by_category_by_day(self, *, start: datetime, end: datetime):
        return await self.events.bq_5_1_quick_view_by_category_by_day(start=start, end=end)
