import pytest

from app.models.product import Product
from app.repositories.product import ProductRepository


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_all_by_seller(product_repo: ProductRepository, test_user, test_product):
    items, count = await product_repo.get_all_by_seller(str(test_user.id), limit=10, offset=0)
    assert count >= 1
    assert any(p.id == test_product.id for p in items)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_by_ids(product_repo: ProductRepository, test_products):
    ids = [p.id for p in test_products]
    items, count = await product_repo.get_by_ids(limit=10, offset=0, ids=ids)
    assert count >= 1
    assert any(p.id == test_products[0].id for p in items)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_all_filtered_by_price(product_repo: ProductRepository, test_product):
    items, count = await product_repo.get_all_filtered_by_price(
        limit=10, offset=0, filters=[Product.price >= 50.0]
    )
    assert count >= 1
    assert any(p.id == test_product.id for p in items)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_decrement_stock_success(product_repo: ProductRepository, test_product):
    initial_stock = test_product.stock
    success = await product_repo.decrement_stock(test_product.id, quantity=1)
    assert success is True
    await product_repo.session.refresh(test_product)
    assert test_product.stock == initial_stock - 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_decrement_stock_insufficient(product_repo: ProductRepository, test_product):
    success = await product_repo.decrement_stock(test_product.id, quantity=1000000)
    assert success is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_increment_stock_success(product_repo: ProductRepository, test_product):
    initial_stock = test_product.stock
    success = await product_repo.increment_stock(test_product.id, quantity=5)
    assert success is True
    await product_repo.session.refresh(test_product)
    assert test_product.stock == initial_stock + 5
