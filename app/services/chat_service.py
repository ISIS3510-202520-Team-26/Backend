from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.chat_repo import ChatRepository
from app.repositories.events_repo import EventRepository

async def create_chat_for_listing(db: AsyncSession, *, listing_id: str, buyer_id: str, seller_id: str) -> str:
    repo = ChatRepository(db)
    chat = await repo.create_with_participants(listing_id=listing_id, buyer_id=buyer_id, seller_id=seller_id)
    ev = EventRepository(db)
    await ev.insert_batch([{
        "event_type": "chat.initiated",
        "session_id": "srv",
        "user_id": buyer_id,
        "listing_id": listing_id,
        "properties": {},
    }])
    await db.flush()
    return chat.id
