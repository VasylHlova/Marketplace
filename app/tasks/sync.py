from elasticsearch.exceptions import ConnectionError, ConnectionTimeout, NotFoundError

from app.core.celery import celery_app
from app.db.elastic import search


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, ConnectionTimeout),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_jitter=True,
)
def index_product_to_es(self, product_id: str, name: str, description: str | None):
    document = {"name": name, "description": description}
    search.index(index="marketplace_products", id=str(product_id), document=document)


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, ConnectionTimeout),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_jitter=True,
)
def update_product_in_es(self, product_id: str, name: str, description: str | None):
    document = {"doc": {"name": name, "description": description}}
    try:
        search.update(index="marketplace_products", id=str(product_id), body=document)
    except NotFoundError:
        pass


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, ConnectionTimeout),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_jitter=True,
)
def delete_product_from_es(self, product_id: str):
    try:
        search.delete(index="marketplace_products", id=str(product_id))
    except NotFoundError:
        pass
