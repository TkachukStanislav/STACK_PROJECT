from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.services.broker import connect, setup_queues

from app.api.deps import redis_client
from app.api.v1.endpoints import health, notifications
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- СТАРТ ---
    connection, channel = await connect()      # подзвонили в RabbitMQ
    await setup_queues(channel)                # переконались, що скриньки на місці
    app.state.rabbit_channel = channel         # поклали канал у шухляду

    yield                                      # сервер працює

    # --- ЗУПИНКА ---
    await connection.close()                   # поклали трубку RabbitMQ
    await redis_client.aclose()
    await engine.dispose()
app = FastAPI(title="Notification Dispatcher", lifespan=lifespan)

app.include_router(health.router)
app.include_router(notifications.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Notification Dispatcher is running"}