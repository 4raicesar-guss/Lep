/**
 * Tipos de datos, interfaces y constantes maestras del juego (Core Loop).
 */

export type View = 'home' | 'merge' | 'formation' | 'battle';

// ---------------------------------------------------------------------------
// Configuración de Unidades del MVP
// ---------------------------------------------------------------------------

export interface UnitConfig {
  id: string;
  name: string;
  sprite: string;
  image: string;
  role: 'Tanque' | 'Daño' | 'Soporte' | 'Control';
  baseHp: number;
}

// NOTA: el backend manda. Estos datos espejan backend/app/engine/data.py
// (UNIT_TEMPLATES / SUMMON_COST) y se mantienen sincronizados a mano por ahora.
export const UNITS_CONFIG: Record<string, UnitConfig> = {
  U01: { id: 'U01', name: 'Cerdo Blindado', sprite: '🐷', image: '/assets/units/u01_cerdo.png', role: 'Tanque', baseHp: 480 },
  U02: { id: 'U02', name: 'Toro Bravo', sprite: '🐂', image: '/assets/units/u02_toro.png', role: 'Tanque', baseHp: 420 },
  U03: { id: 'U03', name: 'Gallo Asesino', sprite: '🐓', image: '/assets/units/u03_gallo.png', role: 'Daño', baseHp: 150 },
  U04: { id: 'U04', name: 'Cabra Francotiradora', sprite: '🐐', image: '/assets/units/u04_cabra.png', role: 'Daño', baseHp: 130 },
  U05: { id: 'U05', name: 'Pato Bombardero', sprite: '🦆', image: '/assets/units/u05_pato.png', role: 'Daño', baseHp: 160 },
  U06: { id: 'U06', name: 'Oveja Sanadora', sprite: '🐑', image: '/assets/units/u06_oveja.png', role: 'Soporte', baseHp: 220 },
  U07: { id: 'U07', name: 'Perro Pastor', sprite: '🐕', image: '/assets/units/u07_perro.png', role: 'Soporte', baseHp: 260 },
  U08: { id: 'U08', name: 'Espantapájaros', sprite: '🌾', image: '/assets/units/u08_espantapajaros.png', role: 'Control', baseHp: 310 },
};

/** Coste en grano de comprar una unidad nivel 1 (espejo de SUMMON_COST del backend). */
export const SUMMON_COST = 100;

/**
 * Fila del tablero 3x3 por rol para "Auto-formar":
 * Tanques en fila 0 (slots 0-2), Soportes/Control en fila 1 (3-5), Daño en fila 2 (6-8).
 */
export const ROLE_ROW: Record<UnitConfig['role'], number> = {
  Tanque: 0,
  Soporte: 1,
  Control: 1,
  'Daño': 2,
};

// ---------------------------------------------------------------------------
// Configuración de Edificios de la Granja
// ---------------------------------------------------------------------------

export type BuildingId = 'silo' | 'galpon' | 'boyero';

export interface BuildingConfig {
  id: BuildingId;
  name: string;
  emoji: string;
  description: string;
  bonusText: (level: number) => string;
}

export const BUILDINGS_CONFIG: Record<BuildingId, BuildingConfig> = {
  silo: {
    id: 'silo',
    name: 'Silo',
    emoji: '🌾',
    description: 'Almacenamiento offline de grano.',
    bonusText: (level) => `Cap: ${Math.min(4 + 2 * level, 12)}h offline`,
  },
  galpon: {
    id: 'galpon',
    name: 'Galpón',
    emoji: '🏚️',
    description: 'Generación pasiva de recursos.',
    bonusText: (level) => `Producción: ${Math.round(120 * (1 + 0.15 * level))} grano/h`,
  },
  boyero: {
    id: 'boyero',
    name: 'Boyero',
    emoji: '⚡',
    description: 'Cercado perimetral y seguridad.',
    bonusText: (level) => `Defensa: Nivel ${level}`,
  },
};

/**
 * Calcula el coste en grano para subir de nivel un edificio:
 * 100 * (1.5 ^ current_level)
 */
export function calculateUpgradeCost(currentLevel: number): number {
  return Math.round(100 * Math.pow(1.5, currentLevel));
}

// ---------------------------------------------------------------------------
// Modelos de la API (Backend FastAPI)
// ---------------------------------------------------------------------------

export interface PlayerInfo {
  telegram_id: number;
  username?: string | null;
  first_name: string;
}

export interface ResourcesInfo {
  grain: number;
  last_collected_at?: string | null;
}

export interface BuildingsInfo {
  silo_level: number;
  galpon_level: number;
  boyero_level: number;
}

export interface UnitInfo {
  id: string; // UUID
  unit_id: string; // Ej: 'U01'
  level: number;
  slot: number | null; // 0 a 8 o null si está en el banco
  acquired_at?: string | null;
}

export interface FormationInfo {
  slots: Record<string, string | null>; // "0".."8" -> UUID o null
}

export interface PlayerStateResponse {
  player: PlayerInfo;
  resources: ResourcesInfo;
  grain?: number | null;
  buildings: BuildingsInfo;
  units: UnitInfo[];
  formation: FormationInfo;
}

export interface CollectResourcesResponse {
  grain_collected: number;
  new_total_grain: number;
  hours_capped: boolean;
}

export interface UpgradeBuildingResponse {
  success: boolean;
  building_id: string;
  new_level: number;
  remaining_grain: number;
  cost: number;
}

export interface UnitInventoryItem {
  id: string; // UUID
  unit_id: string;
  level: number;
  slot: number | null;
}

export interface MergeUnitsResponse {
  success: boolean;
  new_unit_id: string;
  new_level: number;
}

export interface SaveFormationResponse {
  success: boolean;
  slots: Record<string, string | null>;
}

export interface UnitSlot {
  unit_id: string;
  level: number;
  position: number;
}

export interface SimulateRequest {
  player_formation: UnitSlot[];
  wave_number: number;
}

export interface SummonUnitResponse {
  success: boolean;
  unit: UnitInventoryItem;
  cost: number;
  remaining_grain: number;
}
