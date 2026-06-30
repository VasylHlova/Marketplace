from typing import Any

from loguru import logger

from app.core.enums.order import OrderStatus
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.metrics import ORDERS_CANCELED, ORDERS_COMPLETED, ORDERS_CREATED
from app.models.order import Order, OrderItem
from app.models.user import User
from app.repositories import OrderItemRepositoryProtocol, OrderRepositoryProtocol, ProductRepositoryProtocol
from app.tasks.email import send_order_confirmation


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepositoryProtocol,
        order_item_repo: OrderItemRepositoryProtocol,
        product_repo: ProductRepositoryProtocol,
    ) -> None:
        self.order_repo = order_repo
        self.order_item_repo = order_item_repo
        self.product_repo = product_repo

    async def create_order(self, current_user: User, items: list[dict[str, Any]]) -> Order:
        logger.info(f"User {current_user.id} is creating an order with {len(items)} items")
        if not items:
            raise BadRequestError("Order must contain at least one item")
        for item in items:
            if item["quantity"] <= 0:
                raise BadRequestError("Quantity must be greater than 0")
        products_to_buy: list[tuple[Any, int]] = []
        for item in items:
            product = await self.product_repo.get_by_id(item["product_id"])
            if not product:
                logger.warning(f"Failed to create order: Product {item['product_id']} not found")
                raise NotFoundError(f"Product {item['product_id']} not found")
            if product.stock < item["quantity"]:
                logger.warning(f"Failed to create order: Not enough stock for {product.name}")
                if product.stock <= 0:
                    raise BadRequestError(f"Product {product.name} is out of stock")
                raise BadRequestError(f"Not enough stock for {product.name}. Available: {product.stock}")
            products_to_buy.append((product, item["quantity"]))
        try:
            order = await self.order_repo.create(
                {"buyer_id": current_user.id, "status": OrderStatus.ACTIVE.value}
            )
            created_items = []
            total_price = 0.0
            for product, quantity in products_to_buy:
                success = await self.product_repo.decrement_stock(product.id, quantity)
                if not success:
                    logger.warning(f"Failed to create order: Concurrent order conflict for {product.name}")
                    raise BadRequestError(
                        f"Not enough stock for {product.name} (concurrent order conflict)"
                    )
                order_item = await self.order_item_repo.create(
                    {
                        "order_id": order.id,
                        "product_id": product.id,
                        "quantity": quantity,
                        "price_at_purchase": product.price,
                    }
                )
                created_items.append(order_item)
                total_price += quantity * product.price
            await self.order_repo.commit()
            logger.info(f"Order {order.id} created successfully")
            ORDERS_CREATED.inc()
        except (NotFoundError, BadRequestError):
            await self.order_repo.roll_back()
            raise
        except Exception as e:
            logger.error(f"Error while creating order: {e}")
            await self.order_repo.roll_back()
            raise
        order.items = created_items
        send_order_confirmation.delay(
            buyer_email=current_user.email, order_id=str(order.id), total_price=total_price
        )
        return order

    async def complete_order(self, order_id: str) -> Order:
        logger.info(f"Completing order: {order_id}")
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            logger.warning(f"Cannot complete order: Order {order_id} not found")
            raise NotFoundError("Order not found")
        if order.status != OrderStatus.ACTIVE:
            logger.warning(f"Cannot complete order: Order {order_id} is not active")
            raise BadRequestError("Only active orders can be completed")
        try:
            updated_order = await self.order_repo.update(order, {"status": OrderStatus.COMPLETED.value})
            await self.order_repo.commit()
            logger.info(f"Order {order_id} completed successfully")
            ORDERS_COMPLETED.inc()

            return updated_order
        except Exception as e:
            logger.error(f"Failed to complete order {order_id}: {e}")
            await self.order_repo.roll_back()
            raise

    async def get_by_id(self, order_id: str) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order not found")
        return order

    async def get_all_by_buyer(
        self, current_user: User, limit: int, offset: int
    ) -> tuple[list[Order], int]:
        orders, count = await self.order_repo.get_all_by_buyer(
            buyer_id=str(current_user.id), limit=limit, offset=offset
        )
        return (orders, count)

    async def get_seller_summary(self, seller_id: str) -> dict:
        summary = await self.order_item_repo.get_seller_summary(seller_id=seller_id)
        return {"seller_id": seller_id, **summary}

    async def cancel_order(self, order_id: str) -> Order:
        logger.info(f"Canceling order: {order_id}")
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            logger.warning(f"Cannot cancel order: Order {order_id} not found")
            raise NotFoundError("Order not found")
        if order.status != OrderStatus.ACTIVE:
            logger.warning(f"Cannot cancel order: Order {order_id} is not active")
            raise BadRequestError("Only active orders can be canceled")
        try:
            order_items = await self.order_item_repo.get_all_by_order_unpaginated(order_id=order.id)
            for item in order_items:
                await self.product_repo.increment_stock(item.product_id, item.quantity)
            updated_order = await self.order_repo.update(order, {"status": OrderStatus.CANCELED.value})
            await self.order_repo.commit()
            logger.info(f"Order {order_id} canceled successfully")
            ORDERS_CANCELED.inc()
            return updated_order
        except (NotFoundError, BadRequestError):
            await self.order_repo.roll_back()
            raise
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            await self.order_repo.roll_back()
            raise


class OrderItemService:
    def __init__(
        self,
        order_repo: OrderRepositoryProtocol,
        order_item_repo: OrderItemRepositoryProtocol,
        product_repo: ProductRepositoryProtocol,
    ) -> None:
        self.order_repo = order_repo
        self.order_item_repo = order_item_repo
        self.product_repo = product_repo

    async def get_items(self, order_id: str, limit: int, offset: int) -> list[OrderItem]:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order not found")
        items, _ = await self.order_item_repo.get_all_by_order(
            order_id=order_id, limit=limit, offset=offset
        )
        return items
