from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.deps import redis_client
from app.api.v1.endpoints import health, notifications
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()    # закрити з'єднання з Redis
    await engine.dispose()         # закрити пул з'єднань Postgres
app = FastAPI(title="Notification Dispatcher", lifespan=lifespan)

app.include_router(health.router)
app.include_router(notifications.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Notification Dispatcher is running"}