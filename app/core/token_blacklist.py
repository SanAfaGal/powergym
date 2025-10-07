from typing import Optional
from datetime import datetime, timedelta
from app.core.cache import get_cache_manager
from app.core.config import settings

class TokenBlacklist:
    def __init__(self):
        self.cache = get_cache_manager()
        self.prefix = "blacklist:token:"

    async def add_token(self, token: str, expires_in: Optional[int] = None):
        if expires_in is None:
            expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        key = f"{self.prefix}{token}"
        await self.cache.set(key, {"blacklisted_at": datetime.utcnow().isoformat()}, ttl=expires_in)

    async def is_blacklisted(self, token: str) -> bool:
        key = f"{self.prefix}{token}"
        result = await self.cache.get(key)
        return result is not None

    async def remove_token(self, token: str):
        key = f"{self.prefix}{token}"
        await self.cache.delete(key)

_token_blacklist: Optional[TokenBlacklist] = None

def get_token_blacklist() -> TokenBlacklist:
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist
