/**
 * Cliente API y utilidades para comunicación con el backend FastAPI (Día 11).
 */

import { initData } from '@telegram-apps/sdk';
import type { ReplayData } from '../components/CombatViewer';
import type {
  CollectResourcesResponse,
  MergeUnitsResponse,
  PlayerStateResponse,
  SaveFormationResponse,
  SummonUnitResponse,
  UnitInventoryItem,
  UnitSlot,
  UpgradeBuildingResponse,
} from './game';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Obtiene el initData raw de Telegram.
 * En orden de prioridad:
 * 1. initData del SDK de Telegram (@telegram-apps/sdk)
 * 2. Variable de entorno VITE_TELEGRAM_INIT_DATA
 * 3. localStorage 'mock_init_data' (ideal para pruebas en navegador estándar)
 */
export function getTelegramInitData(): string {
  try {
    initData.restore();
    const raw =
      typeof initData.raw === 'function'
        ? initData.raw()
        : (initData.raw as unknown as string | undefined);
    if (raw && raw.trim().length > 0) {
      return raw;
    }
  } catch {
    // Entorno fuera de Telegram o SDK no inicializado
  }

  // Fallback para pruebas locales en navegador
  const envMock = import.meta.env.VITE_TELEGRAM_INIT_DATA;
  if (envMock && typeof envMock === 'string' && envMock.trim().length > 0) {
    return envMock;
  }

  try {
    const localMock = localStorage.getItem('mock_init_data');
    if (localMock && localMock.trim().length > 0) {
      return localMock;
    }
  } catch {
    // Acceso a localStorage restringido
  }

  return '';
}

/**
 * Helper interno para realizar peticiones HTTP con autenticación X-Telegram-Init-Data
 * y extracción de errores formateados de FastAPI (detail).
 */
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const rawInitData = getTelegramInitData();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (rawInitData) {
    headers['X-Telegram-Init-Data'] = rawInitData;
  }

  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Error de red. No se pudo contactar al servidor.';
    throw new Error(`Fallo de conexión: ${message}`);
  }

  if (!response.ok) {
    let errorDetail = `Error ${response.status}: ${response.statusText}`;
    try {
      const data = await response.json();
      if (data && data.detail) {
        if (typeof data.detail === 'string') {
          errorDetail = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorDetail = data.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorDetail = JSON.stringify(data.detail);
        }
      }
    } catch {
      // La respuesta no era JSON
    }
    throw new Error(errorDetail);
  }

  return (await response.json()) as T;
}

// ---------------------------------------------------------------------------
// Endpoints Tipados del Core Loop
// ---------------------------------------------------------------------------

/**
 * GET /api/player/state
 * Obtiene el estado global del jugador (recursos, edificios, unidades y formación).
 */
export async function fetchPlayerState(): Promise<PlayerStateResponse> {
  return apiRequest<PlayerStateResponse>('/api/player/state', {
    method: 'GET',
  });
}

/**
 * POST /api/resources/collect
 * Recolecta el grano acumulado offline según el tiempo transcurrido y nivel de Silo/Galpón.
 */
export async function collectResources(): Promise<CollectResourcesResponse> {
  return apiRequest<CollectResourcesResponse>('/api/resources/collect', {
    method: 'POST',
  });
}

/**
 * POST /api/buildings/upgrade
 * Sube de nivel un edificio ('silo', 'galpon' o 'boyero') consumiendo grano.
 */
export async function upgradeBuilding(buildingId: string): Promise<UpgradeBuildingResponse> {
  return apiRequest<UpgradeBuildingResponse>('/api/buildings/upgrade', {
    method: 'POST',
    body: JSON.stringify({ building_id: buildingId }),
  });
}

/**
 * GET /api/units/inventory
 * Obtiene la lista completa de unidades del usuario con su nivel y slot táctico (o null).
 */
export async function fetchUnitsInventory(): Promise<UnitInventoryItem[]> {
  return apiRequest<UnitInventoryItem[]>('/api/units/inventory', {
    method: 'GET',
  });
}

/**
 * POST /api/units/merge
 * Fusiona exactamente 3 unidades idénticas (mismo tipo y nivel < 3) en una de nivel superior.
 */
export async function mergeUnits(unitIds: string[]): Promise<MergeUnitsResponse> {
  return apiRequest<MergeUnitsResponse>('/api/units/merge', {
    method: 'POST',
    body: JSON.stringify({ unit_ids: unitIds }),
  });
}

/**
 * POST /api/formation/save
 * Guarda la formación táctica en el grid 3x3 (claves "0" a "8" a UUID o null).
 */
export async function saveFormation(
  slots: Record<string, string | null>,
): Promise<SaveFormationResponse> {
  return apiRequest<SaveFormationResponse>('/api/formation/save', {
    method: 'POST',
    body: JSON.stringify({ slots }),
  });
}

/**
 * POST /api/combat/simulate
 * Simula una batalla contra la oleada especificada con la formación real provista.
 */
export async function simulateCombat(
  playerFormation: UnitSlot[],
  waveNumber: number = 1,
): Promise<ReplayData> {
  return apiRequest<ReplayData>('/api/combat/simulate', {
    method: 'POST',
    body: JSON.stringify({
      player_formation: playerFormation,
      wave_number: waveNumber,
    }),
  });
}

/**
 * POST /api/units/summon
 * Compra directa de una unidad nivel 1 por grano.
 */
export async function summonUnit(unitId: string): Promise<SummonUnitResponse> {
  return apiRequest<SummonUnitResponse>('/api/units/summon', {
    method: 'POST',
    body: JSON.stringify({ unit_id: unitId }),
  });
}
