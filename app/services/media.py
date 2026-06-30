from loguru import logger

from app.core.config import settings
from app.core.metrics import MEDIA_PROCESSED
from app.db.minio import minio_session
from app.tasks.media_processor import process_media_task


class MediaService:
    entity_map = {
        "products": "product",
        "avatars": "user",
        "chats": "chat",
    }

    async def generate_presigned_upload_post(self, object_name: str, file_type: str) -> dict:
        logger.info(f"Generating presigned upload post for object: {object_name} with type: {file_type}")
        max_size = settings.VIDEO_MAX_SIZE if file_type.startswith("video/") else settings.IMAGE_MAX_SIZE
        async with minio_session.client(
            "s3",
            endpoint_url=settings.MINIO_URL,
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        ) as client:
            return await client.generate_presigned_post(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_name,
                Fields={"Content-Type": file_type},
                Conditions=[{"Content-Type": file_type}, ["content-length-range", 1, max_size]],
                ExpiresIn=settings.PRSIGNED_URL_TTL,
            )

    async def upload_file(self, object_name: str, file_data: bytes, file_type: str) -> str:
        logger.info(f"Uploading file {object_name} to minio")
        async with minio_session.client(
            "s3",
            endpoint_url=settings.MINIO_URL,
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        ) as client:
            await client.put_object(
                Bucket=settings.MINIO_BUCKET_NAME, Key=object_name, Body=file_data, ContentType=file_type
            )
            public_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/{object_name}"
            return public_url

    async def process_webhook_payload(self, payload: dict) -> None:
        logger.info("Processing webhook payload from MinIO")
        records = payload.get("Records", [])
        if not records:
            return

        for record in records:
            event_name = record.get("eventName", "")
            if not event_name.startswith("s3:ObjectCreated:"):
                continue

            key = record.get("s3", {}).get("object", {}).get("key", "")
            if not key or key.endswith((".webp", ".webm")):
                continue

            parts = key.split("/")
            if len(parts) < 3:
                continue

            entity_type = self.entity_map.get(parts[0])
            if entity_type:
                logger.info(f"Triggering media processing task for entity {entity_type} {parts[1]}")
                MEDIA_PROCESSED.labels(entity_type=entity_type).inc()
                process_media_task.delay(
                    entity_id=parts[1], entity_type=entity_type, original_media_path=key
                )
