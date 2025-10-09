from __future__ import annotations
from datetime import datetime
from pydantic import UUID4, BaseModel, ConfigDict, Field, constr
from app.models.enums import OrderStatus

class OrderCreate(BaseModel):
    listing_id: UUID4
    quantity: int = Field(1, ge=1)
    total_cents: int | None = None
    currency: constr(min_length=3, max_length=3) | None = None
    buyer_id: UUID4 | None = None
    model_config = ConfigDict(extra="ignore")

class OrderUpdateStatus(BaseModel):
    to_status: OrderStatus
    reason: str | None = None

class OrderOut(BaseModel):
    id: UUID4
    buyer_id: UUID4
    seller_id: UUID4
    listing_id: UUID4
    total_cents: int
    currency: constr(min_length=3, max_length=3)
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
