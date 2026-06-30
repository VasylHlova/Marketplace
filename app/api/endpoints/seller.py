from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path

from app.api.dependencies.current_user import CurrentUserDep, get_current_user
from app.api.dependencies.query_params import LimitDep, OffsetDep
from app.api.dependencies.services import OrderServiceDep, UserServiceDep
from app.schemas.order import SellerSummaryRespond
from app.schemas.user import UserRespond, UsersRespond

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.get("/", response_model=UsersRespond, dependencies=[Depends(get_current_user)])
async def list_sellers(service: UserServiceDep, limit: LimitDep = 100, offset: OffsetDep = 0) -> Any:
    sellers, count = await service.get_sellers(limit=limit, offset=offset)
    return UsersRespond(data=[UserRespond.model_validate(s) for s in sellers], count=count)


@router.get("/{seller_id}/summary", response_model=SellerSummaryRespond)
async def get_seller_summary(
    seller_id: Annotated[str, Path()], service: OrderServiceDep, current_user: CurrentUserDep
) -> Any:
    return await service.get_seller_summary(seller_id=seller_id)
