import datetime
import uuid

import jwt
from anyio import to_thread
from loguru import logger

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.metrics import LOGIN_ATTEMPTS
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.repositories import TokenRepositoryProtocol, UserRepositoryProtocol


class AuthService:
    def __init__(
        self, user_repo: UserRepositoryProtocol, token_repo: TokenRepositoryProtocol
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def _save_refresh_token(self, user_id: str | uuid.UUID, token: str, expire: datetime.datetime) -> None:
        time_delta = expire - datetime.datetime.now(datetime.UTC)
        ttl_seconds = int(time_delta.total_seconds())
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        redis_key = f"refresh_token:{user_id}:{decoded_payload['jti']}"
        await self._token_repo.save_token(key=redis_key, ttl_seconds=ttl_seconds)

    async def authenticate(self, email: str, password: str) -> User:
        db_user = await self._user_repo.get_by_email(email)
        if not db_user:
            logger.warning(f"Authentication failed: User not found ({email})")
            LOGIN_ATTEMPTS.labels(status="error_not_found").inc()
            raise UnauthorizedError("User not found")

        verified = await to_thread.run_sync(lambda: verify_password(password, db_user.password))
        if not verified:
            logger.warning(f"Authentication failed: Invalid credentials ({email})")
            LOGIN_ATTEMPTS.labels(status="error_invalid_credentials").inc()
            raise UnauthorizedError("Invalid credentials")

        logger.info(f"User successfully authenticated: {email}")
        LOGIN_ATTEMPTS.labels(status="success").inc()
        return db_user

    async def login(self, email: str, password: str) -> tuple[str, str]:
        logger.info(f"Logging in user: {email}")
        user = await self.authenticate(email, password)

        access_token = create_access_token(
            user.id, expires_delta=datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token, expire = create_refresh_token(str(user.id))
        await self._save_refresh_token(user_id=user.id, token=refresh_token, expire=expire)

        return (access_token, refresh_token)

    async def refresh(self, token: str) -> tuple[str, str]:
        try:
            decoded_jwt = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if decoded_jwt.get("type") != "refresh":
                logger.warning("Refresh token failed: Invalid token type")
                raise UnauthorizedError("Invalid token type")
            user_id = uuid.UUID(decoded_jwt.get("sub"))
            jti = decoded_jwt.get("jti")
        except jwt.PyJWTError as e:
            logger.warning(f"Refresh token failed: Invalid or expired refresh token ({e})")
            raise UnauthorizedError("Invalid or expired refresh token")

        logger.info(f"Refreshing token for user: {user_id}")
        redis_key = f"refresh_token:{user_id}:{jti}"
        token_exists = await self._token_repo.get_token(redis_key)
        if not token_exists:
            logger.warning(f"Refresh token revoked or reused for user: {user_id}")
            raise UnauthorizedError("Refresh token revoked or reused")
        await self._token_repo.delete_token(redis_key)
        refresh_token, expire = create_refresh_token(user_id)
        await self._save_refresh_token(user_id=user_id, token=refresh_token, expire=expire)
        access_token = create_access_token(
            user_id, expires_delta=datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return (access_token, refresh_token)

    async def logout(self, token: str) -> None:
        decoded_jwt = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = decoded_jwt.get("sub")
        jti = decoded_jwt.get("jti")
        logger.info(f"User logged out: {user_id}")
        redis_key = f"refresh_token:{user_id}:{jti}"
        await self._token_repo.delete_token(redis_key)
