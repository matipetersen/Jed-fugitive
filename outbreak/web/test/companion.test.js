const assert = require('assert');
const { OB, make, empty_level } = require('./helpers');

function field(seed = 3, arch = null) {
  const g = make({ seed }), lv = g.world.level, c = OB.comp_current(g);
  for (const a of lv.actors.slice()) if (a !== c) lv.remove_actor(a);
  g.hordes.length = 0; g.ring = null;
  const p = g.player; p.hp = p.max_hp = 1e6; p.infected = false;
  for (let y = p.y - 10; y <= p.y + 10; y++) for (let x = p.x - 12; x <= p.x + 12; x++) lv.set_tile(x, y, OB.T.GRASS);
  if (arch) { c.trait = ''; OB.comp_ensure_person(g, c, arch); }
  return [g, lv, c];
}
const first = (s) => s.split(' ')[0];

{ // you start with one companion from a varied pool
  const seen = new Set();
  for (let seed = 1; seed <= 24; seed++) {
    const g = make({ seed }), c = OB.comp_current(g);
    assert(c); assert.strictEqual(c.state, 'follow'); assert(OB.CONTENT.companions.archetypes.some((a) => a.id === c.trait)); assert(c.name !== 'Survivor'); seen.add(c.trait);
  }
  assert(seen.size >= 5);
  for (const a of OB.CONTENT.companions.archetypes) { assert(a.strength && a.flaw && a.intro && a.farewell); assert.strictEqual(a.backstory.length, 3); }
}
{ // anyone can take the place; only one at a time; a healer is a medic
  const [g, lv, c] = field(); g.companion_uid = 0; c.state = 'patrol';
  const healer = { ...c, uid: 999001, name: 'Healer', role: 'healer', faction: 'enclave', trait: '', state: 'idle', x: c.x + 2, y: c.y };
  lv.add_actor(healer); g.rep.enclave = 40;
  assert.strictEqual(first(OB.ask_join(g, healer)), healer.name); assert.strictEqual(healer.trait, 'medic'); assert.strictEqual(g.companion_uid, healer.uid); assert.strictEqual(healer.state, 'follow');
  const other = { ...healer, uid: 999002, name: 'Trader', role: 'trader', trait: '', state: 'idle', x: healer.x + 1 }; lv.add_actor(other);
  assert(OB.ask_join(g, other).toLowerCase().includes('only one'));
}
{ // strengths
  let [g, lv, c] = field(3, 'medic'); const p = g.player; p.max_hp = 100; p.hp = 30; g.clock.turn = 1000; OB.comp_tick(g); assert(p.hp > 30); assert(g.log.some((m) => m[2] === 'ally'));
  [g, lv, c] = field(3, 'hunter'); const r = OB.make_raider(g, c.x + 4, c.y); r.hidden = true; r.state = 'idle'; lv.add_actor(r); g.clock.turn = 1000; OB.comp_tick(g); assert(!r.hidden);
  [g, lv, c] = field(3, 'scavenger'); g.rng.random = () => 0.0; const n = g.player.inventory.reduce((s, i) => s + i.qty, 0); OB.comp_on_return(g); assert(g.player.inventory.reduce((s, i) => s + i.qty, 0) > n);
  g.rng.random = () => 0.0; g.clock.turn = 50 * 25; const pn = g.pings.length; OB.comp_tick(g); assert(g.pings.length > pn);          // the loud one
  [g, lv, c] = field(3, 'hunter'); g.player.inventory.push({ id: 'food', qty: 3, dur: null, key: false }); c.since = 0; g.clock.turn = 1000; OB.comp_tick(g); assert.strictEqual(g.player.count('food'), 2);
  [g, lv, c] = field(3, 'mechanic'); assert.strictEqual(OB.comp_flee_below(c), 0.6);
  let c2; [g, lv, c2] = field(3, 'preacher'); assert(OB.comp_refuses_to_fight(c2, { kind: 'human' })); assert(!OB.comp_refuses_to_fight(c2, { kind: 'zombie' }));
}
{ // bond: time and gifts up, killing innocents down, a broken bond leaves
  let [g, lv, c] = field(3, 'preacher'); let b = c.bond; g.clock.turn = 100; OB.comp_tick(g); assert(c.bond > b);
  g.player.inventory.push({ id: 'food', qty: 1, dur: null, key: false }); b = c.bond; OB.comp_give(g, c, g.player.inventory.length - 1); assert(c.bond > b);
  b = c.bond; OB.comp_on_player_kills_human(g, { hostile: false }); assert(c.bond < b - 10);
  [g, lv, c] = field(); c.bond = 3; g.clock.turn = 7; OB.comp_tick(g); assert(!OB.comp_current(g)); assert.strictEqual(c.state, 'patrol');
  [g, lv, c] = field(); g.player.humanity = 10; OB.comp_tick(g); assert(!OB.comp_current(g));
}
{ // their story comes out as the bond grows; advice names the next objective
  const [g, lv, c] = field(3, 'veteran'); c.bond = 40; OB.comp_talk(g, c); assert.strictEqual(c.story, 1); c.bond = 90; OB.comp_talk(g, c); OB.comp_talk(g, c); assert.strictEqual(c.story, 3);
  assert(OB.comp_advice(g).includes(c.name));
}
{ // death is permanent and loud; anyone else can follow; the ending remembers
  const [g, lv, c] = field(); const z = OB.spawn_zombie(g, lv, [c.x + 2, c.y], 'walker', false); const name = c.name;
  OB.kill_human_other(g, c, z);
  assert(!OB.comp_current(g)); assert.strictEqual(g.companion_uid, 0); assert.strictEqual(g.fallen_allies[g.fallen_allies.length - 1][0], name);
  assert(g.story.some((m) => m[1].includes('is dead') && m[2] === 'ally')); assert(!lv.actors.includes(c));
  const other = { ...c, uid: 999003, name: 'Soldier', role: 'soldier', faction: 'military', trait: '', state: 'idle', hp: 20, x: g.player.x + 2, y: g.player.y, group: 0 }; lv.add_actor(other); g.rep.military = 30;
  OB.ask_join(g, other); assert.strictEqual(g.companion_uid, other.uid);
  const e = OB.build_ending(g, 'dead', 'test'); assert(e.summary.some((l) => l.includes(name)));
}
{ // the default log is objectives and companion, not noise
  const [g] = field(); g.msg('You swing at the thing and miss.', 'combat'); g.msg('Mina: "hi"', 'ally'); g.msg('Done: x.', 'obj'); g.msg('A horde appears!', 'bad', true);
  const tags = new Set(g.story.map((m) => m[2])); assert(tags.has('ally')); assert(tags.has('obj')); assert(!tags.has('combat')); assert(g.log.some((m) => m[1].includes('swing')));
  g.clock.turn = 10; OB.objective_watch(g); const n = g.story.length; for (const p of Object.values(g.pois)) if (p.component) { p.lead = true; p.revealed = true; } g.clock.turn = 20; OB.objective_watch(g);
  assert(g.story.length >= n);
}
{ // saves keep the companion, the dead and the story
  const [g, lv, c] = field(); g.fallen_allies.push(['Old', 'veteran, 3d, 5 kills']);
  const h = OB.deserialize_game(OB.serialize_game(g)), c2 = OB.comp_current(h);
  assert(c2); assert.strictEqual(c2.name, c.name); assert.strictEqual(c2.trait, c.trait); assert.strictEqual(h.fallen_allies[0][0], 'Old'); assert(h.story.length === g.story.length);
}
console.log('companion: a pool of people, strengths and flaws, bonds, permanent death, and a log that follows the story');
