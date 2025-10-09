from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.schemas.common import IdOut

class TelemetryEventIn(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=80)
    session_id: str = Field(..., min_length=6, max_length=64)
    user_id: str | None = None
    listing_id: str | None = None
    order_id: str | None = None
    chat_id: str | None = None
    step: str | None = Field(None, max_length=40)
    properties: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None 

class TelemetryBatchIn(BaseModel):
    events: List[TelemetryEventIn]

class TelemetryEventOut(IdOut):
    event_type: str
    session_id: str
    user_id: str | None = None
    listing_id: str | None = None
    order_id: str | None = None
    chat_id: str | None = None
    step: str | None = None
    properties: Dict[str, Any]
    occurred_at: datetime
