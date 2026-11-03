"""
Endpoint POST /api/combat/simulate — Día 7.

Recibe la formación del jugador y el número de oleada,
ejecuta la simulación determinista en el motor Python,
persiste el resultado y devuelve el replayData completo al frontend.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.combat_engine import (
    UNIT_TEMPLATES,
    LEVEL_MULT,
    simulate_battle,
)
from app.core.security import TelegramAuthError, validate_init_data
from app.db.database import async_session
from app.db.models import Battle

router = APIRouter(prefix="/api/combat", tags=["combat"])

# ---------------------------------------------------------------------------
# Composición de enemigos por oleada (hardcoded temporal — GDD Oleada 1)
# Estructura: lista de dicts compatibles con SimUnit.__init__
# ---------------------------------------------------------------------------

WAVE_COMPOSITIONS: dict[int, list[dict[str, Any]]] = {
    1: [
        # Oleada 1: Toro Bravo (tanque frontal) + Oveja Sanadora (soporte trasero)
        {
            "id": "E01",
            "unit_id": "U02",  # Toro Bravo
            "level": 1,
            "position": 4,  # Centro del grid
        },
        {
            "id": "E02",
            "unit_id": "U06",  # Oveja Sanadora
            "level": 1,
            "position": 5,  # Derecha-centro
        },
    ],
    2: [
        # Oleada 2: Toro + Gallo + Oveja
        {
            "id": "E01",
            "unit_id": "U02",
            "level": 1,
            "position": 3,
        },
        {
            "id": "E02",
            "unit_id": "U03",
            "level": 1,
            "position": 4,
        },
        {
            "id": "E03",
            "unit_id": "U06",
            "level": 1,
            "position": 5,
        },
    ],
    3: [
        # Oleada 3: Composición reforzada nivel 2
        {
            "id": "E01",
            "unit_id": "U01",
            "level": 2,
            "position": 3,
        },
        {
            "id": "E02",
            "unit_id": "U02",
            "level": 2,
            "position": 4,
        },
        {
            "id": "E03",
            "unit_id": "U07",
            "level": 1,
            "position": 5,
        },
        {
            "id": "E04",
            "unit_id": "U06",
            "level": 2,
            "position": 8,
        },
    ],
}

# Máxima oleada definida — las oleadas fuera de rango caen aquí
MAX_WAVE = max(WAVE_COMPOSITIONS.keys())


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------


class UnitSlot(BaseModel):
    unit_id: str = Field(..., examples=["U01"])
    level: int = Field(1, ge=1, le=3)
    position: int = Field(..., ge=0, le=8)


class SimulateRequest(BaseModel):
    player_formation: list[UnitSlot] = Field(
        ...,
        min_length=1,
        max_length=9,
        description="Formación del jugador: hasta 9 unidades en el grid 3x3.",
    )
    wave_number: int = Field(1, ge=1, description="Número de oleada enemiga a enfrentar.")


class GridCellOut(BaseModel):
    id: str
    unit_id: str
    current_hp: float
    max_hp: float
    is_stunned: bool
    team: str


class ReplayEventOut(BaseModel):
    tick: int
    actor_id: str
    action: str
    target_id: str
    damage: float | None = None
    heal: float | None = None
    stun: bool | None = None


class SimulateResponse(BaseModel):
    winner: str
    total_ticks: int
    seed: int
    replay_log: list[dict[str, Any]]
    initial_grid: list[GridCellOut | None]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_team_dict(slot: UnitSlot, team_prefix: str, index: int) -> dict[str, Any]:
    """Construye el dict que espera SimUnit a partir de un UnitSlot de la request."""
    uid = slot.unit_id.upper()
    template = UNIT_TEMPLATES.get(uid)
    lvl_mult = LEVEL_MULT.get(slot.level, 1.0)

    base_hp = (template.base_hp * lvl_mult) if template else 100.0
    base_dmg = (template.base_dmg * lvl_mult) if template else 10.0
    base_spd = template.atk_speed if template else 1.0

    return {
        "id": f"{team_prefix}{index + 1:02d}",
        "unit_id": uid,
        "level": slot.level,
        "hp": base_hp,
        "max_hp": base_hp,
        "damage": base_dmg,
        "attack_speed": base_spd,
        "position": slot.position,
    }


def _build_enemy_team(wave_number: int) -> list[dict[str, Any]]:
    """Devuelve la composición enemiga para la oleada dada (clamped al máximo definido)."""
    clamped = min(wave_number, MAX_WAVE)
    composition = WAVE_COMPOSITIONS[clamped]
    enemy_team = []
    for entry in composition:
        uid = entry["unit_id"]
        level = entry.get("level", 1)
        template = UNIT_TEMPLATES.get(uid)
        lvl_mult = LEVEL_MULT.get(level, 1.0)
        base_hp = (template.base_hp * lvl_mult) if template else 100.0
        base_dmg = (template.base_dmg * lvl_mult) if template else 10.0
        base_spd = template.atk_speed if template else 1.0
        enemy_team.append(
            {
                "id": entry["id"],
                "unit_id": uid,
                "level": level,
                "hp": base_hp,
                "max_hp": base_hp,
                "damage": base_dmg,
                "attack_speed": base_spd,
                "position": entry["position"],
            }
        )
    return enemy_team


def _build_initial_grid(
    player_team: list[dict[str, Any]],
    enemy_team: list[dict[str, Any]],
) -> list[GridCellOut | None]:
    """Construye el array de 9 celdas (posiciones 0-8) para el visualizador."""
    grid: list[GridCellOut | None] = [None] * 9
    for unit in player_team:
        pos = unit["position"]
        if 0 <= pos <= 8:
            grid[pos] = GridCellOut(
                id=unit["id"],
                unit_id=unit["unit_id"],
                current_hp=unit["hp"],
                max_hp=unit["max_hp"],
                is_stunned=False,
                team="player",
            )
    for unit in enemy_team:
        pos = unit["position"]
        if 0 <= pos <= 8:
            grid[pos] = GridCellOut(
                id=unit["id"],
                unit_id=unit["unit_id"],
                current_hp=unit["hp"],
                max_hp=unit["max_hp"],
                is_stunned=False,
                team="enemy",
            )
    return grid


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    status_code=status.HTTP_200_OK,
    summary="Simula una batalla y devuelve el replayData completo.",
)
async def simulate_combat(
    body: SimulateRequest,
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
) -> SimulateResponse:
    # 1. Autenticación obligatoria
    try:
        user = validate_init_data(x_telegram_init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    user_id: int | None = None
    try:
        raw_uid = user.get("id")
        if raw_uid is not None:
            user_id = int(raw_uid)
    except (ValueError, TypeError):
        pass

    # 2. Seed aleatoria para determinismo reproducible
    seed = random.randint(1, 999_999)

    # 3. Construir equipos
    player_team = [
        _build_team_dict(slot, "P", idx)
        for idx, slot in enumerate(body.player_formation)
    ]
    enemy_team = _build_enemy_team(body.wave_number)

    # 4. Ejecutar simulación
    result = simulate_battle(player_team, enemy_team, seed)

    # 5. Construir grid inicial para el visualizador
    initial_grid = _build_initial_grid(player_team, enemy_team)

    # 6. Persistir en base de datos (fire-and-forget sincrónico dentro del endpoint)
    async with async_session() as session:
        battle = Battle(
            id=uuid.uuid4(),
            user_id=user_id,
            wave_number=body.wave_number,
            seed=seed,
            winner=result["winner"],
            total_ticks=result["total_ticks"],
            player_formation=[slot.model_dump() for slot in body.player_formation],
            replay_log=result["replay_log"],
        )
        session.add(battle)
        await session.commit()

    # 7. Responder con el replayData completo
    return SimulateResponse(
        winner=result["winner"],
        total_ticks=result["total_ticks"],
        seed=seed,
        replay_log=result["replay_log"],
        initial_grid=initial_grid,
    )
