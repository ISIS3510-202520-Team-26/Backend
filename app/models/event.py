from __future__ import annotations
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class Event(Base):
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    event_type: Mapped[str] = mapped_column(sa.String(80), nullable=False)

    user_id:    Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("user.id"))
    session_id: Mapped[str]        = mapped_column(sa.String(64), nullable=False)

    listing_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("listing.id"))
    order_id:   Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("order.id"))
    chat_id:    Mapped[str | None] = mapped_column(UUID(as_uuid=False), sa.ForeignKey("chat.id"))

    step: Mapped[str | None] = mapped_column(sa.String(40))

    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    occurred_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

sa.Index("ix_events_type_time", Event.event_type, Event.occurred_at.desc())
sa.Index("ix_events_user_time", Event.user_id, Event.occurred_at.desc())
sa.Index("ix_events_props_gin", Event.properties, postgresql_using="gin")
