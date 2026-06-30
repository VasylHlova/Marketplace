from elasticsearch import Elasticsearch

from app.core.config import settings

search = Elasticsearch(hosts=[settings.ELASTIC_SEARCH_URL])
