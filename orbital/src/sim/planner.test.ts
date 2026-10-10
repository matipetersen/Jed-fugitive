import { describe, expect, it } from 'vitest';
import { BODIES, bodyPos, bodyVel, indexOf } from './bodies';
import { createWorld, type World } from './physics';
import { predict } from './predict';
import { refineNode, suggestTransfer } from './planner';
import { BASE_STATS } from './tech';
import { YEAR } from './units';

const EARTH = indexOf('earth');
const MOON = indexOf('moon');
const MARS = indexOf('mars');
const VENUS = indexOf('venus');
const JUPITER = indexOf('jupiter');

function leo(angle = 0.4, sigma = 1, t = 0): World {
  const w = createWorld(BASE_STATS, EARTH, Math.PI / 2, t);
  const r = 1250;
  const vc = Math.sqrt(BODIES[EARTH].gm / r);
  const p = bodyPos(EARTH, t);
  const v = bodyVel(EARTH, t);
  w.ship.status = 'flying';
  w.ship.x = p.x + r * Math.cos(angle);
  w.ship.y = p.y + r * Math.sin(angle);
  w.ship.vx = v.x - sigma * vc * Math.sin(angle);
  w.ship.vy = v.y + sigma * vc * Math.cos(angle);
  return w;
}

describe('planner', () => {
  it('suggests a lunar transfer that gets close to the Moon', () => {
    for (const sigma of [1, -1]) {
      const w = leo(0.4, sigma);
      const sug = suggestTransfer(w, MOON)!;
      expect(sug).not.toBeNull();
      expect(sug.dv).toBeGreaterThan(50);
      expect(sug.dv).toBeLessThan(80);
      const p = predict(w, { horizon: sug.eta * 1.4, node: sug.node, target: MOON });
      expect(p.targetClosest!.dist).toBeLessThan(BODIES[MOON].soi);
    }
  });

  it('refines a lunar transfer to a close flyby', () => {
    const w = leo();
    const sug = suggestTransfer(w, MOON)!;
    const r = refineNode(w, MOON, sug.node, sug.eta * 1.4);
    expect(r.closest).toBeLessThan(3000);
  });

  it('plans Earth to Mars, Venus and Jupiter transfers with energy in the right range', () => {
    const w = leo();
    for (const [target, minDv, maxDv] of [[MARS, 50, 110], [VENUS, 30, 110], [JUPITER, 100, 160]] as const) {
      const sug = suggestTransfer(w, target)!;
      expect(sug.dv).toBeGreaterThan(minDv);
      expect(sug.dv).toBeLessThan(maxDv);
      expect(sug.tWindow).toBeGreaterThanOrEqual(0);
      expect(sug.tWindow).toBeLessThan(3 * YEAR);
    }
  });

  it('refines the Mars transfer into the Mars sphere of influence', () => {
    const w = leo();
    const sug = suggestTransfer(w, MARS)!;
    const horizon = sug.eta * 1.2 + (sug.node.t - w.time);
    const first = predict(w, { horizon, node: sug.node, target: MARS });
    const r = refineNode(w, MARS, sug.node, horizon, 600);
    expect(r.closest).toBeLessThan(first.targetClosest!.dist);
    expect(r.closest).toBeLessThan(BODIES[MARS].soi);
  });
});

import { advance, refState, step as physStep, FIXED_DT } from './physics';
import { nodeVector } from './predict';
import { wrapAngle } from './vec';

describe('mission bot', () => {
  it('flies a lunar transfer with a finite burn and enters the Moon sphere of influence', () => {
    const w = leo();
    const sug = suggestTransfer(w, MOON)!;
    const r = refineNode(w, MOON, sug.node, sug.eta * 1.4);
    const node = r.node;
    const none = { throttle: 0, turn: 0 };
    // Warp to just before the node, then burn centred on it.
    const mass = w.stats.dryMass + w.ship.fuel;
    const impulse = nodeVector(w.ship.x, w.ship.y, w.ship.vx, w.ship.vy, w.time, node);
    const burnTime = (Math.hypot(impulse.x, impulse.y) * mass) / w.stats.thrust;
    advance(w, none, Math.max(0, node.t - burnTime / 2 - w.time), 100);
    const dv = nodeVector(w.ship.x, w.ship.y, w.ship.vx, w.ship.vy, w.time, node);
    const v0 = { x: w.ship.vx, y: w.ship.vy };
    const heading = Math.atan2(dv.y, dv.x);
    const target = Math.hypot(dv.x, dv.y);
    w.ship.angle = heading;
    let burned = 0;
    for (let i = 0; i < 120 * 30 && burned < target; i++) {
      const err = wrapAngle(heading - w.ship.angle);
      physStep(w, { throttle: 1, turn: Math.max(-1, Math.min(1, err * 6)) }, FIXED_DT);
      burned = Math.hypot(w.ship.vx - v0.x, w.ship.vy - v0.y);
    }
    expect(burned).toBeGreaterThan(target * 0.9);
    // Mid-course correction: refine a small node shortly after the burn, as a player would.
    advance(w, none, 60, 100);
    const corr = refineNode(w, MOON, { t: w.time + 120, prograde: 0, radial: 0 }, sug.eta * 1.2, 300);
    expect(corr.closest).toBeLessThan(BODIES[MOON].soi);
    advance(w, none, 120, 100);
    const cv = nodeVector(w.ship.x, w.ship.y, w.ship.vx, w.ship.vy, w.time, corr.node);
    w.ship.vx += cv.x;
    w.ship.vy += cv.y;
    // Coast and watch the closest approach to the Moon.
    let closest = Infinity;
    const t1 = w.time + sug.eta * 1.5;
    while (w.time < t1 && w.ship.status === 'flying') {
      advance(w, none, 20, 400);
      const m = bodyPos(MOON, w.time);
      closest = Math.min(closest, Math.hypot(w.ship.x - m.x, w.ship.y - m.y));
    }
    expect(closest).toBeLessThan(BODIES[MOON].soi);
    expect(refState(w).index === MOON || closest < BODIES[MOON].soi).toBe(true);
  });
});
