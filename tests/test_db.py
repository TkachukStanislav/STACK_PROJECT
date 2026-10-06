from sqlalchemy import func, select

from app.models import Notification


async def count_iso_rows(session):
    query = select(func.count()).where(Notification.idempotency_key == "iso-test")
    return await session.scalar(query)


async def test_first_writes(db_session):
    db_session.add(Notification(recipient_id=1, message="hi", idempotency_key="iso-test"))
    await db_session.commit()
    assert await count_iso_rows(db_session) == 1  # запис є


async def test_second_sees_nothing(db_session):
    assert await count_iso_rows(db_session) == 0  # перший тест «стерся»
