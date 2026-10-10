import { afterEach, describe, expect, it } from 'vitest';
import { FIXED_DT, PLANET, SHIP } from './params';
import { orbitElements } from './orbit';
import { predictCoast } from './predict';
import { autopilotTurn } from './autopilot';
import { CONTACT_RADIUS, createWorld, step, type World } from './sim';
import { len, vec } from './vec';

const idle = { throttle: 0, turn: 0 };

function flyingWorld(pos = vec(0, 1500), vel = vec(0, 0), angle = Math.PI / 2): World {
  const w = createWorld();
  w.ship.status = 'flying';
  w.ship.pos = pos;
  w.ship.vel = vel;
  w.ship.angle = angle;
  return w;
}

describe('orbits', () => {
  it('keeps a circular orbit circular over ten revolutions', () => {
    const r = 1500;
    const v = Math.sqrt(PLANET.gm / r);
    const w = flyingWorld(vec(0, r), vec(v, 0));
    const period = 2 * Math.PI * Math.sqrt((r * r * r) / PLANET.gm);
    const steps = Math.round((period * 10) / FIXED_DT);
    let minR = Infinity;
    let maxR = 0;
    for (let i = 0; i < steps; i++) {
      step(w, idle, FIXED_DT);
      const rr = len(w.ship.pos);
      minR = Math.min(minR, rr);
      maxR = Math.max(maxR, rr);
    }
    expect(w.ship.status).toBe('flying');
    expect(Math.abs(minR - r) / r).toBeLessThan(0.001);
    expect(Math.abs(maxR - r) / r).toBeLessThan(0.001);
  });

  it('computes elements consistent with vis-viva', () => {
    const r = 1200;
    const vc = Math.sqrt(PLANET.gm / r);
    const el = orbitElements(vec(0, r), vec(1.2 * vc, 0), PLANET.gm);
    const a = 1 / (2 / r - (1.2 * vc) ** 2 / PLANET.gm);
    expect(el.bound).toBe(true);
    expect(el.periapsis).toBeCloseTo(r, 6);
    expect(el.apoapsis).toBeCloseTo(2 * a - r, 4);
    expect(el.e).toBeCloseTo(1 - r / a, 6);
  });

  it('reports a circular orbit as e ~ 0 and an unbound path as open', () => {
    const r = 1500;
    const vc = Math.sqrt(PLANET.gm / r);
    const circ = orbitElements(vec(0, r), vec(vc, 0), PLANET.gm);
    expect(circ.e).toBeLessThan(1e-9);
    expect(circ.apoapsis).toBeCloseTo(r, 6);
    const escape = orbitElements(vec(0, r), vec(1.5 * vc, 0), PLANET.gm);
    expect(escape.bound).toBe(false);
    expect(escape.apoapsis).toBeNull();
    expect(escape.period).toBeNull();
  });
});

describe('rocket', () => {
  const g = PLANET.surfaceGravity;
  afterEach(() => {
    PLANET.surfaceGravity = g;
  });

  it('obeys the rocket equation in free space', () => {
    PLANET.surfaceGravity = 0;
    const w = flyingWorld(vec(0, 1e6), vec(0, 0), 0);
    const burnTime = (SHIP.fuelMass * SHIP.exhaustVelocity) / SHIP.thrust;
    const steps = Math.ceil((burnTime + 1) / FIXED_DT);
    for (let i = 0; i < steps; i++) step(w, { throttle: 1, turn: 0 }, FIXED_DT);
    const expected = SHIP.exhaustVelocity * Math.log((SHIP.dryMass + SHIP.fuelMass) / SHIP.dryMass);
    expect(w.ship.fuel).toBeCloseTo(0, 6);
    expect(Math.abs(len(w.ship.vel) - expected) / expected).toBeLessThan(0.005);
  });

  it('stays on the pad with no throttle and lifts off at full throttle', () => {
    const w = createWorld();
    for (let i = 0; i < 120; i++) step(w, idle, FIXED_DT);
    expect(w.ship.status).toBe('landed');
    expect(len(w.ship.pos)).toBeCloseTo(CONTACT_RADIUS, 6);

    for (let i = 0; i < 240; i++) step(w, { throttle: 1, turn: 0 }, FIXED_DT);
    expect(w.ship.status).toBe('flying');
    expect(len(w.ship.pos)).toBeGreaterThan(CONTACT_RADIUS + 10);
  });
});

describe('touchdown', () => {
  const nearGround = (vy: number, angle: number): World =>
    flyingWorld(vec(0, CONTACT_RADIUS + 0.05), vec(0, vy), angle);

  it('lands softly when slow and upright', () => {
    const w = nearGround(-5, Math.PI / 2);
    for (let i = 0; i < 20; i++) step(w, idle, FIXED_DT);
    expect(w.ship.status).toBe('landed');
    expect(w.ship.vel).toEqual(vec(0, 0));
  });

  it('crashes when too fast', () => {
    const w = nearGround(-50, Math.PI / 2);
    for (let i = 0; i < 20; i++) step(w, idle, FIXED_DT);
    expect(w.ship.status).toBe('crashed');
  });

  it('crashes when tilted', () => {
    const w = nearGround(-5, Math.PI / 2 + 0.8);
    for (let i = 0; i < 20; i++) step(w, idle, FIXED_DT);
    expect(w.ship.status).toBe('crashed');
  });
});

describe('prediction', () => {
  it('traces a closed orbit without hitting the surface', () => {
    const r = 1500;
    const w = flyingWorld(vec(0, r), vec(Math.sqrt(PLANET.gm / r), 0));
    const p = predictCoast(w.ship);
    expect(p.impact).toBe(false);
    for (let i = 0; i < p.count; i++) {
      const rr = Math.hypot(p.points[i * 2]!, p.points[i * 2 + 1]!);
      expect(Math.abs(rr - r) / r).toBeLessThan(0.002);
    }
  });

  it('flags a suborbital path as an impact', () => {
    const w = flyingWorld(vec(0, 1500), vec(20, 0));
    const p = predictCoast(w.ship);
    expect(p.impact).toBe(true);
  });
});

describe('autopilot', () => {
  it('turns towards prograde and retrograde', () => {
    const w = flyingWorld(vec(0, 1500), vec(100, 0), Math.PI / 2);
    expect(autopilotTurn('prograde', w.ship)).toBeLessThan(0);
    expect(autopilotTurn('retrograde', w.ship)).toBeGreaterThan(0);
    expect(autopilotTurn('off', w.ship)).toBe(0);
  });
});

describe('tuning', () => {
  it('can reach a stable low orbit with a simple gravity turn and fuel to spare', () => {
    const w = createWorld();
    const turnTo = (target: number): number => {
      const err = Math.atan2(Math.sin(target - w.ship.angle), Math.cos(target - w.ship.angle));
      return Math.max(-1, Math.min(1, err * 4));
    };
    let phase: 'ascent' | 'coast' | 'circularize' | 'done' = 'ascent';
    for (let i = 0; i < 120 * 400 && phase !== 'done'; i++) {
      const s = w.ship;
      const r = len(s.pos);
      const alt = r - PLANET.radius;
      const el = orbitElements(s.pos, s.vel, PLANET.gm);
      const radial = Math.atan2(s.pos.y, s.pos.x);
      let throttle = 0;
      let turn = 0;
      if (phase === 'ascent') {
        throttle = 1;
        const tilt = Math.min(1, Math.max(0, (alt - 100) / 900)) * (Math.PI * 0.45);
        turn = turnTo(radial - tilt);
        if (el.bound && (el.apoapsis ?? 0) >= PLANET.radius + 250) phase = 'coast';
      } else if (phase === 'coast') {
        turn = turnTo(radial - Math.PI / 2);
        const vr = (s.pos.x * s.vel.x + s.pos.y * s.vel.y) / r;
        if (vr <= 0) phase = 'circularize';
      } else if (phase === 'circularize') {
        turn = turnTo(radial - Math.PI / 2);
        throttle = 1;
        if (el.periapsis >= PLANET.radius + 150) phase = 'done';
      }
      step(w, { throttle, turn }, FIXED_DT);
      if (w.ship.status === 'crashed') break;
    }
    expect(phase).toBe('done');
    expect(w.ship.status).toBe('flying');
    expect(w.ship.fuel / SHIP.fuelMass).toBeGreaterThan(0.1);
  });
});
