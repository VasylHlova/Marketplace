import uuid

from anyio import to_thread
from loguru import logger

from app.core.exceptions import BadRequestError, ConflictError, DatabaseError, NotFoundError
from app.core.metrics import USERS_CREATED
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories import UserRepositoryProtocol


class UserService:
    def __init__(self, repo: UserRepositoryProtocol) -> None:
        self._repo = repo

    async def create(self, email: str, password: str, role: str = "buyer") -> User:
        logger.info(f"Creating new user with email: {email}")
        existing = await self._repo.get_by_email(email)
        if existing:
            logger.warning(f"User creation failed: Email {email} already exists")
            raise ConflictError("User with this email already exists")
        hashed_password = await to_thread.run_sync(lambda: get_password_hash(password))
        try:
            user = await self._repo.create({"email": email, "password": hashed_password, "role": role})
            await self._repo.commit()
            logger.info(f"User {user.id} created successfully")
            USERS_CREATED.inc()

            return user
        except Exception as e:
            logger.error(f"Database error while creating user {email}: {e}")
            await self._repo.roll_back()
            raise DatabaseError("Failed to create user") from e

    async def update(self, user_id: str, update_data: dict) -> User:
        logger.info(f"Updating user {user_id}")
        user = await self._repo.get_by_id(user_id)
        if not user:
            logger.warning(f"Update failed: User {user_id} not found")
            raise NotFoundError("User not found")
        if "password" in update_data:
            update_data["password"] = await to_thread.run_sync(
                lambda: get_password_hash(update_data.pop("password"))
            )
        if "email" in update_data:
            existing_user = await self._repo.get_by_email(update_data["email"])
            if existing_user and existing_user.id != user.id:
                logger.warning(f"Update failed: Email {update_data['email']} already used by another user")
                raise ConflictError("User with this email already exists")
        try:
            updated_user = await self._repo.update(user, update_data)
            await self._repo.commit()
            logger.info(f"User {user_id} updated successfully")
            return updated_user
        except Exception as e:
            logger.error(f"Database error while updating user {user_id}: {e}")
            await self._repo.roll_back()
            raise DatabaseError("Failed to update user") from e

    async def delete(self, user_id: str) -> None:
        logger.info(f"Deleting user {user_id}")
        user = await self._repo.get_by_id(user_id)
        if not user:
            logger.warning(f"Delete failed: User {user_id} not found")
            raise NotFoundError("User not found")
        try:
            await self._repo.delete(user)
            await self._repo.commit()
            logger.info(f"User {user_id} deleted successfully")
        except Exception as e:
            logger.error(f"Database error while deleting user {user_id}: {e}")
            await self._repo.roll_back()
            raise DatabaseError("Failed to delete user") from e

    async def get_all(self, limit: int, offset: int) -> tuple[list[User], int]:
        return await self._repo.get_all(limit=limit, offset=offset)

    async def get_sellers(self, limit: int, offset: int) -> tuple[list[User], int]:
        return await self._repo.get_all_sellers(limit=limit, offset=offset)

    async def get_by_id(self, id: str | uuid.UUID) -> User:
        user = await self._repo.get_by_id(str(id))
        if not user:
            raise NotFoundError("User not found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self._repo.get_by_email(email)

    async def update_password(self, user: User, current_password: str, new_password: str) -> None:
        logger.info(f"Updating password for user {user.id}")
        verified = await to_thread.run_sync(lambda: verify_password(current_password, user.password))
        if not verified:
            logger.warning(f"Password update failed for user {user.id}: Incorrect password")
            raise BadRequestError("Incorrect password")
        if current_password == new_password:
            logger.warning(f"Password update failed for user {user.id}: New password same as current")
            raise ConflictError("New password cannot be the same as the current one")
        hashed_password = await to_thread.run_sync(lambda: get_password_hash(new_password))
        try:
            await self._repo.update(user, {"password": hashed_password})
            await self._repo.commit()
            logger.info(f"Password for user {user.id} updated successfully")
        except Exception as e:
            logger.error(f"Database error while updating password for user {user.id}: {e}")
            await self._repo.roll_back()
            raise DatabaseError("Failed to update password") from e
