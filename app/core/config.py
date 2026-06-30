from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ENVIRONMENT: str = "dev"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    SQLITE_DB: str = "app.db"
    ELASTIC_SEARCH_URL: str
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    MINIO_URL: str = "http://localhost:9000"
    MINIO_PUBLIC_URL: str = "http://localhost:9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str = "marketplace-media"
    IMAGE_MAX_SIZE: int = 10485760
    VIDEO_MAX_SIZE: int = 104857600
    PRSIGNED_URL_TTL: int = 3600
    ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        db_path = BASE_DIR / self.SQLITE_DB
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def TEST_DATABASE_URI(self) -> str:
        return "sqlite+aiosqlite:///:memory:"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URI(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()  # type: ignore[call-arg]
