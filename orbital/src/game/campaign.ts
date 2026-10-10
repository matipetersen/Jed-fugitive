import { type EngineId, TECHS } from '../sim/tech';
import { type World } from '../sim/physics';

export type Bloc = 'usa' | 'urss';

export interface MilestoneRec {
  done: boolean;
  time: number;
  /** True if the player beat the rival to it. */
  first: boolean;
  points: number;
}

export interface BaseData {
  body: number;
  theta: number;
  name: string;
  stock: number;
  built: number;
}

export interface FlagData {
  body: number;
  theta: number;
  time: number;
}

export interface NewsItem {
  t: number;
  text: string;
  kind: 'rival' | 'event' | 'info' | 'bad' | 'good';
}

export interface Campaign {
  version: 1;
  seed: number;
  bloc: Bloc;
  difficulty: 0 | 1 | 2;
  sandbox: boolean;
  funds: number;
  score: number;
  techs: string[];
  engine: EngineId;
  milestones: MilestoneRec[];
  bases: BaseData[];
  flags: FlagData[];
  shipsLost: number;
  launches: number;
  eventsHandled: number;
  /** Calendar year at which the rival completes each milestone. */
  rivalYears: number[];
  /** How many of the rival's milestones have already happened. */
  rivalDone: number;
  /** Campaign clock in game seconds; the flight world carries the same value while a ship flies. */
  time: number;
  lastBudgetYear: number;
  news: NewsItem[];
  status: 'playing' | 'won' | 'lost';
  /** Last event bin processed, so events are not rolled twice. */
  eventBin: number;
  /** Fuel loaded at launch as a fraction of tank capacity. */
  fuelLoad: number;
}

export const MILESTONE_COUNT = 10;

export function newCampaign(opts: { seed?: number; bloc?: Bloc; difficulty?: 0 | 1 | 2; sandbox?: boolean }): Campaign {
  const sandbox = !!opts.sandbox;
  return {
    version: 1,
    seed: opts.seed ?? Math.floor(Math.random() * 2 ** 31),
    bloc: opts.bloc ?? 'usa',
    difficulty: opts.difficulty ?? 1,
    sandbox,
    funds: sandbox ? 9999 : 80,
    score: 0,
    techs: sandbox ? TECHS.map((t) => t.id) : [],
    engine: 'chem',
    milestones: Array.from({ length: MILESTONE_COUNT }, () => ({ done: false, time: 0, first: false, points: 0 })),
    bases: [],
    flags: [],
    shipsLost: 0,
    launches: 0,
    eventsHandled: 0,
    rivalYears: [],
    rivalDone: 0,
    time: 0,
    lastBudgetYear: 1957,
    news: [],
    status: 'playing',
    eventBin: 0,
    fuelLoad: 1,
  };
}

export interface SaveBlob {
  campaign: Campaign;
  world: World | null;
}

const KEY = 'orbital.save.v1';

export function saveGame(campaign: Campaign, world: World | null): void {
  try {
    localStorage.setItem(KEY, JSON.stringify({ campaign, world } satisfies SaveBlob));
  } catch {
    /* storage unavailable: the game still works without saving */
  }
}

export function loadGame(): SaveBlob | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const blob = JSON.parse(raw) as SaveBlob;
    if (!blob.campaign || blob.campaign.version !== 1) return null;
    // JSON turns Infinity into null; restore it so a loaded ship does not fail instantly.
    if (blob.world && blob.world.ship.failAt == null) blob.world.ship.failAt = Infinity;
    return blob;
  } catch {
    return null;
  }
}

export function clearSave(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
