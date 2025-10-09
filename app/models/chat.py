from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Chat(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    listing_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("listing.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    listing: Mapped["Listing"] = relationship(back_populates="chats")
    participants: Mapped[list["ChatParticipant"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

class ChatParticipant(Base):
    chat_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("chat.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # buyer|seller
    joined_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()
