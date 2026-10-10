import { type ShipStats } from './types';
import { BASE_STATS } from './arena';

/** Permanent progress between missions: what the pilot has learned and bought. */
export interface Upgrades {
  motor: number;
  tank: number;
  hull: number;
  turn: number;
  predictor: number;
  kits: number;
}

export interface MissionRecord {
  /** Stages cleared in that mission (5 = won). */
  stages: number;
  /** Total seconds spent racing in cleared stages. */
  time: number;
  data: number;
  won: boolean;
  deaths: number;
}

export interface Meta {
  version: 1;
  data: number;
  upgrades: Upgrades;
  /** Highest stage cleared at least once (0..5). */
  cleared: number;
  best: (number | null)[];
  attempts: number;
  deaths: number;
  won: boolean;
  records: MissionRecord[];
}

export interface UpgradeDef {
  id: keyof Upgrades;
  name: string;
  desc: string;
  max: number;
  cost: (level: number) => number;
}

export const UPGRADES: UpgradeDef[] = [
  { id: 'motor', name: 'Motor', desc: '+10 % de empuje por nivel', max: 4, cost: (l) => 120 + l * 110 },
  { id: 'tank', name: 'Tanque', desc: '+20 de combustible por nivel', max: 4, cost: (l) => 90 + l * 80 },
  { id: 'hull', name: 'Casco', desc: '+20 de casco por nivel', max: 4, cost: (l) => 100 + l * 90 },
  { id: 'turn', name: 'Giro', desc: '+12 % de velocidad de giro por nivel', max: 3, cost: (l) => 80 + l * 80 },
  { id: 'predictor', name: 'Predictor', desc: 'Muestra tu trayectoria: 1,5 s, 3 s, 5 s', max: 3, cost: (l) => 150 + l * 150 },
  { id: 'kits', name: 'Cápsulas', desc: '+1 cápsula de reparación por misión', max: 3, cost: (l) => 140 + l * 140 },
];

export const MISSION_LIVES = 3;
export const BASE_KITS = 2;

export function newMeta(): Meta {
  return {
    version: 1,
    data: 0,
    upgrades: { motor: 0, tank: 0, hull: 0, turn: 0, predictor: 0, kits: 0 },
    cleared: 0,
    best: [null, null, null, null, null],
    attempts: 0,
    deaths: 0,
    won: false,
    records: [],
  };
}

export function shipStats(u: Upgrades): ShipStats {
  return {
    thrust: BASE_STATS.thrust * (1 + 0.1 * u.motor),
    turnRate: BASE_STATS.turnRate * (1 + 0.12 * u.turn),
    fuelMax: BASE_STATS.fuelMax + 20 * u.tank,
    hullMax: BASE_STATS.hullMax + 20 * u.hull,
  };
}

export const predictorSeconds = (u: Upgrades): number => [0, 1.5, 3, 5][u.predictor] ?? 0;
export const kitCount = (u: Upgrades): number => BASE_KITS + u.kits;

export function buyUpgrade(meta: Meta, id: keyof Upgrades): boolean {
  const def = UPGRADES.find((d) => d.id === id);
  if (!def) return false;
  const level = meta.upgrades[id];
  if (level >= def.max) return false;
  const cost = def.cost(level);
  if (meta.data < cost) return false;
  meta.data -= cost;
  meta.upgrades[id] = level + 1;
  return true;
}

const KEY = 'orbital.arcade.v1';

export function loadMeta(): Meta {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return newMeta();
    const m = JSON.parse(raw) as Meta;
    if (m.version !== 1) return newMeta();
    return { ...newMeta(), ...m, upgrades: { ...newMeta().upgrades, ...m.upgrades } };
  } catch {
    return newMeta();
  }
}

export function saveMeta(meta: Meta): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(meta));
  } catch {
    /* storage unavailable: progress lasts for this session only */
  }
}

export function addRecord(meta: Meta, r: MissionRecord): void {
  meta.records.push(r);
  meta.records.sort((a, b) => Number(b.won) - Number(a.won) || b.stages - a.stages || a.time - b.time);
  meta.records.length = Math.min(meta.records.length, 10);
}
