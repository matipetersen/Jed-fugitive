import { type Arena, SHIP_R } from './arena';
import { type Controls, type Ship } from './types';

const TAU = Math.PI * 2;
const wrap = (a: number): number => {
  let r = (a + Math.PI) % TAU;
  if (r < 0) r += TAU;
  return r - Math.PI;
};
const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

const G = { x: 0, y: 0 };
const PT = { x: 0, y: 0 };
const GT = { x: 0, y: 0 };

export interface LandTarget {
  body: number;
  pad: number;
  /** A ring that hangs over the pad still has to be passed before touching down. */
  ring: boolean;
}

/** The pad to land on right now, if the ship is close enough for guidance to take over from the route planner. */
export function landTarget(arena: Arena, ship: Ship): LandTarget | null {
  const n = ship.nextGate;
  const wp = n < ship.route.length ? ship.route[n].land : null;
  if (wp) {
    arena.padPoint(wp.body, wp.pad, PT);
    return Math.hypot(ship.x - PT.x, ship.y - PT.y) < 700 ? { body: wp.body, pad: wp.pad, ring: false } : null;
  }
  if (n < ship.route.length - 1) return null;
  arena.padPoint(ship.finishPad.body, ship.finishPad.pad, PT);
  if (n < ship.route.length && Math.hypot(ship.x - PT.x, ship.y - PT.y) >= 700) return null;
  return { body: ship.finishPad.body, pad: ship.finishPad.pad, ring: n < ship.route.length };
}

/**
 * Landing guidance in the frame of the target body: line up over the pad, then come down
 * at a speed that shrinks with height. Used by the rival and by the practice bots.
 */
export function landControl(arena: Arena, ship: Ship, tgt: LandTarget): Controls {
  const bi = tgt.body;
  const body = arena.bodies[bi];
  const ang = arena.padPoint(tgt.body, tgt.pad, PT);
  const nx = Math.cos(ang);
  const ny = Math.sin(ang);
  const tx = -ny;
  const ty = nx;
  const qx = ship.x - arena.cur.x[bi];
  const qy = ship.y - arena.cur.y[bi];
  const vx = ship.vx - arena.cur.vx[bi];
  const vy = ship.vy - arena.cur.vy[bi];
  const h = qx * nx + qy * ny - (body.def.r + SHIP_R);
  const l = qx * tx + qy * ty;
  const vn = vx * nx + vy * ny;
  const vt = vx * tx + vy * ty;
  const amax = Math.max(20, ship.stats.thrust * 0.75 - body.def.g);

  // Until the last gate is behind us, the target is the gate (it hangs over the pad); then it is the pad itself.
  let tgtL = 0;
  let tgtH = 0;
  const pending = tgt.ring;
  if (pending) {
    arena.gatePos(ship.nextGate, GT, arena.cur, ship.route);
    const gx = GT.x - arena.cur.x[bi];
    const gy = GT.y - arena.cur.y[bi];
    tgtL = gx * tx + gy * ty;
    tgtH = gx * nx + gy * ny - (body.def.r + SHIP_R);
  }
  const dl = l - tgtL;
  // Over the target when the sideways offset is small for the height; otherwise stay up and slide across.
  const aligned = Math.abs(dl) < 16 + Math.abs(h - tgtH) * 0.3;
  let vtDes = clamp(-1.5 * dl, -110, 110);
  const vtMax = Math.sqrt(2 * 0.45 * amax * Math.abs(dl));
  vtDes = clamp(vtDes, -vtMax, vtMax);
  let vnDes: number;
  if (pending) {
    if (aligned) vnDes = clamp((tgtH - h) * 0.7, -35, 45);
    else vnDes = clamp((tgtH + 60 + Math.min(160, Math.abs(dl) * 0.2) - h) * 0.8, -30, 45);
    vnDes = Math.max(vnDes, -Math.sqrt(2 * 0.3 * amax * Math.max(h - 15, 0)) - 4);
  } else if (aligned) {
    vnDes = -clamp(0.5 * h + 5, 5, 36);
    // Never ask for a descent the engine cannot stop in time.
    vnDes = Math.max(vnDes, -Math.sqrt(2 * 0.3 * amax * Math.max(h - 15, 0)) - 4);
  } else {
    const hold = 80 + Math.min(160, Math.abs(dl) * 0.2);
    vnDes = clamp((hold - h) * 0.8, -30, 45);
  }
  const k = 2.2;
  let ax = k * (vtDes - vt) * tx + k * (vnDes - vn) * nx;
  let ay = k * (vtDes - vt) * ty + k * (vnDes - vn) * ny;
  // On the far side of the body: fly round it at a safe height instead of straight through.
  const dist = Math.hypot(qx, qy);
  let around = false;
  if (qx * nx + qy * ny < body.def.r * 0.4) {
    around = true;
    const polar = Math.atan2(qy, qx);
    const dir = Math.sign(wrap(ang - polar)) || 1;
    const orbit = body.def.r + 120;
    const ux = qx / dist;
    const uy = qy / dist;
    const sp = 70;
    const wx = -uy * dir * sp + ux * clamp((orbit - dist) * 0.8, -40, 40);
    const wy = ux * dir * sp + uy * clamp((orbit - dist) * 0.8, -40, 40);
    ax = k * (wx - vx);
    ay = k * (wy - vy);
  }
  arena.gravity(ship.x, ship.y, arena.cur, G);
  const Tx = ax - G.x;
  const Ty = ay - G.y;
  let want = Math.atan2(Ty, Tx);
  const mag = Math.hypot(Tx, Ty);
  // Close to the ground the nose must stay near vertical, whatever the sideways error.
  if (h < 60 && aligned && !pending && !around) want = ang + clamp(wrap(want - ang), -0.4, 0.4);
  const err = wrap(want - ship.angle);
  const align = clamp(1.4 - Math.abs(err) / 0.5, 0, 1);
  return { throttle: clamp(mag / ship.stats.thrust, 0, 1) * align, turn: clamp(err * 6, -1, 1) };
}
