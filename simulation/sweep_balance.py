"""
Barrido exhaustivo para responder con precisión matemática:
1) ¿Puede un jugador ganar la oleada 10 usando solo unidades de nivel 1?
2) ¿Cuántas unidades de nivel 2-3 necesita mínimo según el número de casillas ocupadas?
3) Identificar al menos 2 composiciones viables y diferentes para vencer la oleada 10.
"""

from simulation.combat_sim import TEMPLATES, LEVEL_MULT, simulate_battle

enemy_wave_10 = [
    ("espantapajaros", 1, (0, 0), False),
    ("toro", 1, (0, 1), True),      # Jefe x3 stats
    ("oveja", 1, (0, 2), False),
]

def sweep_level_1():
    print("=== ANÁLISIS 1: UNIDADES NIVEL 1 SEGÚN TAMAÑO DEL EQUIPO ===")
    comps = {
        "3 unidades Lv1 (Frente + DPS + Soporte)": [
            ("cerdo", 1, (0, 1)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2))
        ],
        "4 unidades Lv1 (Standard Early-Mid)": [
            ("cerdo", 1, (0, 1)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ],
        "5 unidades Lv1": [
            ("cerdo", 1, (0, 1)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0)), ("gallo", 1, (0, 0))
        ],
        "6 unidades Lv1 (DPS Mixto)": [
            ("cerdo", 1, (0, 1)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0)), ("gallo", 1, (0, 0)), ("pato", 1, (2, 1))
        ],
        "7 unidades Lv1 (Doble Tanque)": [
            ("cerdo", 1, (0, 1)), ("toro", 1, (0, 2)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0)), ("gallo", 1, (0, 0)), ("pato", 1, (2, 1))
        ],
        "8 unidades Lv1": [
            ("cerdo", 1, (0, 1)), ("toro", 1, (0, 2)), ("espantapajaros", 1, (0, 0)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0)), ("gallo", 1, (2, 0)), ("pato", 1, (2, 1))
        ],
        "9 unidades Lv1 (Tablero 3x3 Lleno al 100%)": [
            ("cerdo", 1, (0, 0)), ("toro", 1, (0, 1)), ("cerdo", 1, (0, 2)),
            ("perro", 1, (1, 0)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)),
            ("cabra", 1, (2, 0)), ("pato", 1, (2, 1)), ("gallo", 1, (2, 2)),
        ]
    }

    for name, c in comps.items():
        res = simulate_battle(c, enemy_wave_10)
        status = "VICTORIA" if res['won'] else "DERROTA"
        print(f"[{status}] {name} -> Vivos: {res['player_alive_count']}/{len(c)}, Tiempo: {res['time']}s, Boss HP final: {res['boss_remaining_hp']:.1f}")

def sweep_minimum_leveled():
    print("\n=== ANÁLISIS 2: REQUISITOS MÍNIMOS DE NIVEL 2 Y 3 (Para escuadras de 4 a 6 unidades) ===")
    # En auto-battlers de cuadrícula 3x3, el jugador habitualmente llega a la oleada 10 con 4-6 unidades debido al costo y merge.
    tests = [
        ("4 unidades: 0x Lv2 (Todos Lv1)", [
            ("cerdo", 1, (0, 1)), ("cabra", 1, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("4 unidades: 1x Lv2 (Cabra Lv2)", [
            ("cerdo", 1, (0, 1)), ("cabra", 2, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("4 unidades: 2x Lv2 (Cabra Lv2 + Cerdo Lv2)", [
            ("cerdo", 2, (0, 1)), ("cabra", 2, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("4 unidades: 3x Lv2 (Cabra Lv2 + Cerdo Lv2 + Perro Lv2)", [
            ("cerdo", 2, (0, 1)), ("cabra", 2, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 2, (1, 0))
        ]),
        ("4 unidades: 1x Lv3 (Cabra Lv3 + 3x Lv1)", [
            ("cerdo", 1, (0, 1)), ("cabra", 3, (1, 1)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("5 unidades: 2x Lv2 (Cerdo Lv2 + Cabra Lv2 + 3 Lv1)", [
            ("cerdo", 2, (0, 1)), ("cabra", 2, (1, 1)), ("espantapajaros", 1, (0, 0)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("5 unidades: 1x Lv3 (Cabra Lv3 + Cerdo Lv2 + 3 Lv1)", [
            ("cerdo", 2, (0, 1)), ("cabra", 3, (1, 1)), ("espantapajaros", 1, (0, 0)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0))
        ]),
        ("6 unidades: 2x Lv2 (Cerdo Lv2 + Cabra Lv2 + 4 Lv1)", [
            ("cerdo", 2, (0, 1)), ("cabra", 2, (1, 1)), ("espantapajaros", 1, (0, 0)), ("oveja", 1, (1, 2)), ("perro", 1, (1, 0)), ("pato", 1, (2, 1))
        ]),
    ]

    for desc, c in tests:
        res = simulate_battle(c, enemy_wave_10)
        status = "VICTORIA" if res['won'] else "DERROTA"
        print(f"[{status}] {desc} -> Vivos: {res['player_alive_count']}/{len(c)}, Tiempo: {res['time']}s, Boss HP: {res['boss_remaining_hp']:.1f}")

def two_viable_compositions():
    print("\n=== ANÁLISIS 3: DOS COMPOSICIONES COMPLETAMENTE DIFERENTES PARA GANAR LA OLEADA 10 ===")
    
    # Composición 1: "Francotirador Búnker / Front-to-Back"
    # Filosofía: Núcleo defensivo con reducción de daño adyacente (Cerdo Lv2), buffer (Perro Lv1), curandera (Oveja Lv1)
    # y hyper-carry a distancia (Cabra Francotiradora Lv2) que perfora al jefe mientras el Espantapájaros (Lv1) mitiga sus ataques.
    comp1 = [
        ("cerdo", 2, (0, 1)),          # Tanque principal frente al jefe
        ("espantapajaros", 1, (0, 0)), # Control en flanco izquierdo
        ("oveja", 1, (1, 2)),          # Healer protegiendo retaguardia
        ("cabra", 2, (1, 1)),          # Carry DPS en el centro
        ("perro", 1, (1, 0)),          # Buffer potenciando a Cabra y Cerdo
        ("pato", 1, (2, 1)),           # Limpieza de escoltas enemigas con AoE
    ]
    res1 = simulate_battle(comp1, enemy_wave_10)
    print("Composición 1 [Búnker Balístico - Anti-Boss Perforante]:")
    print(f"  Victoria: {res1['won']} | Tiempo: {res1['time']}s | Vivos: {res1['player_alive_count']}/6 | Boss HP: {res1['boss_remaining_hp']:.1f}")

    # Composición 2: "Asalto Melee & Control / Burst Caótico"
    # Filosofía: Presión frontal agresiva con Toro Bravo Lv2 (contraataque retaliatorio), Gallo Asesino Lv2 (burst melee con sinergia de velocidad),
    # Espantapájaros Lv2 (cadena de aturdimientos que cancela habilidades del Jefe) y soporte de Perro y Oveja.
    comp2 = [
        ("toro", 2, (0, 1)),           # Tanque ofensivo frente al jefe
        ("gallo", 2, (0, 2)),          # Asesino melee devorando la oveja enemiga y luego al jefe
        ("espantapajaros", 2, (0, 0)), # Stunner de alto nivel neutralizando al boss
        ("perro", 1, (1, 1)),          # Buffer central adyacente a Toro, Gallo y Espantapájaros (+20% dmg a los 3!)
        ("oveja", 1, (1, 2)),          # Soporte de curación
    ]
    res2 = simulate_battle(comp2, enemy_wave_10)
    print("\nComposición 2 [Presión Melee & Control - Stun-Lock & Burst]:")
    print(f"  Victoria: {res2['won']} | Tiempo: {res2['time']}s | Vivos: {res2['player_alive_count']}/5 | Boss HP: {res2['boss_remaining_hp']:.1f}")

if __name__ == "__main__":
    sweep_level_1()
    sweep_minimum_leveled()
    two_viable_compositions()
