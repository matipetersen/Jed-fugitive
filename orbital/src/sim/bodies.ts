import { TAU, gmKm3ToU, kmToU } from './units';

export type BodyId = 'sun' | 'venus' | 'earth' | 'moon' | 'mars' | 'jupiter' | 'pluto';

export interface AtmosphereDef {
  /** Scale height in u. Exaggerated relative to reality so it is playable. */
  scaleHeight: number;
  /** Surface density relative to Earth's sea level. */
  density: number;
}

export interface SiteDef {
  name: string;
  /** Angle of the site centre around the body, radians from +x. */
  angle: number;
  /** Half width in u. */
  halfWidth: number;
}

export interface BodyDef {
  id: BodyId;
  name: string;
  index: number;
  parent: BodyId | null;
  parentIndex: number;
  radius: number;
  gm: number;
  surfaceGravity: number;
  orbitRadius: number;
  phase0: number;
  /** Angular rate, rad per game second. */
  omega: number;
  period: number;
  /** Sphere-of-influence radius. Infinite for the Sun. */
  soi: number;
  color: string;
  star: boolean;
  gas: boolean;
  atmosphere: AtmosphereDef | null;
  terrainAmp: number;
  terrainSeed: number;
  sites: SiteDef[];
  /** Volatile richness, 0..1. Drives ISRU fuel production. */
  ice: number;
}

interface Raw {
  id: BodyId;
  name: string;
  parent: BodyId | null;
  radiusKm: number;
  gmKm3: number;
  aKm: number;
  phase0: number;
  color: string;
  star?: boolean;
  gas?: boolean;
  atmosphere?: AtmosphereDef;
  terrainAmp?: number;
  terrainSeed?: number;
  sites?: SiteDef[];
  ice?: number;
}

const RAW: Raw[] = [
  { id: 'sun', name: 'Sol', parent: null, radiusKm: 695700, gmKm3: 1.32712440018e11, aKm: 0, phase0: 0, color: '#fff27a', star: true },
  {
    id: 'venus', name: 'Venus', parent: 'sun', radiusKm: 6051.8, gmKm3: 3.24859e5, aKm: 108.208e6, phase0: 2.1, color: '#ffb02e',
    atmosphere: { scaleHeight: 24, density: 6 }, terrainAmp: 12, terrainSeed: 11,
    sites: [{ name: 'Planicie de Guinevere', angle: 0.7, halfWidth: 35 }], ice: 0,
  },
  {
    id: 'earth', name: 'Tierra', parent: 'sun', radiusKm: 6371, gmKm3: 398600.4418, aKm: 149.598e6, phase0: 0, color: '#2f7bff',
    atmosphere: { scaleHeight: 22, density: 1 }, terrainAmp: 6, terrainSeed: 3,
    sites: [
      { name: 'Cabo Cañaveral', angle: Math.PI / 2, halfWidth: 30 },
      { name: 'Baikonur', angle: Math.PI / 2 + 0.55, halfWidth: 30 },
    ],
    ice: 0,
  },
  {
    id: 'moon', name: 'Luna', parent: 'earth', radiusKm: 1737.4, gmKm3: 4902.8, aKm: 384400, phase0: 0.6, color: '#c8d4ff',
    terrainAmp: 14, terrainSeed: 5,
    sites: [
      { name: 'Mar de la Tranquilidad', angle: 0.3, halfWidth: 40 },
      { name: 'Cráter del Polo Sur', angle: -Math.PI / 2, halfWidth: 40 },
    ],
    ice: 0.6,
  },
  {
    id: 'mars', name: 'Marte', parent: 'sun', radiusKm: 3389.5, gmKm3: 42828.4, aKm: 227.94e6, phase0: 4.2, color: '#ff5a3c',
    atmosphere: { scaleHeight: 30, density: 0.12 }, terrainAmp: 16, terrainSeed: 7,
    sites: [{ name: 'Utopia Planitia', angle: 1.1, halfWidth: 40 }, { name: 'Valles Marineris', angle: 3.4, halfWidth: 40 }], ice: 0.9,
  },
  {
    id: 'jupiter', name: 'Júpiter', parent: 'sun', radiusKm: 71492, gmKm3: 1.26686534e8, aKm: 778.57e6, phase0: 1.3, color: '#ff9a5a',
    gas: true, atmosphere: { scaleHeight: 150, density: 0.5 },
  },
  {
    id: 'pluto', name: 'Plutón', parent: 'sun', radiusKm: 1188.3, gmKm3: 869.6, aKm: 5906.4e6, phase0: 3.5, color: '#b48cff',
    atmosphere: { scaleHeight: 40, density: 0.0008 }, terrainAmp: 7, terrainSeed: 13,
    sites: [{ name: 'Sputnik Planitia', angle: 0.8, halfWidth: 45 }], ice: 0.4,
  },
];

export const BODIES: BodyDef[] = [];
const byId = new Map<BodyId, BodyDef>();

for (const r of RAW) {
  const parentDef = r.parent ? byId.get(r.parent) : undefined;
  const gm = gmKm3ToU(r.gmKm3);
  const radius = kmToU(r.radiusKm);
  const orbitRadius = kmToU(r.aKm);
  const period = parentDef ? TAU * Math.sqrt(orbitRadius ** 3 / parentDef.gm) : 0;
  const def: BodyDef = {
    id: r.id,
    name: r.name,
    index: BODIES.length,
    parent: r.parent,
    parentIndex: parentDef ? parentDef.index : -1,
    radius,
    gm,
    surfaceGravity: gm / (radius * radius),
    orbitRadius,
    phase0: r.phase0,
    omega: period > 0 ? TAU / period : 0,
    period,
    soi: parentDef ? orbitRadius * (gm / parentDef.gm) ** 0.4 : Infinity,
    color: r.color,
    star: !!r.star,
    gas: !!r.gas,
    atmosphere: r.atmosphere ?? null,
    terrainAmp: r.terrainAmp ?? 0,
    terrainSeed: r.terrainSeed ?? 0,
    sites: r.sites ?? [],
    ice: r.ice ?? 0,
  };
  BODIES.push(def);
  byId.set(def.id, def);
}

export const BODY_COUNT = BODIES.length;
export const SUN = 0;
export const body = (id: BodyId): BodyDef => byId.get(id)!;
export const indexOf = (id: BodyId): number => byId.get(id)!.index;

const bpx = new Float64Array(BODY_COUNT);
const bpy = new Float64Array(BODY_COUNT);

/** Fills outX/outY with the inertial (Sun-centred) position of every body at time t. */
export function bodyPositions(t: number, outX: Float64Array, outY: Float64Array): void {
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    if (b.parentIndex < 0) {
      outX[i] = 0;
      outY[i] = 0;
    } else {
      const phi = b.phase0 + b.omega * t;
      outX[i] = outX[b.parentIndex] + b.orbitRadius * Math.cos(phi);
      outY[i] = outY[b.parentIndex] + b.orbitRadius * Math.sin(phi);
    }
  }
}

/** Fills positions and velocities of every body at time t. */
export function bodyStates(
  t: number,
  px: Float64Array,
  py: Float64Array,
  vx: Float64Array,
  vy: Float64Array,
): void {
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    if (b.parentIndex < 0) {
      px[i] = 0;
      py[i] = 0;
      vx[i] = 0;
      vy[i] = 0;
    } else {
      const phi = b.phase0 + b.omega * t;
      const c = Math.cos(phi);
      const s = Math.sin(phi);
      const sp = b.orbitRadius * b.omega;
      px[i] = px[b.parentIndex] + b.orbitRadius * c;
      py[i] = py[b.parentIndex] + b.orbitRadius * s;
      vx[i] = vx[b.parentIndex] - sp * s;
      vy[i] = vy[b.parentIndex] + sp * c;
    }
  }
}

export function bodyPos(i: number, t: number): { x: number; y: number } {
  bodyPositions(t, bpx, bpy);
  return { x: bpx[i], y: bpy[i] };
}

export function bodyVel(i: number, t: number): { x: number; y: number } {
  const b = BODIES[i];
  if (b.parentIndex < 0) return { x: 0, y: 0 };
  const pv = bodyVel(b.parentIndex, t);
  const phi = b.phase0 + b.omega * t;
  const sp = b.orbitRadius * b.omega;
  return { x: pv.x - sp * Math.sin(phi), y: pv.y + sp * Math.cos(phi) };
}

/** Index of the body whose sphere of influence contains the point (smallest wins). */
export function referenceBody(x: number, y: number, t: number): number {
  bodyPositions(t, bpx, bpy);
  let best = SUN;
  let bestSoi = Infinity;
  for (let i = 1; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    if (b.soi < bestSoi && Math.hypot(x - bpx[i], y - bpy[i]) < b.soi) {
      best = i;
      bestSoi = b.soi;
    }
  }
  return best;
}
