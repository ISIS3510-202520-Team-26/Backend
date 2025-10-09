from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class ReviewCreate(BaseModel):
    order_id: str
    rater_id: str | None = None
    ratee_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=2000)

class ReviewOut(IdOut):
    order_id: str
    rater_id: str
    ratee_id: str
    rating: int
    comment: str | None
    created_at: datetime
