from __future__ import annotations
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, field_validator, ConfigDict

T = TypeVar("T")

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)

class Page(ORMModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool

class Location(BaseModel):
    latitude: float = Field(..., description="WGS84 latitude")
    longitude: float = Field(..., description="WGS84 longitude")

    @field_validator("latitude")
    @classmethod
    def _lat(cls, v: float) -> float:
        if v < -90 or v > 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def _lon(cls, v: float) -> float:
        if v < -180 or v > 180:
            raise ValueError("longitude must be between -180 and 180")
        return v

class IdOut(ORMModel):
    id: str
