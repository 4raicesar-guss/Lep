from fastapi import APIRouter, Header, HTTPException

from app.core.security import validate_init_data, TelegramAuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram")
async def auth_telegram(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
):
    try:
        user = validate_init_data(x_telegram_init_data)
    except TelegramAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"ok": True, "user": user}
