import { PLANET } from './params';
import { orbitElements } from './orbit';
import { CONTACT_RADIUS, type ShipState } from './sim';

export interface Prediction {
  /** Flat [x0, y0, x1, y1, ...] world positions. */
  points: Float64Array;
  count: number;
  impact: boolean;
}

const MAX_POINTS = 600;
const SUBSTEP = 1 / 50;
const MAX_HORIZON = 900;

/**
 * Coast trajectory (no thrust) from the current state. Covers a bit more than
 * one orbit when bound, and stops at the first surface contact.
 */
export function predictCoast(ship: ShipState, gm: number = PLANET.gm): Prediction {
  const el = orbitElements(ship.pos, ship.vel, gm);
  const horizon = el.period ? Math.min(el.period * 1.05, MAX_HORIZON) : 240;
  const sampleDt = horizon / MAX_POINTS;
  const sub = Math.max(1, Math.ceil(sampleDt / SUBSTEP));
  const h = sampleDt / sub;

  const points = new Float64Array(MAX_POINTS * 2 + 2);
  let x = ship.pos.x;
  let y = ship.pos.y;
  let vx = ship.vel.x;
  let vy = ship.vel.y;
  let count = 0;
  let impact = false;

  points[count * 2] = x;
  points[count * 2 + 1] = y;
  count++;

  for (let i = 0; i < MAX_POINTS && !impact; i++) {
    for (let s = 0; s < sub; s++) {
      let r = Math.hypot(x, y);
      let k = -gm / (r * r * r);
      vx += x * k * h * 0.5;
      vy += y * k * h * 0.5;
      x += vx * h;
      y += vy * h;
      r = Math.hypot(x, y);
      k = -gm / (r * r * r);
      vx += x * k * h * 0.5;
      vy += y * k * h * 0.5;
      if (r < CONTACT_RADIUS) {
        impact = true;
        break;
      }
    }
    points[count * 2] = x;
    points[count * 2 + 1] = y;
    count++;
  }
  return { points, count, impact };
}
