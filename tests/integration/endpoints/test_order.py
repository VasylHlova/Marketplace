import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.enums.order import OrderStatus
from app.models.order import Order
from app.models.product import Product
from tests.factories import OrderItemFactory


@pytest.mark.asyncio
async def test_read_orders(authorized_client: AsyncClient, test_order: Order):
    response = await authorized_client.get("/orders/?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] >= 1
    assert any(o["id"] == str(test_order.id) for o in data["data"])


@pytest.mark.asyncio
async def test_read_order(authorized_client: AsyncClient, test_order: Order):
    response = await authorized_client.get(f"/orders/{test_order.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(test_order.id)


@pytest.mark.asyncio
async def test_create_order(authorized_client: AsyncClient, test_product: Product):
    response = await authorized_client.post(
        "/orders/", json={"items": [{"product_id": str(test_product.id), "quantity": 1}]}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_cancel_order(authorized_client: AsyncClient, test_order: Order):
    response = await authorized_client.patch(f"/orders/{test_order.id}/cancel")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == OrderStatus.CANCELED.value


@pytest.mark.asyncio
async def test_complete_order(authorized_client: AsyncClient, test_order: Order):
    response = await authorized_client.patch(f"/orders/{test_order.id}/complete")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == OrderStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_read_order_items(
    authorized_client: AsyncClient, db_session, test_order: Order, test_product: Product
):
    item = OrderItemFactory(order_id=str(test_order.id), product_id=str(test_product.id))
    db_session.add(item)
    await db_session.commit()
    response = await authorized_client.get(f"/orders/{test_order.id}/items?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(i["id"] == str(item.id) for i in data)
