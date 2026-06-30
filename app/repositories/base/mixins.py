from typing import Any, Generic, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm.attributes import InstrumentedAttribute as IA

from app.repositories.base.protocols import Model


class GetAllByFieldMixin(Generic[Model]):
    session: AsyncSession
    model: type[Model]

    async def get_all_by_field(
        self, column: IA, value: str, limit: int, offset: int, order_by: Any = None
    ) -> tuple[list[Model], int]:
        base_where = column == value
        stmt = select(self.model).where(base_where)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            created_at_col = cast(InstrumentedAttribute, self.model.created_at)  # type: ignore[attr-defined]
            stmt = stmt.order_by(created_at_col.desc())
        result = await self.session.execute(stmt.limit(limit=limit).offset(offset=offset))
        count_result = await self.session.execute(
            select(func.count()).select_from(self.model).where(base_where)
        )
        return (list(result.scalars().all()), count_result.scalar_one())
