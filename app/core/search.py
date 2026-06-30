from elasticsearch.exceptions import NotFoundError

from app.db.elastic import search


def search_products_in_es(query: str | None = None, limit: int = 10, offset: int = 0):
    es_query = (
        {"multi_match": {"query": query, "fields": ["name", "description"], "fuzziness": "AUTO"}}
        if query
        else {"match_all": {}}
    )
    body = {"from": offset, "size": limit, "query": es_query}
    try:
        result = search.search(index="marketplace_products", body=body)
        hits = result["hits"]["hits"]
        total_obj = result["hits"]["total"]
        total = total_obj["value"] if isinstance(total_obj, dict) else total_obj
        return ([hit["_id"] for hit in hits], total)
    except NotFoundError:
        return ([], 0)
