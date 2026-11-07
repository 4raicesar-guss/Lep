/**
 * BattlePage.tsx — Contenedor de combate real conectado al backend (Día 11).
 *
 * Responsabilidades:
 * - Cargar estado del jugador con GET /api/player/state.
 * - Si no tiene unidades en formación, advertir y redirigir a /formation.
 * - Si tiene formación, enviar el array real a POST /api/combat/simulate.
 * - Al ganar, mostrar recompensa de grano y botón "Volver a la Granja" (home).
 * - Disparar trackEvent('win_wave') y trackEvent('start_wave').
 */

import { useState, useEffect, useCallback } from 'react';
import { CombatViewer, type ReplayData } from '../components/CombatViewer';
import { fetchPlayerState, simulateCombat } from '../lib/api';
import { UNITS_CONFIG, type UnitSlot, type View } from '../lib/game';
import { trackEvent } from '../analytics';
import { UnitAvatar } from '../components/UnitAvatar';

interface BattlePageProps {
  onNavigate?: (view: View) => void;
}

type BattlePhase = 'loading' | 'empty_formation' | 'ready_to_fight' | 'simulating' | 'in_combat' | 'error';

export function BattlePage({ onNavigate }: BattlePageProps) {
  const [phase, setPhase] = useState<BattlePhase>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [formationUnits, setFormationUnits] = useState<UnitSlot[]>([]);
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [waveNumber] = useState<number>(1);

  // Carga inicial del estado del jugador
  const loadState = useCallback(async () => {
    setPhase('loading');
    setErrorMessage('');
    try {
      const state = await fetchPlayerState();

      // Extraer unidades que estén desplegadas en slots 0..8
      const equipped: UnitSlot[] = [];
      for (const unit of state.units) {
        if (unit.slot !== null && unit.slot >= 0 && unit.slot <= 8) {
          equipped.push({
            unit_id: unit.unit_id,
            level: unit.level,
            position: unit.slot,
          });
        }
      }

      if (equipped.length === 0) {
        setPhase('empty_formation');
      } else {
        // Ordenar por posición 0..8
        equipped.sort((a, b) => a.position - b.position);
        setFormationUnits(equipped);
        setPhase('ready_to_fight');
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Error al cargar datos del jugador.');
      setPhase('error');
    }
  }, []);

  useEffect(() => {
    loadState();
  }, [loadState]);

  // Simulación de combate
  const handleStartCombat = async () => {
    if (formationUnits.length === 0) {
      setPhase('empty_formation');
      return;
    }

    setPhase('simulating');
    setErrorMessage('');

    try {
      trackEvent('start_wave', {
        wave_number: waveNumber,
        formation_size: formationUnits.length,
      });

      const replay = await simulateCombat(formationUnits, waveNumber);
      setReplayData(replay);
      setPhase('in_combat');

      // Analítica según resultado
      if (replay.winner === 'player') {
        trackEvent('win_wave', { wave_number: waveNumber, grain_reward: 100 });
      } else {
        trackEvent('fail_wave', { wave_number: waveNumber });
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Error al simular la batalla.');
      setPhase('error');
    }
  };

  const handleReset = () => {
    setReplayData(null);
    setPhase('ready_to_fight');
  };

  // -------------------------------------------------------------------------
  // Render: Cargando
  // -------------------------------------------------------------------------
  if (phase === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[340px] text-stone-300 gap-3">
        <div className="w-10 h-10 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        <p className="text-sm font-semibold tracking-wide text-stone-400">Consultando formación activa…</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Sin formación equipada (Validación requerida)
  // -------------------------------------------------------------------------
  if (phase === 'empty_formation') {
    return (
      <div className="w-full max-w-md mx-auto p-6 bg-stone-900/90 border border-stone-800 rounded-2xl flex flex-col items-center text-center shadow-xl mt-4">
        <div className="text-5xl mb-3 animate-bounce">🛡️</div>
        <h2 className="text-xl font-bold text-amber-400 mb-2">Debes formar tu equipo primero</h2>
        <p className="text-sm text-stone-300 mb-6 max-w-xs">
          No tienes unidades asignadas en el tablero táctico. Coloca al menos una unidad para poder combatir.
        </p>
        <button
          type="button"
          onClick={() => onNavigate?.('formation')}
          className="w-full py-3.5 px-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-stone-950 font-bold rounded-xl shadow-lg shadow-amber-900/40 transition active:scale-95"
        >
          ⚔️ Ir a Formación
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error
  // -------------------------------------------------------------------------
  if (phase === 'error') {
    return (
      <div className="w-full max-w-md mx-auto p-5 bg-rose-950/60 border border-rose-600/40 rounded-2xl text-rose-300 flex flex-col items-center text-center gap-3 mt-4">
        <div className="text-3xl">⚠️</div>
        <div className="font-bold text-base">Error en el Combate</div>
        <p className="text-xs text-rose-400/90 break-words">{errorMessage}</p>
        <button
          type="button"
          onClick={loadState}
          className="mt-2 px-5 py-2 bg-stone-800 hover:bg-stone-700 text-stone-200 text-xs font-semibold rounded-lg transition"
        >
          🔄 Reintentar
        </button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: En combate / Replay activo
  // -------------------------------------------------------------------------
  if (phase === 'in_combat' && replayData) {
    const isWinner = replayData.winner === 'player';

    return (
      <div className="flex flex-col items-center w-full max-w-md mx-auto">
        {/* Badge datos reales */}
        <div className="w-full mb-2 px-3 py-1.5 bg-emerald-950/60 border border-emerald-600/40 rounded-xl flex items-center justify-between text-xs">
          <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Servidor Python · Seed <span className="font-mono text-emerald-300">{(replayData as ReplayData & { seed?: number }).seed ?? '—'}</span>
          </span>
          <button
            type="button"
            onClick={handleReset}
            className="text-stone-400 hover:text-stone-200 transition text-xs underline underline-offset-2"
          >
            Preparar otra
          </button>
        </div>

        {/* Visualizador de combate */}
        <CombatViewer replayData={replayData} />

        {/* Banner de Recompensa y Regreso al ganar */}
        {isWinner && (
          <div className="w-full mt-4 p-4 bg-gradient-to-b from-amber-950/70 to-stone-900 border-2 border-amber-500/50 rounded-2xl flex flex-col items-center text-center shadow-2xl animate-fade-in">
            <div className="text-3xl mb-1">🎉</div>
            <h3 className="text-lg font-black text-amber-300 uppercase tracking-wide">
              ¡Victoria en la Oleada {waveNumber}!
            </h3>
            <div className="my-2.5 px-4 py-2 bg-amber-500/20 border border-amber-400/40 rounded-xl flex items-center gap-2 text-amber-200 font-bold text-sm">
              <span className="text-xl">🌾</span> Recompensa: +100 Grano
            </div>
            <button
              type="button"
              onClick={() => onNavigate?.('home')}
              className="w-full mt-1 py-3 px-4 bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-stone-950 font-bold rounded-xl shadow-lg shadow-amber-950/50 transition active:scale-95 text-sm"
            >
              🏠 Volver a la Granja
            </button>
          </div>
        )}

        {/* Si fue derrota */}
        {!isWinner && (
          <div className="w-full mt-4 p-4 bg-stone-900 border border-rose-700/50 rounded-2xl flex flex-col items-center text-center shadow-xl">
            <h3 className="text-base font-bold text-rose-400 mb-2">💀 Derrota Táctica</h3>
            <p className="text-xs text-stone-400 mb-3">Mejora tus unidades en el Banco o ajusta tu formación 3x3.</p>
            <div className="flex gap-2 w-full">
              <button
                type="button"
                onClick={() => onNavigate?.('formation')}
                className="flex-1 py-2.5 px-3 bg-stone-800 hover:bg-stone-700 text-amber-300 font-semibold rounded-xl text-xs transition"
              >
                ⚔️ Ajustar Formación
              </button>
              <button
                type="button"
                onClick={handleStartCombat}
                className="flex-1 py-2.5 px-3 bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold rounded-xl text-xs transition"
              >
                🔄 Reintentar
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Listo para combatir (Mostrar Formación Real del Jugador)
  // -------------------------------------------------------------------------
  return (
    <div className="flex flex-col items-center justify-center gap-5 w-full max-w-md mx-auto">
      {/* Título */}
      <div className="text-center">
        <div className="text-3xl mb-1">⚔️</div>
        <h2 className="text-xl font-bold text-stone-100">Arena de Combate</h2>
        <p className="text-xs text-stone-400">Oleada {waveNumber} · Simulación determinista en servidor</p>
      </div>

      {/* Grid de Formación Real del Jugador */}
      <div className="w-full bg-stone-900/90 border border-stone-800 rounded-2xl p-4 shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-amber-400 font-bold uppercase tracking-wider">Tu Formación ({formationUnits.length}/9)</span>
          <button
            type="button"
            onClick={() => onNavigate?.('formation')}
            className="text-xs text-stone-400 hover:text-amber-400 transition underline underline-offset-2"
          >
            Modificar
          </button>
        </div>

        {/* Grid 3x3 miniatura de la formación actual */}
        <div className="grid grid-cols-3 gap-2 text-center">
          {Array.from({ length: 9 }).map((_, idx) => {
            const unitInSlot = formationUnits.find((u) => u.position === idx);
            const config = unitInSlot ? UNITS_CONFIG[unitInSlot.unit_id] : null;

            return (
              <div
                key={`slot-${idx}`}
                className={`h-20 rounded-xl flex flex-col items-center justify-center border transition-all ${
                  unitInSlot && config
                    ? 'bg-gradient-to-b from-stone-800 to-stone-900 border-amber-500/40 shadow-inner'
                    : 'bg-stone-950/40 border-stone-800/50 border-dashed text-stone-700'
                }`}
              >
                {unitInSlot && config ? (
                  <>
                    <UnitAvatar
                      unitId={unitInSlot.unit_id}
                      className="w-7 h-7 object-contain text-2xl select-none flex items-center justify-center"
                    />
                    <span className="text-[10px] text-stone-300 font-semibold truncate max-w-[80px]">
                      {config.name.split(' ')[0]}
                    </span>
                    <span className="text-[9px] text-amber-400 font-mono">Nv {unitInSlot.level}</span>
                  </>
                ) : (
                  <span className="text-xs font-mono text-stone-700">[{idx}]</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Botón Iniciar Batalla Real */}
      <button
        type="button"
        onClick={handleStartCombat}
        disabled={phase === 'simulating'}
        className={`w-full py-4 rounded-xl font-bold text-base tracking-wide transition-all shadow-xl ${
          phase === 'simulating'
            ? 'bg-stone-700 text-stone-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-amber-500 to-amber-400 text-stone-950 hover:from-amber-400 hover:to-amber-300 active:scale-95 shadow-amber-900/40'
        }`}
      >
        {phase === 'simulating' ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Simulando en el servidor…
          </span>
        ) : (
          '⚔️ Iniciar Batalla Real'
        )}
      </button>
    </div>
  );
}

export default BattlePage;
