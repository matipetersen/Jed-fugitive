import {
  BODIES,
  BODY_COUNT,
  bodyPositions,
  bodyStates,
  referenceBody,
} from './bodies';
import { HEAT_COOL, HEAT_K, SCOOP_K, atmosphereTop, density, dragCoefficient, heatFactor } from './atmosphere';
import { orbitElements, keplerPropagate, type OrbitElements } from './orbit';
import { type ShipStats, BASE_STATS } from './tech';
import { terrainRadius, terrainSlope } from './terrain';
import { wrapAngle } from './vec';

export const FIXED_DT = 1 / 120;
export const LEG_LENGTH = 8;

export type ShipStatus = 'flying' | 'landed' | 'crashed';

export interface ShipState {
  /** Inertial (Sun-centred) position and velocity. */
  x: number;
  y: number;
  vx: number;
  vy: number;
  /** Nose direction in world space, radians (0 = +x, counter-clockwise). */
  angle: number;
  fuel: number;
  throttle: number;
  status: ShipStatus;
  /** Body the ship rests on when landed or crashed, and the angle around it. */
  landedBody: number;
  landedTheta: number;
  heat: number;
  hull: number;
  impactSpeed: number;
  crashReason: string;
  /** Damage and event effects. */
  thrustMult: number;
  /** Fuel lost per second through a leak. */
  leak: number;
  blackoutUntil: number;
  /** Engine failure: thrustMult returns to 1 after this time. */
  thrustFailUntil: number;
  /** Seconds of thrust so far, and the burn time at which the next failure happens. */
  burnTime: number;
  failAt: number;
}

export interface Asteroid {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  /** Time at which this object was detected. */
  born: number;
}

export interface World {
  time: number;
  ship: ShipState;
  stats: ShipStats;
  asteroids: Asteroid[];
}

export interface Controls {
  /** Desired throttle, 0..1. */
  throttle: number;
  /** Rotation command, -1..1, positive is counter-clockwise. */
  turn: number;
}

const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

const PX = new Float64Array(BODY_COUNT);
const PY = new Float64Array(BODY_COUNT);
const VX = new Float64Array(BODY_COUNT);
const VY = new Float64Array(BODY_COUNT);
const GX = new Float64Array(BODY_COUNT);
const GY = new Float64Array(BODY_COUNT);
const ACC = { x: 0, y: 0 };

export function newShipState(): ShipState {
  return {
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    angle: Math.PI / 2,
    fuel: 0,
    throttle: 0,
    status: 'landed',
    landedBody: 0,
    landedTheta: 0,
    heat: 0,
    hull: 100,
    impactSpeed: 0,
    crashReason: '',
    thrustMult: 1,
    leak: 0,
    blackoutUntil: 0,
    thrustFailUntil: 0,
    burnTime: 0,
    failAt: Infinity,
  };
}

/** Contact radius of a body at angle theta, including landing legs for rocky bodies. */
export function contactRadius(i: number, theta: number): number {
  const b = BODIES[i];
  if (b.star) return b.radius;
  if (b.gas) return b.radius * 0.98;
  return terrainRadius(b, theta) + LEG_LENGTH;
}

/** Creates a world with the ship on the ground of body `bodyIndex` at angle theta. */
export function createWorld(
  stats: ShipStats = BASE_STATS,
  bodyIndex = 2,
  theta = Math.PI / 2,
  time = 0,
  fuel: number = stats.fuelCap,
): World {
  const ship = newShipState();
  ship.landedBody = bodyIndex;
  ship.landedTheta = theta;
  ship.fuel = Math.min(fuel, stats.fuelCap);
  ship.angle = theta;
  const w: World = { time, ship, stats, asteroids: [] };
  placeOnBody(w);
  return w;
}

/** Snaps a landed or crashed ship onto its body, which moves along its orbit. */
export function placeOnBody(w: World): void {
  const s = w.ship;
  if (s.status === 'flying') return;
  bodyStates(w.time, PX, PY, VX, VY);
  const i = s.landedBody;
  const r = contactRadius(i, s.landedTheta);
  s.x = PX[i] + r * Math.cos(s.landedTheta);
  s.y = PY[i] + r * Math.sin(s.landedTheta);
  s.vx = VX[i];
  s.vy = VY[i];
}

/** Sum of gravitational accelerations on a point at time t, written into ACC. */
export function gravity(x: number, y: number, t: number): { x: number; y: number } {
  bodyPositions(t, GX, GY);
  let ax = 0;
  let ay = 0;
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    const dx = GX[i] - x;
    const dy = GY[i] - y;
    let d2 = dx * dx + dy * dy;
    const min = b.radius * 0.25;
    if (d2 < min * min) d2 = min * min;
    const d = Math.sqrt(d2);
    const k = b.gm / (d2 * d);
    ax += dx * k;
    ay += dy * k;
  }
  ACC.x = ax;
  ACC.y = ay;
  return ACC;
}

/**
 * Adaptive step for coasting flight: a small fraction of the local dynamical
 * timescale of every body, and short enough that a fast approach to a surface
 * is not stepped over.
 */
export function suggestStep(x: number, y: number, vx: number, vy: number, t: number): number {
  bodyStates(t, PX, PY, VX, VY);
  let h = 3600;
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    const dx = x - PX[i];
    const dy = y - PY[i];
    const d = Math.hypot(dx, dy);
    const dd = Math.max(d, b.radius);
    h = Math.min(h, 0.02 * Math.sqrt((dd * dd * dd) / b.gm));
    const clearance = d - (b.radius + b.terrainAmp * 1.5 + LEG_LENGTH);
    const rel = Math.hypot(vx - VX[i], vy - VY[i]);
    if (clearance < rel * 50) h = Math.min(h, Math.max(1 / 480, (0.2 * Math.max(clearance, 0)) / Math.max(rel, 1)));
  }
  return Math.max(h, 1 / 480);
}


/** One physics step of h seconds. */
export function step(w: World, c: Controls, h: number): void {
  const s = w.ship;
  if (s.status !== 'flying') {
    stepStatic(w, c, h);
    return;
  }
  const st = w.stats;
  const t = w.time;

  s.throttle = s.fuel > 0 ? clamp(c.throttle, 0, 1) : 0;
  s.angle = wrapAngle(s.angle + clamp(c.turn, -1, 1) * st.turnRate * h);

  const mass = st.dryMass + s.fuel;
  const force = s.throttle * st.thrust * s.thrustMult;
  const aT = force / mass;
  const nx = Math.cos(s.angle);
  const ny = Math.sin(s.angle);
  const burn = Math.min(s.fuel, (force * h) / st.ve + s.leak * h);

  // Atmosphere: drag, heating, gas scooping.
  bodyStates(t, PX, PY, VX, VY);
  let dragX = 0;
  let dragY = 0;
  let heating = 0;
  let scoop = 0;
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    if (!b.atmosphere) continue;
    const dx = s.x - PX[i];
    const dy = s.y - PY[i];
    const alt = Math.hypot(dx, dy) - b.radius;
    if (alt > atmosphereTop(b)) continue;
    const rho = density(b, alt);
    const rvx = s.vx - VX[i];
    const rvy = s.vy - VY[i];
    const speed = Math.hypot(rvx, rvy);
    if (speed < 1e-9) continue;
    const aoa = wrapAngle(Math.atan2(rvy, rvx) - s.angle);
    const k = dragCoefficient(rho, aoa, mass);
    dragX -= k * speed * rvx;
    dragY -= k * speed * rvy;
    heating += HEAT_K * rho * speed * speed * speed * heatFactor(aoa);
    if (b.gas) scoop += SCOOP_K * rho * speed;
  }
  s.heat = Math.max(0, s.heat + (heating - HEAT_COOL * s.heat) * h);

  const g0 = gravity(s.x, s.y, t);
  const ax0 = g0.x + nx * aT + dragX;
  const ay0 = g0.y + ny * aT + dragY;
  s.vx += ax0 * h * 0.5;
  s.vy += ay0 * h * 0.5;
  s.x += s.vx * h;
  s.y += s.vy * h;
  const g1 = gravity(s.x, s.y, t + h);
  s.vx += (g1.x + nx * aT + dragX) * h * 0.5;
  s.vy += (g1.y + ny * aT + dragY) * h * 0.5;

  s.fuel = Math.min(st.fuelCap, Math.max(0, s.fuel - burn + scoop * h));
  if (s.throttle > 0) s.burnTime += h;
  w.time = t + h;

  if (s.heat >= st.heatLimit) {
    crashAtNearest(w, 'burn');
    return;
  }
  checkContact(w);
}

function stepStatic(w: World, c: Controls, h: number): void {
  const s = w.ship;
  const st = w.stats;
  w.time += h;
  if (s.status === 'crashed') {
    s.throttle = 0;
    placeOnBody(w);
    return;
  }
  s.throttle = s.fuel > 0 ? clamp(c.throttle, 0, 1) : 0;
  const mass = st.dryMass + s.fuel;
  const force = s.throttle * st.thrust * s.thrustMult;
  const aT = force / mass;
  s.fuel = Math.max(0, s.fuel - (force * h) / st.ve);
  const b = BODIES[s.landedBody];
  const r = contactRadius(s.landedBody, s.landedTheta);
  const lift =
    aT * (Math.cos(s.angle) * Math.cos(s.landedTheta) + Math.sin(s.angle) * Math.sin(s.landedTheta)) -
    b.gm / (r * r);
  s.heat = Math.max(0, s.heat - HEAT_COOL * s.heat * h);
  placeOnBody(w);
  if (lift > 0) s.status = 'flying';
}

function checkContact(w: World): void {
  const s = w.ship;
  bodyStates(w.time, PX, PY, VX, VY);
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    const dx = s.x - PX[i];
    const dy = s.y - PY[i];
    const limit = b.radius + b.terrainAmp * 2.5 + LEG_LENGTH + 1;
    if (Math.abs(dx) > limit || Math.abs(dy) > limit) continue;
    const d = Math.hypot(dx, dy);
    const theta = Math.atan2(dy, dx);
    if (d < contactRadius(i, theta)) {
      touchdown(w, i, theta, VX[i], VY[i]);
      return;
    }
  }
}

function touchdown(w: World, i: number, theta: number, bvx: number, bvy: number): void {
  const s = w.ship;
  const b = BODIES[i];
  const speed = Math.hypot(s.vx - bvx, s.vy - bvy);
  s.impactSpeed = speed;
  s.landedBody = i;
  s.landedTheta = theta;
  s.throttle = 0;
  if (b.star) {
    s.status = 'crashed';
    s.crashReason = 'sun';
    return;
  }
  if (b.gas) {
    s.status = 'crashed';
    s.crashReason = 'crush';
    return;
  }
  const slope = terrainSlope(b, theta);
  const normal = theta - slope;
  const tilt = Math.abs(wrapAngle(s.angle - normal));
  const safe = speed <= w.stats.maxLandSpeed && tilt <= w.stats.maxLandTilt && Math.abs(slope) <= 0.32;
  s.status = safe ? 'landed' : 'crashed';
  s.crashReason = safe ? '' : speed > w.stats.maxLandSpeed ? 'speed' : Math.abs(slope) > 0.32 ? 'slope' : 'tilt';
  placeOnBody(w);
}

/** Marks the ship destroyed and drops the wreck on the closest body. */
export function crashAtNearest(w: World, reason: string): void {
  const s = w.ship;
  bodyStates(w.time, PX, PY, VX, VY);
  let best = 0;
  let bestAlt = Infinity;
  for (let i = 0; i < BODY_COUNT; i++) {
    const alt = Math.hypot(s.x - PX[i], s.y - PY[i]) - BODIES[i].radius;
    if (alt < bestAlt) {
      bestAlt = alt;
      best = i;
    }
  }
  s.landedBody = best;
  s.landedTheta = Math.atan2(s.y - PY[best], s.x - PX[best]);
  s.status = 'crashed';
  s.crashReason = reason;
  s.throttle = 0;
  placeOnBody(w);
}

export function destroyShip(w: World, reason: string): void {
  if (w.ship.status === 'flying') crashAtNearest(w, reason);
  else {
    w.ship.status = 'crashed';
    w.ship.crashReason = reason;
  }
}

function needsFineStep(w: World, c: Controls): boolean {
  const s = w.ship;
  if (c.throttle > 0 && s.fuel > 0) return true;
  bodyPositions(w.time, GX, GY);
  for (let i = 0; i < BODY_COUNT; i++) {
    const b = BODIES[i];
    if (!b.atmosphere) continue;
    if (Math.hypot(s.x - GX[i], s.y - GY[i]) - b.radius < atmosphereTop(b)) return true;
  }
  return false;
}

/** True when drag or thrust forces the simulation to run in real time. */
export function realTimeOnly(w: World, c: Controls): boolean {
  return w.ship.status === 'flying' && needsFineStep(w, c);
}

const MIN_CHILD_ORBIT: number[] = BODIES.map((b) =>
  Math.min(b.soi, ...BODIES.filter((c) => c.parentIndex === b.index).map((c) => c.orbitRadius)),
);

export interface RailsInfo {
  ref: number;
  el: OrbitElements;
  rx: number;
  ry: number;
  rvx: number;
  rvy: number;
}

/**
 * A ship in a stable orbit well inside its body's sphere of influence, clear of
 * the atmosphere and surface, can be advanced analytically instead of stepped.
 */
export function railsInfo(x: number, y: number, vx: number, vy: number, t: number): RailsInfo | null {
  const ref = referenceBody(x, y, t);
  if (ref === 0) return null;
  bodyStates(t, PX, PY, VX, VY);
  const b = BODIES[ref];
  const rx = x - PX[ref];
  const ry = y - PY[ref];
  const rvx = vx - VX[ref];
  const rvy = vy - VY[ref];
  const el = orbitElements(rx, ry, rvx, rvy, b.gm);
  if (!el.bound || el.apoapsis === null) return null;
  // Above the top of the atmosphere there is no drag at all, so such an orbit is stable.
  const clear = b.atmosphere ? atmosphereTop(b) + 2 : b.terrainAmp * 2 + LEG_LENGTH + 10;
  if (el.periapsis - b.radius < clear) return null;
  if (el.apoapsis > 0.3 * MIN_CHILD_ORBIT[ref]) return null;
  return { ref, el, rx, ry, rvx, rvy };
}

/** State of a ship on rails around `ref`, dt after the given relative state, in inertial coordinates. */
export function railsState(ref: number, info: RailsInfo, t: number, dt: number): [number, number, number, number] {
  const [rx, ry, rvx, rvy] = keplerPropagate(info.rx, info.ry, info.rvx, info.rvy, BODIES[ref].gm, dt);
  bodyStates(t + dt, PX, PY, VX, VY);
  return [PX[ref] + rx, PY[ref] + ry, VX[ref] + rvx, VY[ref] + rvy];
}

/**
 * Advances the world by dt seconds using adaptive steps. Stops after maxSteps
 * and returns the simulated time, which can be less than dt at high warp.
 */
export function advance(w: World, c: Controls, dt: number, maxSteps = 600): number {
  let remaining = dt;
  let steps = 0;
  if (remaining > 0.5 && w.ship.status === 'flying' && !(c.throttle > 0 && w.ship.fuel > 0)) {
    const s = w.ship;
    const info = railsInfo(s.x, s.y, s.vx, s.vy, w.time);
    if (info) {
      const [x, y, vx, vy] = railsState(info.ref, info, w.time, remaining);
      s.x = x;
      s.y = y;
      s.vx = vx;
      s.vy = vy;
      s.throttle = 0;
      s.heat *= Math.exp(-HEAT_COOL * remaining);
      w.time += remaining;
      return dt;
    }
  }
  while (remaining > 1e-9 && steps < maxSteps) {
    const s = w.ship;
    let h: number;
    if (s.status !== 'flying') {
      h = c.throttle > 0 && s.status === 'landed' ? FIXED_DT : remaining;
    } else if (needsFineStep(w, c)) {
      h = FIXED_DT;
    } else {
      h = suggestStep(s.x, s.y, s.vx, s.vy, w.time);
    }
    h = Math.min(h, remaining);
    step(w, c, h);
    remaining -= h;
    steps++;
  }
  return dt - remaining;
}

export interface RefState {
  index: number;
  /** Position and velocity relative to the reference body. */
  rx: number;
  ry: number;
  rvx: number;
  rvy: number;
  /** Distance to the centre and altitude above the mean radius. */
  r: number;
  alt: number;
}

/** Ship state relative to the body whose sphere of influence it is in. */
export function refState(w: World): RefState {
  const s = w.ship;
  const index = s.status === 'flying' ? referenceBody(s.x, s.y, w.time) : s.landedBody;
  bodyStates(w.time, PX, PY, VX, VY);
  const rx = s.x - PX[index];
  const ry = s.y - PY[index];
  const r = Math.hypot(rx, ry);
  return { index, rx, ry, rvx: s.vx - VX[index], rvy: s.vy - VY[index], r, alt: r - BODIES[index].radius };
}

/** Delta-v left in the tanks, by the rocket equation. */
export function deltaVLeft(w: World): number {
  const dry = w.stats.dryMass;
  return w.stats.ve * Math.log((dry + w.ship.fuel) / dry);
}

