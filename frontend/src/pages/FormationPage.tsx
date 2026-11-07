/**
 * FormationPage.tsx — Tablero Táctico 3x3 (Día 11).
 *
 * Responsabilidades:
 * - Consultar GET /api/player/state para obtener unidades y formación actual.
 * - Grid táctico 3x3 con celdas clickeables (slots 0 a 8).
 * - Desequipar unidades asignadas (fijando el slot en null).
 * - Al hacer clic en un slot vacío, abrir selector con unidades libres en el banco.
 * - Botón "Guardar Formación" con isSaving y llamada a POST /api/formation/save (claves "0".."8").
 * - Disparar trackEvent('formation_saved') y redirigir a 'battle' o 'home'.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchPlayerState, saveFormation } from '../lib/api';
import {
  ROLE_ROW,
  UNITS_CONFIG,
  type UnitInfo,
  type View,
} from '../lib/game';
import { trackEvent } from '../analytics';
import { UnitAvatar } from '../components/UnitAvatar';

interface FormationPageProps {
  onNavigate: (view: View) => void;
}

export function FormationPage({ onNavigate }: FormationPageProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [allUnits, setAllUnits] = useState<UnitInfo[]>([]);

  // Slots 3x3: Claves "0" a "8" mapeadas a UUID o null
  const [slots, setSlots] = useState<Record<string, string | null>>(() => {
    const initial: Record<string, string | null> = {};
    for (let i = 0; i < 9; i++) {
      initial[String(i)] = null;
    }
    return initial;
  });

  // Slot seleccionado para equipar unidad desde el banco
  const [activeSlotToFill, setActiveSlotToFill] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((cur) => (cur === msg ? null : cur));
    }, 3000);
  };

  // Cargar estado inicial del jugador
  const loadFormationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const state = await fetchPlayerState();
      setAllUnits(state.units);

      // Mapear slots desde state.formation.slots asegurando claves "0" a "8"
      const newSlots: Record<string, string | null> = {};
      for (let i = 0; i < 9; i++) {
        const key = String(i);
        newSlots[key] = state.formation?.slots?.[key] ?? null;
      }

      // Si por alguna razón formation.slots no venía poblado pero las unidades tenían unit.slot
      if (Object.values(newSlots).every((v) => v === null)) {
        for (const unit of state.units) {
          if (unit.slot !== null && unit.slot >= 0 && unit.slot <= 8) {
            newSlots[String(unit.slot)] = unit.id;
          }
        }
      }

      setSlots(newSlots);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar la formación.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFormationData();
  }, [loadFormationData]);

  // Unidades disponibles en reserva (que no están actualmente asignadas a ningún slot del tablero)
  const availableReserveUnits = useMemo(() => {
    const assignedIds = new Set(Object.values(slots).filter((id): id is string => Boolean(id)));
    return allUnits.filter((unit) => !assignedIds.has(unit.id));
  }, [allUnits, slots]);

  // Desequipar unidad de un slot
  const handleUnequipSlot = (slotIndex: number) => {
    setSlots((prev) => ({
      ...prev,
      [String(slotIndex)]: null,
    }));
  };

  // Asignar unidad seleccionada al slot activo
  const handleEquipUnit = (unitId: string) => {
    if (activeSlotToFill === null) return;

    setSlots((prev) => ({
      ...prev,
      [String(activeSlotToFill)]: unitId,
    }));
    setActiveSlotToFill(null);
  };

  // Auto-formar: Tanques en fila 0, Soportes/Control en fila 1, Daño en fila 2.
  // Se prioriza por nivel; si la fila preferida está llena, se usa la fila libre más cercana.
  const handleAutoFormat = () => {
    const placed: Record<string, string | null> = {};
    for (let i = 0; i < 9; i++) placed[String(i)] = null;

    const freeSlotsInRow = (row: number) =>
      [0, 1, 2].map((c) => row * 3 + c).filter((idx) => placed[String(idx)] === null);

    const ordered = [...allUnits].sort((a, b) => b.level - a.level);
    let count = 0;
    for (const unit of ordered) {
      if (count >= 9) break;
      const preferredRow = ROLE_ROW[UNITS_CONFIG[unit.unit_id]?.role ?? 'Daño'];
      const rowsByDistance = [0, 1, 2].sort(
        (a, b) => Math.abs(a - preferredRow) - Math.abs(b - preferredRow) || a - b,
      );
      for (const row of rowsByDistance) {
        const free = freeSlotsInRow(row);
        if (free.length > 0) {
          placed[String(free[0])] = unit.id;
          count++;
          break;
        }
      }
    }

    setSlots(placed);
    showToast(`🪄 Auto-formación: ${count} unidad${count === 1 ? '' : 'es'} desplegada${count === 1 ? '' : 's'}`);
  };

  // Guardar formación en el servidor
  const handleSaveFormation = async (targetDestination: 'battle' | 'home' = 'battle') => {
    if (isSaving) return;
    setIsSaving(true);

    try {
      // Normalizar objeto slots asegurando claves strings "0".."8"
      const payload: Record<string, string | null> = {};
      for (let i = 0; i < 9; i++) {
        payload[String(i)] = slots[String(i)] || null;
      }

      const res = await saveFormation(payload);
      trackEvent('formation_saved', { slots: res.slots });

      showToast('✅ ¡Formación guardada correctamente!');
      setTimeout(() => {
        onNavigate(targetDestination);
      }, 500);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al guardar formación.';
      showToast(`❌ ${msg}`);
      setIsSaving(false);
    }
  };

  // Cantidad de slots ocupados
  const equippedCount = Object.values(slots).filter(Boolean).length;

  // -------------------------------------------------------------------------
  // Render: Cargando
  // -------------------------------------------------------------------------
  if (loading && allUnits.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[360px] text-stone-300 gap-3">
        <div className="w-10 h-10 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        <p className="text-sm font-semibold tracking-wide text-stone-400">Cargando tablero táctico…</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error
  // -------------------------------------------------------------------------
  if (error && allUnits.length === 0) {
    return (
      <div className="w-full max-w-md mx-auto p-5 bg-rose-950/60 border border-rose-600/40 rounded-2xl text-rose-300 flex flex-col items-center text-center gap-3 mt-4">
        <div className="text-3xl">⚠️</div>
        <div className="font-bold text-base">Error al cargar Formación</div>
        <p className="text-xs text-rose-400/90 break-words">{error}</p>
        <button
          type="button"
          onClick={loadFormationData}
          className="mt-2 px-5 py-2 bg-stone-800 hover:bg-stone-700 text-stone-200 text-xs font-semibold rounded-lg transition"
        >
          🔄 Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-md mx-auto select-none">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed top-4 z-50 px-4 py-2 bg-stone-900 border border-amber-500 text-amber-200 text-xs font-semibold rounded-xl shadow-2xl animate-fade-in">
          {toastMessage}
        </div>
      )}

      {/* Cabecera */}
      <div className="w-full bg-stone-900/90 border border-stone-800 rounded-2xl p-3.5 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-stone-100 flex items-center gap-2">
            <span>⚔️</span> Formación Táctica 3x3
          </h2>
          <p className="text-xs text-stone-400 mt-0.5">
            Configura las posiciones de tus tropas para el combate
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-stone-500 block">Equipadas</span>
          <span className="text-sm font-bold text-amber-400 font-mono">
            {equippedCount}/9
          </span>
        </div>
      </div>

      {/* Tablero Táctico 3x3 */}
      <div className="relative w-full aspect-square max-w-[360px] bg-stone-950/90 border-2 border-stone-800 rounded-2xl p-2.5 shadow-2xl">
        <div className="grid grid-cols-3 grid-rows-3 gap-2 w-full h-full relative z-10">
          {Array.from({ length: 9 }).map((_, slotIdx) => {
            const unitUuid = slots[String(slotIdx)];
            const unit = unitUuid ? allUnits.find((u) => u.id === unitUuid) : null;
            const config = unit ? UNITS_CONFIG[unit.unit_id] : null;

            if (unit && config) {
              return (
                <div
                  key={`slot-${slotIdx}`}
                  className="relative flex flex-col items-center justify-between p-1.5 rounded-xl border border-amber-600/40 bg-gradient-to-b from-stone-800 to-stone-900 shadow-md group transition-all"
                >
                  {/* Badge de Posición y Desequipar */}
                  <div className="w-full flex items-center justify-between text-[10px]">
                    <span className="font-mono text-stone-400 font-bold">[{slotIdx}]</span>
                    <button
                      type="button"
                      onClick={() => handleUnequipSlot(slotIdx)}
                      title="Desequipar"
                      className="text-stone-400 hover:text-rose-400 p-0.5 transition"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Sprite */}
                  <div className="my-auto flex items-center justify-center">
                    <UnitAvatar
                      unitId={unit.unit_id}
                      className="w-9 h-9 object-contain text-3xl filter drop-shadow select-none flex items-center justify-center"
                    />
                  </div>

                  {/* Info inferior */}
                  <div className="w-full text-center">
                    <span className="text-[10px] font-semibold text-stone-200 block truncate">
                      {config.name.split(' ')[0]}
                    </span>
                    <span className="text-[9px] font-mono text-amber-400 font-bold">
                      Nv {unit.level}
                    </span>
                  </div>
                </div>
              );
            }

            // Slot Vacío Clickeable
            return (
              <button
                key={`slot-${slotIdx}`}
                type="button"
                onClick={() => setActiveSlotToFill(slotIdx)}
                className="flex flex-col items-center justify-center p-2 rounded-xl border-2 border-dashed border-stone-800/80 bg-stone-900/30 hover:bg-stone-900/60 hover:border-amber-500/50 transition-all text-stone-600 hover:text-amber-400 group"
              >
                <span className="text-xl group-hover:scale-125 transition-transform">➕</span>
                <span className="text-[10px] font-mono mt-1 text-stone-500 group-hover:text-amber-400/80">
                  [{slotIdx}] Vacío
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Botones de Acción */}
      <div className="w-full flex flex-col gap-2 mt-1">
        <button
          type="button"
          onClick={handleAutoFormat}
          disabled={isSaving || allUnits.length === 0}
          className="w-full py-2.5 px-3 bg-stone-900 hover:bg-stone-800 border border-amber-600/40 hover:border-amber-500/70 rounded-xl text-amber-300 text-xs font-bold transition active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          🪄 Auto-formar (Tanques al frente · Soporte · Daño atrás)
        </button>

        <button
          type="button"
          onClick={() => handleSaveFormation('battle')}
          disabled={isSaving}
          className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm tracking-wide transition-all shadow-xl flex items-center justify-center gap-2 ${
            isSaving
              ? 'bg-stone-700 text-stone-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-stone-950 active:scale-95 shadow-amber-900/40'
          }`}
        >
          {isSaving ? (
            <span>Guardando formación…</span>
          ) : (
            <>
              <span>💾</span> Guardar e ir a la Batalla
            </>
          )}
        </button>

        <button
          type="button"
          onClick={() => handleSaveFormation('home')}
          disabled={isSaving}
          className="w-full py-2.5 px-3 bg-stone-900 hover:bg-stone-800 border border-stone-800 rounded-xl text-stone-400 hover:text-stone-200 text-xs font-semibold transition"
        >
          Guardar y volver a la Granja
        </button>
      </div>

      {/* Modal / Selector de Unidades de Reserva */}
      {activeSlotToFill !== null && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-stone-950/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md bg-stone-900 border border-stone-800 rounded-2xl p-4 shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between pb-3 border-b border-stone-800">
              <div className="flex items-center gap-2">
                <span className="text-lg">🛡️</span>
                <h3 className="font-bold text-sm text-stone-100">
                  Equipar en Slot [{activeSlotToFill}]
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveSlotToFill(null)}
                className="text-stone-400 hover:text-stone-200 text-sm p-1"
              >
                ✕
              </button>
            </div>

            <div className="overflow-y-auto py-3 flex flex-col gap-2 flex-1">
              {availableReserveUnits.length === 0 ? (
                <div className="text-center py-8 text-xs text-stone-400">
                  <p>No tienes unidades disponibles en el banco.</p>
                  <p className="text-[11px] text-stone-500 mt-1">
                    Desequipa alguna unidad del tablero o fusiona en el Banco.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {availableReserveUnits.map((unit) => {
                    const config = UNITS_CONFIG[unit.unit_id];
                    return (
                      <button
                        key={unit.id}
                        type="button"
                        onClick={() => handleEquipUnit(unit.id)}
                        className="p-2 bg-stone-800/80 hover:bg-stone-700/80 border border-stone-700/60 hover:border-amber-500/60 rounded-xl flex flex-col items-center justify-center transition active:scale-95 group"
                      >
                        <UnitAvatar
                          unitId={unit.unit_id}
                          className="w-8 h-8 object-contain text-2xl group-hover:scale-110 transition-transform select-none flex items-center justify-center"
                        />
                        <span className="text-[10px] font-semibold text-stone-200 truncate max-w-[80px] mt-1">
                          {config?.name.split(' ')[0] || unit.unit_id}
                        </span>
                        <span className="text-[9px] font-mono text-amber-400">
                          Nv {unit.level}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-stone-800">
              <button
                type="button"
                onClick={() => setActiveSlotToFill(null)}
                className="w-full py-2 bg-stone-800 hover:bg-stone-700 text-stone-300 text-xs font-semibold rounded-xl transition"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FormationPage;
