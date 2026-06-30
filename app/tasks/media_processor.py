import asyncio

from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from app.core.celery import celery_app
from app.core.config import settings
from app.core.media import process_media
from app.db.database import async_session
from app.repositories.media import SqlMediaRepository
from app.storages.client import MinioStorageClient


async def _run(entity_id: str, entity_type: str, original_media_path: str) -> None:
    storage = MinioStorageClient(
        bucket=settings.MINIO_BUCKET_NAME,
        url=settings.MINIO_URL,
        user=settings.MINIO_ROOT_USER,
        password=settings.MINIO_ROOT_PASSWORD,
    )
    async with async_session() as session:
        repo = SqlMediaRepository(session)
        await process_media(entity_id, entity_type, original_media_path, storage, repo)


@celery_app.task(
    bind=True,
    autoretry_for=(BotoCoreError, ClientError),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def process_media_task(self, entity_id: str, entity_type: str, original_media_path: str) -> None:
    try:
        asyncio.run(_run(str(entity_id), str(entity_type), original_media_path))
    except Exception as exc:
        raise self.retry(exc=exc)
