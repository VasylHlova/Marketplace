from typing import Any, Generic, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.repositories.base.protocols import Model


class CRUDRepository(Generic[Model]):
    def __init__(self, session: AsyncSession, model: type[Model]) -> None:
        self.session = session
        self.model = model

    async def create(self, data: Any) -> Model:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: Model, update_data: dict[str, Any]) -> Model:
        for key, value in update_data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: Model) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def get_by_id(self, id: str) -> Model | None:
        id_col = cast(InstrumentedAttribute, self.model.id)  # type: ignore[attr-defined]
        result = await self.session.execute(select(self.model).where(id_col == id))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int, offset: int) -> tuple[list[Model], int]:
        created_at_col = cast(InstrumentedAttribute, self.model.created_at)  # type: ignore[attr-defined]
        instances_result = await self.session.execute(
            select(self.model).order_by(created_at_col.desc()).limit(limit).offset(offset)
        )
        count_result = await self.session.execute(select(func.count()).select_from(self.model))
        return (list(instances_result.scalars().all()), count_result.scalar_one())

    async def commit(self) -> None:
        await self.session.commit()

    async def roll_back(self) -> None:
        await self.session.rollback()
