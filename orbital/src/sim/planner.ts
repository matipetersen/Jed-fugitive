import { BODIES, SUN } from './bodies';
import { orbitElements } from './orbit';
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
  const s = w.ship;
  if (s.status !== 'flying') return null;
  const rs = refState(w);
  const A = BODIES[rs.index];
  const T = BODIES[target];
  if (!T || rs.index === target || A.star) return null;
  const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, A.gm);
  if (!el.bound) return null;
  const r0 = Math.hypot(rs.rx, rs.ry);
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
