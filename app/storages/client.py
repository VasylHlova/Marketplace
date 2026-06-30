from collections.abc import AsyncIterator
from typing import Any

from app.db.minio import minio_session


class MinioStorageClient:
    def __init__(self, bucket: str, url: str, user: str, password: str):
        self.bucket = bucket
        self.url = url
        self.user = user
        self.password = password

    async def download(self, object_key: str, dest_path: str) -> None:
        async with minio_session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.user,
            aws_secret_access_key=self.password,
        ) as client:
            await client.download_file(self.bucket, object_key, dest_path)

    async def upload(self, object_key: str, src_path: str, content_type: str) -> None:
        async with minio_session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.user,
            aws_secret_access_key=self.password,
        ) as client:
            await client.upload_file(
                src_path, self.bucket, object_key, ExtraArgs={"ContentType": content_type}
            )

    async def delete(self, object_key: str) -> None:
        async with minio_session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.user,
            aws_secret_access_key=self.password,
        ) as client:
            await client.delete_object(Bucket=self.bucket, Key=object_key)

    async def list_objects(self) -> AsyncIterator[dict[str, Any]]:
        async with minio_session.client(
            "s3",
            endpoint_url=self.url,
            aws_access_key_id=self.user,
            aws_secret_access_key=self.password,
        ) as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket):
                if "Contents" not in page:
                    continue
                for obj in page["Contents"]:
                    yield obj
