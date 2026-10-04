from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal

# Один клієнт на весь застосунок: всередині він тримає власний пул з'єднань до Redis
redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_redis() -> Redis:
    return redis_client
