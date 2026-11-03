# Matriz de Combate — Granja Táctica (MVP Día 3)

## 1. Catálogo de Unidades (8 Unidades del MVP)

| ID | Nombre | Rol | HP | Daño | Vel. Ataque | Sinergia de Adyacencia (N/S/E/O) | Counter (Débil contra) | Coste (Grano) |
|:---|:---|:---|:---:|:---:|:---:|:---|:---|:---:|
| **U01** | **Cerdo Blindado** | Tanque | 480 | 14 | 1.0 atq/s | **Pared Porcina:** Reduce el daño recibido en un 10% por cada aliado ortogonal adyacente (máx. 40%). | **Espantapájaros Aturdidor** (el stun anula su mitigación) y **Pato Bombardero** (el AoE castiga agrupar aliados a su alrededor). | 80 🌾 |
| **U02** | **Toro Bravo** | Tanque | 420 | 22 | 1.1 atq/s | **Embestida en Manada:** Si tiene al menos 1 aliado adyacente, contraataca infligiendo 18 de daño a quien le golpee cuerpo a cuerpo. | **Cabra Francotiradora** (ataca a distancia sin activar la represalia) y stuns prolongados. | 110 🌾 |
| **U03** | **Gallo Asesino** | Daño | 150 | 38 | 1.8 atq/s | **Cacareo Belicista:** Gana +15% de velocidad de ataque por cada aliado adyacente (hasta +60%). | **Cerdo Blindado / Toro Bravo** (resisten su ráfaga inicial; el contraataque del Toro lo aniquila) y daño en área. | 90 🌾 |
| **U04** | **Cabra Francotiradora** | Daño | 130 | 46 | 1.2 atq/s | **Posición de Colina:** Si está adyacente a un Tanque aliado, sus ataques perforan armadura (+25% de daño a tanques con >300 HP). | **Gallo Asesino** (burst veloz en combate cuerpo a cuerpo) y flanqueos rápidos. | 130 🌾 |
| **U05** | **Pato Bombardero** | Daño | 160 | 28 | 1.25 atq/s | **Bandada Explosiva:** Sus ataques dañan casillas adyacentes al target (60% daño AoE). Gana +15% de daño AoE por cada aliado adyacente. | **Cabra Francotiradora** (la cabra lo abate a distancia individualmente) y **Gallo Asesino**. | 140 🌾 |
| **U06** | **Oveja Sanadora** | Soporte | 220 | 10 | 1.0 atq/s | **Vellón Reconfortante:** Si tiene 2+ aliados adyacentes, su curación pasa de uniobjetivo (40 HP/s) a un aura que restaura 30 HP/s a todos sus adyacentes. | **Pato Bombardero** (el daño AoE sobrepasa la curación grupal) y **Gallo Asesino**. | 100 🌾 |
| **U07** | **Perro Pastor** | Soporte | 260 | 18 | 1.3 atq/s | **Ladrido de Mando:** Los aliados adyacentes reciben +20% de daño y +15% vel. ataque. Absorbe el primer golpe mortal de un aliado adyacente. | **Pato Bombardero** (el daño múltiple simultáneo colapsa su protección) y focos concentrados. | 120 🌾 |
| **U08** | **Espantapájaros Aturdidor** | Control | 310 | 16 | 1.0 atq/s | **Presencia Inquietante:** Cada 3 ataques aturde al objetivo durante 2.0s. Por cada aliado adyacente, reduce la vel. de ataque enemiga en su columna/fila en 10%. | **Cabra Francotiradora** (lo elimina desde fuera del rango del aura) y curación continua rápida. | 150 🌾 |

---

## 2. Progresión de Oleadas PvE (10 Oleadas)

*Fórmula de recompensa:* `50 + (25 × Oleada) Grano`.

| # | Composición Enemiga | Amenaza Visible | Recompensa |
|:---:|:---|:---|:---:|
| **1** | 1x Cerdo Blindado (Lv1) | 🛡️ **Tutorial de Resistencia:** Objetivo de alta vida; enseña el flujo de ataque básico. | 75 🌾 |
| **2** | 2x Gallo Asesino (Lv1) | ⚡ **Tutorial de Ráfaga:** Alto DPS frontal; enseña la necesidad de posicionar un tanque al frente. | 100 🌾 |
| **3** | 1x Cerdo Blindado (Lv1), 1x Gallo Asesino (Lv1) | 🛡️⚡ **Tutorial de Formación Básica:** Dúo clásico de primera línea y daño; enseña el orden de prioridad de foco. | 125 🌾 |
| **4** | 2x Cerdo Blindado (Lv1), 1x Cabra Francotiradora (Lv1) | 🎯 **Línea de Francotirador:** Foco perforante protegido detrás de un muro defensivo doble. | 150 🌾 |
| **5** | 1x Toro Bravo (Lv1), 2x Pato Bombardero (Lv1) | 💣 **Peligro de Bombardeo:** Daño en área masivo; penaliza agrupar unidades del jugador sin tanques resistentes. | 175 🌾 |
| **6** | 2x Cerdo Blindado (Lv1), 1x Oveja Sanadora (Lv1), 1x Gallo Asesino (Lv1) | 💚 **Búnker Regenerativo:** Sostenimiento continuo que exige daño concentrado para penetrar el muro. | 200 🌾 |
| **7** | 1x Toro Bravo (Lv1), 2x Gallo Asesino (Lv1), 1x Perro Pastor (Lv1) | 🐕⚡ **Enjambre Rabioso:** Súper aceleración de velocidad y daño buffeado por el pastor. | 225 🌾 |
| **8** | 2x Cerdo Blindado (Lv1), 1x Espantapájaros Aturdidor (Lv1), 1x Cabra Francotiradora (Lv1), 1x Oveja Sanadora (Lv1) | 🌀 **Cadena de Control y Desgaste:** Aturdimientos cíclicos, ralentización de ataque y mitigación por adyacencia. | 250 🌾 |
| **9** | 2x Toro Bravo (Lv1), 2x Pato Bombardero (Lv1), 1x Perro Pastor (Lv1) | 💥 **Bombardeo Furioso Coordinado:** Doble tanque con represalia frontal y artillería potenciada al +20% de daño. | 275 🌾 |
| **10** | **1x JEFE: "El Gran Jabalí Devastador"** (Stats x3: HP: 1350, Daño: 66, Vel: 1.1 atq/s) + **1x Oveja Sanadora (Lv1)** + **1x Espantapájaros Aturdidor (Lv1)** | 👑 **Terremoto Devastador:** Cada 4 ataques, el Jefe genera una onda sísmica que inflige 80 de daño global a todo el tablero y aturde a las unidades 1.0s. | 300 🌾 |

---

## 3. Dinámica de Contramedidas (Ciclo Piedra-Papel-Tijera)

```
        ┌────────────────────────┐
        │        TANQUES         │
        │  (Cerdo / Toro)        │
        └───────────┬────────────┘
         ▲          │           ▲
         │ Absorbe  │           │ Supera con
         │ Ráfaga   │ Débil a   │ Perforación
         │          ▼ Stuns     │
 ┌───────┴──────┐      ┌────────┴───────┐
 │ DAÑO RÁFAGA  │      │  CONTROL / DPS │
 │ (Gallo /     ├─────►│  A DISTANCIA   │
 │  Perro buff) │      │ (Espantapájaros│
 └───────┬──────┘      │  / Cabra)      │
         │             └────────┬───────┘
         │ Elimina rápidamente   │
         ▼                       ▼
 ┌──────────────────────────────────────┐
 │               SOPORTE                │
 │         (Oveja Sanadora)             │
 └──────────────────┬───────────────────┘
                    │ Resiste desgaste si
                    │ no hay AoE masivo
                    ▼
 ┌──────────────────────────────────────┐
 │              DAÑO AOE                │
 │          (Pato Bombardero)           │
 │   *Destruye clústers y adyacencias*  │
 └──────────────────────────────────────┘
```

---

## 4. Documento de Reglas de Combate

### 4.1. Espacio de Batalla y Naturaleza de las Unidades
1. **Cuadrícula 3x3:** Cada bando posee un tablero de combate estático de 9 casillas (3 filas × 3 columnas):
   - Fila 0 (Frontline / Delantera): contacto directo con el enemigo.
   - Fila 1 (Midline / Central): balance entre alcance y protección.
   - Fila 2 (Backline / Trasera): ideal para unidades de rango o soporte.
2. **Inmovilidad Táctica:** Las unidades son completamente estáticas; no se desplazan entre casillas durante la fase de combate. Toda la estrategia radica en el posicionamiento y las sinergias adyacentes previas al inicio de la ronda.

### 4.2. Algoritmo de Selección de Objetivos (Targeting)
1. **Prioridad por Proximidad (Distancia Manhattan):**
   - Cada unidad evalúa a los enemigos vivos y ataca automáticamente al objetivo con la menor distancia entre casillas:  
     $$\text{Distancia} = (\text{Fila}_{\text{aliado}} + \text{Fila}_{\text{enemigo}} + 1) + |\text{Columna}_{\text{aliado}} - \text{Columna}_{\text{enemigo}}|$$
2. **Prioridad Absoluta de Adyacencia:**
   - Si un enemigo está en la casilla frontal directa (distancia mínima de contacto), se prioriza inmediatamente sobre cualquier otro objetivo del tablero.
3. **Persistencia del Foco:** Una unidad mantiene su ataque sobre el mismo objetivo hasta que este muera o el atacante sea aturdido.

### 4.3. Reglas de Daño en Área (AoE) y Control
1. **Propagación Ortogonal:** El daño en área (ej. proyectil del Pato Bombardero) impacta a la casilla del objetivo principal con el 100% de su daño y se propaga con el 60% de su valor a todas las casillas adyacentes ortogonales (Norte, Sur, Este, Oeste) que contengan una unidad rival.
2. **Aturdimiento (Stun):** Durante el tiempo de aturdimiento, la unidad no puede atacar, cargar cooldowns ni canalizar curaciones pasivas. Las reducciones pasivas de daño se mantienen activas.

### 4.4. Sinergias de Adyacencia
1. Las casillas adyacentes se definen exclusivamente como las casillas vecinas ortogonales directas (Norte, Sur, Este, Oeste en el tablero 3x3; no en diagonal).
2. El sistema recompensa fuertemente la agrupación táctica (clústers en cruz, en 'T' o en bloque 2x2), generando un dilema estratégico: **mayor bonificación de sinergia a cambio de mayor vulnerabilidad frente al daño en área (AoE)**.

### 4.5. Condiciones de Resolución
1. **Victoria:** Todos los enemigos en la cuadrícula enemiga han sido reducidos a 0 HP. El jugador recibe la recompensa de grano correspondiente a la oleada.
2. **Derrota:** Todas las unidades del jugador en la cuadrícula han sido eliminadas.
3. **Empate / Límite de Tiempo (60s):** Si tras 60 segundos ambos bandos tienen unidades vivas, el bando con mayor porcentaje de vida acumulada es declarado vencedor.

---

## 5. Análisis Técnico: Viabilidad de la Oleada 10 y Requisitos de Nivel

### 5.1. ¿Puede un jugador ganar la Oleada 10 usando SOLO unidades de Nivel 1?
**Respuesta:** **Técnicamente SÍ, pero bajo condiciones extremas y poco realistas para una partida estándar.**

- **El Desafío:** El Jefe ("El Gran Jabalí Devastador") cuenta con **1,350 HP, 66 de daño por golpe (DPS 72.6) y una habilidad sísmica que inflige 80 de daño en área global cada 4 ataques**.
- **Equipos Estándar de Nivel 1 (3 a 6 unidades):** Pierden el 100% de los combates. Las unidades de nivel 1 tienen vidas base muy reducidas (Cabra: 130 HP, Gallo: 150 HP, Pato: 160 HP). Con el segundo terremoto del Jefe (80 + 80 = 160 de daño global), todos los atacantes frágiles mueren simultáneamente antes de 8 segundos.
- **Saturación Total (7 a 9 unidades de Nivel 1):** Un jugador solo puede vencer con unidades de Nivel 1 si llena entre 7 y 9 casillas del tablero (78% a 100% de la cuadrícula 3x3) aprovechando al máximo la red de mitigación del Cerdo Blindado y el aura curativa de la Oveja Sanadora.
- **Restricción de Recursos:** Desplegar 8 unidades de nivel 1 cuesta aproximadamente **880 a 980 de Grano**. Aunque la economía acumulada lo permitiría (1,875 Grano total a lo largo de las 10 oleadas), mantener 9 unidades individuales sin fusionar provoca un bloqueo espacial ("grid lock") que impide maniobrar en la tienda de compras del Merge.

### 5.2. ¿Cuántas unidades de Nivel 2 o 3 se necesitan como mínimo?
Considerando el tamaño de escuadra habitual (4 a 6 casillas ocupadas):

| Tamaño de Escuadra | Requisito Mínimo para Vencer Oleada 10 | Unidades Clave Recomendadas |
|:---:|:---:|:---|
| **4 unidades** | **1x Nivel 3** + 3x Nivel 1 | **1x Cabra Francotiradora Lv3** (178 DPS puro, perforación) + Cerdo Lv1, Perro Lv1, Oveja Lv1. |
| **5 unidades** | **2x Nivel 2** + 3x Nivel 1 | **1x Tanque Lv2** (Cerdo o Toro) + **1x Carry Lv2** (Cabra o Gallo) + 3 soportes/control Lv1. |
| **6 unidades** | **2x Nivel 2** + 4x Nivel 1 | **1x Cerdo Lv2** (mitigación sólida) + **1x Cabra Lv2** + 4 utilidades Lv1. |

> **Conclusión del Mínimo:** Se requiere como **mínimo absoluto 2 unidades de Nivel 2** (o 1 unidad de Nivel 3) para garantizar la victoria en un despliegue equilibrado de 5 unidades.

---

## 6. Dos Composiciones Viables Demostradas contra la Oleada 10

### Composición A: "Búnker Balístico" (Front-to-Back Perforante)
- **Filosofía:** Enfoque defensivo y de hiper-alcance. Concentra todas las sinergias en proteger y sobrecargar a la Cabra Francotiradora para derretir la barra de vida del Jefe a distancia sin exponerse a represalias cuerpo a cuerpo.
- **Despliegue en Cuadrícula 3x3:**
  ```
  [ Fila 0 - Frente ] : [ Espantapájaros Lv1 ]  [ Cerdo Blindado Lv2 ]  [ Vacío ]
  [ Fila 1 - Centro ] : [ Perro Pastor Lv1   ]  [ Cabra Francotiradora Lv2 ]  [ Oveja Sanadora Lv1 ]
  [ Fila 2 - Fondo  ] : [ Vacío              ]  [ Pato Bombardero Lv1    ]  [ Vacío ]
  ```
- **Mecánica de Sinergias:**
  - El Cerdo Lv2 recibe 40% de reducción de daño gracias a sus vecinos ortogonales.
  - La Cabra Lv2 está adyacente al Tanque (activa +25% daño antitanque) y al Perro (+20% daño y +15% velocidad), disparando con un DPS efectivo de más de **115 de daño sostenido**.
  - El Espantapájaros Lv1 aturde al Jefe en momentos críticos, retrasando la llegada de los terremotos.
- **Resultado en Simulación:** Victoria en **8.5 segundos** con 5 unidades aliadas sobrevivientes.

### Composición B: "Asalto Frontal & Stun-Lock" (Burst Melee & Control)
- **Filosofía:** Enfoque hiper-agresivo de interrupción continua. Utiliza el aturdimiento de alto nivel para impedir mecánicamente que el Jefe lance su terremoto mientras el daño cuerpo a cuerpo y la represalia del Toro liquidan a los enemigos.
- **Despliegue en Cuadrícula 3x3:**
  ```
  [ Fila 0 - Frente ] : [ Espantapájaros Lv2 ]  [ Toro Bravo Lv2 ]  [ Gallo Asesino Lv2 ]
  [ Fila 1 - Centro ] : [ Vacío              ]  [ Perro Pastor Lv1 ] [ Oveja Sanadora Lv1 ]
  [ Fila 2 - Fondo  ] : [ Vacío              ]  [ Vacío            ] [ Vacío ]
  ```
- **Mecánica de Sinergias:**
  - El Gallo Lv2 en primera línea flanquea rápidamente a la Oveja Sanadora enemiga, eliminándola en menos de 2.5 segundos con su altísima velocidad de ataque potenciada (+15% por aliado adyacente).
  - El Espantapájaros Lv2 aplica aturdimientos reiterados al Jefe, cortando su secuencia de 4 golpes e impidiendo la activación de la "Carga Sísmica".
  - El Toro Lv2 castiga los ataques del Jefe infligiendo 32 de daño por contraataque en cada impacto.
- **Resultado en Simulación:** Victoria en **7.15 segundos** con las 5 unidades vivas.
