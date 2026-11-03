"""
Simulación de combate para Granja Táctica (MVP Día 3).
Evalúa composiciones de unidades contra la Oleada 10.
"""

from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class UnitTemplate:
    id: str
    name: str
    role: str
    base_hp: float
    base_dmg: float
    atk_speed: float
    cost: int
    range_type: str = "melee"
    is_aoe: bool = False
    is_healer: bool = False
    is_buffer: bool = False
    is_stunner: bool = False

TEMPLATES = {
    "cerdo": UnitTemplate("U01", "Cerdo Blindado", "Tanque", 480, 14, 1.0, 80, "melee"),
    "toro": UnitTemplate("U02", "Toro Bravo", "Tanque", 420, 22, 1.1, 110, "melee"),
    "gallo": UnitTemplate("U03", "Gallo Asesino", "Daño", 150, 38, 1.8, 90, "melee"),
    "cabra": UnitTemplate("U04", "Cabra Francotiradora", "Daño", 130, 46, 1.2, 130, "ranged"),
    "pato": UnitTemplate("U05", "Pato Bombardero", "Daño", 160, 28, 1.25, 140, "ranged", is_aoe=True),
    "oveja": UnitTemplate("U06", "Oveja Sanadora", "Soporte", 220, 10, 1.0, 100, "ranged", is_healer=True),
    "perro": UnitTemplate("U07", "Perro Pastor", "Soporte", 260, 18, 1.3, 120, "melee", is_buffer=True),
    "espantapajaros": UnitTemplate("U08", "Espantapájaros Aturdidor", "Control", 310, 16, 1.0, 150, "ranged", is_stunner=True),
}

# Multiplicadores de Merge por Nivel:
# Nivel 1: 1.0x
# Nivel 2: 1.8x
# Nivel 3: 3.24x (1.8 * 1.8)
LEVEL_MULT = {
    1: 1.0,
    2: 1.8,
    3: 3.24
}

@dataclass
class CombatUnit:
    template: UnitTemplate
    level: int
    grid_pos: Tuple[int, int]  # (fila 0-2, col 0-2)
    team: str  # 'player' o 'enemy'
    current_hp: float = 0.0
    max_hp: float = 0.0
    dmg: float = 0.0
    atk_speed: float = 0.0
    attack_cooldown: float = 0.0
    stun_timer: float = 0.0
    hit_counter: int = 0
    is_boss: bool = False
    boss_ability_counter: int = 0

    def __post_init__(self):
        mult = LEVEL_MULT[self.level]
        if self.is_boss:
            # Stats x3 según diseño de la Oleada 10
            mult *= 3.0
        self.max_hp = self.template.base_hp * mult
        self.current_hp = self.max_hp
        self.dmg = self.template.base_dmg * mult
        self.atk_speed = self.template.atk_speed

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

def get_manhattan_dist(pos1: Tuple[int, int], pos2: Tuple[int, int], team1: str, team2: str) -> float:
    # Tablero: Player (filas 0,1,2 donde 0 es frente) vs Enemy (filas 0,1,2 donde 0 es frente).
    if team1 == team2:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    else:
        return (pos1[0] + pos2[0] + 1) + abs(pos1[1] - pos2[1])

def get_adjacent_allies(unit: CombatUnit, army: List[CombatUnit]) -> List[CombatUnit]:
    adj = []
    r, c = unit.grid_pos
    for ally in army:
        if ally is not unit and ally.is_alive:
            ar, ac = ally.grid_pos
            if abs(r - ar) + abs(c - ac) == 1:
                adj.append(ally)
    return adj

def simulate_battle(player_units_config: List[Tuple[str, int, Tuple[int, int]]], 
                     enemy_units_config: List[Tuple[str, int, Tuple[int, int], bool]],
                     max_time: float = 60.0) -> dict:
    player_army = [CombatUnit(TEMPLATES[k], lvl, pos, 'player') for k, lvl, pos in player_units_config]
    enemy_army = [CombatUnit(TEMPLATES[k], lvl, pos, 'enemy', is_boss=boss) for k, lvl, pos, boss in enemy_units_config]

    dt = 0.05
    time = 0.0

    while time < max_time:
        time += dt

        player_alive = [u for u in player_army if u.is_alive]
        enemy_alive = [u for u in enemy_army if u.is_alive]

        if not player_alive or not enemy_alive:
            break

        all_units = player_alive + enemy_alive

        # Actualizar cooldowns y aturdimientos
        for u in all_units:
            if u.stun_timer > 0:
                u.stun_timer -= dt
            if u.attack_cooldown > 0:
                u.attack_cooldown -= dt

        # Acciones
        for u in all_units:
            if not u.is_alive or u.stun_timer > 0 or u.attack_cooldown > 0:
                continue

            current_team_alive = player_alive if u.team == 'player' else enemy_alive
            opp_team_alive = enemy_alive if u.team == 'player' else player_alive

            if not opp_team_alive:
                break

            adj_allies = get_adjacent_allies(u, current_team_alive)
            num_adj = len(adj_allies)

            effective_dmg = u.dmg
            effective_atk_speed = u.atk_speed

            # Sinergias
            # Gallo: +15% atq speed por aliado adyacente
            if u.template.id == "U03":
                effective_atk_speed *= (1.0 + 0.15 * num_adj)
            # Perro: adyacentes reciben +20% daño y +15% vel atq
            for ally in adj_allies:
                if ally.template.id == "U07":
                    effective_dmg *= 1.20
                    effective_atk_speed *= 1.15

            # Cabra: +25% daño si adyacente a Tanque
            if u.template.id == "U04":
                if any(ally.template.role == "Tanque" for ally in adj_allies):
                    effective_dmg *= 1.25

            # Healer: Oveja Sanadora
            if u.template.is_healer:
                heal_val = (40.0 if num_adj < 2 else 30.0) * LEVEL_MULT[u.level]
                if num_adj >= 2:
                    for ally in adj_allies:
                        ally.current_hp = min(ally.max_hp, ally.current_hp + heal_val)
                else:
                    target_heal = None
                    lowest_ratio = 1.0
                    for c in (adj_allies if num_adj > 0 else current_team_alive):
                        ratio = c.current_hp / c.max_hp
                        if ratio < lowest_ratio and ratio < 1.0:
                            lowest_ratio = ratio
                            target_heal = c
                    if target_heal:
                        target_heal.current_hp = min(target_heal.max_hp, target_heal.current_hp + heal_val)
                u.attack_cooldown = 1.0 / effective_atk_speed
                continue

            # Prioridad de target: enemigo más cercano
            best_target = None
            min_dist = 999.0
            for opp in opp_team_alive:
                dist = get_manhattan_dist(u.grid_pos, opp.grid_pos, u.team, opp.team)
                if dist < min_dist:
                    min_dist = dist
                    best_target = opp

            if not best_target:
                continue

            # Mitigación por Cerdo Blindado adyacente o en objetivo
            target_adj = get_adjacent_allies(best_target, opp_team_alive)
            mitigation = 0.0
            if best_target.template.id == "U01":
                mitigation = min(0.40, len(target_adj) * 0.10)

            actual_dmg = effective_dmg * (1.0 - mitigation)
            best_target.current_hp -= actual_dmg

            # Contraataque de Toro Bravo si es golpeado cuerpo a cuerpo
            if best_target.template.id == "U02" and len(target_adj) >= 1 and u.template.range_type == "melee":
                u.current_hp -= 18.0 * LEVEL_MULT[best_target.level]

            # Daño AoE de Pato Bombardero
            if u.template.is_aoe:
                aoe_mult = 0.60 * (1.0 + 0.15 * num_adj)
                for opp in opp_team_alive:
                    if opp is not best_target:
                        if get_manhattan_dist(opp.grid_pos, best_target.grid_pos, opp.team, opp.team) == 1:
                            opp.current_hp -= actual_dmg * aoe_mult

            # Control: Espantapájaros Aturdidor
            if u.template.is_stunner:
                u.hit_counter += 1
                if u.hit_counter >= 3:
                    u.hit_counter = 0
                    stun_dur = 0.5 if best_target.is_boss else 2.0
                    best_target.stun_timer = max(best_target.stun_timer, stun_dur)

            # Habilidad del Jefe (Oleada 10):
            # Terremoto cada 4 ataques: 80 dmg global + stun 1s
            if u.is_boss:
                u.boss_ability_counter += 1
                if u.boss_ability_counter >= 4:
                    u.boss_ability_counter = 0
                    for p in player_alive:
                        p.current_hp -= 80.0
                        p.stun_timer = 1.0

            u.attack_cooldown = 1.0 / effective_atk_speed

    player_alive = [u for u in player_army if u.is_alive]
    enemy_alive = [u for u in enemy_army if u.is_alive]

    boss_hp = [u.current_hp for u in enemy_army if u.is_boss]

    return {
        "won": len(player_alive) > 0 and len(enemy_alive) == 0,
        "time": round(time, 2),
        "player_alive_count": len(player_alive),
        "enemy_alive_count": len(enemy_alive),
        "boss_remaining_hp": boss_hp[0] if boss_hp else 0
    }

if __name__ == "__main__":
    # Oleada 10: Jefe Toro (Gran Jabalí Titánico stats x3) en (0, 1),
    # Oveja en (1, 1), Espantapájaros en (0, 0)
    enemy_wave_10 = [
        ("espantapajaros", 1, (0, 0), False),
        ("toro", 1, (0, 1), True),      # Jefe (stats x3)
        ("oveja", 1, (1, 1), False)
    ]

    print("=== TEST 1: 9 Unidades Nivel 1 en formación óptima ===")
    # 9 slots en 3x3 llenos de nivel 1:
    # Fila 0 (Frente): Cerdo (0,0), Toro (0,1), Cerdo (0,2)
    # Fila 1 (Media): Perro (1,0), Cabra (1,1), Oveja (1,2)
    # Fila 2 (Atrás): Cabra (2,0), Pato (2,1), Gallo (2,2)
    comp_all_lvl1 = [
        ("cerdo", 1, (0, 0)),
        ("toro", 1, (0, 1)),
        ("cerdo", 1, (0, 2)),
        ("perro", 1, (1, 0)),
        ("cabra", 1, (1, 1)),
        ("oveja", 1, (1, 2)),
        ("cabra", 1, (2, 0)),
        ("pato", 1, (2, 1)),
        ("gallo", 1, (2, 2)),
    ]
    res1 = simulate_battle(comp_all_lvl1, enemy_wave_10)
    print(f"Resultado Nivel 1: {res1}")

    print("\n=== TEST 2: Composición A (Cabra Nivel 2 + Tanque Nivel 2 + otros Lv1) ===")
    comp_a = [
        ("cerdo", 2, (0, 1)),
        ("toro", 1, (0, 0)),
        ("cerdo", 1, (0, 2)),
        ("cabra", 2, (1, 1)),
        ("perro", 1, (1, 0)),
        ("oveja", 1, (1, 2)),
        ("pato", 1, (2, 1)),
    ]
    res_a = simulate_battle(comp_a, enemy_wave_10)
    print(f"Resultado Comp A: {res_a}")

    print("\n=== TEST 3: Composición B (Burst / Stun: Espantapájaros Lv2 + Gallo Lv2 + Cabra Lv2) ===")
    comp_b = [
        ("toro", 2, (0, 1)),
        ("cerdo", 1, (0, 0)),
        ("espantapajaros", 2, (1, 1)),
        ("gallo", 2, (0, 2)),
        ("perro", 1, (1, 0)),
        ("oveja", 1, (1, 2)),
    ]
    res_b = simulate_battle(comp_b, enemy_wave_10)
    print(f"Resultado Comp B: {res_b}")
