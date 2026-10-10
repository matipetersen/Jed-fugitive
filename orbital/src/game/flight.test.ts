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
