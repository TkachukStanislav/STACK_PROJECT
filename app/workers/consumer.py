import asyncio

from pydantic import ValidationError

from app.api.deps import redis_client
from app.core.database import AsyncSessionLocal
from app.models import Notification
from app.schemas.notification import NotificationMessage
from app.services.broker import connect, setup_queues
from app.services.idempotency import acquire_lock


async def handle_message(message):
    try:
        data = NotificationMessage.model_validate_json(message.body)
    except ValidationError:
        print("Зламане повідомлення → DLQ:", message.body)
        await message.reject(requeue=False)
        return

    if not await acquire_lock(redis_client, data.idempotency_key):
        print("Дубль, пропускаю:", data.idempotency_key)
        await message.ack()
        return

    async with AsyncSessionLocal() as session:
        notification = await session.get(Notification, data.id)
        notification.status = "sent"
        await session.commit()
        print("Надіслано, статус оновлено:", notification.id)
    await message.ack()


async def main():
    connection, channel = await connect()
    await channel.set_qos(prefetch_count=10)  # брати з черги не більше 10 повідомлень одночасно
    await setup_queues(channel)
    queue = await channel.get_queue("notifications.queue")
    await queue.consume(handle_message)
    print("Воркер слухає чергу... (Ctrl+C, щоб зупинити)")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
