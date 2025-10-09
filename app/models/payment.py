from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Payment(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(sa.String(120))
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False)  
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="payments")
