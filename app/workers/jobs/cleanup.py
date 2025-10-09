from __future__ import annotations
import asyncio
import boto3
from botocore.config import Config
from app.core.config import settings
from app.workers.celery_app import celery_app
from ._session import session_scope
from sqlalchemy import select
from app.models.listing_photo import ListingPhoto

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(signature_version="s3v4"),
)

def _list_all_keys(prefix: str = "listings/") -> set[str]:
    keys = set()
    token = None
    while True:
        kwargs = {"Bucket": settings.s3_bucket, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        resp = _s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.add(obj["Key"])
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return keys

@celery_app.task(name="jobs.cleanup.cleanup_orphan_objects")
def cleanup_orphan_objects(prefix: str = "listings/") -> dict:
    """
    Elimina objetos en S3 bajo 'prefix' que no estén en la tabla listingphoto.storage_key (ni en thumbs/).
    """
    async def _run():
        async with session_scope() as db:
            db_keys = set()
            res = await db.execute(select(ListingPhoto.storage_key))
            for (k,) in res.all():
                db_keys.add(k)

            s3_keys = _list_all_keys(prefix=prefix)
            
            keep = {k for k in s3_keys if "/thumbs/" in k}
            candidates = s3_keys - db_keys - keep

            deleted = []
            if candidates:
                objs = [{"Key": k} for k in candidates]
                for i in range(0, len(objs), 1000):
                    chunk = objs[i:i+1000]
                    _ = _s3.delete_objects(Bucket=settings.s3_bucket, Delete={"Objects": chunk, "Quiet": True})
                    deleted.extend([o["Key"] for o in chunk])
            return {"deleted": len(deleted)}
    return asyncio.run(_run())
