import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.chat import ChatRoom
from app.models.user import User
from tests.factories import ChatMessageFactory


@pytest.mark.asyncio
async def test_create_chat_room(authorized_client: AsyncClient, other_user: User):
    response = await authorized_client.post("/chat/", json={"seller_id": str(other_user.id)})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_get_chat_history(
    authorized_client: AsyncClient, db_session, test_room: ChatRoom, test_user: User
):
    msg = ChatMessageFactory(room_id=str(test_room.id), sender_id=str(test_user.id))
    db_session.add(msg)
    await db_session.commit()
    response = await authorized_client.get(f"/chat/{test_room.id}/history?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(m["id"] == str(msg.id) for m in data)


@pytest.mark.asyncio
async def test_get_chat_attachment_upload_url(
    authorized_client: AsyncClient, test_room: ChatRoom, test_user: User
):
    response = await authorized_client.post(
        f"/chat/{test_room.id}/attachment-url", json={"file_name": "file.png", "file_type": "image/png"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "url" in data
    assert "fields" in data
    assert "Content-Type" in data["fields"]
