/**
 * HomePage.tsx — Granja Central (Día 11).
 *
 * Responsabilidades:
 * - Consultar estado del jugador con GET /api/player/state.
 * - Contador animado de grano total.
 * - Botón "¡Recolectar!" para cobro offline vía POST /api/resources/collect.
 * - Sección de Edificios (Silo, Galpón, Boyero) con coste 100 * 1.5^nivel.
 * - Botón "Mejorar" con protección isProcessing y control de "Grano insuficiente".
 * - Botón principal "¡A la Batalla!" que redirige a 'battle' o 'formation'.
 * - Eventos analíticos: collect_offline, upgrade_building.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { collectResources, fetchPlayerState, upgradeBuilding } from '../lib/api';
import {
  BUILDINGS_CONFIG,
  calculateUpgradeCost,
  type BuildingId,
  type PlayerStateResponse,
  type View,
} from '../lib/game';
import { trackEvent } from '../analytics';
import { TutorialModal } from '../components/TutorialModal';

interface HomePageProps {
  onNavigate: (view: View) => void;
}

interface ToastMessage {
  id: number;
  type: 'success' | 'warning' | 'info';
  message: string;
}

export function HomePage({ onNavigate }: HomePageProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [playerState, setPlayerState] = useState<PlayerStateResponse | null>(null);

  // Estados de bloqueo durante peticiones de escritura
  const [isCollecting, setIsCollecting] = useState<boolean>(false);
  const [upgradingBuilding, setUpgradingBuilding] = useState<string | null>(null);

  // Contador animado de grano
  const [displayGrain, setDisplayGrain] = useState<number>(0);
  const previousGrainRef = useRef<number>(0);

  // Toasts / Alertas flotantes
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Tutorial Onboarding
  const [showTutorial, setShowTutorial] = useState<boolean>(() => {
    try {
      return localStorage.getItem('tutorial_completed_v1') === null;
    } catch {
      return false;
    }
  });

  const handleTutorialComplete = () => {
    try {
      localStorage.setItem('tutorial_completed_v1', 'true');
    } catch {
      // Fallback silencioso
    }
    trackEvent('tutorial_complete');
    setShowTutorial(false);
  };

  const showToast = (message: string, type: 'success' | 'warning' | 'info' = 'info') => {
    const id = Date.now();
    setToast({ id, message, type });
    setTimeout(() => {
      setToast((current) => (current?.id === id ? null : current));
    }, 3500);
  };

  // Carga inicial
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const state = await fetchPlayerState();
      setPlayerState(state);
      const grain = state.resources?.grain ?? state.grain ?? 0;
      setDisplayGrain(grain);
      previousGrainRef.current = grain;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar los datos de la granja.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Animación del contador de grano al cambiar
  const targetGrain = playerState?.resources?.grain ?? playerState?.grain ?? 0;
  useEffect(() => {
    if (loading) return;

    const start = previousGrainRef.current;
    const end = targetGrain;
    if (start === end) return;

    const duration = 600; // ms
    const startTime = performance.now();

    const step = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = Math.round(start + (end - start) * easeProgress);
      setDisplayGrain(currentVal);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        setDisplayGrain(end);
        previousGrainRef.current = end;
      }
    };

    requestAnimationFrame(step);
  }, [targetGrain, loading]);

  // Recolectar recursos offline
  const handleCollect = async () => {
    if (isCollecting) return;
    setIsCollecting(true);

    try {
      const res = await collectResources();
      trackEvent('collect_offline', { grain_amount: res.grain_collected });

      // Actualizar estado local inmediatamente
      setPlayerState((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          grain: res.new_total_grain,
          resources: {
            ...prev.resources,
            grain: res.new_total_grain,
          },
        };
      });

      if (res.grain_collected > 0) {
        showToast(`🌾 ¡Recolectaste +${res.grain_collected.toLocaleString()} granos!`, 'success');
      } else {
        showToast('🌾 No hay grano acumulado en este momento.', 'info');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al recolectar grano.';
      showToast(msg, 'warning');
    } finally {
      setIsCollecting(false);
    }
  };

  // Mejorar edificio
  const handleUpgrade = async (buildingId: BuildingId) => {
    if (upgradingBuilding) return;
    setUpgradingBuilding(buildingId);

    try {
      const res = await upgradeBuilding(buildingId);
      trackEvent('upgrade_building', { building_id: buildingId, new_level: res.new_level });

      // Actualizar niveles y grano restante
      setPlayerState((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          grain: res.remaining_grain,
          resources: {
            ...prev.resources,
            grain: res.remaining_grain,
          },
          buildings: {
            ...prev.buildings,
            [`${buildingId}_level`]: res.new_level,
          },
        };
      });

      const config = BUILDINGS_CONFIG[buildingId];
      showToast(`✨ ¡${config.name} mejorado a Nivel ${res.new_level}! (-${res.cost} grano)`, 'success');
    } catch (err) {
      const rawMsg = err instanceof Error ? err.message : 'Error al mejorar el edificio.';
      // Mensaje amigable si es grano insuficiente
      if (rawMsg.toLowerCase().includes('grano insuficiente') || rawMsg.toLowerCase().includes('requieres')) {
        showToast('🌾 Grano insuficiente para realizar esta mejora.', 'warning');
      } else {
        showToast(rawMsg, 'warning');
      }
    } finally {
      setUpgradingBuilding(null);
    }
  };

  // Validar si el jugador tiene alguna unidad equipada
  const hasEquippedUnits = Boolean(
    playerState?.units?.some((u) => u.slot !== null) ||
      (playerState?.formation?.slots &&
        Object.values(playerState.formation.slots).some((uuid) => uuid !== null))
  );

  const handleGoToBattle = () => {
    if (hasEquippedUnits) {
      onNavigate('battle');
    } else {
      showToast('🛡️ Equipa tu equipo en el tablero antes de luchar.', 'info');
      onNavigate('formation');
    }
  };

  // -------------------------------------------------------------------------
  // Render: Cargando
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[360px] text-stone-300 gap-3">
        <div className="w-10 h-10 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        <p className="text-sm font-semibold tracking-wide text-stone-400">Cargando granja…</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error
  // -------------------------------------------------------------------------
  if (error || !playerState) {
    return (
      <div className="w-full max-w-md mx-auto p-5 bg-rose-950/60 border border-rose-600/40 rounded-2xl text-rose-300 flex flex-col items-center text-center gap-3 mt-4">
        <div className="text-3xl">⚠️</div>
        <div className="font-bold text-base">Error al cargar la Granja</div>
        <p className="text-xs text-rose-400/90 break-words">{error || 'No se pudo obtener el estado.'}</p>
        <button
          type="button"
          onClick={loadData}
          className="mt-2 px-5 py-2 bg-stone-800 hover:bg-stone-700 text-stone-200 text-xs font-semibold rounded-lg transition"
        >
          🔄 Reintentar
        </button>
      </div>
    );
  }

  const buildings = playerState.buildings;

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-md mx-auto select-none">
      {/* Tutorial Onboarding de Primera Sesión */}
      {showTutorial && <TutorialModal onComplete={handleTutorialComplete} />}

      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-4 z-50 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl border transition-all animate-bounce ${
            toast.type === 'success'
              ? 'bg-emerald-900/95 border-emerald-500 text-emerald-100'
              : toast.type === 'warning'
              ? 'bg-amber-900/95 border-amber-500 text-amber-100'
              : 'bg-stone-800/95 border-stone-600 text-stone-100'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Tarjeta de Recursos y Recolección Offline */}
      <div className="w-full bg-gradient-to-b from-stone-900 to-stone-950 border border-stone-800 rounded-2xl p-4 shadow-xl flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-3xl filter drop-shadow">🌾</span>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-stone-400 font-semibold block">
                Grano Almacenado
              </span>
              <div className="text-2xl font-black text-amber-400 font-mono tracking-tight">
                {displayGrain.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="text-right">
            <span className="text-[10px] text-stone-500 block">Capacidad Silo</span>
            <span className="text-xs font-semibold text-stone-300">
              Nv {buildings.silo_level}/5 · {Math.min(4 + 2 * buildings.silo_level, 12)}h
            </span>
          </div>
        </div>

        {/* Botón Grande ¡Recolectar! */}
        <button
          type="button"
          onClick={handleCollect}
          disabled={isCollecting}
          className={`w-full py-3 px-4 rounded-xl font-black text-sm tracking-wide transition-all shadow-lg flex items-center justify-center gap-2 ${
            isCollecting
              ? 'bg-stone-800 text-stone-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-stone-950 active:scale-95 shadow-amber-900/40'
          }`}
        >
          {isCollecting ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Recolectando…
            </span>
          ) : (
            <>
              <span className="text-base">🚜</span> ¡Recolectar Grano!
            </>
          )}
        </button>
      </div>

      {/* Sección de Edificios */}
      <div className="w-full flex flex-col gap-2.5">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-stone-400">Edificios de la Granja</h3>
          <span className="text-[10px] text-stone-500">Nivel Máximo: 5</span>
        </div>

        {(['silo', 'galpon', 'boyero'] as BuildingId[]).map((bId) => {
          const config = BUILDINGS_CONFIG[bId];
          const levelKey = `${bId}_level` as keyof typeof buildings;
          const currentLevel = buildings[levelKey] ?? 1;
          const isMax = currentLevel >= 5;
          const upgradeCost = calculateUpgradeCost(currentLevel);
          const isUpgrading = upgradingBuilding === bId;
          const canAfford = targetGrain >= upgradeCost;

          return (
            <div
              key={bId}
              className="w-full bg-stone-900/90 border border-stone-800/80 rounded-xl p-3 flex items-center justify-between gap-3 shadow-sm hover:border-stone-700/80 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 bg-stone-800/90 border border-stone-700/60 rounded-xl flex items-center justify-center text-2xl shadow-inner select-none">
                  {config.emoji}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-stone-100">{config.name}</span>
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md bg-stone-800 text-amber-400 border border-amber-600/20">
                      Nv {currentLevel}/5
                    </span>
                  </div>
                  <span className="text-[11px] text-stone-400 block mt-0.5">
                    {config.bonusText(currentLevel)}
                  </span>
                </div>
              </div>

              {/* Botón Mejorar */}
              <button
                type="button"
                onClick={() => handleUpgrade(bId)}
                disabled={isMax || isUpgrading || Boolean(upgradingBuilding)}
                className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex flex-col items-center justify-center min-w-[84px] ${
                  isMax
                    ? 'bg-stone-800/40 text-stone-600 cursor-not-allowed border border-stone-800'
                    : isUpgrading
                    ? 'bg-stone-800 text-stone-500 cursor-wait'
                    : canAfford
                    ? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/50 active:scale-95'
                    : 'bg-stone-800/60 hover:bg-stone-800 text-stone-400 border border-stone-700/40'
                }`}
              >
                {isMax ? (
                  <span>Máximo</span>
                ) : isUpgrading ? (
                  <span className="text-[10px]">Mejorando…</span>
                ) : (
                  <>
                    <span className="text-[11px]">⬆️ Mejorar</span>
                    <span className="text-[9px] font-mono text-amber-400 mt-0.5">
                      🌾 {upgradeCost}
                    </span>
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Botón Principal: ¡A la Batalla! */}
      <div className="w-full mt-2">
        <button
          type="button"
          onClick={handleGoToBattle}
          className="w-full py-4 px-4 bg-gradient-to-r from-red-600 via-amber-600 to-amber-500 hover:from-red-500 hover:to-amber-400 text-stone-950 font-black text-base rounded-2xl shadow-xl shadow-red-950/40 transition active:scale-95 flex items-center justify-center gap-2"
        >
          <span className="text-xl">💥</span> ¡A la Batalla!
          {!hasEquippedUnits && (
            <span className="text-[10px] bg-stone-950/60 text-amber-300 px-2 py-0.5 rounded-full font-semibold">
              Formar primero
            </span>
          )}
        </button>
      </div>
    </div>
  );
}

export default HomePage;
