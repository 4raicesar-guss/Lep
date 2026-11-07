"""
Endpoints para gestión y mejora de edificios:
- POST /api/buildings/upgrade: Mejorar nivel de silo, galpon o boyero consumiendo grano (Día 10)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import get_db
from app.db.models import UserBuilding, UserResource

router = APIRouter(prefix="/api/buildings", tags=["buildings"])

VALID_BUILDINGS = {"silo", "galpon", "boyero"}


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class UpgradeBuildingRequest(BaseModel):
    building_id: str = Field(
        ...,
        description="Identificador del edificio a mejorar: 'silo', 'galpon' o 'boyero'.",
        examples=["silo"],
    )


class UpgradeBuildingResponse(BaseModel):
    success: bool
    building_id: str
    new_level: int
    remaining_grain: int
    cost: int


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
    "/upgrade",
    response_model=UpgradeBuildingResponse,
    status_code=status.HTTP_200_OK,
    summary="Mejora el nivel de un edificio de la granja consumiendo grano.",
)
async def upgrade_building(
    body: UpgradeBuildingRequest,
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> UpgradeBuildingResponse:
    user_id = _get_authenticated_user_id(x_telegram_init_data)

    building_id = body.building_id.lower().strip()
    if building_id not in VALID_BUILDINGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Edificio inválido '{body.building_id}'. Opciones válidas: silo, galpon, boyero",
        )

    # 1. Consultar / Inicializar recursos
    user_resource = await db.scalar(
        select(UserResource).where(UserResource.user_id == user_id)
    )
    if user_resource is None:
        user_resource = UserResource(user_id=user_id, grain=500)
        db.add(user_resource)
        await db.flush()

    # 2. Consultar / Inicializar edificios
    user_building = await db.scalar(
        select(UserBuilding).where(UserBuilding.user_id == user_id)
    )
    if user_building is None:
        user_building = UserBuilding(user_id=user_id, silo_level=1, galpon_level=1, boyero_level=1)
        db.add(user_building)
        await db.flush()

    # 3. Validar nivel < 5
    level_field = f"{building_id}_level"
    current_level = getattr(user_building, level_field, 1)

    if current_level >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El edificio '{building_id}' ya ha alcanzado el nivel máximo (5)",
        )

    # 4. Calcular coste: 100 * (1.5 ^ current_level)
    cost = int(round(100.0 * (1.5 ** current_level)))

    # 5. Validar grano suficiente
    if user_resource.grain < cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Grano insuficiente: requieres {cost} pero tienes {user_resource.grain}",
        )

    # 6. Descontar grano y aumentar nivel
    user_resource.grain -= cost
    new_level = current_level + 1
    setattr(user_building, level_field, new_level)

    await db.commit()
    await db.refresh(user_resource)
    await db.refresh(user_building)

    return UpgradeBuildingResponse(
        success=True,
        building_id=building_id,
        new_level=new_level,
        remaining_grain=user_resource.grain,
        cost=cost,
    )
