import { describe, expect, it } from 'vitest';
import { BODIES, bodyPos, bodyVel, indexOf } from '../sim/bodies';
import { createWorld } from '../sim/physics';
import { BASE_STATS } from '../sim/tech';
import { YEAR } from '../sim/units';
import { newCampaign } from './campaign';
import { parseShareCode, shareCode } from './records';
import { MILESTONES, checkMilestones, makeRivalYears, tickCalendar, totalScore, yearBudget } from './rules';

const EARTH = indexOf('earth');

function campaignAt(): ReturnType<typeof newCampaign> {
  const c = newCampaign({ seed: 42, difficulty: 1, bloc: 'usa' });
  c.rivalYears = makeRivalYears(c.seed, c.difficulty);
  return c;
}

describe('rival', () => {
  it('is deterministic, ordered, and scales with difficulty', () => {
    const a = makeRivalYears(7, 1);
    expect(makeRivalYears(7, 1)).toEqual(a);
    for (let i = 1; i < a.length; i++) expect(a[i]).toBeGreaterThan(a[i - 1]);
    const easy = makeRivalYears(7, 0);
    const hard = makeRivalYears(7, 2);
    expect(easy[9]).toBeGreaterThan(a[9]);
    expect(hard[9]).toBeLessThan(a[9]);
    expect(a[9]).toBeGreaterThan(1985);
    expect(a[9]).toBeLessThan(1996);
  });

  it('posts news as the calendar passes the rival milestones and ends the race at Pluto', () => {
    const c = campaignAt();
    tickCalendar(c, YEAR * (c.rivalYears[2] - 1957) + 10);
    expect(c.rivalDone).toBe(3);
    expect(c.news.some((n) => n.kind === 'rival')).toBe(true);
    expect(c.status).toBe('playing');
    const r = tickCalendar(c, YEAR * (c.rivalYears[9] - 1957) + 10);
    expect(r.lost).toBe(true);
    expect(c.status).toBe('lost');
  });

  it('pays a yearly budget that grows with milestones', () => {
    const c = campaignAt();
    const f0 = c.funds;
    tickCalendar(c, YEAR * 3.2);
    expect(c.funds).toBe(f0 + yearBudget(c) * 3);
    c.milestones[0].done = true;
    expect(yearBudget(c)).toBeGreaterThan(70);
  });
});

describe('milestones', () => {
  it('detects altitude, orbit and a lunar flyby, awarding double for being first', () => {
    const c = campaignAt();
    const w = createWorld(BASE_STATS, EARTH, Math.PI / 2, 0);
    const p = bodyPos(EARTH, 0);
    const v = bodyVel(EARTH, 0);
    const vc = Math.sqrt(BODIES[EARTH].gm / 1250);
    w.ship.status = 'flying';
    w.ship.x = p.x;
    w.ship.y = p.y + 1250;
    w.ship.vx = v.x + vc;
    w.ship.vy = v.y;
    const ev = checkMilestones(c, w);
    expect(ev.map((e) => e.id)).toEqual([1, 2]);
    expect(c.milestones[1].first).toBe(true);
    expect(c.milestones[1].points).toBeGreaterThanOrEqual(MILESTONES[1].points * 2);
    // Late completion is worth less.
    const c2 = campaignAt();
    const w2 = createWorld(BASE_STATS, EARTH, Math.PI / 2, 5 * YEAR);
    const p2 = bodyPos(EARTH, w2.time);
    const v2 = bodyVel(EARTH, w2.time);
    w2.ship.status = 'flying';
    w2.ship.x = p2.x;
    w2.ship.y = p2.y + 1250;
    w2.ship.vx = v2.x + vc;
    w2.ship.vy = v2.y;
    const ev2 = checkMilestones(c2, w2);
    expect(ev2.length).toBe(2);
    expect(c2.milestones[1].first).toBe(false);
    expect(c2.milestones[1].points).toBeLessThan(c.milestones[1].points);
    expect(totalScore(c2)).toBeLessThan(totalScore(c));
  });

  it('completes the lunar landing when the flag is planted', () => {
    const c = campaignAt();
    const w = createWorld(BASE_STATS, indexOf('moon'), 0.3, 1000);
    c.flags.push({ body: indexOf('moon'), theta: 0.3, time: 1000 });
    const ev = checkMilestones(c, w);
    expect(ev.map((e) => e.id)).toContain(4);
  });
});

describe('share codes', () => {
  it('round-trips and rejects typos', () => {
    const e = { seed: 123456, difficulty: 2 as const, bloc: 'urss' as const, outcome: 'won' as const, year: 1989, score: 4321 };
    const code = shareCode(e);
    expect(parseShareCode(code)).toEqual(e);
    expect(parseShareCode(code.replace('ORB-', 'ORB-1'))).toBeNull();
  });
});
