import { describe, expect, it } from 'vitest';
import { mulberry32 } from '../sim/rng';
import { RivalDriver } from './ai';
import { Arena, BASE_STATS, STEP } from './arena';
import { UPGRADE_SLOTS, buyUpgrade, newMeta, shipStats, usedSlots } from './meta';
import { generateStage, makeGrandPrix, makeProceduralRace } from './procgen';
import { Mission } from './mission';
import { RACES } from './races';
import { type StageDef } from './types';

const stageOf = (raceId: string, name: string): StageDef => RACES.find((r) => r.id === raceId)!.stages.find((s) => s.name === name)!;

function newPlayer(def: StageDef, stats = BASE_STATS): { arena: Arena; ship: ReturnType<Arena['addShip']> } {
  const arena = new Arena(def);
  const ship = arena.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats, start: def.start, orbit: def.startAt });
  arena.start();
  return { arena, ship };
}

describe('new stage mechanics', () => {
  it('a stage can start in flight, and the ship does not move before GO', () => {
    const def = stageOf('polosur', 'Frenado lunar');
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: true, name: 'p', color: '#0ff', stats: BASE_STATS, start: def.start, orbit: def.startAt });
    expect(ship.status).toBe('flying');
    const x0 = ship.x;
    for (let i = 0; i < 120; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(ship.x).toBe(x0);
    arena.start();
    for (let i = 0; i < 120; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(ship.x).not.toBe(x0);
  });

  it('a landing waypoint advances the route only when the ship lands on its pad', () => {
    const def = stageOf('reutilizables', 'Dos vuelos en dos semanas');
    const { arena, ship } = newPlayer(def);
    const idx = arena.gates.findIndex((g) => g.land);
    expect(idx).toBeGreaterThan(0);
    ship.nextGate = idx;
    ship.status = 'flying';
    const pt = { x: 0, y: 0 };
    const ang = arena.padPoint(arena.gates[idx].land!.body, arena.gates[idx].land!.pad, pt);
    ship.x = pt.x + Math.cos(ang) * 10;
    ship.y = pt.y + Math.sin(ang) * 10;
    ship.vx = 0;
    ship.vy = 0;
    ship.angle = ang;
    for (let i = 0; i < 240; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(ship.status).toBe('landed');
    expect(ship.nextGate).toBe(idx + 1);
  });

  it('cargo makes the ship heavier', () => {
    const def = stageOf('halley', 'Muestra de polvo');
    const a = newPlayer(def);
    const b = newPlayer(def);
    for (const { ship } of [a, b]) {
      ship.status = 'flying';
      ship.x = 2000;
      ship.y = 2000;
      ship.vx = 0;
      ship.vy = 0;
      ship.angle = 0;
    }
    b.ship.cargo = true;
    for (let i = 0; i < 240; i++) {
      a.arena.step([{ throttle: 1, turn: 0 }]);
      b.arena.step([{ throttle: 1, turn: 0 }]);
    }
    expect(b.ship.vx).toBeLessThan(a.ship.vx);
  });

  it('the afterburner pushes harder, then needs to recharge; the shield trims heat damage', () => {
    const def = stageOf('guerra', 'Sputnik');
    const stats = shipStats({ ...newMeta().upgrades, boost: 1, shield: 2 });
    const a = newPlayer(def, stats);
    const b = newPlayer(def, BASE_STATS);
    for (const { ship } of [a, b]) {
      ship.status = 'flying';
      ship.x = 9000;
      ship.y = 9000;
      ship.vx = 0;
      ship.vy = 0;
      ship.angle = 0;
    }
    a.arena.step([{ throttle: 1, turn: 0, boost: true }]);
    for (let i = 0; i < 120; i++) {
      a.arena.step([{ throttle: 1, turn: 0 }]);
      b.arena.step([{ throttle: 1, turn: 0 }]);
    }
    expect(a.ship.vx).toBeGreaterThan(b.ship.vx * 1.15);
    expect(a.ship.boostCd).toBeGreaterThan(0);
    const hull = a.ship.hull;
    a.ship.invuln = 0;
    b.ship.invuln = 0;
    a.arena.damage(a.ship, 10, 'calor');
    b.arena.damage(b.ship, 10, 'calor');
    expect(hull - a.ship.hull).toBeCloseTo(4, 1);
    expect(b.ship.hull).toBe(BASE_STATS.hullMax - 10);
  });

  it('only a few kinds of upgrade fit on the ship at once', () => {
    const meta = newMeta();
    meta.data = 5000;
    for (const id of ['motor', 'tank', 'hull'] as const) expect(buyUpgrade(meta, id)).toBe(true);
    expect(usedSlots(meta.upgrades)).toBe(UPGRADE_SLOTS);
    expect(buyUpgrade(meta, 'shield')).toBe(false);
    expect(buyUpgrade(meta, 'motor')).toBe(true);
  });
});

describe('gravity assist', () => {
  it('a coasting ship that wraps the moving planet leaves faster and bent towards its motion', () => {
    const def = stageOf('asistencias', 'New Horizons: Plutón');
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: false, name: 'r', color: '#f0f', stats: BASE_STATS, start: def.start, infiniteFuel: true });
    arena.start();
    for (let i = 0; i < 20 / STEP; i++) arena.step([undefined as never]);
    const bi = arena.bodyIndex('jupiter');
    const h = (-21 * Math.PI) / 180;
    const off = -520;
    ship.status = 'flying';
    ship.x = arena.cur.x[bi] - Math.cos(h) * 1300 - Math.sin(h) * off;
    ship.y = arena.cur.y[bi] - Math.sin(h) * 1300 + Math.cos(h) * off;
    ship.vx = Math.cos(h) * 250;
    ship.vy = Math.sin(h) * 250;
    for (let i = 0; i < 30 / STEP && (ship.status as string) !== 'dead'; i++) arena.step([{ throttle: 0, turn: 0 }]);
    expect(ship.status).toBe('flying');
    expect(Math.hypot(ship.vx, ship.vy)).toBeGreaterThan(290);
    expect((Math.atan2(ship.vy, ship.vx) * 180) / Math.PI).toBeGreaterThan(20);
  });
});

describe('random races', () => {
  it('are reproducible from the seed and vary with it', () => {
    const a = makeProceduralRace('diaria', 123);
    const b = makeProceduralRace('diaria', 123);
    const c = makeProceduralRace('diaria', 124);
    expect(JSON.stringify(a.stages)).toBe(JSON.stringify(b.stages));
    expect(JSON.stringify(a.stages)).not.toBe(JSON.stringify(c.stages));
    expect(a.stages.length).toBe(6);
    expect(makeProceduralRace('sinfin', 1).stages.length).toBe(10);
  });

  it('the rival can fly the generated stages of every kind', () => {
    const tpls = ['hop', 'circuit', 'gauntlet', 'double', 'cargo', 'fall'] as const;
    let fails = 0;
    let total = 0;
    for (const t of tpls) {
      for (let s = 1; s <= 3; s++) {
        const def = generateStage(s, 1, (s - 1) / 2, t);
        const arena = new Arena(def);
        const ship = arena.addShip({ isPlayer: false, name: 'r', color: '#f0f', stats: { ...BASE_STATS, thrust: BASE_STATS.thrust * def.rival.skill }, start: def.rivalStart, orbit: def.startAt, infiniteFuel: true });
        const d = new RivalDriver(mulberry32(7 + s), def.rival.ai);
        while (arena.t < 140 && !ship.finished) {
          arena.step([d.control(arena, ship)], STEP);
          arena.events.length = 0;
        }
        total++;
        if (!ship.finished) fails++;
      }
    }
    expect(fails / total).toBeLessThan(0.1);
  }, 120000);
});

describe('grand prix', () => {
  it('has 9 to 12 ships on distinct pads all round the planet, reproducible from the seed', () => {
    for (const seed of [1, 2, 3, 4, 5, 6]) {
      const race = makeGrandPrix(seed);
      const st = race.stages[0];
      const total = st.field!.slots.length + 1;
      expect(total).toBeGreaterThanOrEqual(9);
      expect(total).toBeLessThanOrEqual(12);
      const angles = new Set([...st.field!.slots, (st.start.angle * 180) / Math.PI].map((a) => Math.round(((a % 360) + 360) % 360)));
      expect(angles.size).toBe(total);
      expect(JSON.stringify(makeGrandPrix(seed))).toBe(JSON.stringify(race));
    }
  });

  it('the podium decides the stage: top three win, a full podium without the player loses', () => {
    const race = makeGrandPrix(7);
    const win = new Mission(newMeta(), { stage: 0, race });
    win.update(0.1, { throttle: 0, turn: 0 });
    for (let i = 0; i < 40 && win.phase === 'countdown'; i++) win.update(0.1, { throttle: 0, turn: 0 });
    win.arena.finishOrder.push(win.rivals[0].id);
    win.player.finished = true;
    win.player.finishTime = 50;
    win.arena.finishOrder.push(win.player.id);
    win.update(0.1, { throttle: 0, turn: 0 });
    expect(win.result?.won).toBe(true);
    expect(win.result?.place).toBe(2);

    const lose = new Mission(newMeta(), { stage: 0, race });
    for (let i = 0; i < 40 && lose.phase === 'countdown'; i++) lose.update(0.1, { throttle: 0, turn: 0 });
    for (let i = 0; i < 3; i++) lose.arena.finishOrder.push(lose.rivals[i].id);
    lose.update(0.1, { throttle: 0, turn: 0 });
    expect(lose.result?.won).toBe(false);
    expect(lose.result?.place).toBeGreaterThan(0);
  });
});
