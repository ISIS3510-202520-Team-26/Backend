from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import ORMModel, IdOut, Location
from app.schemas.photo import ListingPhotoOut

class ListingCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=140)
    description: str | None = None
    category_id: str
    brand_id: str | None = None
    price_cents: int = Field(..., ge=0)
    currency: str = Field("COP", min_length=3, max_length=3)
    condition: str | None = Field(None, max_length=40)
    quantity: int = Field(1, ge=1)
    location: Location | None = None
    price_suggestion_used: bool = False
    quick_view_enabled: bool = True

class ListingUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=140)
    description: str | None = None
    category_id: str | None = None
    brand_id: str | None = None
    price_cents: int | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    condition: str | None = Field(None, max_length=40)
    quantity: int | None = Field(None, ge=1)
    location: Location | None = None
    price_suggestion_used: bool | None = None
    quick_view_enabled: bool | None = None
    is_active: bool | None = None

class ListingOut(IdOut):
    seller_id: str
    title: str
    description: str | None
    category_id: str
    brand_id: str | None
    price_cents: int
    currency: str
    condition: str | None
    quantity: int
    is_active: bool
    latitude: float | None
    longitude: float | None
    price_suggestion_used: bool
    quick_view_enabled: bool
    created_at: datetime
    updated_at: datetime
    photos: List[ListingPhotoOut] = []
