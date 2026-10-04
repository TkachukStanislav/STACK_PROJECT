import asyncio

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.connect() as conn:                # взяти з'єднання з пулу
        result = await conn.execute(text("SELECT 1"))   # виконати SQL-запит
        print(result.scalar())                          # дістати одне значення з відповіді
    await engine.dispose()                              # закрити пул перед виходом


asyncio.run(main())
