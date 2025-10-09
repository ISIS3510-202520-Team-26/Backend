from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import OrderStatus

class Order(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    buyer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    seller_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    listing_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("listing.id"), nullable=False)
    total_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False, default="COP")
    status: Mapped[OrderStatus] = mapped_column(sa.Enum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.created)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    listing: Mapped["Listing"] = relationship(back_populates="orders")
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    escrow: Mapped["Escrow"] = relationship(back_populates="order", uselist=False)
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    dispute: Mapped["Dispute"] = relationship(back_populates="order", uselist=False)

sa.Index("ix_orders_status_created", Order.status, Order.created_at.desc())
