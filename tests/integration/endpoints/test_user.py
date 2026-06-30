import uuid
from datetime import timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.config import settings
from app.core.enums.user import UserRole
from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_user(async_client: AsyncClient):
    unique_email = f"test_{uuid.uuid4()}@example.com"
    response = await async_client.post(
        "/users/signup",
        json={"email": unique_email, "password": "password123", "role": UserRole.BUYER.value},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == unique_email


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_user_self(authorized_client: AsyncClient, test_user: User):
    response = await authorized_client.get("/users/self")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == test_user.email


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_self(authorized_client: AsyncClient, test_user: User):
    new_email = f"updated_{uuid.uuid4()}@example.com"
    response = await authorized_client.patch("/users/self", json={"email": new_email})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == new_email


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user_self(authorized_client: AsyncClient, test_user: User):
    response = await authorized_client.delete("/users/self")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_password(async_client: AsyncClient, test_user_with_password: User):
    access_token = create_access_token(
        subject=str(test_user_with_password.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    response = await async_client.patch(
        "/users/me/password", json={"current_password": "oldpassword", "new_password": "newpassword123"}
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_avatar_upload_url(authorized_client: AsyncClient, test_user: User):
    response = await authorized_client.post(
        "/users/self/avatar-upload-url", json={"file_name": "avatar.png", "file_type": "image/png"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "url" in data
    assert "fields" in data
    assert "Content-Type" in data["fields"]
