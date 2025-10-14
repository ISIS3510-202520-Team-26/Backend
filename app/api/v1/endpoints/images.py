from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.photo import PresignIn, PresignOut, ConfirmIn, ConfirmOut
from app.services.image_service import make_object_key, presign_put, confirm_and_record, presign_get

# ⬇️ Celery task (worker)
from app.workers.jobs.thumbnails import generate_thumbnail_task

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/presign", response_model=PresignOut, status_code=status.HTTP_201_CREATED)
async def presign_image(data: PresignIn, current=Depends(get_current_user)):
    key = make_object_key(data.listing_id, data.filename)
    try:
        url = presign_put(key, data.content_type)
        return PresignOut(upload_url=url, object_key=key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error presign: {e}")


def _background_thumbnail(object_key: str) -> None:
    # Fallback para cuando Celery no esté disponible (demo de concurrencia simple).
    import time, logging
    logging.getLogger("uvicorn").info(f"[bg] Generando thumbnail para {object_key}...")
    time.sleep(0.5)
    logging.getLogger("uvicorn").info(f"[bg] Thumbnail OK {object_key}")


@router.post("/confirm", response_model=ConfirmOut)
async def confirm_image(
    data: ConfirmIn,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current=Depends(get_current_user),
):
    try:
        # 1) registrar la imagen en DB y devolver preview
        preview = await confirm_and_record(db, listing_id=data.listing_id, object_key=data.object_key)

        # 2) disparar thumbnails con Celery (no bloquea la respuesta)
        try:
            # tamaños más comunes; ajusta a gusto
            generate_thumbnail_task.delay(object_key=data.object_key, sizes=[300, 800])
        except Exception:
            # fallback a BackgroundTasks si por algo Celery no está accesible
            bg.add_task(_background_thumbnail, data.object_key)

        return ConfirmOut(preview_url=preview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirm: {e}")



@router.get("/preview", response_model=ConfirmOut)
async def preview_image(object_key: str, current=Depends(get_current_user)):
    try:
        url = presign_get(object_key)
        return ConfirmOut(preview_url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preview: {e}")