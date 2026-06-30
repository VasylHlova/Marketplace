import pytest

from app.core.enums.order import OrderStatus
from app.core.exceptions import BadRequestError, NotFoundError
from tests.unit.dummies import DummyModel


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_success(
    order_service, mock_order_repo, mock_order_item_repo, mock_product_repo, mocker
):
    user = DummyModel(email="user@example.com")
    product = DummyModel(stock=10, price=100.0, name="Prod")
    mock_product_repo.data[product.id] = product
    mocker.patch("app.services.order.send_order_confirmation.delay")
    result = await order_service.create_order(user, [{"product_id": product.id, "quantity": 2}])
    assert result.buyer_id == user.id
    assert result.status == OrderStatus.ACTIVE.value
    mock_order_repo.create.assert_called_once()
    mock_order_item_repo.create.assert_called_once()
    mock_order_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_empty_items(order_service):
    user = DummyModel()
    with pytest.raises(BadRequestError) as exc:
        await order_service.create_order(user, [])
    assert "at least one item" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_product_not_found(order_service, mock_product_repo):
    user = DummyModel()
    with pytest.raises(NotFoundError) as exc:
        await order_service.create_order(user, [{"product_id": "fake", "quantity": 2}])
    assert "not found" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_product_out_of_stock_zero(order_service, mock_product_repo):
    user = DummyModel()
    product = DummyModel(stock=0, name="Prod")
    mock_product_repo.data[product.id] = product
    with pytest.raises(BadRequestError) as exc:
        await order_service.create_order(user, [{"product_id": product.id, "quantity": 2}])
    assert "out of stock" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_quantity_invalid(order_service, mock_product_repo):
    user = DummyModel()
    product = DummyModel(stock=5, name="Prod")
    mock_product_repo.data[product.id] = product
    with pytest.raises(BadRequestError) as exc:
        await order_service.create_order(user, [{"product_id": product.id, "quantity": 0}])
    assert "greater than 0" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_not_enough_stock(order_service, mock_product_repo):
    user = DummyModel()
    product = DummyModel(stock=1, name="Prod")
    mock_product_repo.data[product.id] = product
    with pytest.raises(BadRequestError) as exc:
        await order_service.create_order(user, [{"product_id": product.id, "quantity": 2}])
    assert "Not enough stock" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_order_db_exception(order_service, mock_product_repo, mock_order_repo):
    user = DummyModel()
    product = DummyModel(stock=10, name="Prod")
    mock_product_repo.data[product.id] = product
    mock_order_repo.fail_on_create = True
    with pytest.raises(Exception) as exc:
        await order_service.create_order(user, [{"product_id": product.id, "quantity": 2}])
    assert "DB error" in str(exc.value)
    mock_order_repo.roll_back.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_order_success(
    order_service, mock_order_repo, mock_order_item_repo, mock_product_repo
):
    user = DummyModel()
    order = DummyModel(buyer_id=user.id, status=OrderStatus.ACTIVE.value)
    product = DummyModel(stock=5)
    order_item = DummyModel(order_id=order.id, product_id=product.id, quantity=2)
    mock_order_repo.data[order.id] = order
    mock_order_item_repo.data[order_item.id] = order_item
    mock_product_repo.data[product.id] = product
    result = await order_service.cancel_order(order.id)
    assert result.status == OrderStatus.CANCELED.value
    mock_product_repo.increment_stock.assert_called_once_with(product.id, 2)
    mock_order_repo.update.assert_called_once()
    mock_order_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_order_not_found(order_service, mock_order_repo):
    with pytest.raises(NotFoundError) as exc:
        await order_service.cancel_order("fake_id")
    assert exc.value.message == "Order not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_order_already_canceled(order_service, mock_order_repo):
    order = DummyModel(status=OrderStatus.CANCELED.value)
    mock_order_repo.data[order.id] = order
    with pytest.raises(BadRequestError) as exc:
        await order_service.cancel_order(order.id)
    assert "Only active orders can be canceled" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_order_db_exception(
    order_service, mock_order_repo, mock_order_item_repo, mock_product_repo
):
    user = DummyModel()
    order = DummyModel(buyer_id=user.id, status=OrderStatus.ACTIVE.value)
    order_item = DummyModel(order_id=order.id, quantity=2, product_id="fake")
    mock_order_repo.data[order.id] = order
    mock_order_item_repo.data[order_item.id] = order_item
    mock_order_repo.fail_on_update = True
    with pytest.raises(Exception) as exc:
        await order_service.cancel_order(order.id)
    assert "DB error" in str(exc.value)
    mock_order_repo.roll_back.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complete_order_success(order_service, mock_order_repo):
    order = DummyModel(status=OrderStatus.ACTIVE.value)
    mock_order_repo.data[order.id] = order
    result = await order_service.complete_order(order.id)
    assert result.status == OrderStatus.COMPLETED.value
    mock_order_repo.update.assert_called_once()
    mock_order_repo.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complete_order_not_found(order_service, mock_order_repo):
    with pytest.raises(NotFoundError) as exc:
        await order_service.complete_order("fake_id")
    assert exc.value.message == "Order not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complete_order_not_active(order_service, mock_order_repo):
    order = DummyModel(status=OrderStatus.CANCELED.value)
    mock_order_repo.data[order.id] = order
    with pytest.raises(BadRequestError) as exc:
        await order_service.complete_order(order.id)
    assert "Only active orders" in exc.value.message


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complete_order_db_exception(order_service, mock_order_repo):
    order = DummyModel(status=OrderStatus.ACTIVE.value)
    mock_order_repo.data[order.id] = order
    mock_order_repo.fail_on_update = True
    with pytest.raises(Exception) as exc:
        await order_service.complete_order(order.id)
    assert "DB error" in str(exc.value)
    mock_order_repo.roll_back.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_by_id_success(order_service, mock_order_repo):
    order = DummyModel()
    mock_order_repo.data[order.id] = order
    result = await order_service.get_by_id(order.id)
    assert result.id == order.id
    mock_order_repo.get_by_id.assert_called_once_with(order.id)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_by_id_not_found(order_service, mock_order_repo):
    with pytest.raises(NotFoundError) as exc:
        await order_service.get_by_id("fake_id")
    assert exc.value.message == "Order not found"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_all_by_buyer(order_service, mock_order_repo):
    user = DummyModel()
    orders = [DummyModel(buyer_id=str(user.id)) for _ in range(3)]
    for o in orders:
        mock_order_repo.data[o.id] = o
    result, count = await order_service.get_all_by_buyer(user, limit=10, offset=0)
    assert len(result) == 3
    assert count == 3
    mock_order_repo.get_all_by_buyer.assert_called_once_with(buyer_id=str(user.id), limit=10, offset=0)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_seller_summary(order_service, mock_order_item_repo):
    user = DummyModel()
    result = await order_service.get_seller_summary(str(user.id))
    assert result == {"seller_id": str(user.id), "total_orders": 3, "total_revenue": 150.0}
    mock_order_item_repo.get_seller_summary.assert_called_once_with(seller_id=str(user.id))


@pytest.mark.asyncio
@pytest.mark.unit
async def test_order_item_get_items_success(order_item_service, mock_order_repo, mock_order_item_repo):
    order = DummyModel()
    mock_order_repo.data[order.id] = order
    items = [DummyModel(order_id=order.id) for _ in range(2)]
    for i in items:
        mock_order_item_repo.data[i.id] = i
    result = await order_item_service.get_items(order.id, limit=10, offset=0)
    assert len(result) == 2
    mock_order_item_repo.get_all_by_order.assert_called_once_with(order_id=order.id, limit=10, offset=0)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_order_item_get_items_not_found(order_item_service, mock_order_repo):
    with pytest.raises(NotFoundError) as exc:
        await order_item_service.get_items("fake_id", limit=10, offset=0)
    assert exc.value.message == "Order not found"
