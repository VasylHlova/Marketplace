import base64
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings
from app.core.websockets import ConnectionManager
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.order import OrderItemService, OrderService
from app.services.product import ProductService
from app.services.user import UserService
from tests.unit.dummies import (
    DummyChatMessageRepository,
    DummyChatRoomRepository,
    DummyMediaRepository,
    DummyOrderItemRepository,
    DummyOrderRepository,
    DummyProductRepository,
    DummyStorageClient,
    DummyTokenRepository,
    DummyUserRepository,
)


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_user_repo(mocker):
    repo = DummyUserRepository()
    mocker.spy(repo, "get_by_email")
    mocker.spy(repo, "create")
    mocker.spy(repo, "commit")
    mocker.spy(repo, "roll_back")
    mocker.spy(repo, "get_by_id")
    mocker.spy(repo, "update")
    mocker.spy(repo, "delete")
    return repo


@pytest.fixture
def user_service(mock_user_repo):
    return UserService(repo=mock_user_repo)


@pytest.fixture
def mock_token_repo(mocker):
    repo = DummyTokenRepository()
    mocker.spy(repo, "save_token")
    mocker.spy(repo, "get_token")
    mocker.spy(repo, "delete_token")
    return repo


@pytest.fixture
def auth_service(mock_user_repo, mock_token_repo):
    return AuthService(user_repo=mock_user_repo, token_repo=mock_token_repo)


@pytest.fixture
def mock_product_repo(mocker):
    repo = DummyProductRepository()
    mocker.spy(repo, "create")
    mocker.spy(repo, "commit")
    mocker.spy(repo, "roll_back")
    mocker.spy(repo, "get_by_id")
    mocker.spy(repo, "update")
    mocker.spy(repo, "delete")
    mocker.spy(repo, "get_all")
    mocker.spy(repo, "get_all_filtered_by_price")
    mocker.spy(repo, "decrement_stock")
    mocker.spy(repo, "increment_stock")
    return repo


@pytest.fixture
def product_service(mock_product_repo):
    return ProductService(repo=mock_product_repo)


@pytest.fixture
def mock_room_repo(mocker):
    repo = DummyChatRoomRepository()
    mocker.spy(repo, "get_by_users")
    mocker.spy(repo, "get_by_id")
    mocker.spy(repo, "create")
    mocker.spy(repo, "commit")
    mocker.spy(repo, "roll_back")
    return repo


@pytest.fixture
def mock_msg_repo(mocker):
    repo = DummyChatMessageRepository()
    mocker.spy(repo, "create")
    mocker.spy(repo, "commit")
    mocker.spy(repo, "roll_back")
    mocker.spy(repo, "get_all_by_room")
    return repo


@pytest.fixture
def chat_service(mock_room_repo, mock_msg_repo):
    return ChatService(room_repo=mock_room_repo, msg_repo=mock_msg_repo)


@pytest.fixture
def mock_order_repo(mocker):
    repo = DummyOrderRepository()
    mocker.spy(repo, "create")
    mocker.spy(repo, "commit")
    mocker.spy(repo, "roll_back")
    mocker.spy(repo, "get_by_id")
    mocker.spy(repo, "update")
    mocker.spy(repo, "get_all_by_buyer")
    return repo


@pytest.fixture
def mock_order_item_repo(mocker):
    repo = DummyOrderItemRepository()
    mocker.spy(repo, "create")
    mocker.spy(repo, "get_all_by_order_unpaginated")
    mocker.spy(repo, "get_seller_summary")
    mocker.spy(repo, "get_all_by_order")
    return repo


@pytest.fixture
def order_service(mock_order_repo, mock_order_item_repo, mock_product_repo):
    return OrderService(
        order_repo=mock_order_repo, order_item_repo=mock_order_item_repo, product_repo=mock_product_repo
    )


@pytest.fixture
def order_item_service(mock_order_repo, mock_order_item_repo, mock_product_repo):
    return OrderItemService(
        order_repo=mock_order_repo, order_item_repo=mock_order_item_repo, product_repo=mock_product_repo
    )


VALID_IMAGE_PNG = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


@pytest.fixture
def old_time():
    return datetime.now(UTC) - timedelta(days=2)


@pytest.fixture
def new_time():
    return datetime.now(UTC)


@pytest.fixture
def dummy_media_repo():
    active_urls = {
        f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/active1.png",
        f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/active2.webp",
    }
    return DummyMediaRepository(active_urls=active_urls)


@pytest.fixture
def dummy_storage(old_time, new_time):
    objects = [
        {"Key": "active1.png", "LastModified": old_time},
        {"Key": "active2.webp", "LastModified": new_time},
        {"Key": "orphaned_old.png", "LastModified": old_time},
        {"Key": "orphaned_new.png", "LastModified": new_time},
    ]
    return DummyStorageClient(download_content=VALID_IMAGE_PNG, objects=objects)
