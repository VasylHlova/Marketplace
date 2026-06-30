from celery import Celery  # type: ignore[import-untyped]
from celery.schedules import crontab  # type: ignore[import-untyped]

from app.core.config import settings

celery_app = Celery(
    "tech1",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email", "app.tasks.sync", "app.tasks.media", "app.tasks.media_processor"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-orphaned-media-daily": {
            "task": "app.tasks.media.cleanup_orphaned_media_task",
            "schedule": crontab(hour=3, minute=0),
        }
    },
)
