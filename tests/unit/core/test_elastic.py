import pytest
from elasticsearch.exceptions import NotFoundError

from app.core.search import search_products_in_es


@pytest.fixture
def mock_search(mocker):
    return mocker.patch("app.core.search.search")


@pytest.mark.unit
def test_search_products_in_es_with_query(mock_search):
    mock_search.search.return_value = {"hits": {"total": {"value": 1}, "hits": [{"_id": "123"}]}}
    ids, total = search_products_in_es(query="test_query", limit=10, offset=0)
    assert ids == ["123"]
    assert total == 1
    mock_search.search.assert_called_once_with(
        index="marketplace_products",
        body={
            "from": 0,
            "size": 10,
            "query": {
                "multi_match": {
                    "query": "test_query",
                    "fields": ["name", "description"],
                    "fuzziness": "AUTO",
                }
            },
        },
    )


@pytest.mark.unit
def test_search_products_in_es_no_query(mock_search):
    mock_search.search.return_value = {"hits": {"total": {"value": 1}, "hits": [{"_id": "123"}]}}
    ids, total = search_products_in_es(limit=10, offset=0)
    assert ids == ["123"]
    assert total == 1
    mock_search.search.assert_called_once_with(
        index="marketplace_products", body={"from": 0, "size": 10, "query": {"match_all": {}}}
    )


@pytest.mark.unit
def test_search_products_in_es_not_found(mock_search):
    mock_search.search.side_effect = NotFoundError(404, "Not Found", {})
    ids, total = search_products_in_es("test_query", limit=10, offset=0)
    assert ids == []
    assert total == 0


@pytest.mark.unit
def test_search_products_in_es_total_int(mock_search):
    mock_search.search.return_value = {"hits": {"total": 1, "hits": [{"_id": "123"}]}}
    ids, total = search_products_in_es("test_query", limit=10, offset=0)
    assert ids == ["123"]
    assert total == 1
