import pytest
from fastapi import status
from httpx import AsyncClient


def _make_payload(key: str, event: str = "s3:ObjectCreated:Put") -> dict:
    return {"Records": [{"eventName": event, "s3": {"object": {"key": key}}}]}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_product_triggers_task(async_client: AsyncClient, mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()
    payload = _make_payload(f"products/{product_id}/img.jpg")

    response = await async_client.post("/webhooks/minio", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success"}
    mock_task.delay.assert_called_once_with(
        entity_id=product_id,
        entity_type="product",
        original_media_path=f"products/{product_id}/img.jpg",
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_avatar_triggers_task(async_client: AsyncClient, mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    user_id = faker.uuid4()
    payload = _make_payload(f"avatars/{user_id}/avatar.jpg")

    response = await async_client.post("/webhooks/minio", json=payload)

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_called_once_with(
        entity_id=user_id,
        entity_type="user",
        original_media_path=f"avatars/{user_id}/avatar.jpg",
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_chat_triggers_task(async_client: AsyncClient, mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    room_id = faker.uuid4()
    user_id = faker.uuid4()
    key = f"chats/{room_id}/{user_id}/photo.jpg"

    response = await async_client.post("/webhooks/minio", json=_make_payload(key))

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_called_once_with(
        entity_id=room_id,
        entity_type="chat",
        original_media_path=key,
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_ignores_webp(async_client: AsyncClient, mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()

    response = await async_client.post(
        "/webhooks/minio", json=_make_payload(f"products/{product_id}/img.webp")
    )

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_ignores_delete_event(async_client: AsyncClient, mocker, faker):
    mock_task = mocker.patch("app.services.media.process_media_task")
    product_id = faker.uuid4()

    response = await async_client.post(
        "/webhooks/minio",
        json=_make_payload(f"products/{product_id}/img.jpg", event="s3:ObjectRemoved:Delete"),
    )

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_empty_payload(async_client: AsyncClient, mocker):
    mock_task = mocker.patch("app.services.media.process_media_task")

    response = await async_client.post("/webhooks/minio", json={})

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_minio_webhook_invalid_json(async_client: AsyncClient):
    response = await async_client.post(
        "/webhooks/minio",
        content=b"not json at all",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ignored", "detail": "Invalid JSON"}
