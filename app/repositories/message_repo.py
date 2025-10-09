from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from .base import BaseRepository

class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def send(
        self, *, chat_id: str, sender_id: str, message_type: str, content: str | None
    ) -> Message:
        msg = Message(chat_id=chat_id, sender_id=sender_id, message_type=message_type, content=content)
        return await self.add(msg)
