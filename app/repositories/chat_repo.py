from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import Chat, ChatParticipant
from .base import BaseRepository

class ChatRepository(BaseRepository[Chat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Chat)

    async def create_with_participants(
        self, *, listing_id: str, buyer_id: str, seller_id: str
    ) -> Chat:
        chat = Chat(listing_id=listing_id)
        self.session.add(chat)
        await self.session.flush()  
        self.session.add_all([
            ChatParticipant(chat_id=chat.id, user_id=buyer_id, role="buyer"),
            ChatParticipant(chat_id=chat.id, user_id=seller_id, role="seller"),
        ])
        await self.session.flush()
        return chat

    async def get_with_participants(self, chat_id: str) -> Chat | None:
        stmt = select(Chat).where(Chat.id == chat_id).options(
            sa.orm.selectinload(Chat.participants)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()
