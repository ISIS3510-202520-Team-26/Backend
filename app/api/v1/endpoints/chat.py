from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.chat_repo import ChatRepository
from app.repositories.listing_repo import ListingRepository
from app.schemas.chat import ChatCreate, ChatOut
from app.models.chat import Chat

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
async def create_chat(data: ChatCreate, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    lrepo = ListingRepository(db)
    listing = await lrepo.get(data.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id == current.id:
        raise HTTPException(status_code=400, detail="Cannot open chat with yourself")

    repo = ChatRepository(db)
    chat = await repo.create_with_participants(listing_id=listing.id, buyer_id=current.id, seller_id=listing.seller_id)
    await db.commit()

    stmt = select(Chat).where(Chat.id == chat.id)
    obj = (await db.execute(stmt)).scalars().first()
    return ChatOut.model_validate(obj)

@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db), current=Depends(get_current_user)):
    repo = ChatRepository(db)
    chat = await repo.get_with_participants(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatOut.model_validate(chat)
