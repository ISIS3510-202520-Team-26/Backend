from __future__ import annotations

import logging
from typing import Any, Dict

import sqlalchemy as sa
from botocore.config import Config as BotoConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# CORS mejorado para producción con IP pública
# Si APP_ENV != prod, permite todos los orígenes
if settings.app_env.lower() != "prod":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # En producción, usar la configuración existente
    setup_cors(app, allow_all=False)

app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# -----------------------------------------------------------------------------
# Startup / Shutdown
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    log = logging.getLogger("uvicorn")
    log.info("=" * 60)
    log.info(f"🚀 Starting Marketplace API v1.0.0")
    log.info(f"📍 Environment: {settings.app_env}")
    log.info(f"🗄️  Database: {settings.database_url.split('@')[-1]}")  # Sin password
    log.info(f"🔴 Redis: {settings.redis_url}")
    log.info(f"📦 S3 Endpoint (internal): {settings.s3_endpoint}")
    log.info(f"🌐 S3 Public Endpoint: {settings.s3_public_endpoint}")
    log.info(f"🪣 S3 Bucket: {settings.s3_bucket}")
    log.info("=" * 60)
    
    log.info("Ensuring DB extensions and seeding minimal catalog...")
    async with AsyncSessionLocal() as db:
        await ensure_extensions(db)
        await seed_minimal_catalog(db)
    log.info("✅ Database initialized")

    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        pong = await app.state.redis.ping()
        log.info(f"✅ Redis connected: {pong}")
    except Exception as e:
        log.warning(f"⚠️  Redis not ready: {e}")

    log.info("🎉 Startup completed successfully!")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    log = logging.getLogger("uvicorn")
    log.info("🛑 Shutting down...")
    r: Redis | None = getattr(app.state, "redis", None)
    if r:
        try:
            await r.close()
            log.info("✅ Redis connection closed")
        except Exception as e:
            log.warning(f"⚠️  Error closing Redis: {e}")
    log.info("👋 Shutdown completed.")

# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------
@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check que valida DB, Redis y acceso S3/MinIO (ligero).
    """
    status: Dict[str, Any] = {"ok": True}

    # Database check
    try:
        async with AsyncSessionLocal() as db:  
            await db.execute(sa.text("SELECT 1"))
        status["db"] = "ok"
    except Exception as e:
        status["ok"] = False
        status["db"] = f"error: {e}"

    # Redis check
    try:
        r: Redis = getattr(app.state, "redis", None) or Redis.from_url(settings.redis_url, decode_responses=True)
        pong = await r.ping()
        status["redis"] = "ok" if pong else "error: no pong"
    except Exception as e:
        status["ok"] = False
        status["redis"] = f"error: {e}"

    # S3/MinIO check
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

    # Additional info
    status["env"] = settings.app_env
    status["version"] = "1.0.0"
    status["s3_public_endpoint"] = settings.s3_public_endpoint
    
    return status

# -----------------------------------------------------------------------------
# Root endpoint
# -----------------------------------------------------------------------------
@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint con información básica de la API.
    """
    return {
        "message": "🛒 Marketplace API v1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/v1",
        "environment": settings.app_env,
    }

# -----------------------------------------------------------------------------
# API v1
# -----------------------------------------------------------------------------
app.include_router(api_router, prefix="/v1")
