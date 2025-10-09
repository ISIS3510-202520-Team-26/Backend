from __future__ import annotations
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device import Device
from .base import BaseRepository

class DeviceRepository(BaseRepository[Device]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Device)

    async def create_for_user(self, *, user_id: str, platform: str, push_token: str | None = None, app_version: str | None = None) -> Device:
        d = Device(user_id=user_id, platform=platform, push_token=push_token, app_version=app_version)
        return await self.add(d)

    async def get_by_push_token(self, push_token: str) -> Device | None:
        stmt = select(Device).where(Device.push_token == push_token)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def list_by_user(self, user_id: str) -> List[Device]:
        stmt = select(Device).where(Device.user_id == user_id).order_by(Device.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()
