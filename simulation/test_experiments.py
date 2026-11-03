"""
Pruebas analíticas de balance para la Oleada 10.
Evalúa:
1) ¿Puede un equipo de solo Nivel 1 vencer al Jefe de la Oleada 10?
2) ¿Qué pasa con equipos de tamaño estándar (4, 5, 6 unidades) vs tamaño máximo (9)?
3) Impacto de la habilidad especial del Jefe (Terremoto AoE).
"""

from simulation.combat_sim import TEMPLATES, LEVEL_MULT, simulate_battle

def run_experiments():
    # Boss: "El Gran Jabalí Devastador"
    # Stats base del jefe: basado en Toro Bravo (HP 450, Dmg 25, Vel 1.1) multiplicado x3:
    # HP = 1350, Dmg = 75, Vel = 1.1 (DPS = 82.5)
    # Escolta de la Oleada 10:
    # 1x Oveja Sanadora Lv1 (cura al boss 40 HP/s)
    # 1x Espantapájaros Lv1 (aturde 2s al frente del jugador cada 3 ataques)
    
    enemy_wave_10 = [
        ("espantapajaros", 1, (0, 0), False),
        ("toro", 1, (0, 1), True),      # Jefe x3 stats
        ("oveja", 1, (0, 2), False),
    ]

    print("--- EXPERIMENTO 1: Equipos de 5 unidades Nivel 1 (Despliegue realista por economía) ---")
    # A wave 10, un jugador que gastó grano en re-rolls o compras tiene 5 unidades en campo:
    comp_5_lvl1 = [
        ("cerdo", 1, (0, 1)),
        ("cabra", 1, (1, 1)),
        ("gallo", 1, (0, 0)),
        ("oveja", 1, (1, 0)),
        ("perro", 1, (1, 2)),
    ]
    r5 = simulate_battle(comp_5_lvl1, enemy_wave_10)
    print(f"5 unidades Lv1: Victoria={r5['won']}, Tiempo={r5['time']}s, Vivos={r5['player_alive_count']}, HP Boss={r5['boss_remaining_hp']}")

    print("\n--- EXPERIMENTO 2: Equipos de 6 unidades Nivel 1 ---")
    comp_6_lvl1 = comp_5_lvl1 + [("pato", 1, (2, 1))]
    r6 = simulate_battle(comp_6_lvl1, enemy_wave_10)
    print(f"6 unidades Lv1: Victoria={r6['won']}, Tiempo={r6['time']}s, Vivos={r6['player_alive_count']}, HP Boss={r6['boss_remaining_hp']}")

    print("\n--- EXPERIMENTO 3: Equipos de 7 unidades Nivel 1 ---")
    comp_7_lvl1 = comp_6_lvl1 + [("cerdo", 1, (0, 2))]
    r7 = simulate_battle(comp_7_lvl1, enemy_wave_10)
    print(f"7 unidades Lv1: Victoria={r7['won']}, Tiempo={r7['time']}s, Vivos={r7['player_alive_count']}, HP Boss={r7['boss_remaining_hp']}")

    print("\n--- EXPERIMENTO 4: Equipos con Unidades Nivel 2 (Merge) ---")
    # Caso 4A: 1 unidad Nivel 2 (Cabra Lv2 + 4 unidades Lv1)
    comp_1_lvl2 = [
        ("cerdo", 1, (0, 1)),
        ("cabra", 2, (1, 1)), # Merged
        ("gallo", 1, (0, 0)),
        ("oveja", 1, (1, 0)),
        ("perro", 1, (1, 2)),
    ]
    r_1_lvl2 = simulate_battle(comp_1_lvl2, enemy_wave_10)
    print(f"1 unidad Lv2 (Cabra) + 4 Lv1: Victoria={r_1_lvl2['won']}, Tiempo={r_1_lvl2['time']}s, Vivos={r_1_lvl2['player_alive_count']}, HP Boss={r_1_lvl2['boss_remaining_hp']}")

    # Caso 4B: 2 unidades Nivel 2 (Tanque Lv2 + DPS Lv2 + 3 unidades Lv1)
    comp_2_lvl2 = [
        ("cerdo", 2, (0, 1)), # Tanque Lv2
        ("cabra", 2, (1, 1)), # DPS Lv2
        ("gallo", 1, (0, 0)),
        ("oveja", 1, (1, 0)),
        ("perro", 1, (1, 2)),
    ]
    r_2_lvl2 = simulate_battle(comp_2_lvl2, enemy_wave_10)
    print(f"2 unidades Lv2 (Cerdo + Cabra) + 3 Lv1: Victoria={r_2_lvl2['won']}, Tiempo={r_2_lvl2['time']}s, Vivos={r_2_lvl2['player_alive_count']}, HP Boss={r_2_lvl2['boss_remaining_hp']}")

    # Caso 4C: 1 unidad Nivel 3 (Cabra Lv3 + Tanque Lv2 + Soporte)
    comp_lvl3 = [
        ("cerdo", 2, (0, 1)),
        ("cabra", 3, (1, 1)), # DPS Lv3
        ("oveja", 1, (1, 0)),
        ("perro", 1, (1, 2)),
    ]
    r_lvl3 = simulate_battle(comp_lvl3, enemy_wave_10)
    print(f"1 unidad Lv3 (Cabra) + 1 Lv2 (Cerdo) + 2 Lv1: Victoria={r_lvl3['won']}, Tiempo={r_lvl3['time']}s, Vivos={r_lvl3['player_alive_count']}, HP Boss={r_lvl3['boss_remaining_hp']}")

if __name__ == "__main__":
    run_experiments()
