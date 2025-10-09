from __future__ import annotations
from io import BytesIO
from PIL import Image
import boto3
from botocore.config import Config
from app.core.config import settings
from app.workers.celery_app import celery_app
from ._session import session_scope
import asyncio

from app.repositories.listing_photo_repo import ListingPhotoRepository

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(signature_version="s3v4"),
)

def _make_thumb_bytes(data: bytes, size=(300, 300)) -> tuple[bytes, tuple[int, int]]:
    with Image.open(BytesIO(data)) as im:
        im = im.convert("RGB")
        im.thumbnail(size)
        w, h = im.size
        out = BytesIO()
        im.save(out, format="JPEG", quality=80)
        out.seek(0)
        return out.read(), (w, h)

def _thumb_key(object_key: str, size: int) -> str:
    parts = object_key.split("/", 2)
    if len(parts) < 2:
        return f"thumbs/{size}/{object_key.rsplit('.',1)[0]}.jpg"
    base_prefix = "/".join(parts[:2])
    fname = object_key.split("/")[-1].rsplit(".", 1)[0] + ".jpg"
    return f"{base_prefix}/thumbs/{size}/{fname}"

@celery_app.task(name="jobs.thumbnails.generate", max_retries=3, default_retry_delay=5)
def generate_thumbnail_task(object_key: str, sizes: list[int] = [300, 800]) -> dict:
    """
    Genera thumbnails en los tamaños indicados y actualiza dimensiones en ListingPhoto.
    Idempotente: si la miniatura ya existe, la sobreescribe (mismo key).
    """
    try:
        obj = _s3.get_object(Bucket=settings.s3_bucket, Key=object_key)
        body = obj["Body"].read()
        results: dict[str, tuple[int, int]] = {}
        for s in sizes:
            thumb, wh = _make_thumb_bytes(body, size=(s, s))
            key = _thumb_key(object_key, s)
            _s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=thumb, ContentType="image/jpeg")
            results[key] = wh

        async def _update():
            async with session_scope() as db:
                repo = ListingPhotoRepository(db)
                # No hay método por storage_key, así que usamos list con filtro manual
                from sqlalchemy import select
                from app.models.listing_photo import ListingPhoto
                res = await db.execute(select(ListingPhoto).where(ListingPhoto.storage_key == object_key))
                photo = res.scalars().first()
                if photo:
                    # Lee tamaño original también
                    with Image.open(BytesIO(body)) as im:
                        photo.width, photo.height = im.size
                    await db.flush()

        asyncio.run(_update())

        return {"ok": True, "generated": list(results.keys())}
    except Exception as exc:
        raise generate_thumbnail_task.retry(exc=exc)
