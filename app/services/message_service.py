from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.message_repo import MessageRepository
from app.repositories.events_repo import EventRepository
from app.services.push_service import PushService
from app.models.enums import MessageType

async def send_message(
    db: AsyncSession,
    *,
    chat_id: str,
    sender_id: str,
    recipient_id: str,
    content: str,
    push: PushService | None = None,
) -> str:
    repo = MessageRepository(db)
    msg = await repo.send(chat_id=chat_id, sender_id=sender_id, message_type=MessageType.text.value, content=content)
    ev = EventRepository(db)
    await ev.insert_batch([{
        "event_type": "chat.message.sent",
        "session_id": "srv",
        "user_id": sender_id,
        "chat_id": chat_id,
        "properties": {"length": len(content or "")},
    }])
    if push:
        await push.send_to_user(db, user_id=recipient_id, title="Nuevo mensaje", body=content[:100])
    await db.flush()
    return msg.id
