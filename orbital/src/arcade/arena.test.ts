import { describe, expect, it } from 'vitest';
import { mulberry32 } from '../sim/rng';
import { RivalDriver } from './ai';
import { Arena, BASE_STATS, STEP } from './arena';
import { STAGES } from './stages';

function runRival(stageIdx: number, maxSeconds = 120): { time: number; deaths: number; gates: number; arena: Arena } {
  const def = STAGES[stageIdx];
  const arena = new Arena(def);
  const ship = arena.addShip({
    isPlayer: false,
    name: 'rival',
    color: '#ff2bd6',
    stats: { ...BASE_STATS, thrust: BASE_STATS.thrust * def.rival.skill },
    start: def.rivalStart,
    infiniteFuel: true,
  });
  const driver = new RivalDriver(mulberry32(7 + stageIdx));
  let deaths = 0;
  while (arena.t < maxSeconds + 3 && !ship.finished) {
    const c = driver.control(arena, ship);
    arena.step([c], STEP);
    for (const e of arena.events) if (e.type === 'die') deaths++;
    arena.events.length = 0;
  }
  return { time: ship.finishTime, deaths, gates: ship.nextGate, arena };
}

describe('arena physics', () => {
  it('keeps a ship in a stable orbit around a static planet', () => {
    const def = { ...STAGES[0], asteroids: [] };
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    const r = 700;
    const vc = Math.sqrt(arena.bodies[0].gm / r);
    arena.start();
    ship.status = 'flying';
    ship.x = 0;
    ship.y = r;
    ship.vx = vc;
    ship.vy = 0;
    let minR = Infinity;
    let maxR = 0;
    for (let i = 0; i < 120 * 60; i++) {
      arena.step([{ throttle: 0, turn: 0 }]);
      const rr = Math.hypot(ship.x, ship.y);
      minR = Math.min(minR, rr);
      maxR = Math.max(maxR, rr);
    }
    expect(ship.deathReason).toBe('');
    expect(ship.status).toBe('flying');
    // Atmosphere reaches 3 scale heights (135 u) above the surface, so r=700 is clear of it.
    expect(maxR - minR).toBeLessThan(2);
  });

  it('lifts off the pad with thrust and falls back and crashes without it', () => {
    const def = STAGES[0];
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    arena.start();
    for (let i = 0; i < 120 * 1.5; i++) arena.step([{ throttle: 1, turn: 0 }]);
    expect(ship.status).toBe('flying');
    expect(Math.hypot(ship.x, ship.y)).toBeGreaterThan(300);
    for (let i = 0; i < 120 * 90 && ship.status === 'flying'; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(['dead', 'landed']).toContain(ship.status);
  });

  it('lands softly and refuels on a bonfire pad, and dies on a hard impact', () => {
    const def = STAGES[0];
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    arena.start();
    ship.status = 'flying';
    ship.fuel = 10;
    ship.hull = 40;
    ship.x = 0;
    ship.y = 240 + 7 + 3;
    ship.vx = 0;
    ship.vy = -10;
    ship.angle = Math.PI / 2;
    for (let i = 0; i < 60; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(ship.status).toBe('landed');
    expect(ship.fuel).toBe(BASE_STATS.fuelMax);
    expect(ship.hull).toBe(BASE_STATS.hullMax);
    expect(ship.bonfire).not.toBeNull();

    const crash = new Arena(def);
    const s2 = crash.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    crash.start();
    s2.status = 'flying';
    s2.x = 0;
    s2.y = 240 + 7 + 3;
    s2.vy = -120;
    s2.angle = Math.PI / 2;
    for (let i = 0; i < 60; i++) crash.step([{ throttle: 0, turn: 0 }]);
    expect(s2.status).toBe('dead');
  });

  it('keeps asteroid motion independent of the player (so stages can be learned)', () => {
    const def = STAGES[1];
    const a = new Arena(def);
    const b = new Arena(def);
    const sa = a.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    b.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start });
    for (let i = 0; i < 120 * 10; i++) {
      a.step([{ throttle: 1, turn: 0.3 }]);
      b.step([{ throttle: 0, turn: 0 }]);
    }
    void sa;
    const ra = a.asteroids.filter((x) => x.alive).map((x) => [x.x, x.y]);
    const rb = b.asteroids.filter((x) => x.alive).map((x) => [x.x, x.y]);
    expect(ra).toEqual(rb);
  });
});

describe('rival alone', () => {
  for (let i = 0; i < STAGES.length; i++) {
    it(`finishes stage ${i + 1} (${STAGES[i].name})`, () => {
      const r = runRival(i);
      const info = `time ${r.time.toFixed(1)} par ${STAGES[i].par} deaths ${r.deaths} gates ${r.gates}/${STAGES[i].gates.length}`;
      console.info(`STAGE ${i + 1}: ${info}`);
      expect(r.gates).toBe(STAGES[i].gates.length);
    });
  }
});
