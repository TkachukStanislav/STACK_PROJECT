from fastapi import APIRouter, Depends, Request  # ← додали Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.broker import publish_notification  # ← нове

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    data: NotificationCreate,
    request: Request,  # ← нове
    session: AsyncSession = Depends(get_db),
):
    notification = Notification(**data.model_dump())
    session.add(notification)
    await session.commit()

    payload = {"id": notification.id, **data.model_dump()}  # ← нове
    channel = request.app.state.rabbit_channel  # ← нове
    await publish_notification(channel, payload)  # ← нове

    return notification
