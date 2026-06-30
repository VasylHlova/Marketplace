from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

SQLALCHEMY_DATABASE_URI = settings.SQLALCHEMY_DATABASE_URI
engine = create_async_engine(SQLALCHEMY_DATABASE_URI, echo=True, connect_args={"check_same_thread": False})
async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)
