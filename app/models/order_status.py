from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class OrderStatusHistory(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(sa.String(20))
    to_status: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="status_history")
