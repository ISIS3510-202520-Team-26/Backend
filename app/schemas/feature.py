from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import ORMModel, IdOut

class FeatureCreate(BaseModel):
    key: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=2, max_length=120)

class FeatureFlagCreate(BaseModel):
    feature_id: str
    scope: str = Field(..., pattern="^(global|user|segment)$")
    enabled: bool = True

class FeatureOut(IdOut):
    key: str
    name: str
    deployed_at: datetime | None = None

class FeatureFlagOut(IdOut):
    feature_id: str
    scope: str
    enabled: bool
    created_at: datetime

class FeatureUseIn(BaseModel):
    feature_key: str