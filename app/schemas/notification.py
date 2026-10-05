from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    recipient_id: int
    message: str
    idempotency_key: str


class NotificationResponse(NotificationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime


class NotificationMessage(BaseModel):
    id: int
    recipient_id: int
    message: str
    idempotency_key: str
