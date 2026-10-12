import { type ShipStats } from './types';
import { BASE_STATS } from './arena';

/** What the ship has bought during the current run. Technology resets at the start of every mission. */
export interface Upgrades {
  motor: number;
  tank: number;
  hull: number;
  turn: number;
  predictor: number;
  kits: number;
  shield: number;
  boost: number;
}

export interface MissionRecord {
  /** Stages cleared in that mission (5 = won). */
  stages: number;
  /** Total seconds spent racing in cleared stages. */
  time: number;
  data: number;
  won: boolean;
  deaths: number;
  race?: string;
}

export interface RaceProgress {
  /** Highest stage count won at least once. */
  cleared: number;
  /** Furthest stage played in a real run (1-based), for unlocking practice. */
  reached: number;
  best: (number | null)[];
  won: boolean;
}

export interface Meta {
  version: 1;
  data: number;
  upgrades: Upgrades;
  races: Record<string, RaceProgress>;
  attempts: number;
  deaths: number;
  records: MissionRecord[];
}

/** Progress in one race, created on first use. */
export function raceProgress(meta: Meta, id: string, stages = 5): RaceProgress {
  let r = meta.races[id];
  if (!r) r = meta.races[id] = { cleared: 0, reached: 0, best: [], won: false };
  while (r.best.length < stages) r.best.push(null);
  return r;
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
  { id: 'shield', name: 'Escudo térmico', desc: '-30 % de daño por calor, radiación y discos de acreción por nivel', max: 3, cost: (l) => 110 + l * 90 },
  { id: 'boost', name: 'Postquemador', desc: 'Botón IMPULSO: +70 % de empuje unos segundos; cada nivel dura más y recarga antes', max: 3, cost: (l) => 130 + l * 100 },
];

/** Lives per stage. */
export const MISSION_LIVES = 3;
export const zeroUpgrades = (): Upgrades => ({ motor: 0, tank: 0, hull: 0, turn: 0, predictor: 0, kits: 0, shield: 0, boost: 0 });
/** Different upgrades a ship can carry at once: a choice, not a shopping list. */
export const UPGRADE_SLOTS = 3;
export const usedSlots = (u: Upgrades): number => Object.values(u).filter((v) => v > 0).length;
export const BASE_KITS = 2;

export function newMeta(): Meta {
  return {
    version: 1,
    data: 0,
    upgrades: zeroUpgrades(),
    races: {},
    attempts: 0,
    deaths: 0,
    records: [],
  };
}

export function shipStats(u: Upgrades): ShipStats {
  return {
    thrust: BASE_STATS.thrust * (1 + 0.1 * u.motor),
    turnRate: BASE_STATS.turnRate * (1 + 0.12 * u.turn),
    fuelMax: BASE_STATS.fuelMax + 20 * u.tank,
    hullMax: BASE_STATS.hullMax + 20 * u.hull,
    shield: Math.min(0.9, 0.3 * u.shield),
    boost: u.boost,
  };
}

export const predictorSeconds = (u: Upgrades): number => [0, 1.5, 3, 5][u.predictor] ?? 0;
export const kitCount = (u: Upgrades): number => BASE_KITS + u.kits;

export function buyUpgrade(meta: Meta, id: keyof Upgrades): boolean {
  const def = UPGRADES.find((d) => d.id === id);
  if (!def) return false;
  const level = meta.upgrades[id];
  if (level >= def.max) return false;
  if (level === 0 && usedSlots(meta.upgrades) >= UPGRADE_SLOTS) return false;
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
    const m = JSON.parse(raw) as Meta & { cleared?: number; reached?: number; best?: (number | null)[]; won?: boolean };
    if (m.version !== 1) return newMeta();
    const meta: Meta = { ...newMeta(), ...m, upgrades: { ...newMeta().upgrades, ...m.upgrades }, races: m.races ?? {} };
    // Saves from before there were several races: that progress belongs to the first one.
    if (!m.races && (m.cleared || m.best)) meta.races.guerra = { cleared: m.cleared ?? 0, reached: m.reached ?? 0, best: m.best ?? [], won: !!m.won };
    return meta;
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
