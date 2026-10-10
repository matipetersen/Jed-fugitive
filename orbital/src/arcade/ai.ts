import { Arena, BURN_RATE, type Frame, SHIP_R, STEP } from './arena';
import { type Controls, type Ship } from './types';

const TAU = Math.PI * 2;
const wrap = (a: number): number => {
  let r = (a + Math.PI) % TAU;
  if (r < 0) r += TAU;
  return r - Math.PI;
};
const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

export interface AiState {
  nextAt: number;
  heading: number;
  throttle: number;
  /** Time of the last gate passed, to detect getting stuck. */
  lastProgress: number;
  lastGate: number;
}

export function newAi(): AiState {
  return { nextAt: 0, heading: Math.PI / 2, throttle: 0, lastProgress: 0, lastGate: 0 };
}

export interface AiOptions {
  /** Planning horizon in seconds and its step. */
  horizon: number;
  dt: number;
  /** How often it replans. */
  interval: number;
  /** Random heading error in radians (a less sharp pilot). */
  noise: number;
}

/** Price of burning fuel for pilots with a finite tank: base and extra as the tank empties. */
export const FUEL_PRICE = { base: 2, gain: 8 };

export const RIVAL_AI: AiOptions = { horizon: 1.6, dt: 0.05, interval: 0.1, noise: 0 };

const THROTTLES = [0, 0.4, 1];
const OFFSETS = [0, 0.18, -0.18, 0.45, -0.45, 0.85, -0.85, 1.4, -1.4, Math.PI];

const PF: Frame = { x: new Float64Array(16), y: new Float64Array(16), vx: new Float64Array(16), vy: new Float64Array(16) };
const GP = { x: 0, y: 0 };
const G = { x: 0, y: 0 };

/**
 * Model-predictive pilot: tries a set of constant headings and throttles for a
 * second or two under the real gravity, and keeps the one that gets closest to
 * the next gate without touching anything.
 */
export function aiControl(arena: Arena, ship: Ship, ai: AiState, rnd: () => number, opts: AiOptions = RIVAL_AI): Controls {
  if (ship.status === 'dead' || ship.finished || ship.nextGate >= arena.gates.length) return { throttle: 0, turn: 0 };
  if (ship.nextGate !== ai.lastGate) {
    ai.lastGate = ship.nextGate;
    ai.lastProgress = arena.t;
  }
  if (arena.t >= ai.nextAt) {
    ai.nextAt = arena.t + opts.interval;
    plan(arena, ship, ai, rnd, opts);
  }
  const err = wrap(ai.heading - ship.angle);
  return { throttle: ai.throttle, turn: clamp(err * 6, -1, 1) };
}

function plan(arena: Arena, ship: Ship, ai: AiState, rnd: () => number, opts: AiOptions): void {
  const steps = Math.round(opts.horizon / opts.dt);
  arena.gatePos(ship.nextGate, GP);
  const gate = arena.gates[ship.nextGate];
  const toGate = Math.atan2(GP.y - ship.y, GP.x - ship.x);
  const speed = Math.hypot(ship.vx, ship.vy);
  const startD = Math.hypot(GP.x - ship.x, GP.y - ship.y);

  // Nearest body for the "up" and "prograde" candidates.
  let near = 0;
  let nearAlt = Infinity;
  for (let i = 0; i < arena.bodies.length; i++) {
    const a = Math.hypot(ship.x - arena.cur.x[i], ship.y - arena.cur.y[i]) - arena.bodies[i].def.r;
    if (a < nearAlt) {
      nearAlt = a;
      near = i;
    }
  }
  const up = Math.atan2(ship.y - arena.cur.y[near], ship.x - arena.cur.x[near]);
  const headings: number[] = OFFSETS.map((o) => toGate + o);
  headings.push(up, up + 0.5, up - 0.5);
  if (speed > 20) {
    const pro = Math.atan2(ship.vy - arena.cur.vy[near], ship.vx - arena.cur.vx[near]);
    headings.push(pro, pro + Math.PI);
  }

  let bestJ = Infinity;
  let bestH = ai.heading;
  let bestT = ai.throttle;
  const thrustMax = ship.stats.thrust;
  for (const h0 of headings) {
    const hd = h0 + (rnd() - 0.5) * 2 * opts.noise;
    for (const thr of THROTTLES) {
      let x = ship.x;
      let y = ship.y;
      let vx = ship.vx;
      let vy = ship.vy;
      let t = arena.t;
      const nx = Math.cos(hd);
      const ny = Math.sin(hd);
      let minD = Infinity;
      let danger = 0;
      let landed = ship.status === 'landed';
      for (let k = 0; k < steps; k++) {
        t += opts.dt;
        arena.framesAt(t, PF);
        const aT = thr * thrustMax;
        // Landed ships hold still until thrust beats gravity.
        if (landed) {
          const b = arena.bodies[ship.landedBody];
          const rel = aT * Math.cos(hd - ship.landedAngle) - b.def.g;
          if (rel <= 0) {
            x = PF.x[ship.landedBody] + (b.def.r + SHIP_R) * Math.cos(ship.landedAngle);
            y = PF.y[ship.landedBody] + (b.def.r + SHIP_R) * Math.sin(ship.landedAngle);
            vx = PF.vx[ship.landedBody];
            vy = PF.vy[ship.landedBody];
            continue;
          }
          landed = false;
        }
        arena.gravity(x, y, PF, G);
        // Drag from atmospheres.
        let fx = 0;
        let fy = 0;
        for (let i = 0; i < arena.bodies.length; i++) {
          const b = arena.bodies[i];
          const atm = b.def.atm;
          if (!atm) continue;
          const d = Math.hypot(x - PF.x[i], y - PF.y[i]);
          if (d - b.def.r > atm.h * 3) continue;
          const rho = Math.exp(-Math.max(d - b.def.r, 0) / atm.h);
          const rvx = vx - PF.vx[i];
          const rvy = vy - PF.vy[i];
          const sp = Math.hypot(rvx, rvy);
          fx -= atm.drag * rho * sp * rvx;
          fy -= atm.drag * rho * sp * rvy;
        }
        vx += (G.x + nx * aT + fx) * opts.dt;
        vy += (G.y + ny * aT + fy) * opts.dt;
        x += vx * opts.dt;
        y += vy * opts.dt;
        arena.gatePos(ship.nextGate, GP, PF);
        const dg = Math.hypot(x - GP.x, y - GP.y);
        if (dg < minD) minD = dg;
        for (let i = 0; i < arena.bodies.length; i++) {
          const b = arena.bodies[i];
          const alt = Math.hypot(x - PF.x[i], y - PF.y[i]) - b.def.r;
          const rel = Math.hypot(vx - PF.vx[i], vy - PF.vy[i]);
          if (b.def.star) {
            if (alt < b.def.r * 0.9) danger += 4000;
            continue;
          }
          // Contact is a loss (the planner does not model landing) unless the ship is still climbing out of a launch.
          const rv = ((vx - PF.vx[i]) * (x - PF.x[i]) + (vy - PF.vy[i]) * (y - PF.y[i])) / Math.max(1, alt + b.def.r);
          if (alt < SHIP_R + 2 && rv < 6) danger += 5000;
          else if (alt < 24 && rel > 60) danger += (24 - alt) * 5;
        }
        for (const a of arena.asteroids) {
          if (!a.alive) continue;
          const ax = a.x + a.vx * (t - arena.t);
          const ay = a.y + a.vy * (t - arena.t);
          const d = Math.hypot(x - ax, y - ay);
          if (d < a.r + SHIP_R + 12) danger += 900;
        }
      }
      arena.gatePos(ship.nextGate, GP, PF);
      const endD = Math.hypot(x - GP.x, y - GP.y);
      const dir = Math.atan2(GP.y - y, GP.x - x);
      const vToward = (vx - PF.vx[0]) * Math.cos(dir) + (vy - PF.vy[0]) * Math.sin(dir);
      // Speed towards the gate is good, but only as much as can be used: no point arriving faster than the gate is far.
      const cap = 80 + startD / 1.1;
      let J = endD * 0.5 + minD - 0.35 * clamp(vToward, -50, Math.min(260, cap)) * opts.horizon + danger;
      // Beyond the speed a pilot can steer, going faster only means missing the next gate.
      const sp = Math.hypot(vx, vy);
      if (sp > 230) J += (sp - 230) * 3;
      if (minD < gate.r * 0.8) J -= 400;
      if (!ship.infiniteFuel) {
        // Fuel is limited: burning has a price that rises as the tank empties.
        const left = ship.fuel / ship.stats.fuelMax;
        J += thr * BURN_RATE * opts.horizon * (FUEL_PRICE.base + FUEL_PRICE.gain * (1 - left));
      }
      if (J < bestJ) {
        bestJ = J;
        bestH = hd;
        bestT = thr;
      }
    }
  }
  ai.heading = bestH;
  ai.throttle = bestT;
}

/** Runs a rival alone, respawning it after death. Used by the game loop and by tests. */
export class RivalDriver {
  readonly ai = newAi();
  constructor(
    private readonly rnd: () => number,
    private readonly opts: AiOptions = RIVAL_AI,
    /** Seconds after GO before the rival starts moving. */
    private readonly delay = 0,
  ) {}

  control(arena: Arena, ship: Ship): Controls {
    if (ship.status === 'dead') {
      if (ship.deadTimer <= 0) {
        // Back in the race at the last gate it passed (or the start).
        const gi = Math.max(0, ship.nextGate - 1);
        const p = { x: 0, y: 0 };
        if (ship.nextGate === 0) {
          arena.respawn(ship, { body: ship.landedBody, angle: ship.landedAngle }, { fuel: ship.stats.fuelMax, hull: ship.stats.hullMax });
        } else {
          arena.gatePos(gi, p);
          arena.respawnFlying(ship, p.x, p.y);
        }
      }
      return { throttle: 0, turn: 0 };
    }
    if (arena.clock < this.delay) return { throttle: 0, turn: 0 };
    return aiControl(arena, ship, this.ai, this.rnd, this.opts);
  }
}

export { STEP };
