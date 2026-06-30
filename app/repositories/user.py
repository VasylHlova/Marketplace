from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums.user import UserRole
from app.models.user import User
from app.repositories.base.crud import CRUDRepository


class UserCreateData(TypedDict):
    email: str
    password: str
    role: str


class UserRepository(CRUDRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def create(self, data: UserCreateData) -> User:  # type: ignore[override]
        return await super().create(data)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all_sellers(self, limit: int, offset: int) -> tuple[list[User], int]:
        where_clause = User.role == UserRole.SELLER
        data_result = await self.session.execute(
            select(User).where(where_clause).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(User).where(where_clause)
        )
        return (list(data_result.scalars().all()), count_result.scalar_one())
