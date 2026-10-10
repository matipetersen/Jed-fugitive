import { BODIES, SUN } from './bodies';
import { atmosphereTop } from './atmosphere';
import { keplerPropagate, orbitElements } from './orbit';
import { type World, refState } from './physics';
import { type BurnNode, predict } from './predict';
import { TAU } from './units';

export interface Suggestion {
  node: BurnNode;
  /** Time of the ideal phase alignment. */
  tWindow: number;
  /** Delta-v of the departure burn. */
  dv: number;
  /** Transfer time in seconds. */
  eta: number;
  /** Excess speed relative to the departure body (heliocentric legs only). */
  vInf: number;
}

/** Smallest t >= now with angle(t) = a0 + rate * (t - now) congruent to target mod 2pi. */
export function solveAngle(a0: number, rate: number, target: number, now: number): number {
  let diff = (target - a0) % TAU;
  if (diff < 0) diff += TAU;
  if (rate >= 0) return now + diff / rate;
  return now + (diff - TAU) / rate;
}

const wrap2 = (a: number): number => {
  const r = a % TAU;
  return r < 0 ? r + TAU : r;
};

/**
 * Suggests a departure burn from a roughly circular parking orbit towards a
 * target body, using a Hohmann transfer between circular coplanar orbits.
 * Only an estimate: refine it with `refineNode`.
 */
export function suggestTransfer(w: World, target: number): Suggestion | null {
  return suggestCore(w, target, null);
}

/** Circular-orbit analogue of a transfer, with the parking orbit's radius given explicitly. */
function suggestCircular(w: World, target: number, radius: number): Suggestion | null {
  return suggestCore(w, target, radius);
}

function suggestCore(w: World, target: number, radiusOverride: number | null): Suggestion | null {
  const s = w.ship;
  if (s.status !== 'flying') return null;
  const rs = refState(w);
  const A = BODIES[rs.index];
  const T = BODIES[target];
  if (!T || rs.index === target || A.star) return null;
  const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, A.gm);
  if (!el.bound) return null;
  if (radiusOverride === null && el.e > 0.03 && el.period) return suggestFromEllipse(w, target, el, A.gm);
  const r0 = radiusOverride ?? Math.hypot(rs.rx, rs.ry);
  const vc = Math.sqrt(A.gm / r0);
  const sigma = el.h >= 0 ? 1 : -1;
  const omegaShip = (sigma * vc) / r0;
  const thetaNow = Math.atan2(rs.ry, rs.rx);
  const now = w.time;

  if (T.parentIndex === A.index) {
    // Moon-style transfer: apoapsis at the target's orbit.
    const at = (r0 + T.orbitRadius) / 2;
    const vp = Math.sqrt(A.gm * (2 / r0 - 1 / at));
    const eta = Math.PI * Math.sqrt((at * at * at) / A.gm);
    // Ship angle at burn must equal the target angle at arrival plus pi.
    // thetaNow + omegaShip*(t-now) = phase0 + omegaT*t + omegaT*eta + pi
    const rate = omegaShip - T.omega;
    const target0 = T.phase0 + T.omega * now + T.omega * eta + Math.PI;
    const tBurn = solveAngle(thetaNow, rate, target0, now);
    return { node: { t: tBurn, prograde: vp - vc, radial: 0 }, tWindow: tBurn, dv: vp - vc, eta, vInf: 0 };
  }

  if (A.parentIndex === SUN && T.parentIndex === SUN) {
    const gms = BODIES[SUN].gm;
    const a1 = A.orbitRadius;
    const a2 = T.orbitRadius;
    const at = (a1 + a2) / 2;
    const vDep = Math.sqrt(gms * (2 / a1 - 1 / at));
    const vA = Math.sqrt(gms / a1);
    const vInf = vDep - vA;
    const eta = Math.PI * Math.sqrt((at * at * at) / gms);
    const lead = wrap2(Math.PI - T.omega * eta);
    // Phase of target minus departure body must equal lead.
    const dPhase0 = T.phase0 - A.phase0;
    const dRate = T.omega - A.omega;
    const tWin = solveAngle(dPhase0 + dRate * now, dRate, lead, now);
    const vInfAbs = Math.abs(vInf);
    const e = 1 + (r0 * vInfAbs * vInfAbs) / A.gm;
    const nuInf = Math.acos(-1 / e);
    // Outgoing asymptote must point along (outward) or against (inward) the body's velocity.
    const dirAt = (t: number): number => A.phase0 + A.omega * t + Math.PI / 2 + (vInf < 0 ? Math.PI : 0);
    // Iterate once: the direction depends on the burn time, which depends on the direction.
    const thetaWin = thetaNow + omegaShip * (tWin - now);
    let tBurn = tWin;
    for (let k = 0; k < 3; k++) {
      const thetaP = dirAt(tBurn) - sigma * nuInf;
      tBurn = solveAngle(thetaWin, omegaShip, thetaP, tWin);
    }
    const vp = Math.sqrt(vInfAbs * vInfAbs + (2 * A.gm) / r0);
    return { node: { t: tBurn, prograde: vp - vc, radial: 0 }, tWindow: tWin, dv: vp - vc, eta, vInf };
  }
  return null;
}

/**
 * Planner for a parking orbit that is not circular. The burn time is searched
 * over one revolution around the window of the circular analogue, with the
 * delta-v set by energy, and every candidate is scored by the real predictor.
 */
function suggestFromEllipse(w: World, target: number, el: ReturnType<typeof orbitElements>, gm: number): Suggestion | null {
  const rs = refState(w);
  const A = BODIES[rs.index];
  const T = BODIES[target];
  const period = el.period!;
  const now = w.time;
  const a = (el.periapsis + (el.apoapsis ?? el.periapsis)) / 2;

  // Circular analogue gives the rough window and the flight time.
  const analogue = suggestCircular(w, target, a);
  if (!analogue) return null;
  const moonStyle = T.parentIndex === A.index;
  const vInfWanted = Math.abs(analogue.vInf);

  let best: { node: BurnNode; d: number } | null = null;
  const horizonBase = analogue.eta * 1.3;
  for (let k = 0; k <= 32; k++) {
    const t = analogue.node.t + ((k / 16 - 1) * period);
    if (t < now + 1) continue;
    const [x, y, vx, vy] = keplerPropagate(rs.rx, rs.ry, rs.rvx, rs.rvy, gm, t - now);
    const r = Math.hypot(x, y);
    const v = Math.hypot(vx, vy);
    let dv: number;
    if (moonStyle) {
      // Apoapsis at the target's orbit: bisection on prograde delta-v.
      let lo = 0;
      let hi = 400;
      for (let i = 0; i < 40; i++) {
        const mid = (lo + hi) / 2;
        const k2 = 1 + mid / v;
        const e2 = orbitElements(x, y, vx * k2, vy * k2, gm);
        const apo = e2.apoapsis ?? Infinity;
        if (apo < T.orbitRadius) lo = mid;
        else hi = mid;
      }
      dv = (lo + hi) / 2;
    } else {
      dv = Math.sqrt(vInfWanted * vInfWanted + (2 * gm) / r) - v;
    }
    if (!(dv > 0) || dv > 600) continue;
    const node: BurnNode = { t, prograde: dv, radial: 0 };
    const p = predict(w, { horizon: t - now + horizonBase, node, target, maxSteps: 4000 });
    const d = p.targetClosest ? p.targetClosest.dist : Infinity;
    if (!best || d < best.d) best = { node, d };
  }
  if (!best) return null;
  return { node: best.node, tWindow: analogue.tWindow, dv: best.node.prograde, eta: analogue.eta, vInf: analogue.vInf };
}

/** Cost used by the refiner: relative distance error of the closest approach. */
function goalDistance(target: number): number {
  const T = BODIES[target];
  return Math.max(T.radius * 5, 1500);
}

export interface RefineResult {
  node: BurnNode;
  closest: number;
  evaluations: number;
}

/**
 * Steers the closest approach to the target by adjusting the node's prograde
 * and radial delta-v. Newton iterations on the miss vector at closest approach,
 * with a pattern search as a fallback when the Jacobian is degenerate.
 */
export function refineNode(w: World, target: number, start: BurnNode, horizon: number, maxEvals = 400): RefineResult {
  const goal = goalDistance(target);
  let evals = 0;
  const miss = (n: BurnNode): { dx: number; dy: number; d: number } => {
    evals++;
    const p = predict(w, { horizon, node: n, target, maxSteps: 4000 });
    const c = p.targetClosest;
    return c ? { dx: c.dx, dy: c.dy, d: c.dist } : { dx: 1e12, dy: 0, d: 1e12 };
  };
  const err = (m: { d: number }): number => Math.abs(m.d - goal) / goal;

  let best = { ...start };
  let bm = miss(best);
  const eps = 0.15;
  for (let it = 0; it < 14 && evals < maxEvals; it++) {
    if (err(bm) < 0.05) break;
    const mp = miss({ ...best, prograde: best.prograde + eps });
    const mr = miss({ ...best, radial: best.radial + eps });
    const j00 = (mp.dx - bm.dx) / eps;
    const j10 = (mp.dy - bm.dy) / eps;
    const j01 = (mr.dx - bm.dx) / eps;
    const j11 = (mr.dy - bm.dy) / eps;
    const det = j00 * j11 - j01 * j10;
    if (Math.abs(det) < 1e-9) break;
    // Desired miss: same direction, goal distance (or unchanged if already inside).
    const k = bm.d > 1e-6 ? goal / bm.d : 1;
    const rx = bm.dx * k - bm.dx;
    const ry = bm.dy * k - bm.dy;
    const dp = (j11 * rx - j01 * ry) / det;
    const dr = (-j10 * rx + j00 * ry) / det;
    let improved = false;
    for (let damp = 1; damp > 0.05 && evals < maxEvals; damp *= 0.5) {
      const n = { ...best, prograde: best.prograde + dp * damp, radial: best.radial + dr * damp };
      const m = miss(n);
      if (err(m) < err(bm)) {
        best = n;
        bm = m;
        improved = true;
        break;
      }
    }
    if (!improved) break;
  }

  // Fallback: pattern search over time and delta-v if Newton did not converge.
  if (err(bm) >= 0.05) {
    const steps = [2, 0.5, 0.5];
    const scales = [1, 1, 1];
    for (let round = 0; round < 40 && evals < maxEvals; round++) {
      let improved = false;
      for (let k = 0; k < 3 && evals < maxEvals; k++) {
        for (const dir of [1, -1]) {
          const n = { ...best };
          const d = steps[k] * scales[k] * dir;
          if (k === 0) n.t += d;
          else if (k === 1) n.prograde += d;
          else n.radial += d;
          const m = miss(n);
          if (err(m) < err(bm)) {
            best = n;
            bm = m;
            improved = true;
            break;
          }
        }
      }
      if (!improved) {
        for (let k = 0; k < 3; k++) scales[k] *= 0.5;
        if (scales[0] < 1e-3) break;
      }
      if (err(bm) < 0.05) break;
    }
  }
  return { node: best, closest: bm.d, evaluations: evals };
}

export interface CircPlan {
  node: BurnNode;
  apoapsisTime: number;
  radius: number;
}

/**
 * Burn that circularises the current orbit. Normally that is a prograde burn at
 * apoapsis. If the ship would hit the ground or atmosphere before getting
 * there, the burn happens right away and also cancels the sinking.
 */
export function planCircularizeOrReason(w: World): CircPlan | { reason: string } {
  const s = w.ship;
  if (s.status !== 'flying') return { reason: 'La nave tiene que estar en vuelo.' };
  const rs = refState(w);
  const body = BODIES[rs.index];
  const gm = body.gm;
  const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, gm);
  if (rs.index === 0) return { reason: 'Es una órbita solar: usá AUTO para planificar.' };
  if (!el.bound || !el.period) return { reason: 'No es una órbita cerrada: vas demasiado rápido.' };
  const top = body.atmosphere ? atmosphereTop(body) : 0;
  const unsafe = el.periapsis - body.radius < top + 2;
  if (el.e < 0.01 && !unsafe) return { reason: 'La órbita ya es circular.' };
  const T = el.period;
  const radiusAt = (dt: number): number => {
    const [x, y] = keplerPropagate(rs.rx, rs.ry, rs.rvx, rs.rvy, gm, dt);
    return Math.hypot(x, y);
  };
  const n = 120;
  let bestK = 0;
  let bestR = -1;
  for (let k = 0; k <= n; k++) {
    const r = radiusAt((k / n) * T);
    if (r > bestR) {
      bestR = r;
      bestK = k;
    }
  }
  let lo = ((bestK - 1) / n) * T;
  let hi = ((bestK + 1) / n) * T;
  for (let i = 0; i < 40; i++) {
    const m1 = lo + (hi - lo) / 3;
    const m2 = hi - (hi - lo) / 3;
    if (radiusAt(m1) < radiusAt(m2)) lo = m1;
    else hi = m2;
  }
  let dtApo = (lo + hi) / 2;
  if (dtApo < 0) dtApo += T;

  // When does the ship reach the ground? Only matters if the orbit is unsafe.
  let dtGround = Infinity;
  if (unsafe) {
    for (let k = 1; k <= 240; k++) {
      const dt = (k / 240) * T;
      if (radiusAt(dt) < body.radius + Math.max(10, top)) {
        dtGround = dt;
        break;
      }
    }
  }

  // Apoapsis only just passed counts as "now" too: waiting a whole orbit would sink into the air.
  const justPassed = T - dtApo < 4;
  if (dtApo > 1.5 && !justPassed && dtApo < dtGround - 2) {
    const [x, y, vx, vy] = keplerPropagate(rs.rx, rs.ry, rs.rvx, rs.rvy, gm, dtApo);
    const r = Math.hypot(x, y);
    return { node: { t: w.time + dtApo, prograde: Math.sqrt(gm / r) - Math.hypot(vx, vy), radial: 0 }, apoapsisTime: w.time + dtApo, radius: r };
  }

  // Burn almost now: aim for a circular orbit at the current height, with the vertical speed cancelled.
  const lead = 1.2;
  const [x, y, vx, vy] = keplerPropagate(rs.rx, rs.ry, rs.rvx, rs.rvy, gm, lead);
  const r = Math.hypot(x, y);
  if (r - body.radius < top + 60) return { reason: 'Estás muy bajo: subí más antes de circularizar.' };
  const sense = el.h >= 0 ? 1 : -1;
  const tx = (-y / r) * sense;
  const ty = (x / r) * sense;
  const vc = Math.sqrt(gm / r);
  const dvx = tx * vc - vx;
  const dvy = ty * vc - vy;
  // Decompose into the node's axes: along the velocity and away from the body.
  const sp = Math.hypot(vx, vy) || 1;
  const ux = vx / sp;
  const uy = vy / sp;
  const rx = x / r;
  const ry = y / r;
  const det = ux * ry - uy * rx;
  if (Math.abs(det) < 1e-3) return { reason: 'Geometría degenerada: esperá un momento y probá de nuevo.' };
  const prograde = (dvx * ry - dvy * rx) / det;
  const radial = (ux * dvy - uy * dvx) / det;
  return { node: { t: w.time + lead, prograde, radial }, apoapsisTime: w.time + lead, radius: r };
}

/** Circularisation plan, or null when there is nothing sensible to do. */
export function planCircularize(w: World): CircPlan | null {
  const r = planCircularizeOrReason(w);
  return 'node' in r ? r : null;
}
