from typing import Annotated

import jwt
from fastapi import Depends, Query, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.api.dependencies.db import AsyncSessionDep
from app.core.config import settings
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.models.user import User
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: AsyncSessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.exceptions.InvalidTokenError, ValidationError):
        raise UnauthorizedError("Could not validate credentials")
    user = await session.get(User, token_data.sub)
    if not user:
        raise NotFoundError("User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_user_ws(session: AsyncSessionDep, token: Annotated[str, Query(...)]) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.exceptions.InvalidTokenError, ValidationError):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = await session.get(User, token_data.sub)
    if not user:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return user


def get_current_buyer(current_user: CurrentUserDep) -> User:
    from app.core.enums.user import UserRole
    from app.core.exceptions import ForbiddenError

    if current_user.role != UserRole.BUYER:
        raise ForbiddenError("Only buyers can perform this action")
    return current_user


CurrentBuyerDep = Annotated[User, Depends(get_current_buyer)]


def get_current_seller(current_user: CurrentUserDep) -> User:
    from app.core.enums.user import UserRole
    from app.core.exceptions import ForbiddenError

    if current_user.role != UserRole.SELLER:
        raise ForbiddenError("Only sellers can perform this action")
    return current_user


CurrentSellerDep = Annotated[User, Depends(get_current_seller)]
