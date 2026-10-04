import asyncio
from pathlib import Path

from app.api.deps import redis_client

CAPACITY = 30                       # скільки жетонів влазить у відро
RATE = 30                           # скільки жетонів додається за секунду
BUCKET_KEY = "rate_limit:telegram"  # назва відра в Redis

# Шлях до scripts/token_bucket.lua відносно цього файлу
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "token_bucket.lua"

# Завантажуємо Lua-скрипт у Redis один раз при імпорті
token_bucket = redis_client.register_script(SCRIPT_PATH.read_text(encoding="utf-8"))


async def acquire_token() -> None:
    while True:
        allowed = await token_bucket(keys=[BUCKET_KEY], args=[CAPACITY, RATE])
        if allowed == 1:
            return
        await asyncio.sleep(1 / RATE)  # приблизно стільки часу наростає один жетон
