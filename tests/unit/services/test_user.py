import pytest

from app.core.enums.user import UserRole
from app.core.exceptions import ConflictError, DatabaseError, NotFoundError
from tests.unit.dummies import DummyModel


@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_user_repo, mocker):
    mock_hashed = "hashed_pw"
    mocker.patch("app.services.user.get_password_hash", return_value=mock_hashed)
    mocker.patch(
        "app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, return_value=mock_hashed
    )
    result = await user_service.create("test@example.com", "password123", UserRole.BUYER.value)
    assert result.email == "test@example.com"
    mock_user_repo.create.assert_called_once_with(
        {"email": "test@example.com", "password": mock_hashed, "role": UserRole.BUYER.value}
    )
    mock_user_repo.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_already_exists(user_service, mock_user_repo):
    user = DummyModel(email="test@example.com")
    mock_user_repo.data[user.id] = user
    with pytest.raises(ConflictError) as exc:
        await user_service.create(user.email, "password123", UserRole.BUYER.value)
    assert exc.value.message == "User with this email already exists"


@pytest.mark.asyncio
async def test_create_user_exception(user_service, mock_user_repo, mocker):
    mock_user_repo.fail_on_create = True
    mocker.patch(
        "app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, return_value="hashed"
    )
    with pytest.raises(DatabaseError) as exc:
        await user_service.create("test@example.com", "password123", UserRole.BUYER.value)
    assert "Failed to create user" in exc.value.message


@pytest.mark.asyncio
async def test_update_user_success(user_service, mock_user_repo, mocker):
    user = DummyModel(email="old@example.com")
    mock_user_repo.data[user.id] = user
    result = await user_service.update(user.id, {"email": "new@example.com"})
    assert result.email == "new@example.com"
    mock_user_repo.update.assert_called_once_with(user, {"email": "new@example.com"})
    mock_user_repo.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_password(user_service, mock_user_repo, mocker):
    user = DummyModel(password="old")
    mock_user_repo.data[user.id] = user
    mocker.patch(
        "app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, return_value="new_hash"
    )
    await user_service.update(user.id, {"password": "newpassword"})
    mock_user_repo.update.assert_called_once_with(user, {"password": "new_hash"})


@pytest.mark.asyncio
async def test_update_user_exception(user_service, mock_user_repo):
    user = DummyModel()
    mock_user_repo.data[user.id] = user
    mock_user_repo.fail_on_update = True
    with pytest.raises(DatabaseError) as exc:
        await user_service.update(user.id, {"email": "new@example.com"})
    assert "Failed to update user" in exc.value.message


@pytest.mark.asyncio
async def test_delete_user_success(user_service, mock_user_repo):
    user = DummyModel()
    mock_user_repo.data[user.id] = user
    await user_service.delete(user.id)
    mock_user_repo.delete.assert_called_once_with(user)
    mock_user_repo.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_exception(user_service, mock_user_repo):
    user = DummyModel()
    mock_user_repo.data[user.id] = user
    mock_user_repo.fail_on_delete = True
    with pytest.raises(DatabaseError) as exc:
        await user_service.delete(user.id)
    assert "Failed to delete user" in exc.value.message


@pytest.mark.asyncio
async def test_update_user_not_found(user_service, mock_user_repo):
    with pytest.raises(NotFoundError) as exc:
        await user_service.update("fake_id", {})
    assert exc.value.message == "User not found"


@pytest.mark.asyncio
async def test_update_email_conflict(user_service, mock_user_repo):
    user = DummyModel(email="old@example.com")
    other_user = DummyModel(email="used@example.com")
    mock_user_repo.data[user.id] = user
    mock_user_repo.data[other_user.id] = other_user
    with pytest.raises(ConflictError) as exc:
        await user_service.update(user.id, {"email": "used@example.com"})
    assert exc.value.message == "User with this email already exists"


@pytest.mark.asyncio
async def test_delete_user_not_found(user_service, mock_user_repo):
    with pytest.raises(NotFoundError) as exc:
        await user_service.delete("fake_id")
    assert exc.value.message == "User not found"


@pytest.mark.asyncio
async def test_update_password_wrong_current(user_service, mocker):
    user = DummyModel(password="pass")
    mocker.patch("app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, return_value=False)
    with pytest.raises(Exception) as exc:
        await user_service.update_password(user, "wrong", "new")
    assert "Incorrect password" in str(exc.value)


@pytest.mark.asyncio
async def test_update_password_same(user_service, mocker):
    user = DummyModel(password="pass")
    mocker.patch("app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, return_value=True)
    with pytest.raises(ConflictError) as exc:
        await user_service.update_password(user, "same", "same")
    assert exc.value.message == "New password cannot be the same as the current one"


@pytest.mark.asyncio
async def test_update_password_success(user_service, mock_user_repo, mocker):
    user = DummyModel(password="pass")
    mocker.patch(
        "app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, side_effect=[True, "hashed"]
    )
    await user_service.update_password(user, "old", "new")
    mock_user_repo.update.assert_called_once_with(user, {"password": "hashed"})
    mock_user_repo.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_password_exception(user_service, mock_user_repo, mocker):
    user = DummyModel(password="pass")
    mocker.patch(
        "app.services.user.to_thread.run_sync", new_callable=mocker.AsyncMock, side_effect=[True, "hashed"]
    )
    mock_user_repo.fail_on_update = True
    with pytest.raises(DatabaseError) as exc:
        await user_service.update_password(user, "old", "new")
    assert "Failed to update password" in exc.value.message
