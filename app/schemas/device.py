from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import ORMModel, IdOut


class DeviceCreate(BaseModel):
    platform: str 
    push_token: str | None = None
    app_version: str | None = None

class DeviceOut(IdOut):
    user_id: str
    platform: str
    push_token: str | None
    app_version: str | None
    created_at: datetime