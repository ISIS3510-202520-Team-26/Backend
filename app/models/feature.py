from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Feature(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    key: Mapped[str] = mapped_column(sa.String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    deployed_at: Mapped[str | None] = mapped_column(sa.DateTime(timezone=True))

    flags: Mapped[list["FeatureFlag"]] = relationship(back_populates="feature", cascade="all, delete-orphan")

class FeatureFlag(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    feature_id: Mapped[str] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("feature.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(sa.String(20), nullable=False) 
    enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    feature: Mapped["Feature"] = relationship(back_populates="flags")
