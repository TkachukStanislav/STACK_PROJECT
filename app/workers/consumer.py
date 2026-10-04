import asyncio

from app.services.broker import connect, setup_queues


async def handle_message(message):
    print("Отримав:", message.body.decode())     # байти → рядок


async def main():
    connection, channel = await connect()
    await setup_queues(channel)
    queue = await channel.get_queue("notifications.queue")
    await queue.consume(handle_message)          # підписались на чергу
    print("Воркер слухає чергу... (Ctrl+C, щоб зупинити)")
    await asyncio.Future()                       # чекати вічно


if __name__ == "__main__":
    asyncio.run(main())