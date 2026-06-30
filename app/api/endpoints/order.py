from typing import Annotated, Any

from fastapi import APIRouter, Path, status

from app.api.dependencies.current_user import CurrentBuyerDep, CurrentUserDep
from app.api.dependencies.policies import OrderItemPoliciesDep, OrderPoliciesDep
from app.api.dependencies.query_params import LimitDep, OffsetDep
from app.api.dependencies.services import OrderItemServiceDep, OrderServiceDep
from app.core.enums.user import UserRole
from app.schemas.order import (
    OrderBuyerRespond,
    OrderCreate,
    OrderItemRespond,
    OrdersBuyerRespond,
    OrderSellerRespond,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=OrdersBuyerRespond)
async def read_orders(
    service: OrderServiceDep,
    policies: OrderPoliciesDep,
    current_user: CurrentUserDep,
    limit: LimitDep = 100,
    offset: OffsetDep = 0,
) -> Any:
    policies.read.apply(current_user)
    orders, count = await service.get_all_by_buyer(current_user=current_user, limit=limit, offset=offset)
    return {"data": orders, "count": count}


@router.get("/{order_id}")
async def read_order(
    order_id: Annotated[str, Path()],
    service: OrderServiceDep,
    policies: OrderPoliciesDep,
    current_user: CurrentUserDep,
) -> Any:
    order = await service.get_by_id(order_id=order_id)
    policies.read.apply(current_user, order)
    if current_user.role == UserRole.SELLER:
        return OrderSellerRespond.model_validate(order)
    return OrderBuyerRespond.model_validate(order)


@router.post("/", response_model=OrderBuyerRespond, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    service: OrderServiceDep,
    current_buyer: CurrentBuyerDep,
) -> Any:
    return await service.create_order(
        current_user=current_buyer, items=[item.model_dump() for item in order_in.items]
    )


@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: Annotated[str, Path()],
    service: OrderServiceDep,
    policies: OrderPoliciesDep,
    current_buyer: CurrentBuyerDep,
) -> Any:
    order = await service.get_by_id(order_id=order_id)
    policies.cancel.apply(current_buyer, order)
    order = await service.cancel_order(order_id=order_id)
    if current_buyer.role == UserRole.SELLER:
        return OrderSellerRespond.model_validate(order)
    return OrderBuyerRespond.model_validate(order)


@router.patch("/{order_id}/complete")
async def complete_order(
    order_id: Annotated[str, Path()],
    service: OrderServiceDep,
    policies: OrderPoliciesDep,
    current_buyer: CurrentBuyerDep,
) -> Any:
    order = await service.get_by_id(order_id=order_id)
    policies.complete.apply(current_buyer, order)
    order = await service.complete_order(order_id=order_id)
    return OrderBuyerRespond.model_validate(order)


@router.get("/{order_id}/items", response_model=list[OrderItemRespond], tags=["order items"])
async def read_order_items(
    order_id: Annotated[str, Path()],
    service: OrderItemServiceDep,
    order_service: OrderServiceDep,
    policies: OrderItemPoliciesDep,
    current_user: CurrentUserDep,
    limit: LimitDep = 100,
    offset: OffsetDep = 0,
) -> Any:
    order = await order_service.get_by_id(order_id=order_id)
    policies.item.apply(current_user, order)
    return await service.get_items(order_id=order_id, limit=limit, offset=offset)
