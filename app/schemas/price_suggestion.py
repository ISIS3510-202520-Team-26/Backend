from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class PriceSuggestionCreate(BaseModel):
    listing_id: str
    suggested_price_cents: int = Field(..., ge=0)
    algorithm: str = "p50"

class PriceSuggestionOut(IdOut):
    listing_id: str
    suggested_price_cents: int
    algorithm: str
    created_at: datetime

class SuggestQuery(BaseModel):
    category_id: str | None = None
    brand_id: str | None = None

class ComputeIn(BaseModel):
    category_id: str | None = None
    brand_id: str | None = None