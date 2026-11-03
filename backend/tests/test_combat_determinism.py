"""
Tests de Determinismo y Rendimiento del Motor de Combate (Día 4).
Compatible tanto con pytest como con unittest standard library.
"""

import time
import unittest

from app.core.combat_engine import simulate_battle


def get_sample_teams():
    """Genera equipos representativos para las pruebas con unidades del MVP."""
    player_team = [
        {"id": 1, "unit_id": "U01", "level": 1, "hp": 480, "max_hp": 480, "damage": 14, "attack_speed": 1.0, "position": 0},
        {"id": 2, "unit_id": "U03", "level": 1, "hp": 150, "max_hp": 150, "damage": 38, "attack_speed": 1.8, "position": 1},
        {"id": 3, "unit_id": "U07", "level": 1, "hp": 260, "max_hp": 260, "damage": 18, "attack_speed": 1.3, "position": 4},
        {"id": 4, "unit_id": "U04", "level": 1, "hp": 130, "max_hp": 130, "damage": 46, "attack_speed": 1.2, "position": 3},
    ]

    enemy_team = [
        {"id": 101, "unit_id": "U01", "level": 1, "hp": 480, "max_hp": 480, "damage": 14, "attack_speed": 1.0, "position": 0},
        {"id": 102, "unit_id": "U02", "level": 1, "hp": 420, "max_hp": 420, "damage": 22, "attack_speed": 1.1, "position": 1},
        {"id": 103, "unit_id": "U05", "level": 1, "hp": 160, "max_hp": 160, "damage": 28, "attack_speed": 1.25, "position": 4},
    ]

    return player_team, enemy_team


class TestCombatDeterminism(unittest.TestCase):

    def test_combat_determinism_identical_replays(self):
        """
        Validación Obligatoria:
        Ejecuta simulate_battle dos veces con la EXACTA misma seed y equipos.
        assert log1 == log2 para garantizar que el replay es idéntico bit a bit.
        """
        player_team, enemy_team = get_sample_teams()
        seed = 42069

        # Ejecución 1
        result1 = simulate_battle(player_team, enemy_team, seed=seed)
        log1 = result1["replay_log"]

        # Ejecución 2
        result2 = simulate_battle(player_team, enemy_team, seed=seed)
        log2 = result2["replay_log"]

        # Comprobación de igualdad estricta bit a bit
        self.assertEqual(log1, log2, "El replay_log debe ser idéntico bit a bit entre ejecuciones con la misma seed")
        self.assertEqual(result1["winner"], result2["winner"], "El ganador debe ser idéntico")
        self.assertEqual(result1["total_ticks"], result2["total_ticks"], "El número de ticks debe ser idéntico")
        self.assertGreater(len(log1), 0, "El replay_log no debe estar vacío")

    def test_combat_performance_10_simulations_under_200ms(self):
        """
        Validación Obligatoria:
        Mide el tiempo de ejecución de 10 simulaciones consecutivas.
        Debe ser < 200ms en total.
        """
        player_team, enemy_team = get_sample_teams()
        num_simulations = 10

        start_time = time.perf_counter()
        for i in range(num_simulations):
            simulate_battle(player_team, enemy_team, seed=1000 + i)
        elapsed_time = time.perf_counter() - start_time

        elapsed_ms = elapsed_time * 1000.0
        print(f"\nTiempo total para {num_simulations} simulaciones: {elapsed_ms:.2f}ms (promedio: {elapsed_ms / num_simulations:.2f}ms/sim)")

        self.assertLess(elapsed_time, 0.200, f"10 simulaciones consecutivas tardaron {elapsed_ms:.2f}ms, debe ser < 200ms")

    def test_targeting_manhattan_distance_and_tiebreak(self):
        """
        Targeting: cada unidad ataca al enemigo vivo más cercano en el tablero
        (distancia Manhattan). En caso de empate, desempata por menor ID de unidad.
        """
        actor_pos = 0  # (0, 0)

        # Enemigo A en pos 1 -> dist = abs(0-0) + abs(0-1) = 1
        # Enemigo B en pos 8 -> dist = abs(0-2) + abs(0-2) = 4
        team_p = [{"id": 1, "unit_id": "U03", "level": 1, "hp": 150, "max_hp": 150, "damage": 50, "attack_speed": 1.0, "position": actor_pos}]
        team_e = [
            {"id": 20, "unit_id": "U01", "level": 1, "hp": 100, "max_hp": 100, "damage": 10, "attack_speed": 0.5, "position": 8},
            {"id": 10, "unit_id": "U01", "level": 1, "hp": 100, "max_hp": 100, "damage": 10, "attack_speed": 0.5, "position": 1},
        ]

        res = simulate_battle(team_p, team_e, seed=1)
        first_action = res["replay_log"][0]
        self.assertEqual(first_action["actor_id"], 1)
        self.assertEqual(first_action["target_id"], 10, "Debe seleccionar al enemigo más cercano (pos 1 frente a pos 8)")

        # Caso de empate en distancia Manhattan:
        # Actor en pos 4 (1, 1)
        # Enemigo en pos 3 (1, 0) -> dist = 1, ID = 50
        # Enemigo en pos 5 (1, 2) -> dist = 1, ID = 25
        team_e_tie = [
            {"id": 50, "unit_id": "U01", "level": 1, "hp": 100, "max_hp": 100, "damage": 10, "attack_speed": 0.5, "position": 3},
            {"id": 25, "unit_id": "U01", "level": 1, "hp": 100, "max_hp": 100, "damage": 10, "attack_speed": 0.5, "position": 5},
        ]
        team_p_center = [{"id": 1, "unit_id": "U03", "level": 1, "hp": 150, "max_hp": 150, "damage": 50, "attack_speed": 1.0, "position": 4}]

        res_tie = simulate_battle(team_p_center, team_e_tie, seed=1)
        first_tie_action = res_tie["replay_log"][0]
        self.assertEqual(first_tie_action["target_id"], 25, "En empate de distancia (ambas dist=1), debe priorizar el ID más bajo (25 vs 50)")

    def test_action_order_by_attack_speed(self):
        """
        Las unidades con mayor velocidad de ataque actúan primero en cada tick.
        """
        team_p = [
            {"id": 1, "unit_id": "U01", "level": 1, "hp": 200, "max_hp": 200, "damage": 10, "attack_speed": 1.0, "position": 0},
            {"id": 2, "unit_id": "U03", "level": 1, "hp": 200, "max_hp": 200, "damage": 10, "attack_speed": 2.5, "position": 8},
        ]
        team_e = [
            {"id": 3, "unit_id": "U01", "level": 1, "hp": 200, "max_hp": 200, "damage": 10, "attack_speed": 1.5, "position": 4},
        ]

        res = simulate_battle(team_p, team_e, seed=1)
        tick1_actors = [action["actor_id"] for action in res["replay_log"] if action["tick"] == 1]
        
        # Orden de velocidad: ID 2 (2.5) -> ID 3 (1.5) -> ID 1 (1.0)
        self.assertEqual(tick1_actors[:3], [2, 3, 1], f"El orden de acción esperado era [2, 3, 1], se obtuvo {tick1_actors[:3]}")

    def test_adjacency_synergies(self):
        """
        Verifica que las sinergias de adyacencia modifiquen correctamente daño y velocidad:
        - Perro Pastor (+20% daño a adyacentes)
        - Cerdo Blindado (-10% daño recibido por aliado adyacente)
        """
        # Escenario 1: Cerdo solo (sin aliados adyacentes) recibe 100 de daño
        p_solo_cerdo = [{"id": 1, "unit_id": "U01", "level": 1, "hp": 480, "max_hp": 480, "damage": 10, "attack_speed": 0.5, "position": 0}]
        e_attacker = [{"id": 99, "unit_id": "U04", "level": 1, "hp": 500, "max_hp": 500, "damage": 100, "attack_speed": 1.5, "position": 8}]

        res_solo = simulate_battle(p_solo_cerdo, e_attacker, seed=1)
        dmg_solo = res_solo["replay_log"][0]["damage"]
        self.assertEqual(dmg_solo, 100, "Cerdo sin adyacentes debe recibir el 100% del daño")

        # Escenario 2: Cerdo con 2 aliados adyacentes (pos 0 adyacente a pos 1 y pos 3) -> 20% mitigación (daño 80)
        p_protected_cerdo = [
            {"id": 1, "unit_id": "U01", "level": 1, "hp": 480, "max_hp": 480, "damage": 10, "attack_speed": 0.5, "position": 0},
            {"id": 2, "unit_id": "U03", "level": 1, "hp": 200, "max_hp": 200, "damage": 10, "attack_speed": 0.5, "position": 1},
            {"id": 3, "unit_id": "U03", "level": 1, "hp": 200, "max_hp": 200, "damage": 10, "attack_speed": 0.5, "position": 3},
        ]
        # Posicionar al atacante enemigo más cerca de Cerdo (pos 0) que de los otros
        e_attacker_close = [{"id": 99, "unit_id": "U04", "level": 1, "hp": 500, "max_hp": 500, "damage": 100, "attack_speed": 1.5, "position": 0}]

        res_mitigated = simulate_battle(p_protected_cerdo, e_attacker_close, seed=1)
        dmg_mitigated = res_mitigated["replay_log"][0]["damage"]
        self.assertEqual(dmg_mitigated, 80, f"Cerdo con 2 adyacentes debe mitigar el 20% del daño (esperado 80, obtenido {dmg_mitigated})")


if __name__ == "__main__":
    unittest.main()
