from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import MessageType

class Message(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    chat_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("chat.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(sa.Enum(MessageType, name="message_type"), nullable=False, default=MessageType.text)
    content: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages")
