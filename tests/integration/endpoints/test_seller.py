from datetime import timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.config import settings
from app.core.enums.user import UserRole
from app.core.security import create_access_token
from app.models.user import User
from tests.factories import OrderFactory, OrderItemFactory, ProductFactory, UserFactory


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seller_summary_by_id(authorized_client: AsyncClient, test_user: User, db_session):
    product = ProductFactory(seller_id=str(test_user.id))
    db_session.add(product)
    await db_session.commit()
    order = OrderFactory(buyer_id=str(test_user.id))
    db_session.add(order)
    await db_session.commit()
    item = OrderItemFactory(
        order_id=str(order.id), product_id=str(product.id), quantity=2, price_at_purchase=50.0
    )
    db_session.add(item)
    await db_session.commit()
    response = await authorized_client.get(f"/sellers/{test_user.id}/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["seller_id"] == str(test_user.id)
    assert data["total_revenue"] == 100.0
    assert data["total_orders"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seller_summary_requires_auth(async_client: AsyncClient):
    response = await async_client.get("/sellers/some-seller-id/summary")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_seller_summary_accessible_by_buyer(async_client: AsyncClient, test_user: User, db_session):
    buyer = UserFactory(role=UserRole.BUYER.value)
    db_session.add(buyer)
    await db_session.commit()
    access_token = create_access_token(
        subject=str(buyer.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    response = await async_client.get(f"/sellers/{test_user.id}/summary")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["seller_id"] == str(test_user.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_sellers(authorized_client: AsyncClient, db_session):
    seller = UserFactory(role=UserRole.SELLER.value)
    db_session.add(seller)
    await db_session.commit()
    response = await authorized_client.get("/sellers/?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] >= 1
    assert any(s["id"] == str(seller.id) for s in data["data"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_sellers_requires_auth(async_client: AsyncClient):
    response = await async_client.get("/sellers/?limit=10&offset=0")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
