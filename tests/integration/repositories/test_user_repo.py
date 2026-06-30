import uuid

import pytest

from app.repositories.user import UserRepository
from tests.factories import UserFactory


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_by_email(user_repo: UserRepository, db_session):
    unique_email = f"test_{uuid.uuid4()}@example.com"
    user = UserFactory(email=unique_email)
    db_session.add(user)
    await db_session.commit()

    fetched = await user_repo.get_by_email(unique_email)
    assert fetched is not None
    assert fetched.id == user.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_by_email_not_found(user_repo: UserRepository):
    fetched = await user_repo.get_by_email("nonexistent@example.com")
    assert fetched is None
