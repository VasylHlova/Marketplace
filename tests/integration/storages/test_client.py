import os
import tempfile

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_storage_client_upload_download_delete(storage_client, faker):
    test_key = f"test_{faker.uuid4()}.txt"
    test_content = b"Integration test content"

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "src.txt")
        dest_path = os.path.join(tmpdir, "dest.txt")

        with open(src_path, "wb") as f:
            f.write(test_content)

        await storage_client.upload(test_key, src_path, "text/plain")

        await storage_client.download(test_key, dest_path)
        with open(dest_path, "rb") as f:
            assert f.read() == test_content

        objects = []
        async for obj in storage_client.list_objects():
            objects.append(obj["Key"])

        assert test_key in objects

        await storage_client.delete(test_key)

        objects_after = []
        async for obj in storage_client.list_objects():
            objects_after.append(obj["Key"])

        assert test_key not in objects_after
