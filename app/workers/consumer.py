import asyncio
import random

from pydantic import ValidationError

from app.api.deps import redis_client
from app.core.database import AsyncSessionLocal
from app.models import DeliveryLog, Notification
from app.schemas.notification import NotificationMessage
from app.services.broker import connect, setup_queues
from app.services.idempotency import acquire_lock
from app.services.sender import send_message


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

    logs = []  # сюди складаємо кожну спробу, щоб потім записати в delivery_logs

    for attempt in range(1, 4):  # 3 спроби
        status_code = await send_message(data.message)
        print(f"Спроба {attempt}: {status_code}")
        logs.append(DeliveryLog(notification_id=data.id, attempt=attempt, status_code=status_code))

        if status_code == 200:  # дійшло → стоп
            break
        if status_code is not None and status_code < 500:  # 4xx → повтор не допоможе
            break

        if attempt < 3:  # пауза: 2 с, потім 4 с
            await asyncio.sleep(2**attempt + random.uniform(0.1, 0.5))

    async with AsyncSessionLocal() as session:
        session.add_all(logs)  # усі спроби → таблиця delivery_logs
        notification = await session.get(Notification, data.id)
        if status_code == 200:  # ← нове
            notification.status = "sent"
        else:
            notification.status = "failed"
        await session.commit()
        print("Відправка:", notification.id, "→", notification.status)  # ← змінили текст
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
