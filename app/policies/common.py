from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass
from app.core.enums.user import UserRole
from app.core.exceptions import ForbiddenError
from app.models.user import User


class AllowAllPolicy:
    def apply(self, current_user: User, resource: Any = None) -> None:
        pass


class IsOwnerPolicy:
    def __init__(
        self, owner_field: str = "seller_id", detail: str = "You are not allowed to perform this action"
    ):
        self.owner_field = owner_field
        self.detail = detail

    def apply(self, current_user: User, resource: Any = None) -> None:
        if resource is None:
            return
        owner_id = getattr(resource, self.owner_field, None)
        if owner_id != current_user.id:
            raise ForbiddenError(self.detail)


class IsRoomParticipantPolicy:
    def apply(self, current_user: User, resource: Any = None) -> None:
        if resource is None:
            return
        buyer_id = str(getattr(resource, "buyer_id", ""))
        seller_id = str(getattr(resource, "seller_id", ""))
        user_id = str(current_user.id)
        if user_id != buyer_id and user_id != seller_id:
            raise ForbiddenError("Access denied to this chat room")


class CanReadOrderPolicy:
    def apply(self, current_user: User, resource: Any = None) -> None:
        if resource is None:
            return
        user_id = str(current_user.id)
        if current_user.role == UserRole.BUYER:
            buyer_id = str(getattr(resource, "buyer_id", ""))
            if user_id != buyer_id:
                raise ForbiddenError("You are not allowed to view this order")
        elif current_user.role == UserRole.SELLER:
            items = getattr(resource, "items", [])
            has_seller_product = any(
                str(getattr(getattr(item, "product", None), "seller_id", "")) == user_id for item in items
            )
            if not has_seller_product:
                raise ForbiddenError("You are not allowed to view this order")
        else:
            raise ForbiddenError("You are not allowed to view this order")
