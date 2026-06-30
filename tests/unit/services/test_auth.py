import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import get_password_hash
from tests.unit.dummies import DummyModel


@pytest.mark.asyncio
async def test_authenticate_success(auth_service, mock_user_repo, mocker):
    password = "password123"
    hashed = get_password_hash(password)
    user = DummyModel(email="test@example.com", password=hashed)
    mock_user_repo.data[user.id] = user
    result = await auth_service.authenticate("test@example.com", password)
    assert result == user
    mock_user_repo.get_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service, mock_user_repo):
    with pytest.raises(UnauthorizedError) as exc:
        await auth_service.authenticate("test@example.com", "password")
    assert "User not found" in exc.value.message


@pytest.mark.asyncio
async def test_authenticate_invalid_credentials(auth_service, mock_user_repo):
    hashed = get_password_hash("realpassword")
    user = DummyModel(email="test@example.com", password=hashed)
    mock_user_repo.data[user.id] = user
    with pytest.raises(UnauthorizedError) as exc:
        await auth_service.authenticate("test@example.com", "wrongpassword")
    assert "Invalid credentials" in exc.value.message


@pytest.mark.asyncio
async def test_login_success(auth_service, mock_user_repo, mock_token_repo):
    password = "password123"
    hashed = get_password_hash(password)
    user = DummyModel(email="test@example.com", password=hashed)
    mock_user_repo.data[user.id] = user
    access_token, refresh_token = await auth_service.login("test@example.com", password)
    assert access_token is not None
    assert refresh_token is not None
    decoded = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    key = f"refresh_token:{user.id}:{decoded['jti']}"
    assert mock_token_repo.data.get(key) == "active"


@pytest.mark.asyncio
async def test_refresh_success(auth_service, mock_user_repo, mock_token_repo):
    user_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=1)
    payload = {"sub": user_id, "exp": expire, "jti": jti, "type": "refresh"}
    refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    key = f"refresh_token:{user_id}:{jti}"
    mock_token_repo.data[key] = "active"
    new_access, new_refresh = await auth_service.refresh(refresh_token)
    assert new_access is not None
    assert new_refresh is not None
    assert key not in mock_token_repo.data
    decoded = jwt.decode(new_refresh, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    new_key = f"refresh_token:{user_id}:{decoded['jti']}"
    assert mock_token_repo.data.get(new_key) == "active"


@pytest.mark.asyncio
async def test_refresh_invalid_type(auth_service):
    payload = {"sub": "123", "type": "access", "exp": datetime.now(UTC) + timedelta(days=1)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(UnauthorizedError) as exc:
        await auth_service.refresh(token)
    assert "Invalid token type" in exc.value.message


@pytest.mark.asyncio
async def test_refresh_token_revoked(auth_service, mock_token_repo):
    user_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=1)
    payload = {"sub": user_id, "exp": expire, "jti": jti, "type": "refresh"}
    refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(UnauthorizedError) as exc:
        await auth_service.refresh(refresh_token)
    assert "Refresh token revoked or reused" in exc.value.message


@pytest.mark.asyncio
async def test_logout_success(auth_service, mock_token_repo):
    user_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=1)
    payload = {"sub": user_id, "exp": expire, "jti": jti, "type": "refresh"}
    refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    key = f"refresh_token:{user_id}:{jti}"
    mock_token_repo.data[key] = "active"
    await auth_service.logout(refresh_token)
    assert key not in mock_token_repo.data
