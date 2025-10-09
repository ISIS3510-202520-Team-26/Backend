from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import EscrowStatus

class Escrow(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    status: Mapped[EscrowStatus] = mapped_column(sa.Enum(EscrowStatus, name="escrow_status"), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="escrow")
    events: Mapped[list["EscrowEvent"]] = relationship(back_populates="escrow", cascade="all, delete-orphan")

class EscrowEvent(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    escrow_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("escrow.id", ondelete="CASCADE"), nullable=False)
    step: Mapped[str] = mapped_column(sa.String(40), nullable=False)     
    result: Mapped[str | None] = mapped_column(sa.String(20)) 
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    escrow: Mapped["Escrow"] = relationship(back_populates="events")
