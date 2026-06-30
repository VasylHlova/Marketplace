from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, status

from app.api.dependencies.current_user import CurrentSellerDep, CurrentUserDep
from app.api.dependencies.policies import ProductPoliciesDep
from app.api.dependencies.query_params import LimitDep, OffsetDep
from app.api.dependencies.services import MediaServiceDep, ProductServiceDep
from app.core.enums.user import UserRole
from app.schemas.media import UploadUrlRequest, UploadUrlResponse
from app.schemas.product import ProductCreate, ProductOwner, ProductPublic, ProductsPublic, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductsPublic)
async def read_products(
    service: ProductServiceDep,
    offset: OffsetDep = 0,
    limit: LimitDep = 100,
    min_price: float | None = None,
    max_price: float | None = None,
) -> Any:
    products, count = await service.get_all(
        limit=limit, offset=offset, min_price=min_price, max_price=max_price
    )
    return ProductsPublic(data=[ProductPublic.model_validate(p) for p in products], count=count)


@router.post("/", response_model=ProductOwner, status_code=status.HTTP_201_CREATED)
async def create_product(
    service: ProductServiceDep, current_seller: CurrentSellerDep, product_in: ProductCreate
) -> Any:
    return await service.create(
        seller_id=str(current_seller.id),
        name=product_in.name,
        price=product_in.price,
        stock=product_in.stock,
        description=product_in.description,
    )


@router.get("/search", response_model=ProductsPublic)
async def search_products(
    service: ProductServiceDep,
    query: Annotated[str, Query(description="Enter search query(name or decsription of a desired poduct)")],
    offset: OffsetDep = 0,
    limit: LimitDep = 100,
) -> Any:
    products, count = await service.search(query=query, limit=limit, offset=offset)
    return ProductsPublic(data=[ProductPublic.model_validate(p) for p in products], count=count)


@router.get("/{product_id}")
async def read_product(
    product_id: Annotated[str, Path()],
    service: ProductServiceDep,
    policies: ProductPoliciesDep,
    current_user: CurrentUserDep,
) -> Any:
    product = await service.get_by_id(product_id=product_id)
    policies.read.apply(current_user, product)
    if current_user.role == UserRole.SELLER:
        return ProductOwner.model_validate(product)
    return ProductPublic.model_validate(product)


@router.patch("/{product_id}", response_model=ProductOwner)
async def update_product(
    product_id: Annotated[str, Path()],
    product_in: ProductUpdate,
    service: ProductServiceDep,
    policies: ProductPoliciesDep,
    current_user: CurrentUserDep,
) -> Any:
    product = await service.get_by_id(product_id=product_id)
    policies.update.apply(current_user, product)
    return await service.update(
        product_id=product_id, update_data=product_in.model_dump(exclude_unset=True)
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: Annotated[str, Path()],
    service: ProductServiceDep,
    policies: ProductPoliciesDep,
    current_user: CurrentUserDep,
) -> None:
    product = await service.get_by_id(product_id=product_id)
    policies.delete.apply(current_user, product)
    await service.delete(product_id=product_id)


@router.post("/{product_id}/image-upload-url", response_model=UploadUrlResponse)
async def get_product_image_upload_url(
    product_id: Annotated[str, Path()],
    upload_req: UploadUrlRequest,
    product_service: ProductServiceDep,
    policies: ProductPoliciesDep,
    media_service: MediaServiceDep,
    current_seller: CurrentSellerDep,
) -> Any:
    product = await product_service.get_by_id(product_id)
    policies.update.apply(current_seller, product)
    object_key = f"products/{product_id}/{upload_req.file_name}"
    presigned_post = await media_service.generate_presigned_upload_post(
        object_name=object_key, file_type=upload_req.file_type
    )
    return presigned_post
