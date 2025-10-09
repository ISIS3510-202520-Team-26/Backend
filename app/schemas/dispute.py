from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class DisputeCreate(BaseModel):
    order_id: str
    raised_by: str = Field(..., pattern="^(buyer|seller)$")
    reason: str | None = None

class DisputeUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|resolved|rejected)$")
    comment: str | None = None

class DisputeOut(IdOut):
    order_id: str
    raised_by: str
    reason: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None
