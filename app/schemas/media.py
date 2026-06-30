from pydantic import BaseModel, field_validator

from app.core.config import settings


class UploadUrlRequest(BaseModel):
    file_name: str
    file_type: str

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        if v not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}")
        return v

    @field_validator("file_name")
    @classmethod
    def validate_file_extension(cls, v: str, info) -> str:
        file_type = info.data.get("file_type")
        if file_type:
            valid_extensions = {
                "image/jpeg": (".jpg", ".jpeg"),
                "image/png": (".png",),
                "image/webp": (".webp",),
                "video/mp4": (".mp4",),
                "video/webm": (".webm",),
            }.get(file_type, ())
            if not v.lower().endswith(valid_extensions):
                raise ValueError(f"File extension must match the requested type: {valid_extensions}")
        return v


class UploadUrlResponse(BaseModel):
    url: str
    fields: dict
