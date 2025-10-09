from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class PriceSuggestion(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    listing_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    suggested_price_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    listing: Mapped["Listing"] = relationship()
