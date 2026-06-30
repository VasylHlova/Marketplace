import pytest

from app.models.order import OrderItem
from app.repositories.order import OrderItemRepository, OrderRepository


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_get_all_by_buyer(order_repo: OrderRepository, test_user, test_order):
    orders, count = await order_repo.get_all_by_buyer(str(test_user.id), limit=10, offset=0)
    assert count >= 1
    assert any(o.id == test_order.id for o in orders)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_item_get_all_by_order(
    order_item_repo: OrderItemRepository, db_session, test_order, test_product
):
    item = OrderItem(order_id=test_order.id, product_id=test_product.id, quantity=2, price_at_purchase=50.0)
    db_session.add(item)
    await db_session.commit()

    items, count = await order_item_repo.get_all_by_order(str(test_order.id), limit=10, offset=0)
    assert count >= 1
    assert any(i.id == item.id for i in items)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_order_item_get_seller_summary(
    order_item_repo: OrderItemRepository, db_session, test_order, test_product, test_user
):
    item = OrderItem(order_id=test_order.id, product_id=test_product.id, quantity=2, price_at_purchase=50.0)
    db_session.add(item)
    await db_session.commit()

    summary = await order_item_repo.get_seller_summary(str(test_user.id))
    assert summary["total_orders"] >= 1
    assert summary["total_revenue"] >= 100.0
