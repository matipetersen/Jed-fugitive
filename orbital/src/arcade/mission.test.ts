import { describe, expect, it } from 'vitest';
import { mulberry32 } from '../sim/rng';
import { BOT_PROFILES, PlayerBot } from './bot';
import { buyUpgrade, newMeta, shipStats } from './meta';
import { Mission } from './mission';

interface BotResult {
  stages: number;
  deaths: number;
  over: string | null;
  reason: string;
  times: number[];
}

/** Plays a whole mission with a bot, as fast as the simulation allows. */
function playMission(profile: keyof typeof BOT_PROFILES, seed: number, startStage = 0): BotResult {
  const meta = newMeta();
  const m = new Mission(meta, { stage: startStage });
  const bot = new PlayerBot(mulberry32(seed), BOT_PROFILES[profile]);
  const times: number[] = [];
  for (let frame = 0; frame < 60 * 60 * 6 && !m.over; frame++) {
    const c = bot.control(m);
    m.update(1 / 60, c);
    m.checkBeacon();
    if (m.phase === 'cleared' && !m.over) {
      times.push(m.result!.time);
      m.nextStage();
    }
  }
  if (m.over === 'won') times.push(m.result?.time ?? 0);
  return { stages: m.stagesCleared, deaths: m.deaths, over: m.over, reason: m.result?.reason ?? '', times };
}

/** Runs the mission for `seconds` in 1/60 s frames. */
function run(m: Mission, seconds: number, c = { throttle: 0, turn: 0 }): void {
  for (let i = 0; i < Math.round(seconds * 60); i++) m.update(1 / 60, c);
}

describe('mission rules', () => {
  it('gives data for gates, loses it on death, and leaves a beacon that returns it', () => {
    const meta = newMeta();
    const m = new Mission(meta);
    const p = m.player;
    // Fly through the first two gates by teleporting along the path.
    run(m, 3.5);
    expect(m.phase).toBe('race');
    const a = m.arena;
    const gp = { x: 0, y: 0 };
    p.status = 'flying';
    for (let i = 0; i < 2; i++) {
      a.gatePos(p.nextGate, gp);
      p.x = gp.x;
      p.y = gp.y;
      p.vx = 0;
      p.vy = 0;
      run(m, 0.02);
    }
    expect(p.nextGate).toBe(2);
    expect(m.carried).toBe(20);
    // Die somewhere.
    p.x += 50;
    a.damage(p, 500, 'prueba');
    run(m, 0.1);
    expect(m.carried).toBe(0);
    expect(m.lives).toBe(2);
    expect(m.beacon?.data).toBe(20);
    // Respawn after the death timer, then touch the beacon.
    run(m, 2.5);
    expect(p.status).not.toBe('dead');
    const bp = m.beaconPos()!;
    p.status = 'flying';
    p.x = bp.x;
    p.y = bp.y;
    m.checkBeacon();
    expect(m.carried).toBe(20);
    expect(m.beacon).toBeNull();
  });

  it('fails the mission when lives run out, keeping banked data', () => {
    const meta = newMeta();
    meta.data = 77;
    const m = new Mission(meta);
    run(m, 3.5);
    for (let i = 0; i < 3; i++) {
      m.player.status = 'flying';
      m.arena.damage(m.player, 999, 'prueba');
      run(m, 3);
      run(m, 1.7);
    }
    expect(m.over).toBe('failed');
    expect(meta.data).toBe(77);
    expect(meta.deaths).toBe(3);
    expect(meta.records.length).toBe(1);
  });

  it('fails the mission when the rival finishes first', () => {
    const meta = newMeta();
    const m = new Mission(meta);
    run(m, 3.5);
    const r = m.rival;
    r.nextGate = m.arena.gates.length;
    r.finished = true;
    r.finishTime = 20;
    run(m, 0.05);
    expect(m.over).toBe('failed');
    expect(m.result?.reason).toContain('llegó primero');
  });

  it('upgrades change the ship and cost data', () => {
    const meta = newMeta();
    expect(buyUpgrade(meta, 'motor')).toBe(false);
    meta.data = 500;
    expect(buyUpgrade(meta, 'motor')).toBe(true);
    expect(meta.data).toBeLessThan(500);
    expect(shipStats(meta.upgrades).thrust).toBeGreaterThan(150);
  });

  it('a precise pilot clears the first stages before the rival', () => {
    for (const stage of [0, 1]) {
      const r = playMission('expert', 100 + stage, stage);
      expect(r.stages).toBeGreaterThanOrEqual(1);
      expect(r.deaths).toBe(0);
    }
  }, 120000);

  it('a whole mission takes about three to five minutes when it goes well', () => {
    const r = playMission('expert', 31, 0);
    expect(r.over).toBe('won');
    const total = r.times.reduce((a, b) => a + b, 0);
    expect(total).toBeGreaterThan(150);
    expect(total).toBeLessThan(330);
  }, 300000);
});
