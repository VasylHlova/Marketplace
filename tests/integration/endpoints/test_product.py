import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.product import Product
from app.models.user import User
from tests.factories import ProductFactory


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_product(seller_client: AsyncClient, test_seller: User):
    response = await seller_client.post(
        "/products/", json={"name": "New Item", "price": 10.5, "stock": 100}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Item"
    assert data["price"] == 10.5
    assert data["stock"] == 100
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_products_public_no_auth(async_client: AsyncClient, test_product: Product):
    response = await async_client.get("/products/?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] >= 1
    assert any(p["id"] == str(test_product.id) for p in data["data"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_products_with_price_filter(async_client: AsyncClient, test_product: Product):
    response = await async_client.get(
        f"/products/?limit=10&offset=0&min_price={test_product.price}&max_price={test_product.price}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_product(seller_client: AsyncClient, test_product: Product):
    response = await seller_client.get(f"/products/{test_product.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(test_product.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_product(seller_client: AsyncClient, test_seller: User, db_session):
    product = ProductFactory(seller_id=str(test_seller.id))
    db_session.add(product)
    await db_session.commit()
    response = await seller_client.patch(f"/products/{product.id}", json={"name": "Updated Item"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated Item"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_product(seller_client: AsyncClient, test_seller: User, db_session):
    product = ProductFactory(seller_id=str(test_seller.id))
    db_session.add(product)
    await db_session.commit()
    response = await seller_client.delete(f"/products/{product.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_product_image_upload_url(seller_client: AsyncClient, test_seller: User, db_session):
    product = ProductFactory(seller_id=str(test_seller.id))
    db_session.add(product)
    await db_session.commit()
    response = await seller_client.post(
        f"/products/{product.id}/image-upload-url", json={"file_name": "test.png", "file_type": "image/png"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "url" in data
    assert "fields" in data
    assert "Content-Type" in data["fields"]
