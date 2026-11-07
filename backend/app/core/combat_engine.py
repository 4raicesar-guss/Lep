"""
Motor de Combate Determinista (Día 4) — Granja Táctica.

Implementa la simulación de combate por ticks en una cuadrícula 3x3 (posiciones 0 a 8),
asegurando determinismo estricto: misma seed + mismos inputs = mismo replay exacto.
"""

from __future__ import annotations

import random
from typing import Any

from app.engine.data import (  # noqa: F401  (re-export para compatibilidad)
    LEVEL_MULT,
    UNIT_ALIASES,
    UNIT_TEMPLATES,
    UnitTemplate,
)


def normalize_unit_id(raw_id: str) -> str:
    cleaned = str(raw_id).strip().lower()
    return UNIT_ALIASES.get(cleaned, str(raw_id).upper())


def get_grid_coords(position: int) -> tuple[int, int]:
    """Convierte una posición 0-8 en coordenadas (fila, columna) en grid 3x3."""
    return divmod(position, 3)


def manhattan_distance(pos1: int, pos2: int) -> int:
    """Calcula la distancia Manhattan entre dos posiciones (0 a 8) en el grid 3x3."""
    r1, c1 = divmod(pos1, 3)
    r2, c2 = divmod(pos2, 3)
    return abs(r1 - r2) + abs(c1 - c2)


def is_adjacent(pos1: int, pos2: int) -> bool:
    """Retorna True si dos casillas son ortogonalmente adyacentes (N, S, E, O)."""
    return manhattan_distance(pos1, pos2) == 1


def format_damage(val: float) -> int | float:
    """Formatea el daño de forma limpia (entero si no tiene decimales, o float con 2 decimales)."""
    rounded = round(val, 2)
    if rounded.is_integer():
        return int(rounded)
    return rounded


class SimUnit:
    """Representación mutable interna de una unidad durante la simulación."""
    __slots__ = (
        "attack_count",
        "base_attack_speed",
        "base_damage",
        "canonical_id",
        "damage_mitigation",
        "effective_attack_speed",
        "effective_damage",
        "hp",
        "id",
        "level",
        "max_hp",
        "position",
        "role",
        "stun_ticks",
        "team",
        "unit_id",
    )

    def __init__(self, raw: dict[str, Any], team: str):
        self.id = raw["id"]
        raw_uid = str(raw.get("unit_id", "U01"))
        self.unit_id = raw_uid
        self.canonical_id = normalize_unit_id(raw_uid)
        template = UNIT_TEMPLATES.get(self.canonical_id)

        self.level = int(raw.get("level", 1))
        lvl_mult = LEVEL_MULT.get(self.level, 1.0)

        default_hp = (template.base_hp * lvl_mult) if template else 100.0
        default_dmg = (template.base_dmg * lvl_mult) if template else 10.0
        default_spd = template.atk_speed if template else 1.0

        self.max_hp = float(raw.get("max_hp", raw.get("hp", default_hp)))
        self.hp = float(raw.get("hp", self.max_hp))
        self.base_damage = float(raw.get("damage", default_dmg))
        self.base_attack_speed = float(raw.get("attack_speed", default_spd))
        self.position = int(raw.get("position", 0))
        self.team = team

        self.role = template.role if template else "Daño"
        self.effective_attack_speed = self.base_attack_speed
        self.effective_damage = self.base_damage
        self.damage_mitigation = 0.0
        self.stun_ticks = 0
        self.attack_count = 0

    @property
    def is_alive(self) -> bool:
        return self.hp > 0.0


def apply_adjacency_synergies(team_units: list[SimUnit]) -> None:
    """
    Calcula y aplica las sinergias de adyacencia (N, S, E, O) antes de cada tick.
    """
    alive_units = [u for u in team_units if u.is_alive]
    pos_map: dict[int, SimUnit] = {u.position: u for u in alive_units}

    for unit in alive_units:
        r, c = get_grid_coords(unit.position)
        adj_allies: list[SimUnit] = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                npos = nr * 3 + nc
                if npos in pos_map:
                    adj_allies.append(pos_map[npos])

        num_adj = len(adj_allies)

        unit.effective_attack_speed = unit.base_attack_speed
        unit.effective_damage = unit.base_damage
        unit.damage_mitigation = 0.0

        # Sinergia U07 Perro Pastor: +20% daño y +15% vel atq a adyacentes
        dogs_adjacent = sum(1 for ally in adj_allies if ally.canonical_id == "U07")
        if dogs_adjacent > 0:
            unit.effective_damage *= (1.0 + 0.20 * dogs_adjacent)
            unit.effective_attack_speed *= (1.0 + 0.15 * dogs_adjacent)

        # Sinergia U03 Gallo Asesino: +15% vel atq por cada aliado adyacente (máx. +60%)
        if unit.canonical_id == "U03":
            gallo_bonus = min(0.60, 0.15 * num_adj)
            unit.effective_attack_speed *= (1.0 + gallo_bonus)

        # Sinergia U04 Cabra Francotiradora: +25% daño si está adyacente a un Tanque
        if unit.canonical_id == "U04":
            has_tank_neighbor = any(ally.role == "Tanque" or ally.canonical_id in ("U01", "U02") for ally in adj_allies)
            if has_tank_neighbor:
                unit.effective_damage *= 1.25

        # Sinergia U01 Cerdo Blindado: reduce daño recibido en 10% por aliado adyacente (máx. 40%)
        if unit.canonical_id == "U01":
            unit.damage_mitigation = min(0.40, 0.10 * num_adj)

        # Sinergia U06 Oveja Sanadora: curación de soporte a adyacentes
        if unit.canonical_id == "U06" and adj_allies:
            lvl_mult = LEVEL_MULT.get(unit.level, 1.0)
            if num_adj >= 2:
                heal_val = 30.0 * lvl_mult
                for ally in adj_allies:
                    ally.hp = min(ally.max_hp, ally.hp + heal_val)
            else:
                heal_val = 40.0 * lvl_mult
                most_wounded = min(adj_allies, key=lambda a: a.hp / a.max_hp)
                most_wounded.hp = min(most_wounded.max_hp, most_wounded.hp + heal_val)


def select_target(actor: SimUnit, enemies: list[SimUnit]) -> SimUnit | None:
    """
    Selecciona el objetivo más cercano por distancia Manhattan.
    En caso de empate en distancia, desempata por el ID numérico más bajo (determinista).
    """
    alive_enemies = [e for e in enemies if e.is_alive]
    if not alive_enemies:
        return None

    return min(
        alive_enemies,
        key=lambda e: (manhattan_distance(actor.position, e.position), e.id)
    )


def simulate_battle(player_team: list, enemy_team: list, seed: int, max_ticks: int = 200) -> dict:
    """
    Simula una batalla completa entre el equipo del jugador y el equipo enemigo.

    Args:
        player_team: Lista de diccionarios con {id, unit_id, level, hp, max_hp, damage, attack_speed, position}.
        enemy_team: Lista de diccionarios con {id, unit_id, level, hp, max_hp, damage, attack_speed, position}.
        seed: Semilla aleatoria entera para inicializar el generador de números aleatorios local.
        max_ticks: Límite de seguridad de ticks para evitar bucles infinitos (por defecto 200).

    Returns:
        dict: {
            "winner": "player" | "enemy",
            "total_ticks": int,
            "replay_log": list[dict]
        }
    """
    rng = random.Random(seed)  # noqa: F841
    player_units = [SimUnit(u, "player") for u in player_team]
    enemy_units = [SimUnit(u, "enemy") for u in enemy_team]

    replay_log: list[dict[str, Any]] = []
    tick = 0

    while tick < max_ticks:
        tick += 1

        player_alive = [u for u in player_units if u.is_alive]
        enemy_alive = [u for u in enemy_units if u.is_alive]

        if not player_alive or not enemy_alive:
            break

        # 1. Aplicar sinergias de adyacencia ANTES de calcular el daño del tick
        apply_adjacency_synergies(player_units)
        apply_adjacency_synergies(enemy_units)

        # 2. Orden de acción: mayor velocidad de ataque primero
        all_units = [u for u in (player_units + enemy_units) if u.is_alive]
        all_units.sort(
            key=lambda u: (-u.effective_attack_speed, 0 if u.team == "player" else 1, u.id)
        )

        # 3. Fase de acciones del tick
        for actor in all_units:
            if not actor.is_alive:
                continue

            if actor.stun_ticks > 0:
                actor.stun_ticks -= 1
                continue

            opponents = enemy_units if actor.team == "player" else player_units
            target = select_target(actor, opponents)

            if not target or not target.is_alive:
                break

            raw_damage = actor.effective_damage
            mitigated_damage = raw_damage * (1.0 - target.damage_mitigation)
            actual_damage = max(1.0, mitigated_damage)

            target.hp = max(0.0, target.hp - actual_damage)
            formatted_dmg = format_damage(actual_damage)

            replay_log.append({
                "tick": tick,
                "actor_id": actor.id,
                "action": "attack",
                "target_id": target.id,
                "damage": formatted_dmg,
            })

            actor.attack_count += 1

            # Sinergia U08 Espantapájaros: aturde al objetivo cada 3 ataques por 1 tick
            if actor.canonical_id == "U08" and actor.attack_count % 3 == 0:
                target.stun_ticks = max(target.stun_ticks, 1)

            # Sinergia U05 Pato Bombardero: daño en área (AoE) a casillas adyacentes al target
            if actor.canonical_id == "U05":
                team_of_actor = player_units if actor.team == "player" else enemy_units
                adj_pato_count = sum(
                    1 for ally in team_of_actor
                    if ally.is_alive and ally.id != actor.id and is_adjacent(actor.position, ally.position)
                )
                aoe_mult = 0.60 * (1.0 + 0.15 * adj_pato_count)
                splash_raw = actual_damage * aoe_mult

                for splash_target in opponents:
                    if splash_target.is_alive and splash_target.id != target.id and is_adjacent(splash_target.position, target.position):
                        splash_mitigated = splash_raw * (1.0 - splash_target.damage_mitigation)
                        splash_dmg = max(1.0, splash_mitigated)
                        splash_target.hp = max(0.0, splash_target.hp - splash_dmg)
                        replay_log.append({
                            "tick": tick,
                            "actor_id": actor.id,
                            "action": "attack",
                            "target_id": splash_target.id,
                            "damage": format_damage(splash_dmg),
                        })

            # Sinergia U02 Toro Bravo: contraataque si tiene al menos 1 aliado adyacente y recibe ataque a distancia corta
            if target.canonical_id == "U02" and target.is_alive:
                target_team = enemy_units if target.team == "enemy" else player_units
                has_adj = any(ally.is_alive and is_adjacent(target.position, ally.position) for ally in target_team if ally.id != target.id)
                if has_adj and manhattan_distance(target.position, actor.position) <= 1:
                    counter_dmg = max(1.0, 18.0 * LEVEL_MULT.get(target.level, 1.0) * (1.0 - actor.damage_mitigation))
                    actor.hp = max(0.0, actor.hp - counter_dmg)
                    replay_log.append({
                        "tick": tick,
                        "actor_id": target.id,
                        "action": "attack",
                        "target_id": actor.id,
                        "damage": format_damage(counter_dmg),
                    })

            if not any(u.is_alive for u in player_units) or not any(u.is_alive for u in enemy_units):
                break

        player_any_alive = any(u.is_alive for u in player_units)
        enemy_any_alive = any(u.is_alive for u in enemy_units)
        if not player_any_alive or not enemy_any_alive:
            break

    player_survivors = [u for u in player_units if u.is_alive]
    enemy_survivors = [u for u in enemy_units if u.is_alive]

    if player_survivors and not enemy_survivors:
        winner = "player"
    elif enemy_survivors and not player_survivors:
        winner = "enemy"
    else:
        player_hp_pct = sum(u.hp / u.max_hp for u in player_units) / max(1, len(player_units))
        enemy_hp_pct = sum(u.hp / u.max_hp for u in enemy_units) / max(1, len(enemy_units))
        winner = "player" if player_hp_pct > enemy_hp_pct else "enemy"

    return {
        "winner": winner,
        "total_ticks": tick,
        "replay_log": replay_log,
    }
