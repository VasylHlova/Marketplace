import asyncio

from loguru import logger

from app.core.exceptions import NotFoundError
from app.core.metrics import PRODUCT_SEARCHES, PRODUCTS_CREATED
from app.core.search import search_products_in_es
from app.models.product import Product
from app.repositories import ProductRepositoryProtocol
from app.tasks.sync import delete_product_from_es, index_product_to_es, update_product_in_es


class ProductService:
    def __init__(self, repo: ProductRepositoryProtocol) -> None:
        self.repo = repo

    async def create(
        self, seller_id: str, name: str, price: float, stock: int, description: str | None
    ) -> Product:
        logger.info(f"Creating product '{name}' for seller {seller_id}")
        try:
            product = await self.repo.create(
                {
                    "seller_id": seller_id,
                    "name": name,
                    "price": price,
                    "stock": stock,
                    "description": description,
                }
            )
            await self.repo.commit()
            PRODUCTS_CREATED.inc()
            logger.info(f"Product '{name}' created successfully with ID {product.id}")

        except Exception as e:
            logger.error(f"Failed to create product '{name}': {e}")
            await self.repo.roll_back()
            raise
        index_product_to_es.delay(product_id=str(product.id), name=name, description=description)
        return product

    async def update(self, product_id: str, update_data: dict) -> Product:
        logger.info(f"Updating product {product_id}")
        product = await self.repo.get_by_id(id=product_id)
        if not product:
            logger.warning(f"Failed to update product: {product_id} not found")
            raise NotFoundError("Product not found")
        try:
            updated_product = await self.repo.update(product, update_data)
            await self.repo.commit()
            logger.info(f"Product {product_id} updated successfully")
        except Exception as e:
            logger.error(f"Failed to update product {product_id}: {e}")
            await self.repo.roll_back()
            raise
        if "name" in update_data or "description" in update_data:
            update_product_in_es.delay(
                product_id=str(updated_product.id),
                name=updated_product.name,
                description=getattr(updated_product, "description", None),
            )
        return updated_product

    async def delete(self, product_id: str) -> None:
        logger.info(f"Deleting product {product_id}")
        product = await self.repo.get_by_id(product_id)
        if not product:
            logger.warning(f"Failed to delete product: {product_id} not found")
            raise NotFoundError("Product not found")
        try:
            await self.repo.delete(product)
            await self.repo.commit()
            logger.info(f"Product {product_id} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            await self.repo.roll_back()
            raise
        delete_product_from_es.delay(product_id=str(product_id))

    async def get_all(
        self, limit: int, offset: int, max_price: float | None = None, min_price: float | None = None
    ) -> tuple[list[Product], int]:
        filters = []
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)
        if filters:
            return await self.repo.get_all_filtered_by_price(limit=limit, offset=offset, filters=filters)
        return await self.repo.get_all(limit=limit, offset=offset)

    async def get_by_id(self, product_id: str) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return product

    async def search(self, query: str | None, limit: int, offset: int) -> tuple[list[Product], int]:
        logger.info(f"Searching products with query: '{query}'")
        PRODUCT_SEARCHES.inc()
        product_ids, total = await asyncio.to_thread(search_products_in_es, query, limit, offset)
        if not product_ids:
            logger.warning(f"No products found for query: '{query}'")
            raise NotFoundError("Product not found")

        products, count = await self.repo.get_by_ids(limit=limit, offset=offset, ids=product_ids)

        return (products, count)
