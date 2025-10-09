from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.device_repo import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(data: DeviceCreate, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = DeviceRepository(db)
    d = await repo.create_for_user(user_id=current.id, platform=data.platform, push_token=data.push_token, app_version=data.app_version)
    await db.commit()
    return DeviceOut.model_validate(d)

@router.get("", response_model=list[DeviceOut])
async def my_devices(db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = DeviceRepository(db)
    items = await repo.list_by_user(current.id)
    return [DeviceOut.model_validate(x) for x in items]
