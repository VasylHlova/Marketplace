import pytest

from app.core.exceptions import NotFoundError
from tests.unit.dummies import DummyModel


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_product_success(product_service, mock_product_repo, mocker):
    mocker.patch("app.services.product.index_product_to_es.delay")
    user = DummyModel()
    result = await product_service.create(user.id, "Test Product", 10.5, 100, "Test Description")
    assert result.name == "Test Product"
    assert result.price == 10.5
    assert result.stock == 100
    mock_product_repo.create.assert_called_once()
    mock_product_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_product_exception(product_service, mock_product_repo):
    user = DummyModel()
    mock_product_repo.fail_on_create = True
    with pytest.raises(Exception) as exc:
        await product_service.create(user.id, "Test Product", 10.5, 100, "Test Description")
    assert "DB error" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_product_success(product_service, mock_product_repo, mocker):
    mocker.patch("app.services.product.update_product_in_es.delay")
    user = DummyModel()
    product = DummyModel(seller_id=user.id, name="Old Name")
    mock_product_repo.data[product.id] = product
    result = await product_service.update(product.id, {"name": "New Name"})
    assert result.name == "New Name"
    mock_product_repo.update.assert_called_once_with(product, {"name": "New Name"})
    mock_product_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_product_not_found(product_service, mock_product_repo):
    with pytest.raises(NotFoundError) as exc:
        await product_service.update("fake_id", {"name": "New Name"})
    assert exc.value.message == "Product not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_product_exception(product_service, mock_product_repo):
    user = DummyModel()
    product = DummyModel(seller_id=user.id)
    mock_product_repo.data[product.id] = product
    mock_product_repo.fail_on_update = True
    with pytest.raises(Exception) as exc:
        await product_service.update(product.id, {"name": "New Name"})
    assert "DB error" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_product_success(product_service, mock_product_repo, mocker):
    mocker.patch("app.services.product.delete_product_from_es.delay")
    user = DummyModel()
    product = DummyModel(seller_id=user.id)
    mock_product_repo.data[product.id] = product
    await product_service.delete(product.id)
    mock_product_repo.delete.assert_called_once_with(product)
    mock_product_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_product_not_found(product_service, mock_product_repo):
    with pytest.raises(NotFoundError) as exc:
        await product_service.delete("fake_id")
    assert exc.value.message == "Product not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_product_exception(product_service, mock_product_repo):
    user = DummyModel()
    product = DummyModel(seller_id=user.id)
    mock_product_repo.data[product.id] = product
    mock_product_repo.fail_on_delete = True
    with pytest.raises(Exception) as exc:
        await product_service.delete(product.id)
    assert "DB error" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_all_products(product_service, mock_product_repo):
    products = [DummyModel() for _ in range(5)]
    for p in products:
        mock_product_repo.data[p.id] = p
    result, count = await product_service.get_all(limit=10, offset=0)
    assert len(result) == 5
    assert count == 5
    mock_product_repo.get_all.assert_called_once_with(limit=10, offset=0)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_all_products_with_filters(product_service, mock_product_repo):
    products = [DummyModel(price=20.0) for _ in range(5)]
    for p in products:
        mock_product_repo.data[p.id] = p
    result, count = await product_service.get_all(limit=10, offset=0, min_price=10.0, max_price=50.0)
    assert len(result) == 5
    assert count == 5
    mock_product_repo.get_all_filtered_by_price.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_by_id_success(product_service, mock_product_repo):
    product = DummyModel()
    mock_product_repo.data[product.id] = product
    result = await product_service.get_by_id(product.id)
    assert result == product
    mock_product_repo.get_by_id.assert_called_once_with(product.id)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_by_id_not_found(product_service, mock_product_repo):
    with pytest.raises(NotFoundError) as exc:
        await product_service.get_by_id("fake_id")
    assert exc.value.message == "Product not found"
