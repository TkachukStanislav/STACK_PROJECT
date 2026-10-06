import httpx
import respx

from app.core.config import settings
from app.services.sender import send_message


@respx.mock
async def test_send_ok():
    route = respx.post(settings.TELEGRAM_URL).respond(200)  # «Telegram сказав ок»

    result = await send_message("Привіт")

    assert result == 200
    assert route.call_count == 1  # запит зроблено рівно 1 раз


@respx.mock
async def test_send_no_connection():
    # «Telegram мовчить»: замість відповіді httpx отримує помилку з'єднання
    respx.post(settings.TELEGRAM_URL).mock(side_effect=httpx.ConnectError("нікого немає"))

    result = await send_message("Привіт")

    assert result is None  # не впали, повернули None
