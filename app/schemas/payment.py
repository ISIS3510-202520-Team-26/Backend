from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class PaymentCreate(BaseModel):
    order_id: str
    provider: str
    amount_cents: int = Field(..., ge=0)

class PaymentOut(IdOut):
    order_id: str
    provider: str
    provider_ref: str | None
    amount_cents: int
    status: str
    created_at: datetime

class PaymentCallbackIn(BaseModel):
    order_id: str
    provider_ref: str
