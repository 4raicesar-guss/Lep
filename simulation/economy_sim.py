"""Simulación Monte Carlo de la economía de Granja Táctica.

5 arquetipos, 500 agentes, 30 días.
Calcula curva promedio diaria acumulando en array daily_grains.
"""
import random
import statistics

DAYS = 30
NUM_AGENTS = 500
SEED = 42

# Arquetipos: (nombre, prob_cosecha, grano_por_cosecha, consumo_diario, prob_evento_negativo)
ARCHETYPES = [
    ("Granjero conservador", 0.85, 10, 6, 0.05),
    ("Granjero agresivo",    0.70, 20, 8, 0.15),
    ("Comerciante",          0.60, 15, 10, 0.10),
    ("Novato",               0.50, 8,  7, 0.20),
    ("Veterano optimizado",  0.90, 12, 5, 0.03),
]


def simulate_agent(archetype: tuple, days: int, rng: random.Random) -> list[int]:
    """Simula un agente individual y retorna su balance diario."""
    name, prob_cosecha, grano_cosecha, consumo, prob_evento = archetype
    balance = 50  # granos iniciales
    history = []

    for day in range(days):
        # Cosecha
        if rng.random() < prob_cosecha:
            balance += grano_cosecha

        # Consumo
        balance -= consumo

        # Evento negativo (plaga, robo, etc.)
        if rng.random() < prob_evento:
            loss = int(balance * rng.uniform(0.1, 0.3))
            balance -= loss

        # No puede bajar de 0
        balance = max(balance, 0)
        history.append(balance)

    return history


def run():
    rng = random.Random(SEED)
    results: dict[str, dict] = {}

    for archetype in ARCHETYPES:
        name = archetype[0]
        agents_per_type = NUM_AGENTS // len(ARCHETYPES)  # 100

        # Acumular curva promedio diaria
        daily_grains = [0] * DAYS

        dead_count = 0
        explode_count = 0
        final_balances = []

        for _ in range(agents_per_type):
            history = simulate_agent(archetype, DAYS, rng)
            final = history[-1]
            final_balances.append(final)

            if final == 0:
                dead_count += 1
            if final > 200:
                explode_count += 1

            for d in range(DAYS):
                daily_grains[d] += history[d]

        avg_curve = [g / agents_per_type for g in daily_grains]

        results[name] = {
            "avg_final": statistics.mean(final_balances),
            "median_final": statistics.median(final_balances),
            "min_final": min(final_balances),
            "max_final": max(final_balances),
            "dead": dead_count,
            "exploded": explode_count,
            "avg_curve_day1": round(avg_curve[0], 1),
            "avg_curve_day15": round(avg_curve[14], 1),
            "avg_curve_day30": round(avg_curve[29], 1),
        }

    return results


def main():
    results = run()
    print(f"{'Arquetipo':<25} {'Avg':>7} {'Med':>7} {'Min':>5} {'Max':>5} {'Dead':>5} {'Boom':>5} {'D1':>6} {'D15':>6} {'D30':>6}")
    print("-" * 92)
    for name, data in results.items():
        print(
            f"{name:<25} "
            f"{data['avg_final']:>7.1f} "
            f"{data['median_final']:>7.1f} "
            f"{data['min_final']:>5} "
            f"{data['max_final']:>5} "
            f"{data['dead']:>5} "
            f"{data['exploded']:>5} "
            f"{data['avg_curve_day1']:>6} "
            f"{data['avg_curve_day15']:>6} "
            f"{data['avg_curve_day30']:>6}"
        )

    # Resumen global
    all_dead = sum(d["dead"] for d in results.values())
    all_exploded = sum(d["exploded"] for d in results.values())
    print(f"\nTotal agentes: {NUM_AGENTS}")
    print(f"Murieron de hambre (balance=0): {all_dead}")
    print(f"Explotaron (balance>200): {all_exploded}")


if __name__ == "__main__":
    main()
