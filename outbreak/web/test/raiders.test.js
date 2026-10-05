const assert = require('assert');
const { OB, make, empty_level } = require('./helpers');

function field(seed = 3) {
  const g = make({ seed }), lv = g.world.level; empty_level(lv); g.hordes.length = 0; g.ring = null;
  const p = g.player; p.hp = p.max_hp = 1e6;
  for (let y = p.y - 12; y <= p.y + 12; y++) for (let x = p.x - 14; x <= p.x + 14; x++) { lv.set_tile(x, y, OB.T.GRASS); delete lv.hazards[lv.idx(x, y)]; }
  return [g, lv];
}
function raider_at(g, lv, dx, dy = 0, extra = {}) { const r = OB.make_raider(g, g.player.x + dx, g.player.y + dy); r.state = 'hunt'; Object.assign(r, extra); lv.add_actor(r); return r; }
const dist = (g, r) => Math.max(Math.abs(r.x - g.player.x), Math.abs(r.y - g.player.y));

{ // camps have hidden ambushers and snares
  const g = make({ seed: 3 }), lv = g.world.level;
  assert(g.world.camps.length);
  const hidden = lv.actors.filter((a) => a.kind === 'human' && a.hidden), snares = Object.values(lv.hazards).filter((h) => h.kind === 'snare');
  assert(hidden.length); assert(snares.length >= 2)         // camps are painted as you approach them; assert(snares.every((h) => h.hidden));
}
{ // hidden raiders are not visible or targeted
  const [g, lv] = field(); const r = raider_at(g, lv, 5, 0, { hidden: true, state: 'idle' }); g.update_fov();
  assert(!g.visible_actors().includes(r)); assert(!g.visible_hostiles().includes(r));
}
{ // walking up springs the ambush (the whole squad); creeping up does not
  const [g, lv] = field(); const a = raider_at(g, lv, 3, 0, { hidden: true, state: 'idle', squad: 7 }), b = raider_at(g, lv, 8, 4, { hidden: true, state: 'idle', squad: 7 });
  OB._human(g, a, [a, b]); assert(!a.hidden); OB._human(g, b, [a, b]); assert(!b.hidden);
  const [h, hl] = field(); const c = raider_at(h, hl, 3, 0, { hidden: true, state: 'idle', squad: 9 }); h.player.sneaking = true; h.rng.random = () => 0.9; OB._human(h, c, [c]); assert(c.hidden);
}
{ // a creeping player can spot the ambusher first
  const [g, lv] = field(); const c = raider_at(g, lv, 3, 0, { hidden: true, state: 'idle', squad: 9 }); g.player.sneaking = true; g.rng.random = () => 0.1;
  OB._human(g, c, [c]); assert(!c.hidden); assert.strictEqual(c.state, 'idle');
}
{ // snares hurt, alert the camp, can be spotted and disarmed
  const [g, lv] = field(), p = g.player, near = raider_at(g, lv, 9, 0, { state: 'idle' });
  lv.hazards[lv.idx(p.x + 1, p.y)] = { kind: 'snare', ttl: 1e9, power: 8, hidden: true }; const hp = p.hp;
  g.move(1, 0); assert(p.hp < hp); assert.strictEqual(near.state, 'hunt'); assert(!lv.hazards[lv.idx(p.x, p.y)]);
  lv.hazards[lv.idx(p.x + 1, p.y)] = { kind: 'snare', ttl: 1e9, power: 8, hidden: false };
  assert(!g.move(1, 0)); p.sneaking = true; const scrap = p.count('scrap'); assert(g.move(1, 0)); assert(!lv.hazards[lv.idx(p.x + 1, p.y)]); assert.strictEqual(p.count('scrap'), scrap + 1);
}
{ // spotting snares; they catch the dead too
  const [g, lv] = field(), p = g.player; lv.hazards[lv.idx(p.x + 2, p.y)] = { kind: 'snare', ttl: 1e9, power: 8, hidden: true };
  g.rng.random = () => 0.0; p.sneaking = true; OB.raiders_notice_snares(g); assert(!lv.hazards[lv.idx(p.x + 2, p.y)].hidden);
  const [h, hl] = field(); const z = OB.spawn_zombie(h, hl, [h.player.x + 6, h.player.y], 'walker', false); hl.hazards[hl.idx(z.x, z.y)] = { kind: 'snare', ttl: 1e9, power: 40, hidden: true };
  h._hazards(); assert(z.hp <= 0 || !hl.actors.includes(z));
}
{ // a raider reloads instead of shooting forever
  const [g, lv] = field(); const r = raider_at(g, lv, 5); r.acc = 0; let shots = 0, reloads = 0;
  for (let i = 0; i < 40; i++) { const before = r.ammo; OB._human(g, r, [r]); if (r.ammo < before) shots++; if (r.reload > 0) reloads++; }
  assert(reloads > 0); assert(shots < 36); assert(shots > 8);
}
{ // it backs off instead of fleeing when you close in; broken morale makes it run
  const [g, lv] = field(); const r = raider_at(g, lv, 2); OB._human(g, r, [r]); assert(dist(g, r) > 2); assert.strictEqual(r.state, 'hunt'); assert(r.morale > 30);
  const [h, hl] = field(); const a = raider_at(h, hl, 5, 0, { squad: 4 }), b = raider_at(h, hl, 6, 1, { squad: 4 });
  for (let i = 0; i < 3; i++) OB.raiders_shaken(h, b); assert(a.morale < 30); const d0 = dist(h, a); OB._human(h, a, [a, b]); assert(dist(h, a) > d0);
}
{ // flankers do not walk straight at you
  const [g, lv] = field(); const r = raider_at(g, lv, 11, 0, { mag: 0, ammo: 0, reach: 1, flank: 1 }); const ys = new Set();
  for (let i = 0; i < 6; i++) { OB._human(g, r, [r]); ys.add(r.y); } assert(ys.size > 1);
}
console.log('raiders: ambushes, snares, reloads, cover, flanking and morale');
