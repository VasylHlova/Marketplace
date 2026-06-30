import asyncio
from datetime import UTC, datetime, timedelta

from app.core.celery import celery_app
from app.core.config import settings
from app.db.database import async_session
from app.repositories.base.protocols import MediaRepositoryProtocol
from app.repositories.media import SqlMediaRepository
from app.storages.client import MinioStorageClient
from app.storages.protocols import StorageClientProtocol


async def _cleanup_orphaned_media(storage: StorageClientProtocol, repo: MediaRepositoryProtocol):
    active_urls = await repo.get_active_urls()
    base_prefix = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/"
    active_keys = {url.replace(base_prefix, "") for url in active_urls}
    cutoff_time = datetime.now(UTC) - timedelta(hours=24)

    async for obj in storage.list_objects():
        obj_key = obj["Key"]
        last_modified = obj["LastModified"]
        if obj_key not in active_keys and last_modified < cutoff_time:
            await storage.delete(obj_key)


async def _run_cleanup_orphaned_media_task():
    storage = MinioStorageClient(
        bucket=settings.MINIO_BUCKET_NAME,
        url=settings.MINIO_URL,
        user=settings.MINIO_ROOT_USER,
        password=settings.MINIO_ROOT_PASSWORD,
    )
    async with async_session() as session:
        repo = SqlMediaRepository(session)
        await _cleanup_orphaned_media(storage, repo)


@celery_app.task(bind=True, max_retries=3)
def cleanup_orphaned_media_task(self):
    try:
        asyncio.run(_run_cleanup_orphaned_media_task())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
