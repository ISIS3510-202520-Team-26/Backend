from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class User(Base):
    id: Mapped[str] = mapped_column(UUID(as_uuid=False),
        primary_key=True, server_default=sa.text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(320), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    campus: Mapped[str | None] = mapped_column(sa.String(120))
    created_at: Mapped[str] = mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login_at: Mapped[str | None] = mapped_column(sa.DateTime(timezone=True))

    devices: Mapped[list["Device"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    listings: Mapped[list["Listing"]] = relationship(back_populates="seller")
    messages: Mapped[list["Message"]] = relationship(back_populates="sender")

sa.Index("uq_users_email_lower", sa.text("lower(email)"), unique=True)
