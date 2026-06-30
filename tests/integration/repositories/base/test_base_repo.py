import pytest

from tests.integration.repositories.base.dummy import DummyRepository


@pytest.mark.asyncio
@pytest.mark.integration
async def test_crud_create_and_get_by_id(dummy_repo: DummyRepository):
    dummy = await dummy_repo.create({"name": "Test1", "status": "active"})
    await dummy_repo.commit()
    assert dummy.id is not None
    assert dummy.name == "Test1"

    fetched = await dummy_repo.get_by_id(str(dummy.id))
    assert fetched is not None
    assert fetched.id == dummy.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_crud_get_all(dummy_repo: DummyRepository):
    for i in range(3):
        await dummy_repo.create({"name": f"Test{i}", "status": "active"})
    await dummy_repo.commit()

    items, count = await dummy_repo.get_all(limit=2, offset=0)
    assert count >= 3
    assert len(items) == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_crud_update(dummy_repo: DummyRepository):
    dummy = await dummy_repo.create({"name": "Test1", "status": "active"})
    await dummy_repo.commit()

    updated = await dummy_repo.update(dummy, {"name": "Updated"})
    await dummy_repo.commit()
    assert updated.name == "Updated"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_crud_delete(dummy_repo: DummyRepository):
    dummy = await dummy_repo.create({"name": "Test1", "status": "active"})
    await dummy_repo.commit()

    await dummy_repo.delete(dummy)
    await dummy_repo.commit()

    deleted = await dummy_repo.get_by_id(str(dummy.id))
    assert deleted is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mixin_get_all_by_field(dummy_repo: DummyRepository):
    await dummy_repo.create({"name": "Test1", "status": "active"})
    await dummy_repo.create({"name": "Test2", "status": "inactive"})
    await dummy_repo.create({"name": "Test3", "status": "active"})
    await dummy_repo.commit()

    items, count = await dummy_repo.get_all_by_status("active", limit=10, offset=0)
    assert count >= 2
    assert all(item.status == "active" for item in items)
