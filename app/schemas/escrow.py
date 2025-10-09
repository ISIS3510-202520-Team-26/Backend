from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import ORMModel, IdOut
from app.models.enums import EscrowStatus

class EscrowCreate(BaseModel):
    order_id: str
    provider: str

class EscrowAction(BaseModel):
    action: str  
class EscrowEventOut(IdOut):
    escrow_id: str
    step: str
    result: str | None
    created_at: datetime

class EscrowOut(IdOut):
    order_id: str
    provider: str
    status: EscrowStatus
    created_at: datetime
    updated_at: datetime

class EscrowStepIn(BaseModel):
    escrow_id: str = Field(..., description="ID de escrow")
    step: str      = Field(..., description="listing_viewed | chat_initiated | payment_made | ...")
    result: str    = Field(..., description="success | cancelled")
