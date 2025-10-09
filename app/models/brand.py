from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Brand(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True, index=True)
    category_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("category.id"))

    category: Mapped["Category"] = relationship(back_populates="brands")
    listings: Mapped[list["Listing"]] = relationship(back_populates="brand")
