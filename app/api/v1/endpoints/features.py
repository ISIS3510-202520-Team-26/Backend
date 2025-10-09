from __future__ import annotations
from fastapi import APIRouter, Depends, status
from app.schemas.feature import FeatureUseIn
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.feature_service import get_feature_flags, register_feature_use

router = APIRouter(prefix="/features", tags=["features"])

@router.get("", response_model=dict[str, bool])
async def list_flags(db: AsyncSession = Depends(get_db)):
    return await get_feature_flags(db)

@router.post("/use", status_code=status.HTTP_202_ACCEPTED)
async def feature_used(
    payload: FeatureUseIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),  
):
    await register_feature_use(db, user_id=getattr(user, "id", None), feature_key=payload.feature_key)
    await db.commit()
    return {"ok": True}
