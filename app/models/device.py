from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Device(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(sa.String(40))  # android|ios
    push_token: Mapped[str | None] = mapped_column(sa.Text)
    app_version: Mapped[str | None] = mapped_column(sa.String(40))
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="devices")
