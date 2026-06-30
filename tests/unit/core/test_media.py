import base64

import pytest
from PIL import Image

from app.core.config import settings
from app.core.media import get_media_config, process_image, process_media, process_video

VALID_IMAGE_PNG = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def test_get_media_config_image():
    config = get_media_config("image/png")
    assert config is not None
    assert config.ext == ".webp"
    assert config.mime == "image/webp"


def test_get_media_config_video():
    config = get_media_config("video/mp4")
    assert config is not None
    assert config.ext == ".webm"
    assert config.mime == "video/webm"


def test_get_media_config_unknown_returns_none():
    config = get_media_config("application/pdf")
    assert config is None


@pytest.mark.asyncio
async def test_process_media_product(dummy_storage, dummy_media_repo, faker):
    product_id = faker.uuid4()
    key = f"products/{product_id}/original.png"

    await process_media(product_id, "product", key, dummy_storage, dummy_media_repo)

    assert dummy_storage.downloads[0][0] == key
    uploaded_key, _, uploaded_mime = dummy_storage.uploads[0]
    assert uploaded_key == f"products/{product_id}/original.webp"
    assert uploaded_mime == "image/webp"
    assert dummy_storage.deletes[0] == key

    assert len(dummy_media_repo.product_updates) == 1
    saved_id, saved_url = dummy_media_repo.product_updates[0]
    assert saved_id == product_id
    assert saved_url.endswith(f"products/{product_id}/original.webp")


@pytest.mark.asyncio
async def test_process_media_user_avatar(dummy_storage, dummy_media_repo, faker):
    user_id = faker.uuid4()
    key = f"avatars/{user_id}/avatar.png"

    await process_media(user_id, "user", key, dummy_storage, dummy_media_repo)

    assert dummy_storage.downloads[0][0] == key
    uploaded_key, _, uploaded_mime = dummy_storage.uploads[0]
    assert uploaded_key == f"avatars/{user_id}/avatar.webp"
    assert uploaded_mime == "image/webp"
    assert dummy_storage.deletes[0] == key

    assert len(dummy_media_repo.avatar_updates) == 1
    saved_id, saved_url = dummy_media_repo.avatar_updates[0]
    assert saved_id == user_id
    assert saved_url.endswith(f"avatars/{user_id}/avatar.webp")


@pytest.mark.asyncio
async def test_process_media_chat_attachment(dummy_storage, dummy_media_repo, faker):
    room_id = faker.uuid4()
    user_id = faker.uuid4()
    key = f"chats/{room_id}/{user_id}/photo.png"

    await process_media(room_id, "chat", key, dummy_storage, dummy_media_repo)

    assert dummy_storage.downloads[0][0] == key
    uploaded_key, _, uploaded_mime = dummy_storage.uploads[0]
    assert uploaded_key == f"chats/{room_id}/{user_id}/photo.webp"
    assert uploaded_mime == "image/webp"
    assert dummy_storage.deletes[0] == key

    assert len(dummy_media_repo.chat_updates) == 1
    original_url, new_url = dummy_media_repo.chat_updates[0]
    assert key in original_url
    assert new_url.endswith(f"chats/{room_id}/{user_id}/photo.webp")


@pytest.mark.asyncio
async def test_process_media_unknown_type_skipped(dummy_media_repo, faker, tmp_path, mocker):
    from tests.unit.dummies import DummyStorageClient

    pdf_bytes = b"%PDF-1.4 fake pdf content"
    storage = DummyStorageClient(download_content=pdf_bytes)

    mock_kind = mocker.MagicMock()
    mock_kind.mime = "application/pdf"
    mocker.patch("app.core.media.filetype.guess", return_value=mock_kind)

    entity_id = faker.uuid4()
    await process_media(entity_id, "product", f"products/{entity_id}/doc.pdf", storage, dummy_media_repo)

    assert len(storage.uploads) == 0
    assert len(storage.deletes) == 0
    assert len(dummy_media_repo.product_updates) == 0


@pytest.mark.asyncio
async def test_process_media_strips_public_url_prefix(dummy_storage, dummy_media_repo, faker):
    product_id = faker.uuid4()
    raw_key = f"products/{product_id}/img.png"
    full_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/{raw_key}"

    await process_media(product_id, "product", full_url, dummy_storage, dummy_media_repo)

    assert dummy_storage.downloads[0][0] == raw_key


@pytest.mark.asyncio
async def test_process_media_unknown_entity_type(dummy_storage, dummy_media_repo, faker):
    product_id = faker.uuid4()
    key = f"products/{product_id}/img.png"

    await process_media(product_id, "unknown_type", key, dummy_storage, dummy_media_repo)

    assert len(dummy_storage.uploads) == 1
    assert len(dummy_storage.deletes) == 1
    assert len(dummy_media_repo.product_updates) == 0
    assert len(dummy_media_repo.avatar_updates) == 0
    assert len(dummy_media_repo.chat_updates) == 0


@pytest.mark.asyncio
async def test_process_media_invalid_file(dummy_storage, dummy_media_repo, faker, mocker):
    mocker.patch("app.core.media.filetype.guess", return_value=None)
    product_id = faker.uuid4()
    key = f"products/{product_id}/img.png"
    with pytest.raises(ValueError, match="Could not determine file type"):
        await process_media(product_id, "product", key, dummy_storage, dummy_media_repo)


def test_process_image_rgba_and_resize(tmp_path):
    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.webp"
    img = Image.new("RGBA", (2048, 1000), color=(255, 0, 0, 128))
    img.save(input_path)

    process_image(str(input_path), str(output_path))

    assert output_path.exists()
    with Image.open(output_path) as out_img:
        assert out_img.mode == "RGB"
        assert out_img.width == 1024
        assert out_img.height == 500


def test_process_video(tmp_path, mocker):

    mock_ffmpeg = mocker.patch("app.core.media.ffmpeg")
    input_path = str(tmp_path / "input.mp4")
    output_path = str(tmp_path / "output.webm")

    process_video(input_path, output_path)

    mock_ffmpeg.input.assert_called_once_with(input_path)
    assert mock_ffmpeg.input.return_value.filter.called
