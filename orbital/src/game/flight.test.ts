import { describe, expect, it } from 'vitest';
import { indexOf } from '../sim/bodies';
import { createWorld } from '../sim/physics';
import { statsFor } from '../sim/tech';
import { DAY } from '../sim/units';
import { type Input } from '../input/input';
import { type Ui } from '../ui/ui';
import { newCampaign } from './campaign';
import { BASE_COST, Flight, tickBases } from './flight';

const MOON = indexOf('moon');

function setup(sandbox = false) {
  const c = newCampaign({ seed: 1, sandbox });
  c.techs = ['tanks1', 'isru', 'hyper', 'nerva'];
  const stats = statsFor(c.techs, 'chem');
  const w = createWorld(stats, MOON, 0.3, 1000, 100);
  const f = new Flight(w, c, {} as Input, {} as Ui);
  return { c, w, f };
}

describe('landed actions', () => {
  it('plants a flag once, builds a base for funds, and refuels from its depot', () => {
    const { c, w, f } = setup();
    expect(f.landedSite()?.name).toBe('Mar de la Tranquilidad');
    const labels = f.contextActions().map((a) => a.id);
    expect(labels).toContain('flag');
    expect(labels).toContain('base');

    f.plantFlag();
    f.plantFlag();
    expect(c.flags.length).toBe(1);

    const funds = c.funds;
    f.buildBase();
    expect(c.bases.length).toBe(1);
    expect(c.funds).toBe(funds - BASE_COST);

    // Production: moon ice richness 0.6, isru x2 -> 1.44 fuel/s.
    tickBases(c, w.stats.isru, 10 * DAY);
    expect(c.bases[0].stock).toBeGreaterThan(900);
    const before = w.ship.fuel;
    f.refuel();
    expect(w.ship.fuel).toBeGreaterThan(before + 800);
    expect(c.bases[0].stock).toBeLessThan(700);
  });

  it('refuses a base without funds and swaps to unlocked engines only', () => {
    const { c, w, f } = setup();
    c.funds = 5;
    f.buildBase();
    expect(c.bases.length).toBe(0);
    f.swapEngine();
    expect(c.engine).toBe('hyper');
    expect(w.stats.ve).toBe(1000);
    f.swapEngine();
    expect(c.engine).toBe('nerva');
    f.swapEngine();
    expect(c.engine).toBe('chem');
  });

  it('does not offer actions off a landing site', () => {
    const c = newCampaign({ seed: 1 });
    const w = createWorld(statsFor([], 'chem'), MOON, 2.0, 0, 100);
    const f = new Flight(w, c, {} as Input, {} as Ui);
    expect(f.landedSite()).toBeNull();
    expect(f.contextActions()).toEqual([]);
  });
});

import { BODIES, bodyPos, bodyVel } from '../sim/bodies';
import { suggestTransfer, refineNode } from '../sim/planner';

describe('automatic burn', () => {
  it('flies a lunar transfer node by itself: warps, aims, burns and finishes', () => {
    const c = newCampaign({ seed: 3, sandbox: true });
    const earth = indexOf('earth');
    const stats = statsFor(c.techs, 'chem');
    const w = createWorld(stats, earth, Math.PI / 2, 0, 800);
    const r = 1250;
    const vc = Math.sqrt(BODIES[earth].gm / r);
    const p = bodyPos(earth, 0);
    const v = bodyVel(earth, 0);
    w.ship.status = 'flying';
    w.ship.x = p.x + r * Math.cos(0.4);
    w.ship.y = p.y + r * Math.sin(0.4);
    w.ship.vx = v.x - vc * Math.sin(0.4);
    w.ship.vy = v.y + vc * Math.cos(0.4);
    const input = { update() {}, turn: 0, throttle: 0, autopilot: 'off', keyCommands: [] as string[], taps: [] as unknown[], zoom: 0.3, zoomManual: false, zoomBy() {}, reset() {} } as unknown as Input;
    const pressed = new Set<string>();
    const ui = { pressed: (id: string) => pressed.delete(id), flush() {}, commit() {}, register() {} } as unknown as Ui;
    const f = new Flight(w, c, input, ui);
    const moon = indexOf('moon');
    const sug = suggestTransfer(w, moon)!;
    const horizon = sug.node.t - w.time + sug.eta * 1.3;
    const refined = refineNode(w, moon, sug.node, horizon, 300);
    f.node = { ...refined.node, eta: sug.eta, dvVec: null, v0: null, total: 0 };
    f.target = moon;
    const fuel0 = w.ship.fuel;
    pressed.add('nburn');
    let finished = false;
    for (let i = 0; i < 20000 && !finished; i++) {
      f.update(0.016, i * 0.016);
      if (!f.node && !f.autoBurn && i > 10) finished = true;
    }
    expect(finished).toBe(true);
    expect(w.ship.fuel).toBeLessThan(fuel0 - 10);
    expect(input.throttle).toBe(0);
    expect(w.time).toBeGreaterThan(refined.node.t - 5);
  });
});

import { planCircularize } from '../sim/planner';
import { orbitElements } from '../sim/orbit';
import { refState } from '../sim/physics';

describe('automatic circularisation from a low arc', () => {
  it('builds an orbit at the top of an ascent without diving into the ground', () => {
    const c = newCampaign({ seed: 3, sandbox: true });
    const earth = indexOf('earth');
    const stats = statsFor(c.techs, 'chem');
    const w = createWorld(stats, earth, Math.PI / 2, 0, 900);
    const p = bodyPos(earth, 0);
    const v = bodyVel(earth, 0);
    // Top of an ascent: 300 u up, mostly sideways, still climbing slowly.
    w.ship.status = 'flying';
    w.ship.x = p.x;
    w.ship.y = p.y + 1300;
    w.ship.vx = v.x + 95;
    w.ship.vy = v.y + 20;
    w.ship.angle = 0;
    const input = { update() {}, turn: 0, throttle: 0, autopilot: 'off', keyCommands: [] as string[], taps: [] as unknown[], zoom: 0.3, zoomManual: false, zoomBy() {}, reset() {} } as unknown as Input;
    const pressed = new Set<string>();
    const ui = { pressed: (id: string) => pressed.delete(id), flush() {}, commit() {}, register() {} } as unknown as Ui;
    const f = new Flight(w, c, input, ui);
    const plan = planCircularize(w)!;
    f.node = { ...plan.node, eta: 0, dvVec: null, v0: null, total: 0, kind: 'circ', goalPe: Math.max(plan.radius * 0.93, 1000 + 176 + 25) };
    pressed.add('nburn');
    for (let i = 0; i < 20000 && w.ship.status === 'flying' && (f.node || f.autoBurn); i++) f.update(0.016, i * 0.016);
    expect(w.ship.status).toBe('flying');
    const rs = refState(w);
    const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, BODIES[earth].gm);
    expect(el.bound).toBe(true);
    expect(el.periapsis - BODIES[earth].radius).toBeGreaterThan(200);
  });
});

import { planCircularizeOrReason } from '../sim/planner';

describe('circularisation from many ascent end states', () => {
  const cases: [number, number, number][] = [
    [340, 0, 90], [340, -10, 60], [450, 0, 120], [450, 40, 90], [300, 70, 60], [450, -10, 120], [340, 40, 120], [450, -30, 90],
  ];
  for (const [alt, vr, vt] of cases) {
    it(`alt ${alt} vr ${vr} vt ${vt} ends in a safe orbit`, () => {
      const c = newCampaign({ seed: 3, sandbox: true });
      const earth = indexOf('earth');
      const w = createWorld(statsFor(c.techs, 'chem'), earth, Math.PI / 2, 0, 600);
      const p = bodyPos(earth, 0);
      const v = bodyVel(earth, 0);
      w.ship.status = 'flying';
      w.ship.x = p.x;
      w.ship.y = p.y + 1000 + alt;
      w.ship.vx = v.x + vt;
      w.ship.vy = v.y + vr;
      const input = { update() {}, turn: 0, throttle: 0, autopilot: 'off', keyCommands: [] as string[], taps: [] as unknown[], zoom: 0.3, zoomManual: false, zoomBy() {}, reset() {} } as unknown as Input;
      const pressed = new Set<string>();
      const ui = { pressed: (id: string) => pressed.delete(id), flush() {}, commit() {}, register() {} } as unknown as Ui;
      const f = new Flight(w, c, input, ui);
      const plan = planCircularizeOrReason(w);
      expect('node' in plan).toBe(true);
      if (!('node' in plan)) return;
      f.node = { ...plan.node, eta: 0, dvVec: null, v0: null, total: 0, kind: 'circ', goalPe: Math.max(plan.radius * 0.93, 1000 + 176 + 25) };
      pressed.add('nburn');
      for (let i = 0; i < 20000 && w.ship.status === 'flying' && (f.node || f.autoBurn); i++) f.update(0.016, i * 0.016);
      expect(w.ship.status).toBe('flying');
      const rs = refState(w);
      const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, BODIES[earth].gm);
      expect(el.bound).toBe(true);
      expect(el.periapsis - BODIES[earth].radius).toBeGreaterThan(180);
    });
  }

  it('says why it cannot plan when the ship is too low or already circular', () => {
    const c = newCampaign({ seed: 3, sandbox: true });
    const earth = indexOf('earth');
    const w = createWorld(statsFor(c.techs, 'chem'), earth, Math.PI / 2, 0, 600);
    const p = bodyPos(earth, 0);
    const v = bodyVel(earth, 0);
    w.ship.status = 'flying';
    w.ship.x = p.x;
    w.ship.y = p.y + 1210;
    w.ship.vx = v.x + 60;
    w.ship.vy = v.y - 10;
    const low = planCircularizeOrReason(w);
    expect('reason' in low && low.reason).toContain('bajo');
    const r = 1300;
    w.ship.y = p.y + r;
    w.ship.vx = v.x + Math.sqrt(BODIES[earth].gm / r);
    w.ship.vy = v.y;
    const circ = planCircularizeOrReason(w);
    expect('reason' in circ && circ.reason).toContain('circular');
  });
});
