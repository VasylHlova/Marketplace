from typing import Any, TypedDict, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.models.product import Product
from app.repositories.base.crud import CRUDRepository
from app.repositories.base.mixins import GetAllByFieldMixin


class ProductCreateData(TypedDict):
    seller_id: str
    name: str
    price: float
    stock: int
    description: str | None


class ProductRepository(CRUDRepository[Product], GetAllByFieldMixin[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def create(self, data: ProductCreateData) -> Product:  # type: ignore[override]
        return await super().create(data)

    async def get_all_by_seller(self, seller_id: str, limit: int, offset: int) -> tuple[list[Product], int]:
        return await self.get_all_by_field(
            column=self.model.seller_id, value=seller_id, limit=limit, offset=offset
        )

    async def get_by_ids(self, limit: int, offset: int, ids: list[str]) -> tuple[list[Product], int]:
        id_col = cast(InstrumentedAttribute, self.model.id)  # type: ignore[attr-defined]
        created_at_col = cast(InstrumentedAttribute, self.model.created_at)  # type: ignore[attr-defined]
        instances_result = await self.session.execute(
            select(self.model)
            .where(id_col.in_(ids))
            .order_by(created_at_col.desc())
            .limit(limit)
            .offset(offset)
        )
        count_result = await self.session.execute(select(func.count()).select_from(self.model))
        return (list(instances_result.scalars().all()), count_result.scalar_one())

    async def get_all_filtered_by_price(
        self, limit: int, offset: int, filters: list[Any]
    ) -> tuple[list[Product], int]:
        created_at_col = cast(InstrumentedAttribute, self.model.created_at)  # type: ignore[attr-defined]
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = stmt.order_by(created_at_col.desc()).limit(limit).offset(offset)
        instances_result = await self.session.execute(stmt)
        count_result = await self.session.execute(count_stmt)
        return (list(instances_result.scalars().all()), count_result.scalar_one())

    async def decrement_stock(self, product_id: str, quantity: int) -> bool:
        raw_result = await self.session.execute(
            update(Product)
            .where(Product.id == product_id, Product.stock >= quantity)
            .values(stock=Product.stock - quantity)
        )
        cursor = cast(CursorResult, raw_result)
        return cursor.rowcount == 1

    async def increment_stock(self, product_id: str, quantity: int) -> bool:
        raw_result = await self.session.execute(
            update(Product).where(Product.id == product_id).values(stock=Product.stock + quantity)
        )
        cursor = cast(CursorResult, raw_result)
        return cursor.rowcount == 1
