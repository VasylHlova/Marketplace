from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.repositories.base.crud import CRUDRepository
from app.repositories.base.mixins import GetAllByFieldMixin


class OrderCreateData(TypedDict):
    buyer_id: str
    status: str


class OrderItemCreateData(TypedDict):
    order_id: str
    product_id: str
    quantity: int
    price_at_purchase: float


class OrderRepository(CRUDRepository[Order], GetAllByFieldMixin[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    async def create(self, data: OrderCreateData) -> Order:  # type: ignore[override]
        return await super().create(data)

    async def get_all_by_buyer(self, buyer_id: str, limit: int, offset: int) -> tuple[list[Order], int]:
        return await self.get_all_by_field(
            column=self.model.buyer_id, value=buyer_id, limit=limit, offset=offset
        )


class OrderItemRepository(CRUDRepository[OrderItem], GetAllByFieldMixin[OrderItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderItem)

    async def create(self, data: OrderItemCreateData) -> OrderItem:  # type: ignore[override]
        return await super().create(data)

    async def get_all_by_order(self, order_id: str, limit: int, offset: int) -> tuple[list[OrderItem], int]:
        return await self.get_all_by_field(
            column=self.model.order_id, value=order_id, limit=limit, offset=offset
        )

    async def get_all_by_order_unpaginated(self, order_id: str) -> list[OrderItem]:
        result = await self.session.execute(select(self.model).where(self.model.order_id == order_id))
        return list(result.scalars().all())

    async def get_seller_summary(self, seller_id: str) -> dict:
        from app.core.enums.order import OrderStatus

        stmt = (
            select(
                func.count(func.distinct(OrderItem.order_id)).label("total_orders"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.price_at_purchase), 0).label(
                    "total_revenue"
                ),
            )
            .join(Product, OrderItem.product_id == Product.id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Product.seller_id == seller_id)
            .where(Order.status != OrderStatus.CANCELED.value)
        )
        result = await self.session.execute(stmt)
        row = result.one()
        return {"total_orders": row.total_orders, "total_revenue": float(row.total_revenue)}
