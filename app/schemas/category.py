from __future__ import annotations
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut

class CategoryCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=60)
    name: str = Field(..., min_length=2, max_length=80)

class CategoryOut(IdOut):
    slug: str
    name: str

