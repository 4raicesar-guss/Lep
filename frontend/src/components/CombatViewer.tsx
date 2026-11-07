import { useState, useEffect, useCallback } from 'react';
import { hapticFeedback as HapticFeedback } from '@telegram-apps/sdk';
import { UnitAvatar } from './UnitAvatar';
import { UNITS_CONFIG } from '../lib/game';

/* =========================================================================
   TIPOS E INTERFACES DEL VISUALIZADOR DE COMBATE
   ========================================================================= */

export interface UnitConfig {
  name: string;
  sprite: string;
  image?: string;
  max_hp: number;
  role?: string;
}

export type UnitsConfigMap = Record<string, UnitConfig>;

export interface GridCell {
  id: number | string;
  unit_id: string;
  current_hp: number;
  max_hp: number;
  is_stunned?: boolean;
  team?: 'player' | 'enemy';
}

export interface ReplayLogEvent {
  tick: number;
  actor_id: number | string;
  action: 'attack' | 'heal' | 'stun' | string;
  target_id: number | string;
  damage?: number;
  heal?: number;
  stun?: boolean | number;
  target_hp?: number;
}

export interface ReplayData {
  winner: 'player' | 'enemy' | string;
  total_ticks: number;
  replay_log: ReplayLogEvent[];
  initial_grid?: (GridCell | null)[];
}

export interface CombatViewerProps {
  replayData?: ReplayData;
  unitsConfig?: UnitsConfigMap;
}

/* =========================================================================
   CONFIGURACIÓN POR DEFECTO Y MOCK REPLAY DATA (3-4 TICKS)
   ========================================================================= */

// Derivado de la fuente única del cliente (lib/game.ts), que espeja backend/app/engine/data.py
const DEFAULT_UNITS_CONFIG: UnitsConfigMap = Object.fromEntries(
  Object.values(UNITS_CONFIG).map((u) => [
    u.id,
    { name: u.name, sprite: u.sprite, image: u.image, max_hp: u.baseHp, role: u.role },
  ]),
);

/**
 * Grid Inicial Mock 3x3:
 * Posiciones 0-8:
 * [0] Cerdo (Aliado)   [1] Gallo (Aliado)   [2] Espantapájaros (Aliado)
 * [3] Vacío            [4] Toro (Enemigo)   [5] Oveja (Enemigo)
 * [6] Vacío            [7] Vacío            [8] Vacío
 */
const DEFAULT_INITIAL_GRID: (GridCell | null)[] = [
  { id: 1, unit_id: 'U01', current_hp: 480, max_hp: 480, is_stunned: false, team: 'player' },
  { id: 2, unit_id: 'U03', current_hp: 150, max_hp: 150, is_stunned: false, team: 'player' },
  { id: 8, unit_id: 'U08', current_hp: 310, max_hp: 310, is_stunned: false, team: 'player' },
  null,
  { id: 101, unit_id: 'U02', current_hp: 420, max_hp: 420, is_stunned: false, team: 'enemy' },
  { id: 102, unit_id: 'U06', current_hp: 220, max_hp: 220, is_stunned: false, team: 'enemy' },
  null,
  null,
  null,
];

const MOCK_REPLAY_DATA: ReplayData = {
  winner: 'player',
  total_ticks: 4,
  initial_grid: DEFAULT_INITIAL_GRID,
  replay_log: [
    // Tick 1: Gallo Asesino (id: 2) ataca al Toro Bravo enemigo (id: 101) infligiendo 38 de daño
    {
      tick: 1,
      actor_id: 2,
      action: 'attack',
      target_id: 101,
      damage: 38,
      target_hp: 382,
    },
    // Tick 2: Cerdo Blindado (id: 1) embiste al Toro enemigo (id: 101) infligiendo 14 de daño
    {
      tick: 2,
      actor_id: 1,
      action: 'attack',
      target_id: 101,
      damage: 14,
      target_hp: 368,
    },
    // Tick 3: Toro enemigo (id: 101) contraataca a Cerdo (id: 1) por 14 dmg,
    // y Espantapájaros (id: 8) lanza stun a Oveja enemiga (id: 102) por 16 dmg
    {
      tick: 3,
      actor_id: 101,
      action: 'attack',
      target_id: 1,
      damage: 14,
      target_hp: 466,
    },
    {
      tick: 3,
      actor_id: 8,
      action: 'attack',
      target_id: 102,
      damage: 16,
      target_hp: 204,
      stun: true,
    },
    // Tick 4: Gallo Asesino (id: 2) asesta golpe veloz a Toro enemigo (id: 101) por 38 dmg
    {
      tick: 4,
      actor_id: 2,
      action: 'attack',
      target_id: 101,
      damage: 38,
      target_hp: 330,
    },
  ],
};

/* =========================================================================
   ESTRUCTURA DE TEXTOS FLOTANTES DE DAÑO (-{damage})
   ========================================================================= */
interface FloatingDamage {
  key: string;
  gridIndex: number;
  damage: number;
}

/* =========================================================================
   COMPONENTE PRINCIPAL: CombatViewer
   ========================================================================= */

export function CombatViewer({
  replayData = MOCK_REPLAY_DATA,
  unitsConfig = DEFAULT_UNITS_CONFIG,
}: CombatViewerProps) {
  // Determina el grid de partida (props o mock)
  const initialGrid = replayData.initial_grid || DEFAULT_INITIAL_GRID;

  // Estado local requerido
  const [currentTick, setCurrentTick] = useState<number>(0);
  const [gridState, setGridState] = useState<(GridCell | null)[]>(() =>
    initialGrid.map((c) => (c ? { ...c } : null))
  );

  // Estados visuales de Juice
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [damagedIndices, setDamagedIndices] = useState<Set<number>>(new Set());
  const [attackingIndices, setAttackingIndices] = useState<Set<number>>(new Set());
  const [floatingDamages, setFloatingDamages] = useState<FloatingDamage[]>([]);

  // Helper para disparar retroalimentación háptica segura de Telegram Mini Apps
  const triggerHaptic = useCallback((style: 'light' | 'medium' | 'heavy' = 'medium') => {
    try {
      if (HapticFeedback && typeof HapticFeedback.impactOccurred === 'function') {
        HapticFeedback.impactOccurred(style);
      }
    } catch {
      // Fallback silencioso cuando se ejecuta fuera de la aplicación móvil de Telegram
    }
  }, []);

  /**
   * Reinicia la batalla al Tick 0 con las unidades iniciales intactas.
   */
  const handleReplay = useCallback(() => {
    setCurrentTick(0);
    setGridState(initialGrid.map((c) => (c ? { ...c } : null)));
    setDamagedIndices(new Set());
    setAttackingIndices(new Set());
    setFloatingDamages([]);
    setIsPlaying(true);
  }, [initialGrid]);

  /**
   * Aplica un tick del replay_log al gridState sin calcular daño en el frontend.
   * "El frontend es un títere mudo: NO calcula daño, solo asigna valores desde el log".
   */
  const processTick = useCallback(
    (tickNumber: number) => {
      const events = replayData.replay_log.filter((e) => e.tick === tickNumber);
      if (events.length === 0) return;

      const newDamagedSlots = new Set<number>();
      const newAttackerSlots = new Set<number>();
      const newFloatingNumbers: FloatingDamage[] = [];

      setGridState((prevGrid) => {
        // Clon superficial de las celdas para inmutabilidad limpia
        const nextGrid = prevGrid.map((cell) => (cell ? { ...cell } : null));

        for (const event of events) {
          // Encontrar índice del actor y del objetivo
          const actorIdx = nextGrid.findIndex((c) => c && c.id === event.actor_id);
          const targetIdx = nextGrid.findIndex((c) => c && c.id === event.target_id);

          if (actorIdx !== -1) {
            newAttackerSlots.add(actorIdx);
          }

          if (event.action === 'attack') {
            // JUICE OBLIGATORIO: HapticFeedback.impactOccurred('medium')
            triggerHaptic('medium');

            if (targetIdx !== -1 && nextGrid[targetIdx]) {
              const targetUnit = nextGrid[targetIdx]!;
              newDamagedSlots.add(targetIdx);

              // Asignación directa desde el log (sin fórmula ni lógica de mitigación)
              if (event.target_hp !== undefined) {
                targetUnit.current_hp = event.target_hp;
              } else if (event.damage !== undefined) {
                targetUnit.current_hp = Math.max(0, targetUnit.current_hp - event.damage);
              }

              // Aplicar aturdimiento si el log lo indica
              if (event.stun !== undefined) {
                targetUnit.is_stunned = Boolean(event.stun);
              }

              // JUICE: Texto flotante -{damage}
              if (event.damage !== undefined) {
                newFloatingNumbers.push({
                  key: `${tickNumber}-${event.actor_id}-${event.target_id}-${Math.random()}`,
                  gridIndex: targetIdx,
                  damage: event.damage,
                });
              }
            }
          } else if (event.action === 'stun' && targetIdx !== -1 && nextGrid[targetIdx]) {
            nextGrid[targetIdx]!.is_stunned = true;
          } else if (event.action === 'heal' && targetIdx !== -1 && nextGrid[targetIdx]) {
            const targetUnit = nextGrid[targetIdx]!;
            if (event.target_hp !== undefined) {
              targetUnit.current_hp = event.target_hp;
            } else if (event.heal !== undefined) {
              targetUnit.current_hp = Math.min(targetUnit.max_hp, targetUnit.current_hp + event.heal);
            }
          }
        }

        return nextGrid;
      });

      // Activar sacudida (animate-shake) y destello rojo (flash-red) temporal
      if (newDamagedSlots.size > 0) {
        setDamagedIndices(newDamagedSlots);
        setTimeout(() => {
          setDamagedIndices(new Set());
        }, 450);
      }

      if (newAttackerSlots.size > 0) {
        setAttackingIndices(newAttackerSlots);
        setTimeout(() => {
          setAttackingIndices(new Set());
        }, 350);
      }

      // Registrar textos flotantes y eliminarlos a los 1000ms
      if (newFloatingNumbers.length > 0) {
        setFloatingDamages((prev) => [...prev, ...newFloatingNumbers]);
        setTimeout(() => {
          setFloatingDamages((prev) =>
            prev.filter((d) => !newFloatingNumbers.some((n) => n.key === d.key))
          );
        }, 1000);
      }
    },
    [replayData.replay_log, triggerHaptic]
  );

  /**
   * Bucle de animación por ticks:
   * Usa useEffect con setInterval a 500ms por tick según las instrucciones.
   */
  useEffect(() => {
    if (!isPlaying || currentTick >= replayData.total_ticks) return;

    const intervalId = window.setInterval(() => {
      const nextTick = currentTick + 1;
      processTick(nextTick);
      setCurrentTick(nextTick);

      if (nextTick >= replayData.total_ticks) {
        setIsPlaying(false);
      }
    }, 500);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isPlaying, currentTick, replayData.total_ticks, processTick]);

  const isCombatOver = currentTick >= replayData.total_ticks;

  return (
    <div className="flex flex-col items-center justify-center p-4 max-w-md mx-auto select-none font-sans text-stone-100">
      {/* CABECERA DEL COMBATE (HUD) */}
      <div className="w-full bg-stone-900/90 border border-stone-800 rounded-xl p-3 mb-3 shadow-lg flex items-center justify-between">
        <div>
          <span className="text-xs uppercase tracking-wider text-amber-400 font-semibold block">
            Simulación de Batalla
          </span>
          <div className="text-lg font-bold text-stone-200">
            Tick <span className="text-amber-400 font-mono">{currentTick}</span> / {replayData.total_ticks}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsPlaying((p) => !p)}
            disabled={isCombatOver}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              isCombatOver
                ? 'opacity-40 cursor-not-allowed bg-stone-800 text-stone-500'
                : isPlaying
                ? 'bg-amber-600/80 hover:bg-amber-600 text-white'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/50 shadow-md'
            }`}
          >
            {isPlaying ? '⏸ Pausa' : '▶ Reproducir'}
          </button>

          <button
            type="button"
            onClick={handleReplay}
            className="px-3 py-1.5 text-xs font-bold bg-amber-500 hover:bg-amber-400 text-stone-950 rounded-lg shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-1"
          >
            <span>🔁</span> Replay
          </button>
        </div>
      </div>

      {/* RESULTADO AL FINALIZAR */}
      {isCombatOver && (
        <div
          className={`w-full py-2 px-4 rounded-lg mb-3 text-center text-sm font-bold shadow-md transition-all ${
            replayData.winner === 'player'
              ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-600/50'
              : 'bg-rose-950/80 text-rose-300 border border-rose-600/50'
          }`}
        >
          {replayData.winner === 'player' ? '🏆 ¡VICTORIA ALIADA!' : '💀 DERROTA EN COMBATE'}
        </div>
      )}

      {/* TABLERO DE COMBATE 3x3 */}
      <div className="relative w-full aspect-square max-w-[360px] bg-stone-950/90 border-2 border-stone-800 rounded-2xl p-2.5 shadow-2xl backdrop-blur-sm">
        {/* Marcador táctico de fondo */}
        <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 p-2.5 pointer-events-none opacity-10">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={`grid-line-${i}`} className="border border-stone-600 rounded-lg m-0.5" />
          ))}
        </div>

        <div className="grid grid-cols-3 grid-rows-3 gap-2 w-full h-full relative z-10">
          {gridState.map((cell, index) => {
            const config = cell ? unitsConfig[cell.unit_id] : null;
            const isDamaged = damagedIndices.has(index);
            const isAttacking = attackingIndices.has(index);
            const isDead = cell ? cell.current_hp <= 0 : false;
            const hpPercent = cell
              ? Math.max(0, Math.min(100, (cell.current_hp / cell.max_hp) * 100))
              : 0;

            // Filtro de daños flotantes que pertenecen a esta celda
            const cellDamages = floatingDamages.filter((d) => d.gridIndex === index);

            return (
              <div
                key={`cell-${index}`}
                className={`relative flex flex-col items-center justify-between p-1.5 rounded-xl border transition-all duration-200 overflow-visible ${
                  cell
                    ? cell.team === 'player'
                      ? 'bg-gradient-to-b from-stone-800 to-stone-900 border-amber-600/40'
                      : 'bg-gradient-to-b from-rose-950/40 to-stone-900 border-rose-600/40'
                    : 'bg-stone-900/30 border-stone-800/40 border-dashed'
                } ${isDamaged ? 'animate-shake flash-red' : ''} ${
                  isAttacking ? 'scale-105 ring-2 ring-amber-400/70' : ''
                } ${isDead ? 'opacity-40 grayscale' : ''}`}
              >
                {/* TEXTOS FLOTANTES DE DAÑO (-{damage}) */}
                {cellDamages.map((dmg) => (
                  <div
                    key={dmg.key}
                    className="absolute -top-3 z-30 font-black text-rose-400 text-base md:text-lg tracking-wider drop-shadow-[0_2px_4px_rgba(0,0,0,1)] animate-float-damage select-none"
                  >
                    -{dmg.damage}
                  </div>
                ))}

                {cell && config ? (
                  <>
                    {/* BARRAS Y BADGES SUPERIORES */}
                    <div className="w-full flex items-center justify-between text-[10px] text-stone-400 px-0.5">
                      <span className="font-semibold truncate max-w-[60px] text-stone-300">
                        {config.name.split(' ')[0]}
                      </span>
                      {cell.is_stunned && (
                        <span
                          title="Aturdido"
                          className="animate-stun text-amber-300 text-xs leading-none"
                        >
                          💫
                        </span>
                      )}
                    </div>

                    {/* SPRITE DE LA UNIDAD */}
                    <div className="relative my-auto flex items-center justify-center">
                      <UnitAvatar
                        unitId={cell.unit_id}
                        className="w-10 h-10 object-contain text-3xl md:text-4xl filter drop-shadow-md select-none transform transition-transform hover:scale-110 flex items-center justify-center"
                      />
                      {isDead && (
                        <div className="absolute inset-0 flex items-center justify-center font-bold text-red-500 text-2xl">
                          ❌
                        </div>
                      )}
                    </div>

                    {/* BARRA DE VIDA (current_hp / max_hp) */}
                    <div className="w-full mt-auto">
                      <div className="w-full bg-stone-950 rounded-full h-2 overflow-hidden border border-stone-700/60 p-[1px]">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            hpPercent > 50
                              ? 'bg-gradient-to-r from-emerald-600 to-emerald-400'
                              : hpPercent > 20
                              ? 'bg-gradient-to-r from-amber-600 to-amber-400'
                              : 'bg-gradient-to-r from-rose-700 to-rose-500'
                          }`}
                          style={{ width: `${hpPercent}%` }}
                        />
                      </div>
                      <div className="text-[9px] text-center text-stone-400 font-mono mt-0.5">
                        {Math.round(cell.current_hp)}/{cell.max_hp}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-stone-700 text-xs font-mono">
                    [{index}]
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* PIE CON LEYENDA TÁCTICA */}
      <div className="w-full mt-3 flex items-center justify-between text-[11px] text-stone-400 px-2">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
          <span>Aliados (Player)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
          <span>Enemigos (Wave)</span>
        </div>
      </div>
    </div>
  );
}

export default CombatViewer;
