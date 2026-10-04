import asyncio

from pydantic import ValidationError                                    # ← нове

from app.schemas.notification import NotificationMessage                # ← нове
from app.services.broker import connect, setup_queues


async def handle_message(message):
    try:                                                                # ← нове
        data = NotificationMessage.model_validate_json(message.body)
    except ValidationError:
        print("Зламане повідомлення → DLQ:", message.body)
        await message.reject(requeue=False)
        return

    print("Отримав нормальне:", data)
    await message.ack()


async def main():
    connection, channel = await connect()
    await setup_queues(channel)
    queue = await channel.get_queue("notifications.queue")
    await queue.consume(handle_message)
    print("Воркер слухає чергу... (Ctrl+C, щоб зупинити)")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())