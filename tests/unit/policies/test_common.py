from dataclasses import dataclass

import pytest

from app.core.exceptions import ForbiddenError
from app.policies.common import (
    AllowAllPolicy,
    IsOwnerPolicy,
    IsRoomParticipantPolicy,
)
from tests.factories import ChatRoomFactory, UserFactory


@pytest.mark.unit
def test_allow_all_policy():
    policy = AllowAllPolicy()
    user = UserFactory.build()
    policy.apply(user, None)


@dataclass
class DummyResource:
    user_id: str


@pytest.mark.unit
def test_is_owner_policy():
    policy = IsOwnerPolicy(owner_field="user_id")
    user = UserFactory.build()
    other_user = UserFactory.build()
    resource = DummyResource(user_id=user.id)
    policy.apply(user, resource)
    with pytest.raises(ForbiddenError):
        policy.apply(other_user, resource)


@pytest.mark.unit
def test_is_owner_policy_no_resource():
    policy = IsOwnerPolicy()
    user = UserFactory.build()
    policy.apply(user, None)


@pytest.mark.unit
def test_is_owner_policy_custom_detail():
    policy = IsOwnerPolicy(owner_field="user_id", detail="Custom error")
    user = UserFactory.build()
    other_user = UserFactory.build()
    resource = DummyResource(user_id=other_user.id)
    with pytest.raises(ForbiddenError) as exc:
        policy.apply(user, resource)
    assert exc.value.message == "Custom error"


@pytest.mark.unit
def test_is_room_participant_as_buyer():
    buyer = UserFactory.build()
    room = ChatRoomFactory.build(buyer_id=buyer.id)
    policy = IsRoomParticipantPolicy()
    policy.apply(buyer, room)


@pytest.mark.unit
def test_is_room_participant_as_seller():
    seller = UserFactory.build()
    room = ChatRoomFactory.build(seller_id=seller.id)
    policy = IsRoomParticipantPolicy()
    policy.apply(seller, room)


@pytest.mark.unit
def test_is_room_participant_stranger_forbidden():
    stranger = UserFactory.build()
    room = ChatRoomFactory.build()
    policy = IsRoomParticipantPolicy()
    with pytest.raises(ForbiddenError) as exc:
        policy.apply(stranger, room)
    assert "Access denied" in exc.value.message


@pytest.mark.unit
def test_is_room_participant_no_resource():
    user = UserFactory.build()
    policy = IsRoomParticipantPolicy()
    policy.apply(user, None)
