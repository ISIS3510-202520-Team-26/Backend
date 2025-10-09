from __future__ import annotations
from uuid import uuid4
import boto3
from botocore.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.repositories.listing_photo_repo import ListingPhotoRepository

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(signature_version="s3v4"),
)

def make_object_key(listing_id: str, filename: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "bin").lower()
    return f"listings/{listing_id}/{uuid4()}.{ext}"

def presign_put(object_key: str, content_type: str, expires_seconds: int = 900) -> str:
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key, "ContentType": content_type},
        ExpiresIn=expires_seconds,
    )

def presign_get(object_key: str, expires_seconds: int = 900) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key},
        ExpiresIn=expires_seconds,
    )

async def confirm_and_record(
    db: AsyncSession, *, listing_id: str, object_key: str, width: int | None = None, height: int | None = None
) -> str:
    """Guarda el registro en DB y devuelve una URL prefirmada de lectura para preview."""
    repo = ListingPhotoRepository(db)
    await repo.add_photo(listing_id=listing_id, storage_key=object_key, image_url=None, width=width, height=height)
    await db.commit()
    return presign_get(object_key)
