import httpx

from app.core.config import settings


async def send_message(text: str) -> int:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(settings.TELEGRAM_URL, json={"text": text})
    return response.status_code
