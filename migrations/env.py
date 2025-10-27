from __future__ import annotations

from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import create_engine

from app.db.base import Base
from app.models.brand import Brand
from app.models.category import Category
from app.models.chat import Chat, ChatParticipant
from app.models.device import Device
from app.models.dispute import Dispute
from app.models.escrow import Escrow, EscrowEvent
from app.models.event import Event
from app.models.feature import Feature, FeatureFlag
from app.models.listing_photo import ListingPhoto
from app.models.listing import Listing
from app.models.message import Message
from app.models.order import Order
from app.models.order_status import OrderStatusHistory
from app.models.payment import Payment
from app.models.price_suggestion import PriceSuggestion
from app.models.review import Review
from app.models.user import User
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Toma primero ALEMBIC_DATABASE_URL, luego DATABASE_URL, y convierte a sync (quita +asyncpg)
raw_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
sync_url = raw_url.replace("+asyncpg", "")  # p.ej. postgresql://...

# Asegura que Alembic tenga la URL (por si algún flujo la lee de config)
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata

EXCLUDED_SCHEMAS = {"tiger", "tiger_data", "topology"}
EXCLUDED_TABLES = {
    "spatial_ref_sys", "geometry_columns", "geography_columns",
    "raster_columns", "raster_overviews"
}

def include_object(object, name, type_, reflected, compare_to):
    schema = getattr(object, "schema", None)
    if type_ == "table":
        if schema in EXCLUDED_SCHEMAS:
            return False
        if name in EXCLUDED_TABLES:
            return False
    return True

def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,  # no toca objetos de extensiones, pero permite ver schema si lo usas
        version_table_schema=None,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    engine = create_engine(sync_url, pool_pre_ping=True, future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            compare_type=True,
            version_table_schema="public", 
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
