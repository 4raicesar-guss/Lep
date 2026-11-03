import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import validate_init_data, TelegramAuthError
from app.db.database import async_session
from app.db.models import AnalyticsEvent

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class EventRequest(BaseModel):
    event_name: str
    payload: dict[str, Any] = Field(default_factory=dict)


async def save_event(event_name: str, payload: dict[str, Any], user_id: int | None) -> None:
    async with async_session() as session:
        event = AnalyticsEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_name=event_name,
            payload=payload,
        )
        session.add(event)
        await session.commit()


@router.post("/event", status_code=status.HTTP_202_ACCEPTED)
async def track_event(
    event: EventRequest,
    background_tasks: BackgroundTasks,
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
):
    user_id: int | None = None

    if x_telegram_init_data:
        try:
            user = validate_init_data(x_telegram_init_data)
            raw_user_id = user.get("id")
            if raw_user_id is not None:
                user_id = int(raw_user_id)
        except TelegramAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Telegram auth: {e}",
            )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format in Telegram data",
            )

    background_tasks.add_task(save_event, event.event_name, event.payload, user_id)
    return {"status": "accepted"}
