from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.services import AuthServiceDep
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.schemas.token import Token

router = APIRouter(tags=["Auth"])


@router.post("/login")
async def login(
    user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
    response: Response,
) -> Token:
    access_token, refresh_token = await service.login(
        email=user_credentials.username, password=user_credentials.password
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "prod",
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: AuthServiceDep,
    token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> None:
    if token:
        await service.logout(token)
    response.delete_cookie(key="refresh_token")


@router.post("/refresh")
async def refresh(
    response: Response,
    service: AuthServiceDep,
    token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> Token:
    if not token:
        raise UnauthorizedError("Refresh token missing")
    access_token, new_refresh_token = await service.refresh(token)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "prod",
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return Token(access_token=access_token)
