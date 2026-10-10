import { BODIES, BODY_COUNT, bodyPositions } from '../sim/bodies';
import { type Asteroid, type World, destroyShip } from '../sim/physics';
import { hash01 } from '../sim/rng';
import { AU, DAY, TAU, YEAR } from '../sim/units';
import { type Campaign } from './campaign';
import { addNews, rivalName } from './rules';

export interface EventResult {
  text: string;
  kind: 'info' | 'bad' | 'good';
  /** Drop time warp to x1 and sound an alarm. */
  interrupt: boolean;
}

const PX = new Float64Array(BODY_COUNT);
const PY = new Float64Array(BODY_COUNT);

/** Event kinds in a fixed order so their seeded rolls are independent. */
const KINDS = ['asteroid', 'micro', 'leak', 'flare', 'cut', 'windfall', 'espionage', 'sabotage'] as const;
type Kind = (typeof KINDS)[number];

/** Events per game year. */
const RATE: Record<Kind, number> = {
  asteroid: 0.5,
  micro: 1.5,
  leak: 0.8,
  flare: 1.2,
  cut: 0.3,
  windfall: 0.3,
  espionage: 0.35,
  sabotage: 0.25,
};
const BELT_ASTEROID_RATE = 8;

let nextAsteroidId = 1;

interface Where {
  deep: boolean;
  belt: boolean;
  sunDist: number;
}

function whereIs(w: World | null): Where {
  if (!w || w.ship.status !== 'flying') return { deep: false, belt: false, sunDist: 0 };
  const s = w.ship;
  bodyPositions(w.time, PX, PY);
  let minAlt = Infinity;
  for (let i = 0; i < BODY_COUNT; i++) {
    minAlt = Math.min(minAlt, Math.hypot(s.x - PX[i], s.y - PY[i]) - BODIES[i].radius);
  }
  const sunDist = Math.hypot(s.x, s.y);
  return { deep: minAlt > 1500, belt: sunDist > 2.0 * AU && sunDist < 3.4 * AU, sunDist };
}

/** Rolls every event kind for one day-long bin. Deterministic in (seed, bin). */
export function rollBin(c: Campaign, w: World | null, bin: number): EventResult[] {
  const out: EventResult[] = [];
  const where = whereIs(w);
  for (let k = 0; k < KINDS.length; k++) {
    const kind = KINDS[k];
    let rate = RATE[kind];
    if (kind === 'asteroid') rate = where.belt ? BELT_ASTEROID_RATE : where.deep ? rate : 0;
    else if (kind === 'micro' || kind === 'leak') rate = where.deep ? rate : 0;
    else if (kind === 'flare') rate = where.deep && where.sunDist < 6 * AU ? rate : 0;
    if (rate <= 0) continue;
    const p = 1 - Math.exp(-(rate * DAY) / YEAR);
    if (hash01(c.seed, bin, k) >= p) continue;
    const r = fire(kind, c, w, hash01(c.seed, bin, 100 + k), hash01(c.seed, bin, 200 + k), hash01(c.seed, bin, 300 + k));
    if (r) out.push(r);
  }
  return out;
}

function fire(kind: Kind, c: Campaign, w: World | null, u1: number, u2: number, u3: number): EventResult | null {
  const rival = rivalName(c.bloc);
  switch (kind) {
    case 'asteroid':
      return w ? spawnAsteroid(w, u1, u2, u3) : null;
    case 'micro':
      if (!w) return null;
      w.ship.hull = Math.max(1, w.ship.hull - (3 + u1 * 6));
      return { text: 'MICROMETEORITOS: DAÑO MENOR AL CASCO', kind: 'info', interrupt: false };
    case 'leak':
      if (!w) return null;
      w.ship.leak = 0.5 + u1 * 0.5;
      return { text: 'FUGA DE COMBUSTIBLE: SELLÁ LA VÁLVULA', kind: 'bad', interrupt: true };
    case 'flare':
      if (!w) return null;
      w.ship.blackoutUntil = w.time + 90;
      return { text: 'TORMENTA SOLAR: SIN COMUNICACIONES UN MOMENTO', kind: 'bad', interrupt: true };
    case 'cut': {
      const loss = Math.min(c.funds, Math.round(c.funds * 0.2 + 10));
      c.funds -= loss;
      return { text: `RECORTE DE PRESUPUESTO: -${loss} FONDOS`, kind: 'bad', interrupt: false };
    }
    case 'windfall':
      c.funds += 30;
      return { text: 'APOYO PÚBLICO: +30 FONDOS', kind: 'good', interrupt: false };
    case 'espionage': {
      let moved = false;
      for (let i = c.rivalDone; i < c.rivalYears.length; i++) {
        c.rivalYears[i] -= 0.3;
        moved = true;
      }
      return moved ? { text: `ESPIONAJE: ${rival} ACELERA SU PROGRAMA (-0,3 AÑOS)`, kind: 'bad', interrupt: false } : null;
    }
    case 'sabotage': {
      for (let i = c.rivalDone; i < c.rivalYears.length; i++) c.rivalYears[i] += 0.5;
      return { text: `SABOTAJE EN ${rival}: SU PROGRAMA SE RETRASA 0,5 AÑOS`, kind: 'good', interrupt: false };
    }
  }
}

function spawnAsteroid(w: World, u1: number, u2: number, u3: number): EventResult {
  const s = w.ship;
  const angle = u1 * TAU;
  const range = Math.max(2400, w.stats.radarRange);
  const rel = 60 + u2 * 80;
  const r = 8 + u3 * 20;
  const hits = hash01(Math.floor(u1 * 1e6), Math.floor(u2 * 1e6)) < 0.7;
  const miss = hits ? (u3 - 0.5) * (r + 3) : (r + 6) * (2 + u2 * 3);
  const px = s.x + Math.cos(angle) * range;
  const py = s.y + Math.sin(angle) * range;
  const nx = -Math.sin(angle);
  const ny = Math.cos(angle);
  const ax = s.x + nx * miss - px;
  const ay = s.y + ny * miss - py;
  const al = Math.hypot(ax, ay);
  const a: Asteroid = {
    id: nextAsteroidId++,
    x: px,
    y: py,
    vx: s.vx + (ax / al) * rel,
    vy: s.vy + (ay / al) * rel,
    r,
    born: w.time,
  };
  w.asteroids.push(a);
  return { text: `ASTEROIDE DETECTADO: IMPACTO EN ${(range / rel).toFixed(0)} s`, kind: 'bad', interrupt: true };
}

export interface AsteroidOutcome {
  hit: boolean;
  damage: number;
  destroyed: boolean;
}

/** Moves asteroids and resolves impacts or safe passes. Returns what happened this call. */
export function stepAsteroids(w: World, c: Campaign, dt: number, push: (r: EventResult) => void): void {
  const s = w.ship;
  for (let i = w.asteroids.length - 1; i >= 0; i--) {
    const a = w.asteroids[i];
    a.x += a.vx * dt;
    a.y += a.vy * dt;
    if (s.status !== 'flying') {
      w.asteroids.splice(i, 1);
      continue;
    }
    const rx = a.x - s.x;
    const ry = a.y - s.y;
    const d = Math.hypot(rx, ry);
    const rvx = a.vx - s.vx;
    const rvy = a.vy - s.vy;
    if (d < a.r + 6) {
      const damage = a.r < 14 ? 25 : a.r < 22 ? 55 : 100;
      s.hull -= damage;
      w.asteroids.splice(i, 1);
      if (s.hull <= 0) {
        destroyShip(w, 'asteroid');
        push({ text: 'IMPACTO DE ASTEROIDE: NAVE DESTRUIDA', kind: 'bad', interrupt: true });
      } else {
        push({ text: `IMPACTO DE ASTEROIDE: CASCO -${damage}%`, kind: 'bad', interrupt: true });
      }
      continue;
    }
    const closing = rx * rvx + ry * rvy < 0;
    if (!closing && d > a.r + 40) {
      w.asteroids.splice(i, 1);
      c.eventsHandled++;
      addNews(c, w.time, 'Asteroide esquivado', 'good');
      push({ text: 'ASTEROIDE ESQUIVADO (+10)', kind: 'good', interrupt: false });
    }
  }
}

/** Arms the next engine failure for a ship. */
export function armFailure(c: Campaign, w: World, n: number): void {
  const u = hash01(c.seed, n, 777);
  w.ship.failAt = w.ship.burnTime - Math.log(1 - u) * 600;
}

/** Engine failure and recovery, driven by accumulated burn time. */
export function checkEngine(c: Campaign, w: World, push: (r: EventResult) => void): void {
  const s = w.ship;
  if (s.thrustMult < 1 && w.time >= s.thrustFailUntil) {
    s.thrustMult = 1;
    c.eventsHandled++;
    push({ text: 'MOTOR RECUPERADO (+10)', kind: 'good', interrupt: false });
  }
  if (s.burnTime >= s.failAt && s.status === 'flying') {
    s.thrustMult = 0.5;
    s.thrustFailUntil = w.time + 600;
    c.launches += 0;
    armFailure(c, w, Math.floor(s.burnTime));
    push({ text: 'FALLA DE MOTOR: EMPUJE AL 50% POR UN RATO', kind: 'bad', interrupt: true });
  }
}

/** Processes day bins up to time t. Returns the events that fired. */
export function processEvents(c: Campaign, w: World | null, t: number, push: (r: EventResult) => void): void {
  if (c.sandbox) return;
  const last = Math.floor(t / DAY);
  const from = Math.max(c.eventBin + 1, last - 20000);
  for (let bin = from; bin <= last; bin++) {
    for (const r of rollBin(c, w, bin)) {
      addNews(c, t, r.text, r.kind === 'bad' ? 'bad' : r.kind === 'good' ? 'good' : 'event');
      push(r);
    }
  }
  c.eventBin = last;
}
