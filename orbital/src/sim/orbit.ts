import { type Vec2, cross, dot, len, vec } from './vec';

export interface OrbitElements {
  bound: boolean;
  /** Eccentricity. */
  e: number;
  /** Unit vector from the focus towards periapsis. */
  periDir: Vec2;
  /** Periapsis radius from the planet centre. */
  periapsis: number;
  /** Apoapsis radius from the planet centre, null when unbound. */
  apoapsis: number | null;
  /** Orbital period in seconds, null when unbound. */
  period: number | null;
}

/** Two-body orbital elements of a position/velocity pair around a mass at the origin. */
export function orbitElements(pos: Vec2, vel: Vec2, gm: number): OrbitElements {
  const r = len(pos);
  const v2 = dot(vel, vel);
  const energy = v2 / 2 - gm / r;
  const h = cross(pos, vel);
  const k = v2 - gm / r;
  const ev = vec((k * pos.x - dot(pos, vel) * vel.x) / gm, (k * pos.y - dot(pos, vel) * vel.y) / gm);
  const e = len(ev);
  const periDir = e > 1e-9 ? vec(ev.x / e, ev.y / e) : vec(pos.x / r, pos.y / r);

  if (energy < 0) {
    const a = -gm / (2 * energy);
    return {
      bound: true,
      e,
      periDir,
      periapsis: a * (1 - e),
      apoapsis: a * (1 + e),
      period: 2 * Math.PI * Math.sqrt((a * a * a) / gm),
    };
  }
  return {
    bound: false,
    e,
    periDir,
    periapsis: (h * h) / (gm * (1 + e)),
    apoapsis: null,
    period: null,
  };
}
