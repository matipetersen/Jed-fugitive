import { type BodyDef, type SiteDef } from './bodies';

/** Terrain wavelengths in u. Slopes stay moderate on small bodies because they are set in length, not in turns. */
const WAVELENGTHS = [900, 520, 300, 170, 100];

interface Profile {
  freqs: number[];
  phases: number[];
  amps: number[];
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

function profile(b: BodyDef): Profile {
  let p = cache.get(b.index);
  if (!p) {
    const rnd = mulberry32(b.terrainSeed * 7919 + 17);
    const freqs: number[] = [];
    const amps: number[] = [];
    for (const lambda of WAVELENGTHS) {
      const k = Math.max(2, Math.round((2 * Math.PI * b.radius) / lambda));
      if (freqs.includes(k)) continue;
      freqs.push(k);
      amps.push((b.terrainAmp / 14) * 0.0095 * ((2 * Math.PI * b.radius) / k));
    }
    p = { freqs, phases: freqs.map(() => rnd() * Math.PI * 2), amps };
    cache.set(b.index, p);
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
  const p = profile(b);
  let h = 0;
  for (let i = 0; i < p.freqs.length; i++) h += p.amps[i] * Math.sin(p.freqs[i] * theta + p.phases[i]);
  return b.radius + h * (1 - flatness(b, theta));
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
