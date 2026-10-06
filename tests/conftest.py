import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.api.v1.endpoints import notifications
from app.core.config import settings
from app.main import app


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


@pytest.fixture
def published(monkeypatch):
    # «пустушка» замість RabbitMQ: нічого не надсилає, лише запам'ятовує payload
    messages = []

    async def fake_publish(channel, payload):
        messages.append(payload)

    monkeypatch.setattr(notifications, "publish_notification", fake_publish)
    return messages


@pytest.fixture
async def client(db_session, published):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db  # ендпоінт отримає «олівцеву» сесію
    app.state.rabbit_channel = None  # lifespan у тестах не запускається, кладемо заглушку
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
