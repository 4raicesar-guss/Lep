"""Alta de jugadores: crea el estado inicial y entrega el Kit de Inicio."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Player, UserBuilding, UserFormation, UserResource, UserUnit
from app.engine.data import STARTER_PACK, STARTING_GRAIN


async def ensure_player_state(db: AsyncSession, telegram_id: int, user_data: dict[str, Any]) -> Player:
    """Garantiza Player, recursos, edificios, formación y Kit de Inicio. No hace commit.

    El Kit de Inicio se entrega solo si el jugador no tiene ninguna unidad
    (un jugador con unidades nunca baja a 0: el merge consume 3 y crea 1).
    """
    player = await db.scalar(select(Player).where(Player.telegram_id == telegram_id))
    if player is None:
        player = Player(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name", "Farmer"),
        )
        db.add(player)
        await db.flush()

    if await db.scalar(select(UserResource).where(UserResource.user_id == telegram_id)) is None:
        db.add(UserResource(user_id=telegram_id, grain=STARTING_GRAIN))

    if await db.scalar(select(UserBuilding).where(UserBuilding.user_id == telegram_id)) is None:
        db.add(UserBuilding(user_id=telegram_id, silo_level=1, galpon_level=1, boyero_level=1))

    if await db.scalar(select(UserFormation).where(UserFormation.user_id == telegram_id)) is None:
        db.add(UserFormation(user_id=telegram_id))

    unit_count = await db.scalar(
        select(func.count()).select_from(UserUnit).where(UserUnit.user_id == telegram_id)
    )
    if not unit_count:
        for unit_id in STARTER_PACK:
            db.add(UserUnit(user_id=telegram_id, unit_id=unit_id, level=1))

    await db.flush()
    return player
