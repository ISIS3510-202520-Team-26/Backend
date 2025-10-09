from __future__ import annotations

import logging
from typing import Any, Dict

import sqlalchemy as sa
from botocore.config import Config as BotoConfig
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.cors import setup_cors
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.init_db import ensure_extensions, seed_minimal_catalog
from app.db.session import AsyncSessionLocal

# -----------------------------------------------------------------------------
# App bootstrap
# -----------------------------------------------------------------------------
setup_logging(logging.INFO)

app = FastAPI(
    title="Marketplace API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

setup_cors(app, allow_all=(settings.app_env.lower() != "prod"))

app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# -----------------------------------------------------------------------------
# Startup / Shutdown
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    log = logging.getLogger("uvicorn")
    log.info("Starting up... ensuring DB extensions and base seed.")
    async with AsyncSessionLocal() as db:
        await ensure_extensions(db)
        await seed_minimal_catalog(db)

    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        pong = await app.state.redis.ping()
        log.info(f"Redis ping: {pong}")
    except Exception as e:
        log.warning(f"Redis not ready: {e}")

    log.info("Startup completed.")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    log = logging.getLogger("uvicorn")
    log.info("Shutting down...")
    r: Redis | None = getattr(app.state, "redis", None)
    if r:
        try:
            await r.close()
        except Exception:  
            pass
    log.info("Shutdown completed.")

# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------
@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check que valida DB, Redis y acceso S3/MinIO (ligero).
    """
    status: Dict[str, Any] = {"ok": True}

    try:
        async with AsyncSessionLocal() as db:  
            await db.execute(sa.text("SELECT 1"))
        status["db"] = "ok"
    except Exception as e:
        status["ok"] = False
        status["db"] = f"error: {e}"

    try:
        r: Redis = getattr(app.state, "redis", None) or Redis.from_url(settings.redis_url, decode_responses=True)
        pong = await r.ping()
        status["redis"] = "ok" if pong else "error: no pong"
    except Exception as e:
        status["ok"] = False
        status["redis"] = f"error: {e}"


    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=BotoConfig(signature_version="s3v4", connect_timeout=2, read_timeout=2),
        )
        _ = s3.list_buckets()
        status["s3"] = "ok"
    except Exception as e:
        status["ok"] = False
        status["s3"] = f"error: {e}"

    status["env"] = settings.app_env
    status["version"] = "1.0.0"
    return status

# -----------------------------------------------------------------------------
# API v1
# -----------------------------------------------------------------------------
app.include_router(api_router, prefix="/v1")
