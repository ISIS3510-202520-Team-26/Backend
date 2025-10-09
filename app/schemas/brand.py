from __future__ import annotations
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    category_id: str | None = None

class BrandOut(IdOut):
    name: str
    slug: str
    category_id: str | None = None
