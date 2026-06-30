import pytest

from app.core.enums.user import UserRole
from app.core.exceptions import BadRequestError
from tests.unit.dummies import DummyModel


@pytest.mark.asyncio
async def test_create_room_success(chat_service, mock_room_repo):
    buyer = DummyModel(id="b1", role=UserRole.BUYER.value)
    seller = DummyModel(id="s1")
    result = await chat_service.create_room(seller.id, buyer)
    assert result.buyer_id == buyer.id
    assert result.seller_id == seller.id
    mock_room_repo.create.assert_called_once()
    mock_room_repo.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_room_existing(chat_service, mock_room_repo):
    buyer = DummyModel(id="b1", role=UserRole.BUYER.value)
    seller = DummyModel(id="s1")
    room = DummyModel(buyer_id=buyer.id, seller_id=seller.id)
    mock_room_repo.data[room.id] = room
    result = await chat_service.create_room(seller.id, buyer)
    assert result.id == room.id
    mock_room_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_room_exception(chat_service, mock_room_repo):
    buyer = DummyModel(id="b1", role=UserRole.BUYER.value)
    seller = DummyModel(id="s1")
    mock_room_repo.fail_on_create = True
    with pytest.raises(Exception) as exc:
        await chat_service.create_room(seller.id, buyer)
    assert "db error" in str(exc.value).lower()
    mock_room_repo.roll_back.assert_called_once()


@pytest.mark.asyncio
async def test_create_room_with_self(chat_service, mock_room_repo):
    buyer = DummyModel(id="b1", role=UserRole.BUYER.value)
    with pytest.raises(BadRequestError) as exc:
        await chat_service.create_room(buyer.id, buyer)
    assert "You cannot create a chat room with yourself" in exc.value.message


@pytest.mark.asyncio
async def test_get_chat_history_success(chat_service, mock_room_repo, mock_msg_repo):
    room = DummyModel()
    messages = [DummyModel(room_id=room.id) for _ in range(5)]
    mock_room_repo.data[room.id] = room
    for m in messages:
        mock_msg_repo.data[m.id] = m
    result = await chat_service.get_chat_history(room.id, limit=10, offset=0)
    assert len(result) == 5
    mock_msg_repo.get_all_by_room.assert_called_once_with(room_id=room.id, limit=10, offset=0)


@pytest.mark.asyncio
async def test_save_message_success(chat_service, mock_msg_repo, mocker):
    user = DummyModel(id="user_id_1")
    room_id = "room_id_1"
    created_message = DummyModel(id="msg_1", room_id=room_id, text="hello")
    mock_msg_repo.create = mocker.AsyncMock(return_value=created_message)
    result = await chat_service.save_message(
        room_id, "hello", user, attachment_url="http://example.com/img.jpg"
    )
    mock_msg_repo.create.assert_called_once_with(
        {
            "room_id": room_id,
            "sender_id": user.id,
            "text": "hello",
            "attachment_url": "http://example.com/img.jpg",
        }
    )
    mock_msg_repo.commit.assert_called_once()
    assert result.id == "msg_1"
