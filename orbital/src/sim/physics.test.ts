import { describe, expect, it } from 'vitest';
import { BODIES, body, bodyPos, bodyVel, indexOf, referenceBody } from './bodies';
import { orbitElements } from './orbit';
import { FIXED_DT, advance, createWorld, deltaVLeft, refState, step, type World } from './physics';
import { AU, YEAR, T_S } from './units';
import { BASE_STATS } from './tech';

const EARTH = indexOf('earth');
const MOON = indexOf('moon');

/** Puts the ship in a circular orbit of radius r around body i, counter-clockwise. */
function orbitWorld(i: number, r: number, t = 0, angle = 0): World {
  const w = createWorld(BASE_STATS, EARTH, Math.PI / 2, t);
  const b = BODIES[i];
  const p = bodyPos(i, t);
  const v = bodyVel(i, t);
  const vc = Math.sqrt(b.gm / r);
  w.ship.status = 'flying';
  w.ship.x = p.x + r * Math.cos(angle);
  w.ship.y = p.y + r * Math.sin(angle);
  w.ship.vx = v.x - vc * Math.sin(angle);
  w.ship.vy = v.y + vc * Math.cos(angle);
  return w;
}

describe('solar system scale', () => {
  it('uses real periods and consistent Earth units', () => {
    expect(body('earth').radius).toBeCloseTo(1000, 3);
    expect(body('earth').surfaceGravity).toBeCloseTo(25, 6);
    expect(body('earth').period / YEAR).toBeCloseTo(1, 2);
    expect(body('mars').period / YEAR).toBeCloseTo(1.881, 2);
    expect(body('jupiter').period / YEAR).toBeCloseTo(11.86, 1);
    expect(body('pluto').period / YEAR).toBeGreaterThan(247);
    expect(body('moon').period * T_S / 86400).toBeCloseTo(27.3, 0);
    expect(body('earth').orbitRadius / AU).toBeCloseTo(1, 2);
  });

  it('finds the sphere of influence', () => {
    const e = bodyPos(EARTH, 0);
    expect(referenceBody(e.x + 1100, e.y, 0)).toBe(EARTH);
    const m = bodyPos(MOON, 0);
    expect(referenceBody(m.x + 500, m.y, 0)).toBe(MOON);
    expect(referenceBody(e.x + 1e6, e.y, 0)).toBe(0);
  });
});

describe('orbits', () => {
  it('holds a low Earth orbit for 20 revolutions', () => {
    const r = 1250;
    const w = orbitWorld(EARTH, r);
    const period = 2 * Math.PI * Math.sqrt((r * r * r) / body('earth').gm);
    const noThrust = { throttle: 0, turn: 0 };
    let minR = Infinity;
    let maxR = 0;
    const t0 = w.time;
    while (w.time - t0 < period * 20) {
      advance(w, noThrust, 1, 200);
      const rs = refState(w);
      minR = Math.min(minR, rs.r);
      maxR = Math.max(maxR, rs.r);
    }
    expect(w.ship.status).toBe('flying');
    expect((maxR - minR) / r).toBeLessThan(0.01);
  });

  it('keeps a heliocentric orbit for a year with adaptive steps', () => {
    const w = orbitWorld(0, 0.5 * AU);
    const noThrust = { throttle: 0, turn: 0 };
    const a = 0.5 * AU;
    let drift = 0;
    const end = YEAR;
    while (w.time < end) {
      advance(w, noThrust, 2000, 2000);
      drift = Math.max(drift, Math.abs(Math.hypot(w.ship.x, w.ship.y) - a) / a);
    }
    expect(drift).toBeLessThan(0.01);
  });

  it('computes elements relative to the reference body', () => {
    const w = orbitWorld(EARTH, 1300);
    const rs = refState(w);
    const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, body('earth').gm);
    expect(rs.index).toBe(EARTH);
    expect(el.e).toBeLessThan(1e-6);
    expect(el.periapsis).toBeCloseTo(1300, 3);
  });
});

describe('rocket and atmosphere', () => {
  it('lifts off the pad and stays landed without throttle', () => {
    const w = createWorld();
    for (let i = 0; i < 120; i++) step(w, { throttle: 0, turn: 0 }, FIXED_DT);
    expect(w.ship.status).toBe('landed');
    for (let i = 0; i < 240; i++) step(w, { throttle: 1, turn: 0 }, FIXED_DT);
    expect(w.ship.status).toBe('flying');
    expect(refState(w).alt).toBeGreaterThan(10);
  });

  it('has the expected delta-v budget', () => {
    const w = createWorld();
    expect(deltaVLeft(w)).toBeCloseTo(866 * Math.log(2), 0);
  });

  it('slows a falling ship in the atmosphere to near terminal speed', () => {
    const w = createWorld();
    const p = bodyPos(EARTH, 0);
    const v = bodyVel(EARTH, 0);
    w.ship.status = 'flying';
    w.ship.x = p.x;
    w.ship.y = p.y + 1000 + 90;
    w.ship.vx = v.x;
    w.ship.vy = v.y;
    w.ship.angle = -Math.PI / 2;
    const c = { throttle: 0, turn: 0 };
    let landedSpeed = 0;
    for (let i = 0; i < 120 * 60 && w.ship.status === 'flying'; i++) step(w, c, FIXED_DT);
    landedSpeed = w.ship.impactSpeed;
    expect(landedSpeed).toBeGreaterThan(40);
    expect(landedSpeed).toBeLessThan(90);
    expect(w.ship.status).toBe('crashed');
  });
});

import { autoHorizon, predict } from './predict';

describe('prediction', () => {
  it('traces a closed low orbit without impact', () => {
    const w = orbitWorld(EARTH, 1250);
    const p = predict(w, { horizon: autoHorizon(w) });
    expect(p.end).toBe('horizon');
    const e = (i: number) => bodyPos(EARTH, p.t[i]);
    for (let i = 0; i < p.count; i += 7) {
      const rr = Math.hypot(p.x[i] - e(i).x, p.y[i] - e(i).y);
      expect(Math.abs(rr - 1250) / 1250).toBeLessThan(0.01);
    }
  });

  it('flags a suborbital arc as an impact and a deep dive as atmosphere', () => {
    const w = orbitWorld(EARTH, 1250);
    const ev = bodyVel(EARTH, w.time);
    w.ship.vx = ev.x + (w.ship.vx - ev.x) * 0.5;
    w.ship.vy = ev.y + (w.ship.vy - ev.y) * 0.5;
    const p = predict(w, { horizon: 600 });
    expect(['impact', 'atmosphere']).toContain(p.end);
    expect(p.endBody).toBe(EARTH);
  });

  it('applies a node burn', () => {
    const w = orbitWorld(EARTH, 1250);
    const base = predict(w, { horizon: 60 });
    const burn = predict(w, { horizon: 60, node: { t: w.time + 5, prograde: 20, radial: 0 } });
    expect(burn.nodeIndex).toBeGreaterThan(0);
    expect(Math.hypot(burn.nodeDv!.x, burn.nodeDv!.y)).toBeCloseTo(20, 5);
    expect(burn.x[burn.count - 1]).not.toBeCloseTo(base.x[base.count - 1], 0);
  });
});

import { keplerPropagate } from './orbit';

describe('rails', () => {
  it('kepler propagation matches a conic exactly', () => {
    const mu = body('earth').gm;
    const r = 1300;
    const vc = Math.sqrt(mu / r);
    const [x, y] = keplerPropagate(r, 0, 0, vc * 1.1, mu, 300);
    const el0 = orbitElements(r, 0, 0, vc * 1.1, mu);
    const [x2, y2, vx2, vy2] = keplerPropagate(r, 0, 0, vc * 1.1, mu, 300);
    const el1 = orbitElements(x2, y2, vx2, vy2, mu);
    expect(el1.periapsis).toBeCloseTo(el0.periapsis, 6);
    expect(el1.apoapsis!).toBeCloseTo(el0.apoapsis!, 6);
    expect(Math.hypot(x, y)).toBeGreaterThan(1299);
    // Whole periods return to the start.
    const [xp, yp] = keplerPropagate(r, 0, 0, vc * 1.1, mu, el0.period! * 7);
    expect(xp).toBeCloseTo(r, 3);
    expect(yp).toBeCloseTo(0, 3);
  });

  it('matches n-body stepping for a low orbit', () => {
    const a = orbitWorld(EARTH, 1250, 0, 0.3);
    const b = orbitWorld(EARTH, 1250, 0, 0.3);
    const none = { throttle: 0, turn: 0 };
    for (let i = 0; i < 600; i++) step(a, none, FIXED_DT * 10);
    advance(b, none, a.time, 10);
    const ra = refState(a);
    const rb = refState(b);
    expect(Math.hypot(ra.rx - rb.rx, ra.ry - rb.ry)).toBeLessThan(2);
  });

  it('warps through months in orbit in one call', () => {
    const w = orbitWorld(EARTH, 1250);
    const none = { throttle: 0, turn: 0 };
    advance(w, none, YEAR / 2, 10);
    const rs = refState(w);
    expect(rs.r).toBeCloseTo(1250, 0);
    expect(w.time).toBeCloseTo(YEAR / 2, 3);
  });
});
