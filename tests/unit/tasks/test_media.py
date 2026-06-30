import pytest

from app.tasks.media import _cleanup_orphaned_media


@pytest.mark.asyncio
async def test_cleanup_orphaned_media(dummy_storage, dummy_media_repo):
    await _cleanup_orphaned_media(dummy_storage, dummy_media_repo)

    assert len(dummy_storage.deletes) == 1
    assert dummy_storage.deletes[0] == "orphaned_old.png"
