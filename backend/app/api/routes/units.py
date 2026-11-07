"""
Endpoints para gestión de unidades:
- POST /api/units/merge: Fusión tripartita de unidades idénticas (Día 10)
- GET /api/units/inventory: Lista completa de unidades del jugador con su posición táctica (Día 10)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import get_db
from app.db.models import UserFormation, UserResource, UserUnit
from app.engine.data import SUMMON_COST, UNIT_TEMPLATES
from app.services.player_service import ensure_player_state

router = APIRouter(prefix="/api/units", tags=["units"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class MergeUnitsRequest(BaseModel):
    unit_ids: list[str] = Field(
        ...,
        description="Lista de exactamente 3 UUIDs de unidades a fusionar.",
    )


class MergeUnitsResponse(BaseModel):
    success: bool
    new_unit_id: str
    new_level: int


class UnitInventoryItem(BaseModel):
    id: str
    unit_id: str
    level: int
    slot: int | None = Field(
        None,
        description="Índice de la celda táctica (0 a 8) o null si está en el banco.",
    )


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
    "/merge",
    response_model=MergeUnitsResponse,
    status_code=status.HTTP_200_OK,
    summary="Fusiona 3 unidades idénticas en 1 unidad de nivel superior.",
)
async def merge_units(
    body: MergeUnitsRequest,
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> MergeUnitsResponse:
    user_id = _get_authenticated_user_id(x_telegram_init_data)

    # 1. Validación de cantidad: exactamente 3 IDs
    if len(body.unit_ids) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se deben proporcionar exactamente 3 IDs de unidades para fusionar",
        )

    # 2. Validación de UUIDs únicos y válidos
    if len(set(body.unit_ids)) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los 3 IDs de unidades deben ser distintos entre sí",
        )

    parsed_uuids: list[uuid.UUID] = []
    for uid_str in body.unit_ids:
        try:
            parsed_uuids.append(uuid.UUID(uid_str))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ID '{uid_str}' no es un UUID válido",
            )

    parsed_uuids_set = set(parsed_uuids)

    # 3. Buscar las unidades en la base de datos
    result = await db.execute(
        select(UserUnit).where(
            UserUnit.id.in_(parsed_uuids),
            UserUnit.user_id == user_id,
        )
    )
    units = list(result.scalars().all())

    # 4. Validar que existan y pertenezcan al usuario
    if len(units) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una o más unidades no existen o no pertenecen al usuario autenticado",
        )

    # 5. Validar que todas tengan el mismo unit_id
    first_unit = units[0]
    if any(u.unit_id != first_unit.unit_id for u in units):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todas las unidades a fusionar deben tener el mismo tipo (unit_id)",
        )

    # 6. Validar que todas tengan el mismo nivel
    if any(u.level != first_unit.level for u in units):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todas las unidades a fusionar deben tener el mismo nivel",
        )

    # 7. Validar que el nivel sea menor a 3
    if first_unit.level >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden fusionar unidades de nivel 3 o superior",
        )

    target_level = first_unit.level + 1
    target_unit_id = first_unit.unit_id

    # 8. Acción Transaccional Atómica
    # Crear la nueva unidad de nivel superior
    new_unit = UserUnit(
        id=uuid.uuid4(),
        user_id=user_id,
        unit_id=target_unit_id,
        level=target_level,
    )
    db.add(new_unit)
    await db.flush()

    # Actualizar UserFormation si alguna unidad vieja estaba desplegada
    formation = await db.scalar(
        select(UserFormation).where(UserFormation.user_id == user_id)
    )
    if formation is not None:
        first_replaced = False
        for i in range(9):
            slot_attr = f"slot_{i}"
            slot_val = getattr(formation, slot_attr, None)
            if slot_val in parsed_uuids_set:
                if not first_replaced:
                    setattr(formation, slot_attr, new_unit.id)
                    first_replaced = True
                else:
                    setattr(formation, slot_attr, None)

    # Eliminar las 3 unidades anteriores
    await db.execute(
        delete(UserUnit).where(
            UserUnit.id.in_(parsed_uuids),
            UserUnit.user_id == user_id,
        )
    )

    await db.commit()

    return MergeUnitsResponse(
        success=True,
        new_unit_id=str(new_unit.id),
        new_level=target_level,
    )


@router.get(
    "/inventory",
    response_model=list[UnitInventoryItem],
    status_code=status.HTTP_200_OK,
    summary="Devuelve la lista completa de unidades del jugador con su estado de formación.",
)
async def get_inventory(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> list[UnitInventoryItem]:
    user_id = _get_authenticated_user_id(x_telegram_init_data)

    # 1. Consultar unidades del jugador
    units_result = await db.execute(
        select(UserUnit).where(UserUnit.user_id == user_id).order_by(UserUnit.acquired_at)
    )
    units = list(units_result.scalars().all())

    # 2. Consultar formación táctica activa
    formation = await db.scalar(
        select(UserFormation).where(UserFormation.user_id == user_id)
    )

    unit_slot_map: dict[uuid.UUID, int] = {}
    if formation is not None:
        for i in range(9):
            slot_uuid = getattr(formation, f"slot_{i}", None)
            if slot_uuid is not None:
                unit_slot_map[slot_uuid] = i

    return [
        UnitInventoryItem(
            id=str(u.id),
            unit_id=u.unit_id,
            level=u.level,
            slot=unit_slot_map.get(u.id),
        )
        for u in units
    ]


class SummonUnitRequest(BaseModel):
    unit_id: str = Field(..., examples=["U01"], description="Tipo de unidad a comprar (U01..U08).")


class SummonUnitResponse(BaseModel):
    success: bool
    unit: UnitInventoryItem
    cost: int
    remaining_grain: int


@router.post(
    "/summon",
    response_model=SummonUnitResponse,
    status_code=status.HTTP_200_OK,
    summary="Compra directa de una unidad nivel 1 por grano.",
)
async def summon_unit(
    body: SummonUnitRequest,
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> SummonUnitResponse:
    try:
        user_data = validate_init_data(x_telegram_init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    try:
        user_id = int(user_data["id"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta o es inválido el campo 'id' en los datos de usuario de Telegram",
        )

    unit_type = body.unit_id.strip().upper()
    if unit_type not in UNIT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unidad inválida '{body.unit_id}'. Opciones: {', '.join(sorted(UNIT_TEMPLATES))}",
        )

    # Asegura jugador + Kit de Inicio (si es nuevo) antes de cobrar
    await ensure_player_state(db, user_id, user_data)

    # Bloqueo de fila para evitar doble gasto con peticiones concurrentes
    resource = await db.scalar(
        select(UserResource).where(UserResource.user_id == user_id).with_for_update()
    )
    assert resource is not None
    current_grain = resource.grain
    if current_grain < SUMMON_COST:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grano insuficiente: requieres {SUMMON_COST} pero tienes {current_grain}",
        )

    resource.grain -= SUMMON_COST
    new_unit = UserUnit(id=uuid.uuid4(), user_id=user_id, unit_id=unit_type, level=1)
    db.add(new_unit)
    await db.commit()

    return SummonUnitResponse(
        success=True,
        unit=UnitInventoryItem(id=str(new_unit.id), unit_id=unit_type, level=1, slot=None),
        cost=SUMMON_COST,
        remaining_grain=resource.grain,
    )
