import { BODIES, BODY_COUNT, bodyPositions, bodyStates, referenceBody } from './bodies';
import { atmosphereTop } from './atmosphere';
import { orbitElements } from './orbit';
import { type World, gravity, railsInfo, railsState, refState, suggestStep } from './physics';
import { YEAR } from './units';

export interface BurnNode {
  /** Absolute game time of the burn. */
  t: number;
  /** Delta-v along the velocity relative to the reference body, u/s. */
  prograde: number;
  /** Delta-v away from the reference body, u/s. */
  radial: number;
}

export interface Encounter {
  body: number;
  tEnter: number;
  tClosest: number;
  /** Closest distance to the body centre during the pass. */
  closest: number;
  impact: boolean;
}

export interface Prediction {
  t: Float64Array;
  x: Float64Array;
  y: Float64Array;
  count: number;
  /** Index of the first point after the node burn, or -1. */
  nodeIndex: number;
  /** Inertial delta-v vector of the node, if any. */
  nodeDv: { x: number; y: number } | null;
  /** Position of the node on the path. */
  nodePos: { x: number; y: number } | null;
  encounters: Encounter[];
  /** Closest approach to the chosen target body over the whole path. */
  targetClosest: { dist: number; t: number; dx: number; dy: number } | null;
  end: 'horizon' | 'steps' | 'impact' | 'atmosphere';
  endBody: number;
}

export interface PredictOptions {
  horizon: number;
  node?: BurnNode | null;
  target?: number;
  maxSteps?: number;
}

const PX = new Float64Array(BODY_COUNT);
const PY = new Float64Array(BODY_COUNT);

const SVX = new Float64Array(BODY_COUNT);
const SVY = new Float64Array(BODY_COUNT);

/** Inertial delta-v vector for a node given the ship state at the node time. */
export function nodeVector(x: number, y: number, vx: number, vy: number, t: number, node: BurnNode): { x: number; y: number } {
  const ref = referenceBody(x, y, t);
  bodyStates(t, PX, PY, SVX, SVY);
  const rx = x - PX[ref];
  const ry = y - PY[ref];
  const rvx = vx - SVX[ref];
  const rvy = vy - SVY[ref];
  const sp = Math.hypot(rvx, rvy) || 1;
  const rr = Math.hypot(rx, ry) || 1;
  return {
    x: (rvx / sp) * node.prograde + (rx / rr) * node.radial,
    y: (rvy / sp) * node.prograde + (ry / rr) * node.radial,
  };
}

/** Coasting trajectory (no thrust, no drag) from the ship's current state. */
export function predict(w: World, opts: PredictOptions, reuse?: Prediction): Prediction {
  const maxSteps = opts.maxSteps ?? 6000;
  const fits = reuse !== undefined && reuse.t.length >= maxSteps + 2;
  const out: Prediction = {
    t: fits ? reuse.t : new Float64Array(maxSteps + 2),
    x: fits ? reuse.x : new Float64Array(maxSteps + 2),
    y: fits ? reuse.y : new Float64Array(maxSteps + 2),
    count: 0,
    nodeIndex: -1,
    nodeDv: null,
    nodePos: null,
    encounters: [],
    targetClosest: null,
    end: 'horizon',
    endBody: -1,
  };
  const s = w.ship;
  if (s.status !== 'flying') return out;

  let x = s.x;
  let y = s.y;
  let vx = s.vx;
  let vy = s.vy;
  let t = w.time;
  const tEnd = t + opts.horizon;
  const node = opts.node && opts.node.t > t ? opts.node : null;
  let nodeDone = !node;

  const push = (): void => {
    out.t[out.count] = t;
    out.x[out.count] = x;
    out.y[out.count] = y;
    out.count++;
  };
  push();

  // A stable parking orbit before the node is traced analytically, which makes
  // waiting for a launch window cheap.
  if (node) {
    const info = railsInfo(x, y, vx, vy, t);
    if (info && info.el.period) {
      const total = node.t - t;
      const period = info.el.period;
      const spanA = Math.min(period * 1.02, total);
      const n = 200;
      const sample = (dt: number): void => {
        const q = railsState(info.ref, info, t0, dt);
        out.t[out.count] = t0 + dt;
        out.x[out.count] = q[0];
        out.y[out.count] = q[1];
        out.count++;
      };
      const t0 = t;
      for (let k = 1; k <= n; k++) sample((spanA * k) / n);
      if (total > spanA) {
        const partial = total % period;
        for (let k = 1; k <= 120; k++) sample(total - partial + (partial * k) / 120);
      }
      const q = railsState(info.ref, info, t0, total);
      x = q[0];
      y = q[1];
      vx = q[2];
      vy = q[3];
      t = node.t;
    }
  }

  // Per-body encounter tracking.
  const inside = new Array<{ tEnter: number; tClosest: number; closest: number } | null>(BODY_COUNT).fill(null);
  const target = opts.target ?? -1;

  let steps = 0;
  while (t < tEnd && steps < maxSteps) {
    let h = suggestStep(x, y, vx, vy, t);
    if (!nodeDone && node && t + h >= node.t) h = node.t - t;
    h = Math.min(h, tEnd - t);

    if (h > 0) {
      const g0 = gravity(x, y, t);
      vx += g0.x * h * 0.5;
      vy += g0.y * h * 0.5;
      x += vx * h;
      y += vy * h;
      const g1 = gravity(x, y, t + h);
      vx += g1.x * h * 0.5;
      vy += g1.y * h * 0.5;
      t += h;
    }
    steps++;

    if (!nodeDone && node && t >= node.t - 1e-9) {
      const dv = nodeVector(x, y, vx, vy, t, node);
      out.nodeDv = dv;
      out.nodePos = { x, y };
      vx += dv.x;
      vy += dv.y;
      nodeDone = true;
      push();
      out.nodeIndex = out.count - 1;
      continue;
    }
    push();

    bodyPositions(t, PX, PY);
    let stop = false;
    for (let i = 1; i < BODY_COUNT; i++) {
      const b = BODIES[i];
      const d = Math.hypot(x - PX[i], y - PY[i]);
      if (i === target) {
        if (!out.targetClosest || d < out.targetClosest.dist) out.targetClosest = { dist: d, t, dx: x - PX[i], dy: y - PY[i] };
      }
      let e = inside[i];
      if (d < b.soi) {
        if (!e) e = inside[i] = { tEnter: t, tClosest: t, closest: d };
        if (d < e.closest) {
          e.closest = d;
          e.tClosest = t;
        }
        const hit = d < b.radius + b.terrainAmp;
        const atmo = b.atmosphere && d - b.radius < atmosphereTop(b) * 0.4;
        if (hit || atmo) {
          out.encounters.push({ body: i, tEnter: e.tEnter, tClosest: e.tClosest, closest: e.closest, impact: !!hit });
          inside[i] = null;
          out.end = hit ? 'impact' : 'atmosphere';
          out.endBody = i;
          stop = true;
          break;
        }
      } else if (e) {
        out.encounters.push({ body: i, tEnter: e.tEnter, tClosest: e.tClosest, closest: e.closest, impact: false });
        inside[i] = null;
      }
    }
    if (stop) return out;
    if (Math.hypot(x - PX[0], y - PY[0]) < BODIES[0].radius) {
      out.end = 'impact';
      out.endBody = 0;
      return out;
    }
  }
  if (steps >= maxSteps) out.end = 'steps';
  for (let i = 1; i < BODY_COUNT; i++) {
    const e = inside[i];
    if (e) out.encounters.push({ body: i, tEnter: e.tEnter, tClosest: e.tClosest, closest: e.closest, impact: false });
  }
  return out;
}

export const HORIZON_LEVELS: { label: string; seconds: number }[] = [
  { label: 'AUTO', seconds: 0 },
  { label: '10d', seconds: YEAR / 36.5 },
  { label: '1a', seconds: YEAR },
  { label: '5a', seconds: YEAR * 5 },
  { label: '20a', seconds: YEAR * 20 },
  { label: '60a', seconds: YEAR * 60 },
];

/** Default look-ahead: about one orbit when bound, a few years when escaping. */
export function autoHorizon(w: World): number {
  const rs = refState(w);
  const ref = BODIES[rs.index];
  const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, ref.gm);
  if (el.bound && el.period) {
    if (ref.index === 0) return Math.min(el.period * 1.02, YEAR * 80);
    if ((el.apoapsis ?? 0) < ref.soi * 0.8) return Math.max(el.period * 1.05, 10);
  }
  return YEAR * 3;
}
