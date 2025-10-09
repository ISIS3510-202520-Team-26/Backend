from __future__ import annotations
import os
from celery import Celery
from datetime import timedelta
from app.core.config import settings

BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.redis_url)      
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", settings.redis_url)

celery_app = Celery("marketplace", broker=BROKER_URL, backend=RESULT_BACKEND)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "jobs.thumbnails.*": {"queue": "thumbnails"},
        "jobs.price_precompute.*": {"queue": "analytics"},
        "jobs.cleanup.*": {"queue": "maintenance"},
    },
    beat_schedule={
        "price-precompute-hourly": {
            "task": "jobs.price_precompute.precompute_recent_prices",
            "schedule": timedelta(hours=1),
            "args": [],
        },
        "cleanup-orphans-weekly": {
            "task": "jobs.cleanup.cleanup_orphan_objects",
            "schedule": timedelta(days=7),
            "args": [],
        },
    },
)


celery_app.autodiscover_tasks(packages=["app.workers.jobs"], related_name="*")
