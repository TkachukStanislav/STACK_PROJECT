from app.models import Notification

PAYLOAD = {"recipient_id": 42, "message": "Привіт", "idempotency_key": "test-endpoint-1"}


async def test_create_notification(client, db_session, published):
    response = await client.post("/api/v1/notifications", json=PAYLOAD)

    # 1. API відповів правильно
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["message"] == "Привіт"

    # 2. Запис справді з'явився в базі
    notification = await db_session.get(Notification, body["id"])
    assert notification is not None
    assert notification.idempotency_key == "test-endpoint-1"

    # 3. Повідомлення «надіслано» в чергу рівно один раз, з правильними даними
    assert len(published) == 1
    assert published[0]["id"] == body["id"]


async def test_invalid_payload_returns_422(client, published):
    response = await client.post("/api/v1/notifications", json={"recipient_id": "abc"})

    assert response.status_code == 422  # Pydantic відхилив
    assert published == []  # у чергу нічого не пішло
