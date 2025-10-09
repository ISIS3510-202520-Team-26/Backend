from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user  # opcional exigir auth
from app.services.contact_service import match_contacts_by_email_hash
from app.schemas.user import ContactMatchOut, ContactsMatchIn

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/match", response_model=list[ContactMatchOut])
async def match_contacts(
    body: ContactsMatchIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),  # si no quieres exigir auth, quítalo
):
    matches = await match_contacts_by_email_hash(db, email_hashes=list(body.email_hashes), limit=500)
    # mapea a salida
    return [ContactMatchOut(user_id=m["user_id"], name=m["name"], email=m["email"]) for m in matches]
