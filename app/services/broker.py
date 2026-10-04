import aio_pika

from app.core.config import settings


async def connect():
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    return connection, channel


async def setup_queues(channel):
    # 1. DLQ: скринька для зламаних повідомлень
    dlx = await channel.declare_exchange(
        "notifications.dlx", aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlq = await channel.declare_queue("notifications.dlq", durable=True)
    await dlq.bind(dlx, routing_key="dlq")

    # 2. Основна черга, яка знає, куди відправляти зламані повідомлення
    exchange = await channel.declare_exchange(
        "notifications.direct", aio_pika.ExchangeType.DIRECT, durable=True
    )
    queue = await channel.declare_queue(
        "notifications.queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "notifications.dlx",
            "x-dead-letter-routing-key": "dlq",
        },
    )
    await queue.bind(exchange, routing_key="notifications")