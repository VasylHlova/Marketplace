from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.services import get_auth_service
from app.core.config import settings
from app.core.enums.user import UserRole
from app.core.security import create_access_token
from app.main import app as main_app
from app.models.chat import ChatRoom
from app.models.product import Product
from app.models.user import User
from app.repositories.chat import ChatMessageRepository, ChatRoomRepository
from app.repositories.media import SqlMediaRepository
from app.repositories.order import OrderItemRepository, OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.token import TokenRepository
from app.repositories.user import UserRepository
from app.services import AuthService
from app.storages.client import MinioStorageClient
from tests.factories import ProductFactory, UserFactory
from tests.integration.repositories.base.dummy import DummyRepository


@pytest.fixture
def app():
    return main_app


@pytest_asyncio.fixture(autouse=True)
async def setup_redis():
    from fastapi import Depends

    from app.api.dependencies.db import get_db

    test_redis = Redis.from_url("redis://localhost:6379/1", decode_responses=True)

    def override_auth_service(session: AsyncSession = Depends(get_db)):
        user_repo = UserRepository(session)
        token_repo = TokenRepository(test_redis)
        return AuthService(user_repo=user_repo, token_repo=token_repo)

    main_app.dependency_overrides[get_auth_service] = override_auth_service
    yield test_redis
    main_app.dependency_overrides.pop(get_auth_service, None)
    await test_redis.aclose()


@pytest_asyncio.fixture
async def test_seller(db_session) -> User:
    seller = UserFactory(role=UserRole.SELLER.value)
    db_session.add(seller)
    await db_session.commit()
    return seller


@pytest_asyncio.fixture
async def seller_client(async_client: AsyncClient, test_seller: User) -> AsyncClient:
    access_token = create_access_token(
        subject=str(test_seller.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    return async_client


@pytest_asyncio.fixture
async def test_room(db_session, test_user: User, other_user: User) -> ChatRoom:
    room = ChatRoom(buyer_id=str(test_user.id), seller_id=str(other_user.id))
    db_session.add(room)
    await db_session.commit()
    return room


@pytest_asyncio.fixture
async def test_products(db_session: AsyncSession, test_user: User) -> list[Product]:
    products = []
    for i in range(5):
        product = ProductFactory(seller_id=str(test_user.id))
        db_session.add(product)
        products.append(product)

    await db_session.commit()
    return products


@pytest.fixture
def order_repo(db_session: AsyncSession):
    return OrderRepository(db_session)


@pytest.fixture
def order_item_repo(db_session: AsyncSession):
    return OrderItemRepository(db_session)


@pytest.fixture
def user_repo(db_session: AsyncSession):
    return UserRepository(db_session)


@pytest.fixture
def product_repo(db_session: AsyncSession):
    return ProductRepository(db_session)


@pytest.fixture
def chat_room_repo(db_session: AsyncSession):
    return ChatRoomRepository(db_session)


@pytest.fixture
def chat_msg_repo(db_session: AsyncSession):
    return ChatMessageRepository(db_session)


@pytest.fixture
def dummy_repo(db_session: AsyncSession):
    return DummyRepository(db_session)


@pytest.fixture
def media_repo(db_session: AsyncSession):
    return SqlMediaRepository(db_session)


@pytest.fixture
def storage_client():
    return MinioStorageClient(
        bucket=settings.MINIO_BUCKET_NAME,
        url="http://localhost:9000",
        user=settings.MINIO_ROOT_USER,
        password=settings.MINIO_ROOT_PASSWORD,
    )
