/**
 * BattlePage.tsx — Contenedor de integración Frontend ↔ Backend (Día 7).
 *
 * Responsabilidades:
 * - Solicitar una simulación real al endpoint POST /api/combat/simulate.
 * - Pasar el replayData resultante al <CombatViewer />.
 * - Gestionar estados: cargando, error y combate activo.
 */

import { useState, useCallback } from 'react';
import { initData } from '@telegram-apps/sdk';
import { CombatViewer, type ReplayData } from '../components/CombatViewer';

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Formación de prueba hardcodeada (se puede reemplazar por el selector real).
 * Posiciones en el grid 3x3 (0-8):
 *   [0] Cerdo Blindado   [1] Gallo Asesino   [2] Espantapájaros
 *   [3] —                [4] —                [5] —
 *   [6] —                [7] —                [8] —
 */
const TEST_FORMATION = [
  { unit_id: 'U01', level: 1, position: 0 },
  { unit_id: 'U03', level: 1, position: 1 },
  { unit_id: 'U08', level: 1, position: 2 },
];

const TEST_WAVE = 1;

// ---------------------------------------------------------------------------
// Tipos internos
// ---------------------------------------------------------------------------

type BattleState =
  | { phase: 'idle' }
  | { phase: 'loading' }
  | { phase: 'ready'; data: ReplayData }
  | { phase: 'error'; message: string };

// ---------------------------------------------------------------------------
// Helper: obtiene el raw initData de Telegram de forma segura
// ---------------------------------------------------------------------------

function getRawInitData(): string | null {
  try {
    initData.restore();
    const raw =
      typeof initData.raw === 'function'
        ? initData.raw()
        : (initData.raw as unknown as string | undefined);
    return raw || null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Componente BattlePage
// ---------------------------------------------------------------------------

export function BattlePage() {
  const [state, setState] = useState<BattleState>({ phase: 'idle' });

  /**
   * Lanza la petición al backend y actualiza el estado local.
   */
  const startBattle = useCallback(async () => {
    setState({ phase: 'loading' });

    const rawInitData = getRawInitData();

    if (!rawInitData) {
      setState({
        phase: 'error',
        message: 'No se pudo obtener el initData de Telegram. Abre la app desde Telegram.',
      });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/combat/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': rawInitData,
        },
        body: JSON.stringify({
          player_formation: TEST_FORMATION,
          wave_number: TEST_WAVE,
        }),
      });

      if (!response.ok) {
        let detail = `Error ${response.status}`;
        try {
          const body = await response.json();
          detail = body.detail || detail;
        } catch {
          // Respuesta no-JSON: usar status text
          detail = response.statusText || detail;
        }
        setState({ phase: 'error', message: detail });
        return;
      }

      const replayData: ReplayData = await response.json();
      setState({ phase: 'ready', data: replayData });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Error de red desconocido. Verifica tu conexión.';
      setState({ phase: 'error', message });
    }
  }, []);

  /**
   * Reinicia la página al estado idle para pedir una nueva batalla.
   */
  const handleReset = useCallback(() => {
    setState({ phase: 'idle' });
  }, []);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  if (state.phase === 'ready') {
    return (
      <div className="flex flex-col items-center w-full">
        {/* Badge que indica datos reales */}
        <div className="w-full max-w-md mb-2 px-3 py-1.5 bg-emerald-900/60 border border-emerald-600/40 rounded-lg flex items-center justify-between text-xs">
          <span className="text-emerald-400 font-semibold">
            ✅ Datos reales · Seed{' '}
            <span className="font-mono text-emerald-300">
              {(state.data as ReplayData & { seed?: number }).seed ?? '—'}
            </span>
          </span>
          <button
            type="button"
            onClick={handleReset}
            className="text-stone-400 hover:text-stone-200 transition text-xs underline underline-offset-2"
          >
            Nueva batalla
          </button>
        </div>

        <CombatViewer replayData={state.data} />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-6 mt-8 w-full max-w-md mx-auto px-4">
      {/* Título */}
      <div className="text-center">
        <div className="text-3xl mb-2">⚔️</div>
        <h2 className="text-xl font-bold text-stone-100">Arena de Combate</h2>
        <p className="text-sm text-stone-400 mt-1">
          Simulación determinista impulsada por el motor Python del servidor.
        </p>
      </div>

      {/* Formación de prueba (visual) */}
      <div className="w-full bg-stone-900/80 border border-stone-700/50 rounded-xl p-4">
        <p className="text-xs text-amber-400 font-semibold uppercase tracking-wider mb-3">
          Formación de prueba · Oleada {TEST_WAVE}
        </p>
        <div className="grid grid-cols-3 gap-2 text-center text-xs text-stone-300">
          {TEST_FORMATION.map((slot) => (
            <div
              key={`${slot.unit_id}-${slot.position}`}
              className="bg-stone-800/80 border border-amber-600/30 rounded-lg py-2 px-1"
            >
              <div className="text-lg">
                {slot.unit_id === 'U01'
                  ? '🐷'
                  : slot.unit_id === 'U03'
                    ? '🐓'
                    : slot.unit_id === 'U08'
                      ? '🌾'
                      : '❓'}
              </div>
              <div className="font-mono text-[10px] text-stone-400">{slot.unit_id}</div>
              <div className="text-[10px] text-amber-400">Nv {slot.level}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Estado: error */}
      {state.phase === 'error' && (
        <div className="w-full bg-rose-950/60 border border-rose-600/40 rounded-xl p-4 text-sm text-rose-300">
          <p className="font-semibold mb-1">❌ Error al iniciar la batalla</p>
          <p className="text-rose-400/80 text-xs break-words">{state.message}</p>
        </div>
      )}

      {/* Botón principal */}
      <button
        type="button"
        onClick={startBattle}
        disabled={state.phase === 'loading'}
        className={`w-full py-4 rounded-xl font-bold text-base tracking-wide transition-all shadow-lg ${
          state.phase === 'loading'
            ? 'bg-stone-700 text-stone-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-amber-500 to-amber-400 text-stone-950 hover:from-amber-400 hover:to-amber-300 active:scale-95 shadow-amber-900/40'
        }`}
      >
        {state.phase === 'loading' ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Simulando batalla…
          </span>
        ) : state.phase === 'error' ? (
          '🔄 Reintentar'
        ) : (
          '⚔️ Iniciar Batalla Real'
        )}
      </button>

      {/* Nota técnica */}
      <p className="text-[11px] text-stone-600 text-center">
        La simulación ocurre en el servidor (Python) con seed aleatoria.
        <br />
        El frontend recibe el replay y lo anima tick a tick.
      </p>
    </div>
  );
}

export default BattlePage;
