import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import ffmpeg  # type: ignore[import-untyped]
import filetype  # type: ignore[import-untyped]
from PIL import Image

from app.core.config import settings
from app.repositories.base.protocols import MediaRepositoryProtocol
from app.storages.protocols import StorageClientProtocol


def process_image(input_path: str, output_path: str) -> None:
    with Image.open(input_path) as img:
        img_rgb: Any = img
        if img.mode in ("RGBA", "P"):
            img_rgb = img.convert("RGB")
        if img_rgb.width > 1024:
            ratio = 1024.0 / img_rgb.width
            new_height = int(img_rgb.height * ratio)
            img_rgb = img_rgb.resize((1024, new_height), Image.Resampling.LANCZOS)
        img_rgb.save(output_path, "WEBP", quality=80)


def process_video(input_path: str, output_path: str) -> None:
    ffmpeg.input(input_path).filter("scale", "min(1280,iw)", "-2").output(
        output_path, vcodec="libvpx-vp9", crf=30, **{"b:v": "0"}
    ).overwrite_output().run(capture_stdout=True, capture_stderr=True)


@dataclass
class MediaTypeConfig:
    ext: str
    mime: str
    processor: Callable[[str, str], None]


MEDIA_TYPE_MAP: dict[str, MediaTypeConfig] = {
    "image/": MediaTypeConfig(ext=".webp", mime="image/webp", processor=process_image),
    "video/": MediaTypeConfig(ext=".webm", mime="video/webm", processor=process_video),
}


def get_media_config(mime: str) -> MediaTypeConfig | None:
    return next((cfg for prefix, cfg in MEDIA_TYPE_MAP.items() if mime.startswith(prefix)), None)


async def process_media(
    entity_id: str,
    entity_type: str,
    original_media_path: str,
    storage: StorageClientProtocol,
    repo: MediaRepositoryProtocol,
) -> None:
    from collections.abc import Awaitable

    base_prefix = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/"
    original_key = original_media_path.removeprefix(base_prefix)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input_media")
        await storage.download(original_key, input_path)

        kind = filetype.guess(input_path)
        if not kind:
            raise ValueError("Could not determine file type")

        config = get_media_config(kind.mime)
        if not config:
            return

        new_key = os.path.splitext(original_key)[0] + config.ext
        output_path = os.path.join(tmpdir, f"output{config.ext}")
        config.processor(input_path, output_path)

        await storage.upload(new_key, output_path, config.mime)
        new_public_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/{new_key}"
        original_public_url = f"{base_prefix}{original_key}"

        repo_update_map: dict[str, Callable[[], Awaitable[None]]] = {
            "product": lambda: repo.update_product_media(entity_id, new_public_url),
            "user": lambda: repo.update_user_avatar(entity_id, new_public_url),
            "chat": lambda: repo.update_chat_media(original_public_url, new_public_url),
        }
        update_fn = repo_update_map.get(entity_type)
        if update_fn:
            await update_fn()

        await storage.delete(original_key)
