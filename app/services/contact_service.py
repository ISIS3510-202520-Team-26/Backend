from __future__ import annotations
import hashlib
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User

def sha256_lower(v: str) -> str:
    return hashlib.sha256(v.strip().lower().encode("utf-8")).hexdigest()

async def match_contacts_by_email_hash(
    db: AsyncSession,
    *,
    email_hashes: List[str],
    limit: int = 200,
) -> List[Dict]:
    """
    Empareja contactos usando SHA-256 del email en minúsculas.
    No requiere nuevos modelos: calcula hash del email de User on-the-fly.
    WARNING: Para producción, conviene una columna persistida con índice.
    """
    email_hashes_set = set(h.lower() for h in email_hashes)
    users = (await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))).scalars().all()
    matches: List[Dict] = []
    for u in users:
        h = sha256_lower(u.email)
        if h in email_hashes_set:
            matches.append({"user_id": u.id, "name": u.name, "email": u.email})
    return matches
