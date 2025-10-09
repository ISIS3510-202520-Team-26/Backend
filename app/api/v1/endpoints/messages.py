from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.message import MessageCreate, MessageOut
from app.models.chat import ChatParticipant
from app.repositories.message_repo import MessageRepository
from app.services.push_service import PushService

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user)
):
    res = await db.execute(select(ChatParticipant).where(ChatParticipant.chat_id == data.chat_id))
    parts = res.scalars().all()
    if not parts or current.id not in {p.user_id for p in parts}:
        raise HTTPException(status_code=403, detail="Not in chat")
    target = next((p.user_id for p in parts if p.user_id != current.id), None)
    if not target:
        raise HTTPException(status_code=400, detail="No recipient found")

    repo = MessageRepository(db)
    msg = await repo.send(chat_id=data.chat_id, sender_id=current.id, message_type=data.message_type, content=data.content)
    push = PushService()
    await push.send_to_user(db, user_id=target, title="Nuevo mensaje", body=(data.content or "")[:100])
    await db.commit()
    return MessageOut.model_validate(msg)
