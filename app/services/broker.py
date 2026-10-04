import aio_pika

from app.core.config import settings


async def connect():
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    return connection, channel  