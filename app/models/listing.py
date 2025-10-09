from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Listing(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    seller_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(sa.String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text)
    category_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("category.id"), nullable=False)
    brand_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("brand.id"))
    price_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False, default="COP")
    condition: Mapped[str | None] = mapped_column(sa.String(40))
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)

    latitude: Mapped[float | None] = mapped_column(sa.Float)
    longitude: Mapped[float | None] = mapped_column(sa.Float)

    price_suggestion_used: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    quick_view_enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)

    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    seller: Mapped["User"] = relationship(back_populates="listings")
    category: Mapped["Category"] = relationship(back_populates="listings")
    brand: Mapped["Brand"] = relationship(back_populates="listings")
    photos: Mapped[list["ListingPhoto"]] = relationship(back_populates="listing", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship(back_populates="listing")
    orders: Mapped[list["Order"]] = relationship(back_populates="listing")

sa.Index("ix_listing_cat_created", Listing.category_id, Listing.created_at.desc())
sa.Index("ix_listing_geo", Listing.latitude, Listing.longitude)
