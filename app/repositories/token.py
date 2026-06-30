from redis.asyncio import Redis


class TokenRepository:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def save_token(self, key: str, ttl_seconds: int, value: str = "active") -> None:
        await self._redis.setex(name=key, time=ttl_seconds, value=value)

    async def get_token(self, key: str) -> str | None:
        value = await self._redis.get(key)
        if isinstance(value, bytes):
            return value.decode()
        return value

    async def delete_token(self, key: str) -> None:
        await self._redis.delete(key)
