from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Category(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    slug: Mapped[str] = mapped_column(sa.String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(80), nullable=False)

    brands: Mapped[list["Brand"]] = relationship(back_populates="category")
    listings: Mapped[list["Listing"]] = relationship(back_populates="category")
