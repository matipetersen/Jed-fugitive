import { BODIES, bodyPos as bodyPosAt, indexOf } from '../sim/bodies';
import { orbitElements } from '../sim/orbit';
import { type World, refState } from '../sim/physics';
import { mulberry32 } from '../sim/rng';
import { AU, YEAR, yearOf } from '../sim/units';
import { type Bloc, type Campaign, MILESTONE_COUNT, type NewsItem } from './campaign';

export interface MilestoneDef {
  id: number;
  name: string;
  desc: string;
  points: number;
  /** Rival's target year on normal difficulty. */
  rivalYear: number;
}

export const MILESTONES: MilestoneDef[] = [
  { id: 1, name: 'Vuelo suborbital', desc: 'Superá los 150 u de altitud sobre la Tierra.', points: 40, rivalYear: 1958.0 },
  { id: 2, name: 'Órbita terrestre', desc: 'Una órbita estable con periapsis sobre los 160 u.', points: 60, rivalYear: 1958.8 },
  { id: 3, name: 'Sobrevuelo lunar', desc: 'Pasá a menos de 3000 u de la Luna.', points: 80, rivalYear: 1960.5 },
  { id: 4, name: 'Aterrizaje lunar', desc: 'Aterrizá en la Luna y plantá la bandera.', points: 150, rivalYear: 1963.8 },
  { id: 5, name: 'Base lunar', desc: 'Instalá una base en la Luna.', points: 180, rivalYear: 1968.0 },
  { id: 6, name: 'Sobrevuelo planetario', desc: 'Pasá cerca de Marte o de Venus.', points: 200, rivalYear: 1971.5 },
  { id: 7, name: 'Marte: bandera y base', desc: 'Plantá la bandera e instalá una base en Marte.', points: 350, rivalYear: 1977.0 },
  { id: 8, name: 'Cinturón de asteroides', desc: 'Cruzá más allá de 3,3 UA del Sol.', points: 250, rivalYear: 1979.5 },
  { id: 9, name: 'Júpiter', desc: 'Acercate a 4 radios de Júpiter o recogé gas de su atmósfera.', points: 300, rivalYear: 1981.0 },
  { id: 10, name: 'Plutón', desc: 'Aterrizá en Plutón y plantá la bandera. El primero gana.', points: 1500, rivalYear: 1991.0 },
];

export const rivalName = (bloc: Bloc): string => (bloc === 'usa' ? 'URSS' : 'EE.UU.');
export const playerName = (bloc: Bloc): string => (bloc === 'usa' ? 'EE.UU.' : 'URSS');

const DIFFICULTY_PACE = [1.35, 1.0, 0.85];

/** The rival's calendar: the same ladder with seeded noise, scaled by difficulty. */
export function makeRivalYears(seed: number, difficulty: 0 | 1 | 2): number[] {
  const rnd = mulberry32(seed ^ 0x51ed);
  const pace = DIFFICULTY_PACE[difficulty];
  let prev = 1957;
  return MILESTONES.map((m, i) => {
    const base = 1957 + (m.rivalYear - 1957) * pace;
    const noise = (rnd() - 0.5) * (i === 9 ? 1.6 : 1.0);
    const y = Math.max(prev + 0.1, base + noise);
    prev = y;
    return y;
  });
}

export function doneCount(c: Campaign): number {
  return c.milestones.filter((m) => m.done).length;
}

export function yearBudget(c: Campaign): number {
  return 70 + 12 * doneCount(c) + (c.difficulty === 0 ? 15 : c.difficulty === 2 ? -10 : 0);
}

export const LAUNCH_COST = 15;

export function addNews(c: Campaign, t: number, text: string, kind: NewsItem['kind'] = 'info'): void {
  c.news.unshift({ t, text, kind });
  if (c.news.length > 40) c.news.length = 40;
}

export interface MilestoneEvent {
  id: number;
  first: boolean;
  points: number;
}

function complete(c: Campaign, i: number, world: World | null, time: number): MilestoneEvent {
  const m = c.milestones[i];
  const def = MILESTONES[i];
  const first = yearOf(time) < c.rivalYears[i];
  const fuelBonus = world ? Math.round((world.ship.fuel / world.stats.fuelCap) * 30) : 0;
  m.done = true;
  m.time = time;
  m.first = first;
  m.points = Math.round(def.points * (first ? 2 : 0.5)) + fuelBonus;
  addNews(
    c,
    time,
    first ? `¡HITO! ${def.name}: ${playerName(c.bloc)} llega primero (+${m.points})` : `${def.name}: logrado, pero ${rivalName(c.bloc)} ya lo había hecho (+${m.points})`,
    first ? 'good' : 'info',
  );
  return { id: i + 1, first, points: m.points };
}

/** Checks every pending milestone against the current flight. Returns the ones just completed. */
export function checkMilestones(c: Campaign, world: World): MilestoneEvent[] {
  if (c.sandbox || c.status !== 'playing') return [];
  const out: MilestoneEvent[] = [];
  const s = world.ship;
  const t = world.time;
  const flying = s.status === 'flying';
  const earth = indexOf('earth');
  const moon = indexOf('moon');
  const mars = indexOf('mars');
  const venus = indexOf('venus');
  const jup = indexOf('jupiter');
  const rs = refState(world);
  const dist = (i: number): number => {
    const b = BODIES[i];
    const p = bodyOffset(world, i);
    return Math.hypot(p.x, p.y) - 0 * b.radius;
  };
  const done = (i: number): boolean => c.milestones[i].done;
  const flagged = (i: number): boolean => c.flags.some((f) => f.body === i);
  const based = (i: number): boolean => c.bases.some((b) => b.body === i);
  const try_ = (i: number, ok: boolean): void => {
    if (!done(i) && ok) out.push(complete(c, i, world, t));
  };

  if (flying) {
    try_(0, rs.index === earth && rs.alt >= 150);
    if (!done(1) && rs.index === earth) {
      const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, BODIES[earth].gm);
      try_(1, el.bound && el.periapsis - BODIES[earth].radius >= 160);
    }
    try_(2, dist(moon) < 3000);
    try_(5, dist(mars) < BODIES[mars].radius * 12 || dist(venus) < BODIES[venus].radius * 12);
    try_(7, Math.hypot(s.x, s.y) >= 3.3 * AU);
    try_(8, dist(jup) < BODIES[jup].radius * 4);
  }
  try_(3, flagged(moon));
  try_(4, based(moon));
  try_(6, flagged(mars) && based(mars));
  try_(9, flagged(indexOf('pluto')));
  return out;
}

function bodyOffset(world: World, i: number): { x: number; y: number } {
  // Distance vector from the ship to body i at the world's time.
  const s = world.ship;
  const p = bodyPosAt(i, world.time);
  return { x: s.x - p.x, y: s.y - p.y };
}


export interface CalendarResult {
  news: NewsItem[];
  lost: boolean;
}

/** Advances the campaign calendar to `time`: yearly budgets and the rival's milestones. */
export function tickCalendar(c: Campaign, time: number): CalendarResult {
  c.time = time;
  const news: NewsItem[] = [];
  const year = yearOf(time);
  while (Math.floor(year) > c.lastBudgetYear) {
    c.lastBudgetYear++;
    if (c.sandbox) continue;
    const b = yearBudget(c);
    c.funds += b;
    news.push({ t: time, text: `Presupuesto ${c.lastBudgetYear}: +${b} fondos`, kind: 'info' });
  }
  while (!c.sandbox && c.rivalDone < MILESTONE_COUNT && year >= c.rivalYears[c.rivalDone]) {
    const def = MILESTONES[c.rivalDone];
    const mine = c.milestones[c.rivalDone];
    const text = mine.done
      ? `${rivalName(c.bloc)} completa «${def.name}»`
      : `${rivalName(c.bloc)} completa «${def.name}» antes que vos`;
    news.push({ t: time, text, kind: mine.done ? 'info' : 'rival' });
    c.rivalDone++;
  }
  for (const n of news) addNews(c, n.t, n.text, n.kind);
  let lost = false;
  if (!c.sandbox && c.status === 'playing' && !c.milestones[MILESTONE_COUNT - 1].done && year >= c.rivalYears[MILESTONE_COUNT - 1]) {
    c.status = 'lost';
    lost = true;
    addNews(c, time, `${rivalName(c.bloc)} aterrizó en Plutón primero. La carrera terminó.`, 'bad');
  }
  return { news, lost };
}

export function registerVictory(c: Campaign): void {
  if (c.status === 'playing' && c.milestones[MILESTONE_COUNT - 1].done) {
    c.status = c.milestones[MILESTONE_COUNT - 1].first ? 'won' : 'lost';
  }
}

export interface ScoreRow {
  label: string;
  value: number;
}

export function scoreBreakdown(c: Campaign): ScoreRow[] {
  const rows: ScoreRow[] = [];
  const ms = c.milestones.reduce((a, m) => a + m.points, 0);
  rows.push({ label: 'Hitos', value: ms });
  rows.push({ label: `Banderas (${c.flags.length})`, value: c.flags.length * 50 });
  rows.push({ label: `Bases (${c.bases.length})`, value: c.bases.length * 30 });
  rows.push({ label: `Eventos resueltos (${c.eventsHandled})`, value: c.eventsHandled * 10 });
  rows.push({ label: `Naves perdidas (${c.shipsLost})`, value: -c.shipsLost * 40 });
  const last = c.milestones[MILESTONE_COUNT - 1];
  if (c.status === 'won' && last.done) {
    const early = Math.max(0, c.rivalYears[MILESTONE_COUNT - 1] - yearOf(last.time));
    rows.push({ label: 'Victoria', value: 1000 + Math.round(early * 60) });
  }
  return rows;
}

export const totalScore = (c: Campaign): number => Math.max(0, scoreBreakdown(c).reduce((a, r) => a + r.value, 0));

export const YEAR_SECONDS = YEAR;
