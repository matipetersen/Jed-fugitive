import { type BodyDef, type SiteDef } from './bodies';

const FREQS = [5, 9, 17, 31, 57, 113, 223];

interface Profile {
  phases: number[];
  weights: number[];
}

const cache = new Map<number, Profile>();

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function profile(seed: number): Profile {
  let p = cache.get(seed);
  if (!p) {
    const rnd = mulberry32(seed * 7919 + 17);
    const raw = FREQS.map((k) => Math.pow(k, -0.9));
    const sum = raw.reduce((a, b) => a + b, 0);
    p = { phases: FREQS.map(() => rnd() * Math.PI * 2), weights: raw.map((w) => w / sum) };
    cache.set(seed, p);
  }
  return p;
}

const smooth = (x: number): number => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};

function wrap(a: number): number {
  const tp = Math.PI * 2;
  let r = (a + Math.PI) % tp;
  if (r < 0) r += tp;
  return r - Math.PI;
}

/** Flatness factor 0..1: 1 on the core of a landing site, ramping out to 0. */
export function flatness(b: BodyDef, theta: number): number {
  let f = 0;
  for (const s of b.sites) {
    const half = s.halfWidth / b.radius;
    const d = Math.abs(wrap(theta - s.angle));
    f = Math.max(f, d <= half ? 1 : smooth(1 - (d - half) / (half * 1.5)));
  }
  return f;
}

/** Ground radius of a body at angle theta. Gas giants and stars have no terrain. */
export function terrainRadius(b: BodyDef, theta: number): number {
  if (b.terrainAmp === 0) return b.radius;
  const p = profile(b.terrainSeed);
  let h = 0;
  for (let i = 0; i < FREQS.length; i++) h += p.weights[i] * Math.sin(FREQS[i] * theta + p.phases[i]);
  return b.radius + b.terrainAmp * h * 2.2 * (1 - flatness(b, theta));
}

/** Slope angle of the ground at theta in radians (0 = flat). */
export function terrainSlope(b: BodyDef, theta: number): number {
  if (b.terrainAmp === 0) return 0;
  const e = 1e-4;
  const dr = (terrainRadius(b, theta + e) - terrainRadius(b, theta - e)) / (2 * e);
  return Math.atan(dr / terrainRadius(b, theta));
}

/** The landing site whose flat core contains theta, if any. */
export function siteAt(b: BodyDef, theta: number): SiteDef | null {
  for (const s of b.sites) {
    if (Math.abs(wrap(theta - s.angle)) * b.radius <= s.halfWidth * 1.3) return s;
  }
  return null;
}
