# Taxonomía de Eventos — Granja Táctica

## Eventos Naturales
| ID | Evento | Probabilidad base | Efecto |
|----|--------|-------------------|--------|
| N01 | Lluvia favorable | 0.20/día | +15% cosecha siguiente turno |
| N02 | Sequía | 0.08/día | -30% cosecha por 2 turnos |
| N03 | Plaga de langostas | 0.05/día | Pierde 20-40% del grano almacenado |
| N04 | Tormenta | 0.03/día | Destruye 1 estructura aleatoria |

## Eventos Sociales
| ID | Evento | Trigger | Efecto |
|----|--------|---------|--------|
| S01 | Comerciante ambulante | Cada 5 días | Ofrece intercambio grano ↔ recurso raro |
| S02 | Bandidos | Grano > 150 | Robo del 10-25% del grano |
| S03 | Festival de cosecha | Día 15 y 30 | Bonus colectivo si la aldea supera umbral |

## Eventos de Jugador
| ID | Evento | Condición | Efecto |
|----|--------|-----------|--------|
| P01 | Nivel up | XP acumulado | Desbloquea slot de cultivo |
| P02 | Descubrimiento | Exploración > 3 | Semilla rara |
| P03 | Alianza | 2 jugadores cooperan | Reducción de consumo -10% ambos |

## Notas de Diseño
- Los eventos N01-N04 se resuelven al inicio del turno, antes de la acción del jugador.
- S01-S03 se evalúan después de la fase de cosecha.
- P01-P03 son persistentes y se acumulan entre sesiones.
