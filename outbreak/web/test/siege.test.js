const assert = require('assert');
const { OB, make, empty_level, teleport } = require('./helpers');

function at_pad(seed = 3) {
  const g = make({ scenario: 'dash', seed }); teleport(g, g.final_site_id + ':0'); empty_level(g.world.level);
  g.player.hp = g.player.max_hp = 1e6; return [g, g.level];
}
const zombies = (lv) => lv.actors.filter((a) => a.kind === 'zombie');

{ // side doors, and a ready check that warns once
  const [g, lv] = at_pad(); assert.strictEqual(g._siege_doors(lv).length, 3);
  assert(!g.use_bench(true)); assert(!g.final); assert(g.log.slice(-2).some((m) => /barricaded/.test(m[1])));
  assert(g.use_bench(true)); assert(g.final);
}
{ // all secured: no warning
  const [g, lv] = at_pad(); for (const d of g._siege_doors(lv)) lv.door_hp[lv.idx(d[0], d[1])] = 40; assert(g.use_bench(true));
}
{ // an open door breaks at once; a barricade holds, then they all come together
  const [g, lv] = at_pad(); g.use_bench(); const f = g.final, [weak, strong] = f.doors;
  lv.door_hp[lv.idx(strong[0], strong[1])] = 40;
  g._siege_wave(f, weak, 3); assert.strictEqual(lv.tile(weak[0], weak[1]), OB.T.DOOR_OPEN); assert.strictEqual(zombies(lv).length, 3);
  g._siege_wave(f, strong, 3); assert.strictEqual(lv.tile(strong[0], strong[1]), OB.T.DOOR); assert.strictEqual(zombies(lv).length, 3);
  for (let i = 0; i < 4; i++) g._siege_wave(f, strong, 3);
  assert.strictEqual(lv.tile(strong[0], strong[1]), OB.T.DOOR_OPEN); assert(zombies(lv).length >= 18);
}
{ // waves speed up
  const [g] = at_pad(); g.use_bench(); const f = g.final;
  f.turns_left = f.total - 2; f.next_wave = 1; g._final_tick(); const early = f.next_wave;
  f.turns_left = 8; f.next_wave = 1; g._final_tick(); assert(f.next_wave < early);
}
{ // a trap hurts the first zombie to step on it
  const [g, lv] = at_pad(), p = g.player;
  p.inventory.push({ id: 'spike_trap', qty: 1, dur: null }); assert(g.use(p.inventory.length - 1));
  const k = lv.idx(p.x, p.y); assert.strictEqual(lv.hazards[k].kind, 'spikes');
  const z = OB.spawn_zombie(g, lv, [p.x + 3, p.y - 3], 'walker', false); const hp = z.hp;
  lv.occ.delete(lv.idx(z.x, z.y)); z.x = p.x; z.y = p.y; lv.occ.set(k, z); p.x += 2; p.y -= 2;
  g._hazards(); assert(!lv.hazards[k]); assert(z.hp < hp || !lv.actors.includes(z));
}
console.log('siege: doors break, barricades hold, waves escalate, traps bite');
