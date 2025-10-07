from typing import Optional, Any
from functools import wraps
import json
import hashlib
from app.core.config import settings

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheManager:
    def __init__(self):
        self._redis_client: Optional[Any] = None
        self._memory_cache: dict[str, Any] = {}

    async def get_redis_client(self):
        if not REDIS_AVAILABLE or not settings.REDIS_URL:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis_client.ping()
            except Exception:
                self._redis_client = None

        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        client = await self.get_redis_client()

        if client:
            try:
                value = await client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass

        return self._memory_cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        client = await self.get_redis_client()

        if client:
            try:
                await client.setex(key, ttl, json.dumps(value))
            except Exception:
                pass

        self._memory_cache[key] = value

    async def delete(self, key: str):
        client = await self.get_redis_client()

        if client:
            try:
                await client.delete(key)
            except Exception:
                pass

        self._memory_cache.pop(key, None)

    async def clear_pattern(self, pattern: str):
        client = await self.get_redis_client()

        if client:
            try:
                keys = await client.keys(pattern)
                if keys:
                    await client.delete(*keys)
            except Exception:
                pass

        keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            self._memory_cache.pop(key, None)

_cache_manager: Optional[CacheManager] = None

def get_cache_manager() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def cache_key(*args, **kwargs) -> str:
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(prefix: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            key = f"{prefix}:{cache_key(*args, **kwargs)}"

            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
