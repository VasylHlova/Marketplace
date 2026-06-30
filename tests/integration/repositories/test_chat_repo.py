import pytest

from app.models.chat import ChatMessage, ChatRoom
from app.repositories.chat import ChatMessageRepository, ChatRoomRepository


@pytest.mark.asyncio
async def test_chat_room_get_by_users(
    chat_room_repo: ChatRoomRepository, test_user, other_user, db_session
):
    room = ChatRoom(buyer_id=str(test_user.id), seller_id=str(other_user.id))
    db_session.add(room)
    await db_session.commit()

    fetched = await chat_room_repo.get_by_users(str(test_user.id), str(other_user.id))
    assert fetched is not None
    assert fetched.id == room.id


@pytest.mark.asyncio
async def test_chat_room_get_all_by_buyer(
    chat_room_repo: ChatRoomRepository, test_user, other_user, db_session
):
    room = ChatRoom(buyer_id=str(test_user.id), seller_id=str(other_user.id))
    db_session.add(room)
    await db_session.commit()

    rooms, count = await chat_room_repo.get_all_by_buyer(str(test_user.id), limit=10, offset=0)
    assert count >= 1
    assert any(r.id == room.id for r in rooms)


@pytest.mark.asyncio
async def test_chat_room_get_all_by_seller(
    chat_room_repo: ChatRoomRepository, test_user, other_user, db_session
):
    room = ChatRoom(buyer_id=str(test_user.id), seller_id=str(other_user.id))
    db_session.add(room)
    await db_session.commit()

    rooms, count = await chat_room_repo.get_all_by_seller(str(other_user.id), limit=10, offset=0)
    assert count >= 1
    assert any(r.id == room.id for r in rooms)


@pytest.mark.asyncio
async def test_chat_message_get_all_by_room(
    chat_msg_repo: ChatMessageRepository, test_user, other_user, db_session
):
    room = ChatRoom(buyer_id=str(test_user.id), seller_id=str(other_user.id))
    db_session.add(room)
    await db_session.flush()

    msg = ChatMessage(room_id=room.id, sender_id=str(test_user.id), text="Hello")
    db_session.add(msg)
    await db_session.commit()

    messages, count = await chat_msg_repo.get_all_by_room(str(room.id), limit=10, offset=0)
    assert count >= 1
    assert any(m.id == msg.id for m in messages)
