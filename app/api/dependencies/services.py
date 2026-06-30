from typing import Annotated

from fastapi import Depends

from app.api.dependencies.db import AsyncSessionDep
from app.db.redis import redis_client
from app.repositories import ProductRepository, UserRepository
from app.repositories.chat import ChatMessageRepository, ChatRoomRepository
from app.repositories.order import OrderItemRepository, OrderRepository
from app.repositories.token import TokenRepository
from app.services import (
    AuthService,
    AuthServiceProtocol,
    ChatService,
    ChatServiceProtocol,
    MediaService,
    MediaServiceProtocol,
    OrderItemService,
    OrderItemServiceProtocol,
    OrderService,
    OrderServiceProtocol,
    ProductService,
    ProductServiceProtocol,
    UserService,
    UserServiceProtocol,
)


def get_user_service(session: AsyncSessionDep) -> UserServiceProtocol:
    repo = UserRepository(session)
    return UserService(repo=repo)


def get_product_service(session: AsyncSessionDep) -> ProductServiceProtocol:
    repo = ProductRepository(session)
    return ProductService(repo=repo)


def get_order_service(session: AsyncSessionDep) -> OrderServiceProtocol:
    order_repo = OrderRepository(session)
    order_item_repo = OrderItemRepository(session)
    product_repo = ProductRepository(session)
    return OrderService(order_repo=order_repo, order_item_repo=order_item_repo, product_repo=product_repo)


def get_order_item_service(session: AsyncSessionDep) -> OrderItemServiceProtocol:
    order_repo = OrderRepository(session)
    order_item_repo = OrderItemRepository(session)
    product_repo = ProductRepository(session)
    return OrderItemService(
        order_repo=order_repo, order_item_repo=order_item_repo, product_repo=product_repo
    )


def get_chat_service(session: AsyncSessionDep) -> ChatServiceProtocol:
    room_repo = ChatRoomRepository(session)
    msg_repo = ChatMessageRepository(session)
    return ChatService(room_repo=room_repo, msg_repo=msg_repo)


def get_auth_service(session: AsyncSessionDep) -> AuthServiceProtocol:
    user_repo = UserRepository(session)
    token_repo = TokenRepository(redis_client)
    return AuthService(user_repo=user_repo, token_repo=token_repo)


def get_media_service() -> MediaServiceProtocol:
    return MediaService()


UserServiceDep = Annotated[UserServiceProtocol, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductServiceProtocol, Depends(get_product_service)]
OrderServiceDep = Annotated[OrderServiceProtocol, Depends(get_order_service)]
OrderItemServiceDep = Annotated[OrderItemServiceProtocol, Depends(get_order_item_service)]
ChatServiceDep = Annotated[ChatServiceProtocol, Depends(get_chat_service)]
AuthServiceDep = Annotated[AuthServiceProtocol, Depends(get_auth_service)]
MediaServiceDep = Annotated[MediaServiceProtocol, Depends(get_media_service)]
