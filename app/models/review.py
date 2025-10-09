from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Review(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False, unique=True)
    rater_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    ratee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    rating: Mapped[int] = mapped_column(sa.Integer, nullable=False)  # 1..5
    comment: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship()
    rater: Mapped["User"] = relationship(foreign_keys=[rater_id])
    ratee: Mapped["User"] = relationship(foreign_keys=[ratee_id])
