import { describe, expect, it } from 'vitest';
import { mulberry32 } from '../sim/rng';
import { RivalDriver } from './ai';
import { Arena, BASE_STATS, STEP } from './arena';
import { UPGRADE_SLOTS, buyUpgrade, newMeta, shipStats, usedSlots } from './meta';
import { generateStage, makeGrandPrix, makeProceduralRace } from './procgen';
import { Mission } from './mission';
import { endlessDifficulty, makeEndlessRace } from './endless';
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

  it('every ship runs the same distance from its own pad, whichever side of the planet it starts on', () => {
    for (const seed of [11, 12, 13]) {
      const race = makeGrandPrix(seed);
      const m = new Mission(newMeta(), { stage: 0, race });
      const ships = [m.player, ...m.rivals];
      const len = m.player.route.length;
      expect(len).toBe(2 * m.arena.gates.length + 1);
      const pads = new Set<number>();
      for (const sh of ships) {
        expect(sh.route.length).toBe(len);
        pads.add(sh.finishPad.pad);
        // The first gate is a short hop ahead: well under half a lap from the ship, the same for all.
        const g0 = sh.route[0];
        const a0 = Math.atan2(g0.def.y, g0.def.x);
        const a1 = Math.atan2(sh.y, sh.x);
        const ahead = ((((a0 - a1) * race.stages[0].field!.dir) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
        expect(ahead).toBeGreaterThan(0.29);
        expect(ahead).toBeLessThan((2 * Math.PI) / 8 + 0.35 + 0.8);
      }
      expect(pads.size).toBe(ships.length);
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

describe('same start', () => {
  it('the rival leaves the pad at the same moment as the player, on any stage', () => {
    for (const [raceId, name] of [['guerra', 'Sputnik'], ['kessel', 'Los Cúmulos'], ['polosur', 'Doble alunizaje']] as const) {
      const m = new Mission(newMeta(), { stage: RACES.find((r) => r.id === raceId)!.stages.findIndex((s) => s.name === name), race: RACES.find((r) => r.id === raceId)! });
      for (let i = 0; i < 60 && m.phase === 'countdown'; i++) m.update(0.1, { throttle: 0, turn: 0 });
      expect(m.phase).toBe('race');
      for (let i = 0; i < 12; i++) m.update(0.1, { throttle: 0, turn: 0 });
      expect(m.rival.status === 'flying' || m.rival.throttle > 0, `${raceId} ${name}`).toBe(true);
    }
  });
});

describe('endless mode', () => {
  it('is reproducible, mixes kinds and alternates difficulty', () => {
    const a = makeEndlessRace(42);
    const b = makeEndlessRace(42);
    expect(JSON.stringify(a.stages.slice(0, 12))).toBe(JSON.stringify(b.stages.slice(0, 12)));
    expect(a.stages.length).toBeGreaterThanOrEqual(100);
    const kinds = new Set(a.stages.slice(0, 20).map((s) => s.kind));
    expect(kinds.size).toBeGreaterThanOrEqual(5);
    expect(a.stages.slice(0, 20).some((s) => s.sprint)).toBe(true);
    expect(a.stages.slice(0, 40).some((s) => s.field)).toBe(true);
    // Waves: every third stage is harder than the one before it, but the run still climbs.
    expect(endlessDifficulty(2)).toBeGreaterThan(endlessDifficulty(1));
    expect(endlessDifficulty(3)).toBeLessThan(endlessDifficulty(2));
    expect(endlessDifficulty(60)).toBeGreaterThan(endlessDifficulty(0));
  });

  it('losing stages spends continues until the run ends; a streak of wins earns one back', () => {
    const race = makeEndlessRace(7);
    const m = new Mission(newMeta(), { stage: 0, race });
    const lose = (): void => {
      for (let i = 0; i < 60 && m.phase === 'countdown'; i++) m.update(0.1, { throttle: 0, turn: 0 });
      m.rival.finished = true;
      m.rival.finishTime = 5;
      m.update(0.1, { throttle: 0, turn: 0 });
    };
    const win = (): void => {
      for (let i = 0; i < 60 && m.phase === 'countdown'; i++) m.update(0.1, { throttle: 0, turn: 0 });
      m.player.finished = true;
      m.player.finishTime = 5;
      m.arena.winner = m.player.id;
      m.update(0.1, { throttle: 0, turn: 0 });
    };
    expect(m.continues).toBe(3);
    for (let i = 0; i < 5; i++) {
      win();
      expect(m.phase).toBe('cleared');
      expect(m.nextStage()).toBe(true);
    }
    expect(m.streak).toBe(5);
    expect(m.continues).toBe(4);
    lose();
    expect(m.continues).toBe(3);
    expect(m.streak).toBe(0);
    expect(m.over).toBeNull();
    m.nextStage();
    lose();
    m.nextStage();
    lose();
    m.nextStage();
    lose();
    expect(m.continues).toBe(0);
    expect(m.over).toBe('failed');
    expect(m.stagesCleared).toBe(5);
  });
});
