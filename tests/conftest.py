import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


@pytest.fixture
async def db_session():
    # окремий двигун для тестів, без пулу: кожен тест отримує свіже з'єднання
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()  # «беремо олівець»
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",  # commit у коді стає «несправжнім»
        )
        yield session
        await session.close()
        await transaction.rollback()  # «стираємо гумкою» все, що записав тест
    await engine.dispose()
