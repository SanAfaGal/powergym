from supabase import create_client, Client
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db, get_async_db
from typing import Generator, AsyncGenerator
import asyncio
from functools import lru_cache

class SupabaseConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool: list[Client] = []
        self._lock = asyncio.Lock()

    def _create_client(self) -> Client:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    async def get_client(self) -> Client:
        async with self._lock:
            if len(self._pool) < self.max_connections:
                client = self._create_client()
                self._pool.append(client)
                return client
            return self._pool[0]

    def get_client_sync(self) -> Client:
        if len(self._pool) < self.max_connections:
            client = self._create_client()
            self._pool.append(client)
            return client
        if self._pool:
            return self._pool[0]
        client = self._create_client()
        self._pool.append(client)
        return client

@lru_cache()
def get_connection_pool() -> SupabaseConnectionPool:
    return SupabaseConnectionPool(max_connections=10)

def get_supabase_client() -> Client:
    pool = get_connection_pool()
    return pool.get_client_sync()

async def get_supabase_client_async() -> Client:
    pool = get_connection_pool()
    return await pool.get_client()

def get_db_session() -> Generator[Session, None, None]:
    """
    Get SQLAlchemy database session for synchronous operations.
    """
    return get_db()

async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get SQLAlchemy database session for asynchronous operations.
    """
    async for session in get_async_db():
        yield session
