import { describe, expect, it } from 'vitest';
import { bodyPos, bodyVel, indexOf } from '../sim/bodies';
import { createWorld, step } from '../sim/physics';
import { BASE_STATS } from '../sim/tech';
import { AU, DAY, YEAR } from '../sim/units';
import { newCampaign } from './campaign';
import { type EventResult, processEvents, rollBin, stepAsteroids } from './events';

function deepWorld() {
  const w = createWorld(BASE_STATS, indexOf('earth'), Math.PI / 2, 0);
  w.ship.status = 'flying';
  w.ship.x = 2.5 * AU;
  w.ship.y = 0;
  w.ship.vx = 0;
  w.ship.vy = 150;
  return w;
}

describe('events', () => {
  it('rolls deterministically from the seed', () => {
    const c1 = newCampaign({ seed: 99 });
    const c2 = newCampaign({ seed: 99 });
    const a: string[] = [];
    const b: string[] = [];
    const w1 = deepWorld();
    const w2 = deepWorld();
    for (let bin = 1; bin < 800; bin++) {
      a.push(...rollBin(c1, w1, bin).map((r) => r.text));
      b.push(...rollBin(c2, w2, bin).map((r) => r.text));
    }
    expect(a).toEqual(b);
    expect(a.length).toBeGreaterThan(2);
  });

  it('fires asteroids much more often in the belt than outside it', () => {
    const c = newCampaign({ seed: 5 });
    const count = (x: number): number => {
      const w = deepWorld();
      w.ship.x = x;
      let n = 0;
      for (let bin = 1; bin < 2000; bin++) n += rollBin(c, w, bin).filter((r) => r.text.startsWith('ASTEROIDE')).length;
      return n;
    };
    expect(count(2.8 * AU)).toBeGreaterThan(count(8 * AU) * 3);
  });

  it('spawns an asteroid that hits unless the ship dodges, and credits a dodge', () => {
    const c = newCampaign({ seed: 5 });
    const results: EventResult[] = [];
    let w = deepWorld();
    // Find a bin that spawns an asteroid headed for the ship.
    let found = -1;
    for (let bin = 1; bin < 20000 && found < 0; bin++) {
      const ww = deepWorld();
      ww.ship.x = 2.8 * AU;
      const r = rollBin(c, ww, bin);
      if (r.some((e) => e.text.startsWith('ASTEROIDE')) && ww.asteroids.length === 1) {
        const a = ww.asteroids[0];
        const rx = a.x - ww.ship.x;
        const ry = a.y - ww.ship.y;
        const rvx = a.vx - ww.ship.vx;
        const rvy = a.vy - ww.ship.vy;
        const ttc = -(rx * rvx + ry * rvy) / (rvx * rvx + rvy * rvy);
        const miss = Math.hypot(rx + rvx * ttc, ry + rvy * ttc);
        if (miss < a.r) {
          found = bin;
          w = ww;
        }
      }
    }
    expect(found).toBeGreaterThan(0);
    const hit = structuredClone(w);
    for (let i = 0; i < 4000 && hit.asteroids.length > 0; i++) {
      step(hit, { throttle: 0, turn: 0 }, 0.05);
      stepAsteroids(hit, c, 0.05, (r) => results.push(r));
    }
    expect(hit.ship.hull).toBeLessThan(100);

    // Dodge: a small sideways burn well before impact.
    const dodge = structuredClone(w);
    const ax = dodge.asteroids[0];
    const rx = ax.x - dodge.ship.x;
    const ry = ax.y - dodge.ship.y;
    const l = Math.hypot(rx, ry);
    dodge.ship.vx += (-ry / l) * 4;
    dodge.ship.vy += (rx / l) * 4;
    const ev: EventResult[] = [];
    for (let i = 0; i < 4000 && dodge.asteroids.length > 0; i++) {
      step(dodge, { throttle: 0, turn: 0 }, 0.05);
      stepAsteroids(dodge, c, 0.05, (r) => ev.push(r));
    }
    expect(dodge.ship.hull).toBe(100);
    expect(c.eventsHandled).toBe(1);
    expect(ev.some((e) => e.text.includes('ESQUIVADO'))).toBe(true);
  });

  it('handles politics without a ship', () => {
    const c = newCampaign({ seed: 11 });
    c.sandbox = false;
    c.rivalYears = Array.from({ length: 10 }, (_, i) => 1960 + i * 3);
    const out: EventResult[] = [];
    processEvents(c, null, 30 * YEAR, (r) => out.push(r));
    expect(out.length).toBeGreaterThan(0);
    expect(c.eventBin).toBe(Math.floor((30 * YEAR) / DAY));
    void bodyPos;
    void bodyVel;
  });
});
