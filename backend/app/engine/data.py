"""
Fuente única de verdad de los datos de juego (backend manda).

El frontend (`frontend/src/lib/game.ts`) espeja los campos de presentación
(nombre, sprite, rol, hp base) y se mantiene sincronizado a mano con este archivo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitTemplate:
    id: str
    name: str
    role: str
    base_hp: float
    base_dmg: float
    atk_speed: float
    range_type: str = "melee"
    is_aoe: bool = False
    is_healer: bool = False
    is_buffer: bool = False
    is_stunner: bool = False


UNIT_TEMPLATES: dict[str, UnitTemplate] = {
    "U01": UnitTemplate("U01", "Cerdo Blindado", "Tanque", 480.0, 14.0, 1.0, "melee"),
    "U02": UnitTemplate("U02", "Toro Bravo", "Tanque", 420.0, 22.0, 1.1, "melee"),
    "U03": UnitTemplate("U03", "Gallo Asesino", "Daño", 150.0, 38.0, 1.8, "melee"),
    "U04": UnitTemplate("U04", "Cabra Francotiradora", "Daño", 130.0, 46.0, 1.2, "ranged"),
    "U05": UnitTemplate("U05", "Pato Bombardero", "Daño", 160.0, 28.0, 1.25, "ranged", is_aoe=True),
    "U06": UnitTemplate("U06", "Oveja Sanadora", "Soporte", 220.0, 10.0, 1.0, "ranged", is_healer=True),
    "U07": UnitTemplate("U07", "Perro Pastor", "Soporte", 260.0, 18.0, 1.3, "melee", is_buffer=True),
    "U08": UnitTemplate("U08", "Espantapájaros Aturdidor", "Control", 310.0, 16.0, 1.0, "ranged", is_stunner=True),
}

UNIT_ALIASES: dict[str, str] = {
    "cerdo": "U01", "cerdo_blindado": "U01", "u01": "U01",
    "toro": "U02", "toro_bravo": "U02", "u02": "U02",
    "gallo": "U03", "gallo_asesino": "U03", "u03": "U03",
    "cabra": "U04", "cabra_francotiradora": "U04", "u04": "U04",
    "pato": "U05", "pato_bombardero": "U05", "u05": "U05",
    "oveja": "U06", "oveja_sanadora": "U06", "u06": "U06",
    "perro": "U07", "perro_pastor": "U07", "u07": "U07",
    "espantapajaros": "U08", "espantapajaros_aturdidor": "U08", "u08": "U08",
}

LEVEL_MULT: dict[int, float] = {
    1: 1.0,
    2: 1.8,
    3: 3.24,
}

# --- Economía de unidades (valores temporales, ajustables) ---------------------

# Coste en grano de comprar directamente una unidad nivel 1 (POST /api/units/summon).
SUMMON_COST: int = 100

# Kit de inicio entregado al crear un jugador nuevo.
STARTER_PACK: tuple[str, ...] = ("U01", "U03", "U06")

# Grano inicial de un jugador nuevo.
STARTING_GRAIN: int = 500
