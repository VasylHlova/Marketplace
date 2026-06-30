import pytest

from app.core.config import settings
from app.services.media import MediaService


class MockContextManager:
    def __init__(self, mock_client):
        self.mock_client = mock_client

    async def __aenter__(self):
        return self.mock_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_generate_presigned_upload_post_image(mocker):
    service = MediaService()
    mock_client = mocker.AsyncMock()
    mock_client.generate_presigned_post.return_value = {"url": "http://test", "fields": {"key": "val"}}
    mocker.patch("app.services.media.minio_session.client", return_value=MockContextManager(mock_client))
    result = await service.generate_presigned_upload_post("test/key.png", "image/png")
    assert result == {"url": "http://test", "fields": {"key": "val"}}
    mock_client.generate_presigned_post.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key="test/key.png",
        Fields={"Content-Type": "image/png"},
        Conditions=[
            {"Content-Type": "image/png"},
            ["content-length-range", 1, settings.IMAGE_MAX_SIZE],
        ],
        ExpiresIn=settings.PRSIGNED_URL_TTL,
    )


@pytest.mark.asyncio
async def test_generate_presigned_upload_post_video(mocker):
    service = MediaService()
    mock_client = mocker.AsyncMock()
    mock_client.generate_presigned_post.return_value = {"url": "http://test", "fields": {"key": "val"}}
    mocker.patch("app.services.media.minio_session.client", return_value=MockContextManager(mock_client))
    result = await service.generate_presigned_upload_post("test/key.mp4", "video/mp4")
    assert result == {"url": "http://test", "fields": {"key": "val"}}
    mock_client.generate_presigned_post.assert_called_once_with(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key="test/key.mp4",
        Fields={"Content-Type": "video/mp4"},
        Conditions=[
            {"Content-Type": "video/mp4"},
            ["content-length-range", 1, settings.VIDEO_MAX_SIZE],
        ],
        ExpiresIn=settings.PRSIGNED_URL_TTL,
    )


# ---------------------------------------------------------------------------
# process_webhook_payload
# ---------------------------------------------------------------------------


def _make_record(key: str, event: str = "s3:ObjectCreated:Put") -> dict:
    return {"eventName": event, "s3": {"object": {"key": key}}}


@pytest.mark.asyncio
async def test_webhook_triggers_product_task(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()
    payload = {"Records": [_make_record(f"products/{product_id}/img.jpg")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_called_once_with(
        entity_id=product_id,
        entity_type="product",
        original_media_path=f"products/{product_id}/img.jpg",
    )


@pytest.mark.asyncio
async def test_webhook_triggers_avatar_task(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    user_id = faker.uuid4()
    payload = {"Records": [_make_record(f"avatars/{user_id}/avatar.jpg")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_called_once_with(
        entity_id=user_id,
        entity_type="user",
        original_media_path=f"avatars/{user_id}/avatar.jpg",
    )


@pytest.mark.asyncio
async def test_webhook_triggers_chat_task(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    room_id = faker.uuid4()
    user_id = faker.uuid4()
    key = f"chats/{room_id}/{user_id}/photo.jpg"
    payload = {"Records": [_make_record(key)]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_called_once_with(
        entity_id=room_id,
        entity_type="chat",
        original_media_path=key,
    )


@pytest.mark.asyncio
async def test_webhook_ignores_already_processed_webp(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()
    payload = {"Records": [_make_record(f"products/{product_id}/img.webp")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_ignores_already_processed_webm(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()
    payload = {"Records": [_make_record(f"products/{product_id}/vid.webm")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_ignores_non_create_events(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()
    payload = {"Records": [_make_record(f"products/{product_id}/img.jpg", event="s3:ObjectRemoved:Delete")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_ignores_unknown_path_prefix(mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    payload = {"Records": [_make_record("unknown/path/img.jpg")]}

    await MediaService().process_webhook_payload(payload)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_empty_records_does_nothing(mocker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    await MediaService().process_webhook_payload({"Records": []})
    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_missing_records_does_nothing(mocker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    await MediaService().process_webhook_payload({})
    mock_task.delay.assert_not_called()
