/**
 * MergePage.tsx — Banco de Unidades y Fusión Tripartita (Día 11).
 *
 * Responsabilidades:
 * - Consultar GET /api/units/inventory.
 * - Agrupar visualmente las unidades por unit_id y level.
 * - Selección estricta de hasta 3 unidades del MISMO tipo y nivel (nivel < 3).
 * - Botón "Fusionar" con isProcessing y llamada a POST /api/units/merge.
 * - Al completar con éxito, mostrar la nueva unidad creada y refrescar el inventario.
 * - Disparar trackEvent('merge_unit').
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchPlayerState, fetchUnitsInventory, mergeUnits, summonUnit } from '../lib/api';
import {
  SUMMON_COST,
  UNITS_CONFIG,
  type UnitInventoryItem,
  type View,
} from '../lib/game';
import { trackEvent } from '../analytics';
import { UnitAvatar } from '../components/UnitAvatar';

interface MergePageProps {
  onNavigate?: (view: View) => void;
}

interface MergedSuccessData {
  newUnitId: string;
  newLevel: number;
  unitType: string;
}

export function MergePage({ onNavigate }: MergePageProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [inventory, setInventory] = useState<UnitInventoryItem[]>([]);
  const [selectedUuids, setSelectedUuids] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [successData, setSuccessData] = useState<MergedSuccessData | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [grain, setGrain] = useState<number>(0);
  const [buyingUnit, setBuyingUnit] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((cur) => (cur === msg ? null : cur));
    }, 3000);
  };

  // Cargar inventario completo y grano disponible
  const loadInventory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [items, state] = await Promise.all([fetchUnitsInventory(), fetchPlayerState()]);
      setInventory(items);
      setGrain(state.resources?.grain ?? state.grain ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar inventario de unidades.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  // Compra directa de una unidad nivel 1
  const handleBuy = async (unitType: string) => {
    if (buyingUnit || isProcessing) return;
    setBuyingUnit(unitType);
    try {
      const res = await summonUnit(unitType);
      trackEvent('summon_unit', { unit_id: unitType, cost: res.cost });
      setInventory((prev) => [...prev, res.unit]);
      setGrain(res.remaining_grain);
      showToast(`✅ ${UNITS_CONFIG[unitType]?.name ?? unitType} comprado (-${res.cost} 🌾)`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al comprar la unidad.';
      showToast(`❌ ${msg}`);
    } finally {
      setBuyingUnit(null);
    }
  };

  // Encontrar la unidad de referencia actualmente seleccionada (para restringir selecciones futuras)
  const referenceUnit = useMemo(() => {
    if (selectedUuids.length === 0) return null;
    return inventory.find((u) => u.id === selectedUuids[0]) || null;
  }, [selectedUuids, inventory]);

  // Manejo de clic en unidad para selección / deselección
  const toggleSelectUnit = (unit: UnitInventoryItem) => {
    if (isProcessing) return;

    // Si ya está seleccionada -> deseleccionar
    if (selectedUuids.includes(unit.id)) {
      setSelectedUuids((prev) => prev.filter((id) => id !== unit.id));
      return;
    }

    // Validación: Nivel máximo
    if (unit.level >= 3) {
      showToast('⚠️ Las unidades de Nivel 3 ya están al máximo nivel de poder.');
      return;
    }

    // Si no hay nada seleccionado, agregamos directamente
    if (selectedUuids.length === 0) {
      setSelectedUuids([unit.id]);
      return;
    }

    // Si ya hay unidades seleccionadas, verificar que coincida tipo y nivel
    if (referenceUnit) {
      if (unit.unit_id !== referenceUnit.unit_id || unit.level !== referenceUnit.level) {
        showToast('⚠️ Solo puedes fusionar 3 unidades del MISMO tipo y nivel.');
        return;
      }
    }

    if (selectedUuids.length >= 3) {
      showToast('⚠️ Ya seleccionaste las 3 unidades requeridas para la fusión.');
      return;
    }

    setSelectedUuids((prev) => [...prev, unit.id]);
  };

  // Ejecutar fusión tripartita
  const handleMerge = async () => {
    if (selectedUuids.length !== 3 || isProcessing) return;

    setIsProcessing(true);
    try {
      const res = await mergeUnits(selectedUuids);
      const unitType = referenceUnit?.unit_id || 'U01';

      trackEvent('merge_unit', {
        unit_ids: selectedUuids,
        new_level: res.new_level,
      });

      setSuccessData({
        newUnitId: res.new_unit_id,
        newLevel: res.new_level,
        unitType,
      });

      setSelectedUuids([]);
      // Refrescar inventario
      await loadInventory();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al fusionar unidades.';
      showToast(`❌ ${msg}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Agrupamiento visual por unit_id y level
  const groupedUnits = useMemo(() => {
    const groups: Record<string, { unit_id: string; level: number; units: UnitInventoryItem[] }> = {};

    for (const unit of inventory) {
      const key = `${unit.unit_id}_L${unit.level}`;
      if (!groups[key]) {
        groups[key] = {
          unit_id: unit.unit_id,
          level: unit.level,
          units: [],
        };
      }
      groups[key].units.push(unit);
    }

    // Ordenar grupos alfabéticamente por unit_id y luego nivel ascendente
    return Object.values(groups).sort((a, b) => {
      if (a.unit_id !== b.unit_id) return a.unit_id.localeCompare(b.unit_id);
      return a.level - b.level;
    });
  }, [inventory]);

  // -------------------------------------------------------------------------
  // Render: Cargando
  // -------------------------------------------------------------------------
  if (loading && inventory.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[360px] text-stone-300 gap-3">
        <div className="w-10 h-10 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        <p className="text-sm font-semibold tracking-wide text-stone-400">Consultando Banco de Unidades…</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error
  // -------------------------------------------------------------------------
  if (error && inventory.length === 0) {
    return (
      <div className="w-full max-w-md mx-auto p-5 bg-rose-950/60 border border-rose-600/40 rounded-2xl text-rose-300 flex flex-col items-center text-center gap-3 mt-4">
        <div className="text-3xl">⚠️</div>
        <div className="font-bold text-base">Error al cargar el Banco</div>
        <p className="text-xs text-rose-400/90 break-words">{error}</p>
        <button
          type="button"
          onClick={loadInventory}
          className="mt-2 px-5 py-2 bg-stone-800 hover:bg-stone-700 text-stone-200 text-xs font-semibold rounded-lg transition"
        >
          🔄 Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 w-full max-w-md mx-auto select-none">
      {/* Toast de validación */}
      {toastMessage && (
        <div className="fixed top-4 z-50 px-4 py-2 bg-stone-900 border border-amber-500/80 text-amber-300 text-xs font-semibold rounded-xl shadow-2xl animate-fade-in">
          {toastMessage}
        </div>
      )}

      {/* Modal / Banner de Éxito al Fusionar */}
      {successData && (
        <div className="w-full p-4 bg-gradient-to-b from-amber-950/80 to-stone-900 border-2 border-amber-500 rounded-2xl text-center shadow-2xl animate-fade-in">
          <div className="text-4xl mb-1 animate-bounce">⭐</div>
          <h3 className="text-base font-black text-amber-300 uppercase tracking-wide">
            ¡Fusión Tripartita Exitosa!
          </h3>
          <div className="my-2 flex items-center justify-center gap-2 text-stone-100">
            <UnitAvatar
              unitId={successData.unitType}
              className="w-9 h-9 object-contain text-3xl select-none flex items-center justify-center"
            />
            <div className="text-left">
              <span className="font-bold text-sm block">
                {UNITS_CONFIG[successData.unitType]?.name || successData.unitType}
              </span>
              <span className="text-xs font-mono text-amber-400 font-bold">
                Nivel {successData.newLevel}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setSuccessData(null)}
            className="mt-1 px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-stone-950 text-xs font-bold rounded-lg transition"
          >
            Aceptar
          </button>
        </div>
      )}

      {/* Establo / Comprar */}
      <div className="w-full bg-stone-900/90 border border-stone-800 rounded-2xl p-4 shadow-xl flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-stone-100 flex items-center gap-2">
              <span>🐄</span> Establo / Comprar
            </h2>
            <p className="text-xs text-stone-400 mt-0.5">
              {SUMMON_COST} 🌾 por unidad · compra 3 iguales para fusionar
            </p>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-stone-500 block">Grano</span>
            <span className="text-sm font-bold text-amber-400 font-mono">🌾 {grain.toLocaleString()}</span>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2">
          {Object.values(UNITS_CONFIG).map((cfg) => {
            const canAfford = grain >= SUMMON_COST;
            const isBuying = buyingUnit === cfg.id;
            return (
              <button
                key={cfg.id}
                type="button"
                onClick={() => handleBuy(cfg.id)}
                disabled={!canAfford || Boolean(buyingUnit) || isProcessing}
                title={`${cfg.name} (${cfg.role})`}
                className={`p-2 rounded-xl flex flex-col items-center justify-center border transition-all ${
                  canAfford && !buyingUnit
                    ? 'bg-stone-800/80 hover:bg-stone-700/80 border-stone-700/60 hover:border-amber-500/60 active:scale-95'
                    : 'bg-stone-950/40 border-stone-800/40 opacity-50 cursor-not-allowed'
                } ${isBuying ? 'animate-pulse' : ''}`}
              >
                <UnitAvatar
                  unitId={cfg.id}
                  className="w-7 h-7 object-contain text-2xl select-none flex items-center justify-center"
                />
                <span className="text-[9px] text-stone-300 font-semibold truncate max-w-full mt-1">
                  {cfg.name.split(' ')[0]}
                </span>
                <span className="text-[9px] text-amber-400 font-mono">🌾 {SUMMON_COST}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Cabecera del Banco */}
      <div className="w-full bg-stone-900/90 border border-stone-800 rounded-2xl p-4 shadow-xl flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-stone-100 flex items-center gap-2">
            <span>🔄</span> Banco de Unidades
          </h2>
          <p className="text-xs text-stone-400 mt-0.5">
            Selecciona 3 unidades idénticas para fusionar
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-stone-500 block">Total en banco</span>
          <span className="text-sm font-bold text-amber-400 font-mono">
            {inventory.length} unidades
          </span>
        </div>
      </div>

      {/* Barra de Fusión Flotante / Superior */}
      <div className="w-full bg-stone-900/95 border border-stone-800 rounded-2xl p-3.5 shadow-xl flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            {[0, 1, 2].map((slotIdx) => {
              const selectedUuid = selectedUuids[slotIdx];
              const unit = inventory.find((u) => u.id === selectedUuid);
              const config = unit ? UNITS_CONFIG[unit.unit_id] : null;

              return (
                <div
                  key={`slot-${slotIdx}`}
                  className={`w-10 h-10 rounded-xl border flex items-center justify-center text-lg transition-all ${
                    unit && config
                      ? 'bg-amber-500/20 border-amber-500 text-amber-300 scale-105 shadow-inner'
                      : 'bg-stone-950/60 border-stone-800 border-dashed text-stone-600 text-xs font-mono'
                  }`}
                >
                  {unit && config ? (
                    <UnitAvatar
                      unitId={unit.unit_id}
                      className="w-8 h-8 object-contain text-lg select-none flex items-center justify-center"
                    />
                  ) : (
                    `${slotIdx + 1}`
                  )}
                </div>
              );
            })}
          </div>
          <div className="text-xs">
            <span className="font-bold text-stone-200 block">
              {selectedUuids.length}/3 seleccionadas
            </span>
            <span className="text-[10px] text-stone-400">
              {referenceUnit
                ? `${UNITS_CONFIG[referenceUnit.unit_id]?.name.split(' ')[0]} Nv ${referenceUnit.level}`
                : 'Elige 3 iguales'}
            </span>
          </div>
        </div>

        {/* Botón Fusionar */}
        <button
          type="button"
          onClick={handleMerge}
          disabled={selectedUuids.length !== 3 || isProcessing}
          className={`py-3 px-4 rounded-xl font-black text-xs tracking-wide transition-all shadow-md ${
            selectedUuids.length === 3 && !isProcessing
              ? 'bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-stone-950 active:scale-95 shadow-amber-900/40 animate-pulse'
              : 'bg-stone-800 text-stone-600 cursor-not-allowed border border-stone-700/40'
          }`}
        >
          {isProcessing ? 'Fusionando…' : '⚡ Fusionar (3)'}
        </button>
      </div>

      {/* Lista Agrupada de Unidades */}
      <div className="w-full flex flex-col gap-3">
        {groupedUnits.length === 0 ? (
          <div className="w-full p-8 text-center text-stone-400 text-xs bg-stone-900/40 border border-stone-800/40 rounded-2xl flex flex-col items-center gap-3">
            <p className="text-stone-500">No tienes unidades en tu inventario.</p>
            {onNavigate && (
              <button
                type="button"
                onClick={() => onNavigate('home')}
                className="px-4 py-2 bg-stone-800 hover:bg-stone-700 text-amber-300 font-semibold rounded-xl text-xs transition"
              >
                🏠 Ir a la Granja
              </button>
            )}
          </div>
        ) : (
          groupedUnits.map((group) => {
            const config = UNITS_CONFIG[group.unit_id];
            const canFuseGroup = group.units.length >= 3 && group.level < 3;

            return (
              <div
                key={`${group.unit_id}-${group.level}`}
                className="w-full bg-stone-900/80 border border-stone-800 rounded-2xl p-3 flex flex-col gap-2.5 shadow-sm"
              >
                {/* Cabecera del Grupo */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <UnitAvatar
                      unitId={group.unit_id}
                      className="w-7 h-7 object-contain text-2xl select-none flex items-center justify-center"
                    />
                    <div>
                      <span className="font-bold text-xs text-stone-200">
                        {config?.name || group.unit_id}
                      </span>
                      <span className="text-[10px] text-amber-400 font-mono ml-2">
                        Nivel {group.level}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {canFuseGroup && (
                      <span className="text-[9px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                        ¡Fusionable!
                      </span>
                    )}
                    <span className="text-[10px] text-stone-400 font-mono">
                      x{group.units.length}
                    </span>
                  </div>
                </div>

                {/* Grid de Unidades del Grupo */}
                <div className="grid grid-cols-4 gap-2">
                  {group.units.map((unit) => {
                    const isSelected = selectedUuids.includes(unit.id);
                    const isInFormation = unit.slot !== null;

                    // Deshabilitado visualmente si hay referencia incompatible
                    const isMismatched =
                      referenceUnit &&
                      (referenceUnit.unit_id !== unit.unit_id || referenceUnit.level !== unit.level);

                    return (
                      <button
                        key={unit.id}
                        type="button"
                        onClick={() => toggleSelectUnit(unit)}
                        disabled={isProcessing || Boolean(isMismatched)}
                        className={`relative p-2 rounded-xl flex flex-col items-center justify-center border transition-all ${
                          isSelected
                            ? 'bg-amber-500/25 border-amber-400 ring-2 ring-amber-400 scale-105 shadow-md'
                            : isMismatched
                            ? 'bg-stone-950/40 border-stone-800/40 opacity-40 cursor-not-allowed'
                            : 'bg-stone-800/80 hover:bg-stone-800 border-stone-700/60 active:scale-95'
                        }`}
                      >
                        {/* Indicador de posición en formación */}
                        {isInFormation && (
                          <span
                            title="Equipada en el tablero táctico"
                            className="absolute top-1 left-1 text-[8px] bg-stone-900/90 text-amber-300 px-1 rounded border border-amber-500/30 font-mono"
                          >
                            P{unit.slot}
                          </span>
                        )}

                        {/* Indicador de selección */}
                        {isSelected && (
                          <span className="absolute top-1 right-1 w-4 h-4 bg-amber-400 text-stone-950 rounded-full text-[10px] font-black flex items-center justify-center shadow">
                            ✓
                          </span>
                        )}

                        <UnitAvatar
                          unitId={unit.unit_id}
                          className="w-7 h-7 object-contain text-2xl mt-1 select-none flex items-center justify-center"
                        />
                        <span className="text-[9px] text-stone-400 font-mono mt-1">
                          Nv {unit.level}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default MergePage;
