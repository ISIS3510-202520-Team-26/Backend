from __future__ import annotations
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.device_repo import DeviceRepository

class PushService:
    """
    Stub listo para conectar con FCM/APNs.
    Por ahora 'envía' (log) a todos los dispositivos del usuario.
    """
    async def send_to_user(self, db: AsyncSession, *, user_id: str, title: str, body: str, data: Optional[dict] = None) -> int:
        repo = DeviceRepository(db)
        devices = await repo.list_by_user(user_id)
        # Aquí integrarías FCM HTTP v1 con httpx/aiohttp. Por ahora, retornamos cuántos dispositivos.
        # Ejemplo (futuro): await self._send_fcm(tokens=[d.push_token for d in devices if d.push_token], title=title, body=body, data=data)
        return len([d for d in devices if d.push_token])
