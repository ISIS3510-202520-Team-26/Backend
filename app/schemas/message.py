from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel, IdOut
from app.models.enums import MessageType

class MessageCreate(BaseModel):
    chat_id: str
    message_type: MessageType = MessageType.text
    content: str | None = Field(None, max_length=4000)

class MessageOut(IdOut):
    chat_id: str
    sender_id: str
    message_type: MessageType
    content: str | None
    created_at: datetime
