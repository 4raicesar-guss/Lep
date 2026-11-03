# Documentación de Diseño: Visualizador de Combate y Experiencia de "Juice" (Día 5/6)
*Granja Táctica — Telegram Mini App*

---

## 1. Flujo de Pantallas Resumido (Core Game Loop)

El ciclo de juego está diseñado para sesiones cortas (1-3 minutos) adaptadas a la naturaleza de las Telegram Mini Apps, optimizando retención y dinamismo sin tiempos de espera innecesarios.

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ 1. Home      │  ───► │ 2. Merge     │  ───► │ 3. Formación │
│    (Granja)  │       │    (Banco)   │       │    (3x3)     │
└──────────────┘       └──────────────┘       └──────────────┘
                                                     │
                                                     ▼
┌──────────────┐       ┌─────────────────────────────────────┐
│ 5. Recompensa│  ◄─── │ 4. Combate (Visualizador Replay)   │
│    (Botín)   │       │    (Títere mudo: animación + juice) │
└──────┬───────┘       └─────────────────────────────────────┘
       │
       └───────────────► Regreso a Home / Siguiente Oleada
```

### Detalle de cada pantalla:

1. **Home (Granja Central):**
   - **Propósito:** Hub principal del jugador.
   - **Elementos:** Visualización del silo de grano acumulado, nivel de granja, corrales de animales y acceso directo a la tienda cosmética y al botón de acción principal `[¡A la Batalla!]`.
   - **Interacción:** Sonido suave y háptica sutil al consultar los depósitos de recursos.

2. **Merge (Banco de Unidades):**
   - **Propósito:** Bucle económico y de síntesis.
   - **Elementos:** Cuadrícula de reserva donde residen las unidades adquiridas con grano.
   - **Mecánica:** Fusión tripartita (3 unidades de Nivel 1 $\rightarrow$ 1 unidad de Nivel 2 al $1.8\times$ de poder; 3 de Nivel 2 $\rightarrow$ 1 de Nivel 3 al $3.24\times$).
   - **Micro-feedback:** Al arrastrar y soltar con éxito, se dispara una contracción elástica y vibración de confirmación.

3. **Formación (Táctica 3x3):**
   - **Propósito:** Fase de despliegue estratégico antes de iniciar el enfrentamiento.
   - **Elementos:** Tablero de 9 casillas (3 filas: Frente, Media, Retaguardia).
   - **Mecánica:** Posicionamiento deliberado para activar sinergias de adyacencia ortogonal (N, S, E, O):
     - Tanques (Cerdo/Toro) en la vanguardia para absorber daño y ganar mitigación.
     - Daño a distancia (Cabra/Pato) en segunda fila tras los tanques para activar bonos de perforación (+25%).
     - Soportes (Perro/Oveja) en posiciones centrales para maximizar aliados alcanzados por auras de daño (+20%) y sanación.

4. **Combate (Visualizador Replay - "Títere Mudo"):**
   - **Propósito:** Espectáculo visual determinista de alta fidelidad.
   - **Mecánica:** El frontend no computa vida ni daño; simplemente interpreta el `replay_log` provisto por el backend a 500ms por tick.
   - **Experiencia de Juice:** Sacudidas de impacto, destellos rojos de absorción, textos flotantes dinámicos de daño (`-{damage}`) y retroalimentación háptica inmediata vía `@telegram-apps/sdk`.

5. **Recompensa (Botín y Liquidación):**
   - **Propósito:** Celebración del éxito y progresión.
   - **Elementos:** Pantalla de victoria/derrota con resumen de grano obtenido (`50 + 25 × Oleada`), cofre de botín interactivo con apertura festiva, confeti visual y botón directo para `[Reintentar]` o `[Siguiente Oleada]`.

---

## 2. La "Juice List" Completa (Mapeo de Acción $\rightarrow$ Háptica + Efecto Visual)

La siguiente tabla resume todos los micro-detalles diseñados para que cada evento dentro del cliente de Telegram se sienta tangible, reactivo y premium:

| Acción en Juego | Disparador / Evento | Retroalimentación Háptica (`@telegram-apps/sdk`) | Efecto Visual / CSS en Pantalla | Duración / Timing |
|:---|:---|:---|:---|:---:|
| **Ataque Básico / Impacto** | `event.action === 'attack'` | `HapticFeedback.impactOccurred('medium')` | Destello rojo (`.flash-red`) + Sacudida de impacto (`.animate-shake`) en la casilla del objetivo. Ligera escala del atacante (`scale-105`). | 350ms - 450ms |
| **Texto de Daño Flotante** | Proceso de daño en tick | — (Acompaña al impacto de ataque) | Número flotante `-{damage}` en rojo/oro brillante con sombra profunda, elevándose hacia arriba y desvaneciéndose (`.animate-float-damage`). | 1000ms |
| **Ataque Fuerte / Crítico** | Daño $\ge 40$ o ataque especial | `HapticFeedback.impactOccurred('heavy')` | Sacudida de mayor amplitud ($\pm 8\text{px}$) + resplandor blanco instantáneo en la tarjeta golpeada. | 500ms |
| **Contraataque (Toro Bravo)** | Trigger pasiva adyacencia | `HapticFeedback.impactOccurred('rigid')` | Estela de cuernos dorados y devolución instantánea de daño hacia el agresor cuerpo a cuerpo. | 300ms |
| **Daño en Área (AoE Pato)** | Daño splash colateral | `HapticFeedback.impactOccurred('soft')` | Onda de choque concéntrica translúcida expandiéndose desde la casilla del impacto primario a las adyacentes. | 400ms |
| **Aplicación de Aturdimiento (Stun)** | `event.stun === true` | `HapticFeedback.notificationOccurred('warning')` | Icono giratorio de mareo (`💫`) sobre la unidad con animación de pulso rotativo (`.animate-stun`) y reducción de opacidad/color. | Mientras dure el stun |
| **Sanación (Oveja Sanadora)** | `event.action === 'heal'` | `HapticFeedback.impactOccurred('light')` | Aura verde esmeralda con partículas `+HP` flotantes en verde lima y barra de vida creciendo suavemente. | 600ms |
| **Muerte de Unidad** | `current_hp <= 0` | `HapticFeedback.impactOccurred('heavy')` | Desaturación completa a escala de grises, superposición de icono `❌` y desvanecimiento progresivo a 40% de opacidad. | 400ms |
| **Fusión en Banco (Merge)** | 3 unidades combinadas | `HapticFeedback.notificationOccurred('success')` | Destello central, escala expansiva $1.25\times \rightarrow 1.0\times$ y estallido radial de estrellas/chispas. | 500ms |
| **Botón Replay / Taps en UI** | Clic en controles | `HapticFeedback.impactOccurred('light')` | Micro-contracción del botón (`active:scale-95`) con cambio instantáneo de estado. | 150ms |
| **Victoria de Oleada** | Fin de replay (`winner === 'player'`) | `HapticFeedback.notificationOccurred('success')` | Banner esmeralda dorado con corona `🏆`, lluvia de confeti ligero y revelación de botín. | Constante al terminar |
| **Derrota de Oleada** | Fin de replay (`winner === 'enemy'`) | `HapticFeedback.notificationOccurred('error')` | Banner carmesí oscuro `💀`, viñeta de bordes enrojecidos y vibración de fallo. | Constante al terminar |

---

## 3. Catálogo Cosmético V1 (Monetización con Telegram Stars ⭐)

Conforme a las normativas de monetización de Telegram Mini Apps, los bienes virtuales cosméticos no otorgan ventaja competitiva ("pay-to-win") y se adquieren exclusivamente a través de **Telegram Stars** (`⭐`).

### Item 1: Skin de Unidad — *Cerdo Centurión Imperial*
- **Precio:** `150 ⭐` (Aprox. $2.99 USD)
- **Tipo:** Skin Cosmética de Unidad (Equipable para **U01 - Cerdo Blindado**).
- **Descripción de Valor:**
  - Sustituye el sprite base por un imponente cerdo blindado con casco de legionario romano y capa púrpura imperial.
  - Al activar su pasiva de mitigación (*Pared Porcina*), despliega un escudo de torre dorado translúcido con chispas metálicas.
  - Otorga una animación de impacto personalizada con sonido de escudo metálico y háptica `rigid` enriquecida.

### Item 2: Tablero Táctico — *Arena Coliseo de Barro*
- **Precio:** `250 ⭐` (Aprox. $4.99 USD)
- **Tipo:** Skin de Tablero 3x3.
- **Descripción de Valor:**
  - Sustituye la cuadrícula táctica oscura genérica por una arena circular de combate rústica, con vallas de madera tallada, fardos de heno en los bordes y terreno de tierra batida.
  - Cada vez que una unidad se desplaza o ataca en melé, se proyectan micro-partículas de salpicadura de barro dinámicas en el piso.
  - Los marcadores de adyacencia brillan con un tono rúnico anaranjado cálido.

### Item 3: Efecto de Impacto — *Furia de Neón Retro*
- **Precio:** `100 ⭐` (Aprox. $1.99 USD)
- **Tipo:** Efecto Visual Global de Combate (VFX Pack).
- **Descripción de Valor:**
  - Modifica la apariencia de todos los textos flotantes de daño (`-{damage}`): tipografía estilo arcade retro 8-bit en colores cian y magenta neón ultra-brillantes con resplandor exterior (`drop-shadow neon glow`).
  - Cada impacto crítico emite una pequeña explosión pixel-art retro.
  - Altamente visible y gratificante durante oleadas avanzadas de ritmo rápido.
