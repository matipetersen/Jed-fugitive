import { type Arena, type Frame } from './arena';
import { type Ship } from './types';

const F: Frame = { x: new Float64Array(16), y: new Float64Array(16), vx: new Float64Array(16), vy: new Float64Array(16) };
const G = { x: 0, y: 0 };

export interface PathResult {
  /** Flat [x0, y0, x1, y1, ...]. */
  points: number[];
  /** True if the path ends in a body or the star. */
  hits: boolean;
}

/** Coasting path of a ship for `seconds`, under the real gravity and drag, with no thrust. */
export function coastPath(arena: Arena, ship: Ship, seconds: number, dt = 0.05): PathResult {
  const points: number[] = [ship.x, ship.y];
  let x = ship.x;
  let y = ship.y;
  let vx = ship.vx;
  let vy = ship.vy;
  let t = arena.t;
  let hits = false;
  const steps = Math.round(seconds / dt);
  for (let k = 0; k < steps; k++) {
    t += dt;
    arena.framesAt(t, F);
    arena.gravity(x, y, F, G);
    let fx = 0;
    let fy = 0;
    for (let i = 0; i < arena.bodies.length; i++) {
      const b = arena.bodies[i];
      const atm = b.def.atm;
      if (!atm) continue;
      const d = Math.hypot(x - F.x[i], y - F.y[i]);
      if (d - b.def.r > atm.h * 3) continue;
      const rho = Math.exp(-Math.max(d - b.def.r, 0) / atm.h);
      const rvx = vx - F.vx[i];
      const rvy = vy - F.vy[i];
      const sp = Math.hypot(rvx, rvy);
      fx -= atm.drag * rho * sp * rvx;
      fy -= atm.drag * rho * sp * rvy;
    }
    vx += (G.x + fx) * dt;
    vy += (G.y + fy) * dt;
    x += vx * dt;
    y += vy * dt;
    points.push(x, y);
    for (let i = 0; i < arena.bodies.length; i++) {
      if (Math.hypot(x - F.x[i], y - F.y[i]) < arena.bodies[i].def.r + 7) {
        hits = true;
        break;
      }
    }
    if (hits) break;
  }
  return { points, hits };
}
