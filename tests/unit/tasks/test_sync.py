import pytest
from elasticsearch.exceptions import NotFoundError

from app.tasks.sync import delete_product_from_es, index_product_to_es, update_product_in_es


@pytest.fixture
def mock_search(mocker):
    return mocker.patch("app.tasks.sync.search")


def test_index_product_to_es(mock_search):
    index_product_to_es("123", "Test Product", "Test Description")
    mock_search.index.assert_called_once_with(
        index="marketplace_products",
        id="123",
        document={"name": "Test Product", "description": "Test Description"},
    )


def test_index_product_to_es_null_desc(mock_search):
    index_product_to_es("123", "Test Product", None)
    mock_search.index.assert_called_once_with(
        index="marketplace_products", id="123", document={"name": "Test Product", "description": None}
    )


def test_update_product_in_es(mock_search):
    update_product_in_es("123", "Updated Product", "Updated Description")
    mock_search.update.assert_called_once_with(
        index="marketplace_products",
        id="123",
        body={"doc": {"name": "Updated Product", "description": "Updated Description"}},
    )


def test_update_product_in_es_not_found(mock_search):
    mock_search.update.side_effect = NotFoundError(404, "Not Found", {})
    update_product_in_es("123", "Updated Product", "Updated Description")
    mock_search.update.assert_called_once()


def test_delete_product_from_es(mock_search):
    delete_product_from_es("123")
    mock_search.delete.assert_called_once_with(index="marketplace_products", id="123")


def test_delete_product_from_es_not_found(mock_search):
    mock_search.delete.side_effect = NotFoundError(404, "Not Found", {})
    delete_product_from_es("123")
    mock_search.delete.assert_called_once()
