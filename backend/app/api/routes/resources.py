"""
Endpoints para gestión de recursos económicos:
- POST /api/resources/collect: Recolección offline de grano según el tiempo transcurrido (Día 10)
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import get_db
from app.db.models import UserBuilding, UserResource

router = APIRouter(prefix="/api/resources", tags=["resources"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class CollectResourcesResponse(BaseModel):
    grain_collected: int
    new_total_grain: int
    hours_capped: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_authenticated_user_id(x_telegram_init_data: str) -> int:
    """Extrae y valida el telegram_id a partir del initData de Telegram."""
    try:
        user_data = validate_init_data(x_telegram_init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    raw_user_id = user_data.get("id")
    if raw_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el campo 'id' en los datos de usuario de Telegram",
        )

    try:
        return int(raw_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de telegram_id inválido",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/collect",
    response_model=CollectResourcesResponse,
    status_code=status.HTTP_200_OK,
    summary="Recolecta grano acumulado offline según tiempo transcurrido y niveles de Silo y Galpón.",
)
async def collect_resources(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> CollectResourcesResponse:
    user_id = _get_authenticated_user_id(x_telegram_init_data)

    # 1. Consultar / Inicializar recursos del jugador
    user_resource = await db.scalar(
        select(UserResource).where(UserResource.user_id == user_id)
    )
    if user_resource is None:
        user_resource = UserResource(user_id=user_id, grain=500)
        db.add(user_resource)
        await db.flush()

    # 2. Consultar / Inicializar niveles de edificios
    user_building = await db.scalar(
        select(UserBuilding).where(UserBuilding.user_id == user_id)
    )
    if user_building is None:
        user_building = UserBuilding(user_id=user_id, silo_level=1, galpon_level=1, boyero_level=1)
        db.add(user_building)
        await db.flush()

    # 3. Calcular horas transcurridas desde last_collected_at
    now = datetime.now(UTC)
    last_collected = user_resource.last_collected_at
    if last_collected is None:
        last_collected = now
    elif last_collected.tzinfo is None:
        last_collected = last_collected.replace(tzinfo=UTC)

    elapsed_seconds = max(0.0, (now - last_collected).total_seconds())
    hours = elapsed_seconds / 3600.0

    # 4. Calcular cap de horas según silo_level (base 4h + 2h por nivel, máx 12h)
    silo_level = user_building.silo_level or 1
    galpon_level = user_building.galpon_level or 1

    max_cap = min(4.0 + 2.0 * silo_level, 12.0)
    effective_hours = min(hours, max_cap)
    hours_capped = hours >= max_cap

    # 5. Calcular grano ganado: effective_hours * (120 * (1 + 0.15 * galpon_level))
    hourly_rate = 120.0 * (1.0 + 0.15 * galpon_level)
    grain_collected = int(round(effective_hours * hourly_rate))

    # 6. Actualizar modelo
    user_resource.grain += grain_collected
    user_resource.last_collected_at = now

    await db.commit()
    await db.refresh(user_resource)

    return CollectResourcesResponse(
        grain_collected=grain_collected,
        new_total_grain=user_resource.grain,
        hours_capped=hours_capped,
    )
