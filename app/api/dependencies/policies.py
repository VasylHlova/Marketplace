from typing import Annotated

from fastapi import Depends

from app.policies.common import (
    AllowAllPolicy,
    CanReadOrderPolicy,
    IsOwnerPolicy,
    IsRoomParticipantPolicy,
)
from app.policies.policy_set import PolicySet


def get_user_policies() -> PolicySet:
    return PolicySet(update=IsOwnerPolicy(owner_field="id"), delete=IsOwnerPolicy(owner_field="id"))


def get_product_policies() -> PolicySet:
    return PolicySet(
        read=AllowAllPolicy(),
        update=IsOwnerPolicy(owner_field="seller_id"),
        delete=IsOwnerPolicy(owner_field="seller_id"),
    )


def get_order_policies() -> PolicySet:
    return PolicySet(
        read=CanReadOrderPolicy(),
        cancel=IsOwnerPolicy(owner_field="buyer_id"),
        complete=IsOwnerPolicy(owner_field="buyer_id"),
    )


def get_order_item_policies() -> PolicySet:
    return PolicySet(item=IsOwnerPolicy(owner_field="buyer_id"))


def get_chat_policies() -> PolicySet:
    return PolicySet(read=IsRoomParticipantPolicy())


UserPoliciesDep = Annotated[PolicySet, Depends(get_user_policies)]
ProductPoliciesDep = Annotated[PolicySet, Depends(get_product_policies)]
OrderPoliciesDep = Annotated[PolicySet, Depends(get_order_policies)]
OrderItemPoliciesDep = Annotated[PolicySet, Depends(get_order_item_policies)]
ChatPoliciesDep = Annotated[PolicySet, Depends(get_chat_policies)]
