import asyncio
import os
from dotenv import load_dotenv
import redis.asyncio as redis
from datetime import timedelta
from typing import Any, Optional

load_dotenv()

class AsyncRedisClient:
    """
    Async wrapper around a shared Redis client providing insert, update, get, and flush methods.
    """
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        max_connections: int = None,
        connect_timeout: float = None,
        socket_timeout: float = None,
    ):
        # Load parameters from environment or use provided values
        REDIS_HOST = host or os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = port or int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = db or int(os.getenv("REDIS_DB", 0))

        MAX_CONN = max_connections or int(os.getenv("REDIS_MAX_CONNECTIONS", 10))
        CONNECT_TIMEOUT = connect_timeout or float(os.getenv("REDIS_CONNECT_TIMEOUT", 5.0))
        SOCKET_TIMEOUT = socket_timeout or float(os.getenv("REDIS_SOCKET_TIMEOUT", 5.0))

        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            encoding="utf-8",
            decode_responses=True,
            max_connections=MAX_CONN,
            socket_connect_timeout=CONNECT_TIMEOUT,
            socket_timeout=SOCKET_TIMEOUT,
        )

    async def insert(
        self,
        key: str,
        value: Any,
        ttl_hours: int
    ) -> None:
        """
        Insert a key-value pair with an expiration time in hours.
        """
        expire_seconds = int(timedelta(hours=ttl_hours).total_seconds())
        await self.client.set(key, value, ex=expire_seconds)

    async def update(
        self,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None
    ) -> None:
        """
        Update a key with a new value. If ttl_hours is provided, reset expiration.
        Otherwise, keep the existing TTL (no expiration change).
        """
        if ttl_hours is not None:
            expire_seconds = int(timedelta(hours=ttl_hours).total_seconds())
            await self.client.set(key, value, ex=expire_seconds)
        else:
            await self.client.set(key, value)

    async def get(
        self,
        key: str
    ) -> Optional[str]:
        """
        Retrieve the value for a given key, or None if not found.
        """
        return await self.client.get(key)

    async def flush_db(self) -> None:
        """
        Remove all keys from the current Redis database.
        """
        print("flushing redis")
        await self.client.flushdb()

# Shared instance
redis_client = AsyncRedisClient()