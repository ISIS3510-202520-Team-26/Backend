from __future__ import annotations
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

log = logging.getLogger(__name__)

# (opcional) sigue dejando el seed aquí
SEED_CATEGORIES_SQL = """
INSERT INTO category (id, slug, name) VALUES
  (gen_random_uuid(), 'laptops', 'Laptops'),
  (gen_random_uuid(), 'phones', 'Phones'),
  (gen_random_uuid(), 'accessories', 'Accessories'),
  (gen_random_uuid(), 'textbooks', 'Textbooks'),
  (gen_random_uuid(), 'services', 'Services')
ON CONFLICT DO NOTHING;
"""

async def ensure_extensions(db: AsyncSession) -> None:
    """
    Ejecuta cada CREATE EXTENSION en su propia llamada para evitar el error:
    'cannot insert multiple commands into a prepared statement'
    """
    stmts = [
        'CREATE EXTENSION IF NOT EXISTS postgis',
        'CREATE EXTENSION IF NOT EXISTS "pgcrypto"',
        'CREATE EXTENSION IF NOT EXISTS "citext"',
    ]
    for sql in stmts:
        await db.execute(text(sql))
    await db.commit()
    log.info("DB extensions ensured (postgis, pgcrypto, citext).")

async def seed_minimal_catalog(db: AsyncSession) -> None:
    await db.execute(text(SEED_CATEGORIES_SQL))
    await db.commit()
    log.info("Seeded base categories.")
