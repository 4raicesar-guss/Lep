"""
Endpoint GET /api/player/state — Día 9.

Valida la identidad del jugador vía X-Telegram-Init-Data y devuelve el estado completo:
- Recursos (grano y última recolección)
- Niveles de edificios (silo, galpón, boyero)
- Unidades adquiridas y su posición táctica (slot 0-8 o null en reserva)
- Formación táctica activa
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import get_db
from app.db.models import UserBuilding, UserFormation, UserResource, UserUnit
from app.services.player_service import ensure_player_state

router = APIRouter(prefix="/api/player", tags=["player"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class PlayerInfo(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str

    model_config = ConfigDict(from_attributes=True)


class ResourcesInfo(BaseModel):
    grain: int
    last_collected_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BuildingsInfo(BaseModel):
    silo_level: int
    galpon_level: int
    boyero_level: int

    model_config = ConfigDict(from_attributes=True)


class UnitInfo(BaseModel):
    id: str
    unit_id: str
    level: int
    slot: int | None = Field(None, description="Índice del slot en la formación (0 a 8) o null si está en el banco.")
    acquired_at: datetime | None = None


class FormationInfo(BaseModel):
    slots: dict[str, str | None] = Field(
        ...,
        description="Mapeo de los 9 slots del grid táctico 3x3 ('0' a '8') a UUID de la unidad o null.",
    )


class PlayerStateResponse(BaseModel):
    player: PlayerInfo
    resources: ResourcesInfo
    grain: int | None = None
    buildings: BuildingsInfo
    units: list[UnitInfo]
    formation: FormationInfo


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/state",
    response_model=PlayerStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtiene el estado completo del jugador autenticado.",
)
async def get_player_state(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> PlayerStateResponse:
    # 1. Autenticación y extracción del telegram_id
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
        telegram_id = int(raw_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de telegram_id inválido",
        )

    # 2-5. Asegurar Player, recursos, edificios, formación y Kit de Inicio (1x U01, 1x U03, 1x U06)
    player = await ensure_player_state(db, telegram_id, user_data)
    await db.commit()
    resources = await db.scalar(select(UserResource).where(UserResource.user_id == telegram_id))
    buildings = await db.scalar(select(UserBuilding).where(UserBuilding.user_id == telegram_id))
    formation = await db.scalar(select(UserFormation).where(UserFormation.user_id == telegram_id))
    assert resources is not None and buildings is not None and formation is not None
    await db.refresh(resources)
    await db.refresh(buildings)
    await db.refresh(formation)

    # 6. Consultar todas las unidades adquiridas por el jugador
    units_result = await db.execute(
        select(UserUnit).where(UserUnit.user_id == telegram_id).order_by(UserUnit.acquired_at)
    )
    units_list = list(units_result.scalars().all())

    # 7. Mapear slots ocupados en la formación táctica
    formation_slots: dict[str, str | None] = {}
    unit_slot_map: dict[uuid.UUID, int] = {}
    for i in range(9):
        slot_uuid: uuid.UUID | None = getattr(formation, f"slot_{i}", None)
        formation_slots[str(i)] = str(slot_uuid) if slot_uuid else None
        if slot_uuid is not None:
            unit_slot_map[slot_uuid] = i

    # 8. Asignar la posición a cada unidad
    units_response = [
        UnitInfo(
            id=str(u.id),
            unit_id=u.unit_id,
            level=u.level,
            slot=unit_slot_map.get(u.id),
            acquired_at=u.acquired_at,
        )
        for u in units_list
    ]

    return PlayerStateResponse(
        player=PlayerInfo(
            telegram_id=player.telegram_id,
            username=player.username,
            first_name=player.first_name,
        ),
        resources=ResourcesInfo(
            grain=resources.grain,
            last_collected_at=resources.last_collected_at,
        ),
        grain=resources.grain,
        buildings=BuildingsInfo(
            silo_level=buildings.silo_level,
            galpon_level=buildings.galpon_level,
            boyero_level=buildings.boyero_level,
        ),
        units=units_response,
        formation=FormationInfo(slots=formation_slots),
    )
