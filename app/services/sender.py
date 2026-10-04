import httpx

from app.core.config import settings


async def send_message(recipient_id: int, text: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(
            settings.TELEGRAM_URL,
            json={"chat_id": recipient_id, "text": text},
        )
    return response
