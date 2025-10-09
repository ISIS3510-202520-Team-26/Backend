from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import ORMModel, IdOut

class ChatCreate(BaseModel):
    listing_id: str

class ChatOut(IdOut):
    listing_id: str
    created_at: datetime

class ChatParticipantOut(ORMModel):
    chat_id: str
    user_id: str
    role: str
    joined_at: datetime

class ChatWithParticipants(IdOut):
    listing_id: str
    created_at: datetime
    participants: List[ChatParticipantOut] = []
