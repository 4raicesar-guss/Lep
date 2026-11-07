"""
Endpoints para gestión de la formación táctica:
- POST /api/formation/save: Configurar y guardar la formación táctica (slots 0 a 8) (Día 10)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import get_db
from app.db.models import UserFormation, UserUnit

router = APIRouter(prefix="/api/formation", tags=["formation"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class SaveFormationRequest(BaseModel):
    slots: dict[str, str | None] = Field(
        ...,
        description="Mapeo de slots '0' a '8' a UUID de la unidad o null.",
    )


class SaveFormationResponse(BaseModel):
    success: bool
    slots: dict[str, str | None]


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
    "/save",
    response_model=SaveFormationResponse,
    status_code=status.HTTP_200_OK,
    summary="Guarda la formación táctica del jugador en el grid 3x3.",
)
async def save_formation(
    body: SaveFormationRequest,
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> SaveFormationResponse:
    user_id = _get_authenticated_user_id(x_telegram_init_data)

    parsed_slots: dict[int, uuid.UUID | None] = {}
    specified_uuids: list[uuid.UUID] = []

    # Validar claves y parsear UUIDs
    for slot_idx in range(9):
        key = str(slot_idx)
        raw_val = body.slots.get(key)
        if raw_val is not None:
            try:
                parsed_uuid = uuid.UUID(raw_val)
            except (ValueError, TypeError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El valor '{raw_val}' en slot '{key}' no es un UUID válido",
                )
            parsed_slots[slot_idx] = parsed_uuid
            specified_uuids.append(parsed_uuid)
        else:
            parsed_slots[slot_idx] = None

    # Validar que no haya UUIDs duplicados en la formación
    if len(specified_uuids) != len(set(specified_uuids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se permiten unidades duplicadas en la formación",
        )

    # Validar que todos los UUIDs no nulos existan y pertenezcan al jugador
    if specified_uuids:
        result = await db.execute(
            select(UserUnit).where(
                UserUnit.id.in_(specified_uuids),
                UserUnit.user_id == user_id,
            )
        )
        found_units = list(result.scalars().all())
        if len(found_units) != len(specified_uuids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Una o más unidades no existen o no pertenecen al jugador",
            )

    # Consultar o inicializar UserFormation
    formation = await db.scalar(
        select(UserFormation).where(UserFormation.user_id == user_id)
    )
    if formation is None:
        formation = UserFormation(user_id=user_id)
        db.add(formation)

    # Asignar los slots
    response_slots: dict[str, str | None] = {}
    for i in range(9):
        assigned_uuid = parsed_slots.get(i)
        setattr(formation, f"slot_{i}", assigned_uuid)
        response_slots[str(i)] = str(assigned_uuid) if assigned_uuid else None

    await db.commit()

    return SaveFormationResponse(
        success=True,
        slots=response_slots,
    )
