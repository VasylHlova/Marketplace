import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login(async_client: AsyncClient, test_user_with_password: User):
    response = await async_client.post(
        "/login",
        data={"username": test_user_with_password.email, "password": "oldpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_token(async_client: AsyncClient, test_user_with_password: User):
    login_resp = await async_client.post(
        "/login",
        data={"username": test_user_with_password.email, "password": "oldpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    refresh_token = login_resp.cookies.get("refresh_token")
    async_client.cookies.set("refresh_token", refresh_token)
    response = await async_client.post("/refresh")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout(async_client: AsyncClient, test_user_with_password: User):
    login_resp = await async_client.post(
        "/login",
        data={"username": test_user_with_password.email, "password": "oldpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    refresh_token = login_resp.cookies.get("refresh_token")
    async_client.cookies.set("refresh_token", refresh_token)
    response = await async_client.post("/logout")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert "refresh_token" not in response.cookies
