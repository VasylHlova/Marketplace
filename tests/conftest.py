import asyncio
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies.db import get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.base import Base
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from tests.factories import OrderFactory, ProductFactory, UserFactory


@pytest.fixture(autouse=True)
def mock_celery_tasks(mocker):
    mocker.patch("app.services.product.index_product_to_es.delay")
    mocker.patch("app.services.product.update_product_in_es.delay")
    mocker.patch("app.services.product.delete_product_from_es.delay")
    mocker.patch("app.services.order.send_order_confirmation.delay")
    mocker.patch("app.services.media.process_media_task.delay")


engine = create_async_engine(settings.TEST_DATABASE_URI, echo=False, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_db] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{settings.API_V1_STR}"
    ) as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def authorized_client(
    async_client: AsyncClient, test_user: User
) -> AsyncGenerator[AsyncClient, None]:
    access_token = create_access_token(
        subject=str(test_user.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    yield async_client
    async_client.headers.pop("Authorization", None)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = UserFactory()
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_product(db_session: AsyncSession, test_user: User) -> Product:
    product = ProductFactory(seller_id=str(test_user.id))
    db_session.add(product)
    await db_session.commit()
    return product


@pytest_asyncio.fixture
async def test_order(db_session: AsyncSession, test_user: User) -> Order:
    order = OrderFactory(buyer_id=str(test_user.id))
    db_session.add(order)
    await db_session.commit()
    return order


@pytest_asyncio.fixture
async def test_user_with_password(db_session: AsyncSession) -> User:
    user = UserFactory(password=get_password_hash("oldpassword"))
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    user = UserFactory()
    db_session.add(user)
    await db_session.commit()
    return user
