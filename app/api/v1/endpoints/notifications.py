from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    data: NotificationCreate,
    session: AsyncSession = Depends(get_db),
):
    notification = Notification(**data.model_dump())   # схема → модель
    session.add(notification)                          # додати в сесію
    await session.commit()                             # зберегти в базу
    return notification                                # повернути клієнту