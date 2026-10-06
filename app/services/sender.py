import httpx

from app.core.config import settings


async def send_message(text: str) -> int | None:
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.post(settings.TELEGRAM_URL, json={"text": text})
        except httpx.RequestError:  # варіант 3: тиша
            return None  # «відповіді не було»
    return response.status_code
