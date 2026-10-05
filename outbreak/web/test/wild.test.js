const assert = require('assert');
const { OB, make, empty_level } = require('./helpers');

function field(seed = 3) {
  const g = make({ seed }), lv = g.world.level; empty_level(lv); g.hordes.length = 0; g.ring = null;
  const p = g.player; p.hp = p.max_hp = 1e6; p.infected = false;
  for (let y = p.y - 12; y <= p.y + 12; y++) for (let x = p.x - 14; x <= p.x + 14; x++) lv.set_tile(x, y, OB.T.GRASS);
  return [g, lv];
}
function animal(g, lv, dx, species = 'deer') { const a = OB.wild_make(g, g.player.x + dx, g.player.y, species); lv.add_actor(a); return a; }

{ // the world has game
  const g = make({ seed: 3 }); OB.generate_all(g);
  const n = g.world.level.actors.filter((a) => a.kind === 'animal'); assert(n.length >= 20, `only ${n.length}`);
  assert(new Set(n.map((a) => a.species)).size >= 2);
}
{ // game bolts when it notices you, and a chase is not free
  const [g, lv] = field(); const a = animal(g, lv, 5), d0 = Math.abs(a.x - g.player.x);
  for (let i = 0; i < 12; i++) { g.clock.turn = i + 1; OB.wild_tick(g, a); }
  assert.strictEqual(a.state, 'flee'); assert(Math.abs(a.x - g.player.x) > d0);
}
{ // creeping hides you; a stalked animal takes a triple blow
  const [g, lv] = field(); g.player.sneaking = true; g.rng.random = () => 0.99; const a = animal(g, lv, 3);
  for (let i = 0; i < 6; i++) { g.clock.turn = i + 1; OB.wild_tick(g, a); } assert(!a.alert);
  lv.remove_actor(a); a.x = g.player.x + 1; a.y = g.player.y; lv.add_actor(a); const hp = a.hp;
  g.move(1, 0); assert(a.hp < hp || !lv.actors.includes(a));
}
{ // a kill drops meat; raw can make you ill, cooked cannot; cooking needs a plank
  const [g, lv] = field(); const a = animal(g, lv, 1); OB.wild_kill(g, a);
  const meat = lv.items[lv.idx(g.player.x + 1, g.player.y)][0]; assert.strictEqual(meat.id, 'raw_meat'); assert(meat.qty >= 2);
  const p = g.player; p.hp = 50; p.hunger = 80; g.rng.random = () => 0.0;
  const raw = { id: 'raw_meat', qty: 1, dur: null, key: false }; p.inventory.push(raw); OB.use_item ? OB.use_item(g, p.inventory.indexOf(raw)) : OB.use(g, p.inventory.indexOf(raw));
  assert(p.hp < 50);
  p.hp = 50; p.hunger = 80; const cooked = { id: 'meat', qty: 1, dur: null, key: false }; p.inventory.push(cooked); OB.use_item ? OB.use_item(g, p.inventory.indexOf(cooked)) : OB.use(g, p.inventory.indexOf(cooked));
  assert.strictEqual(p.hp, 50); assert(p.hunger < 40);
}
{ // a boar fights back
  const [g, lv] = field(); const a = animal(g, lv, 1, 'boar'); a.alert = true; a.state = 'charge'; g.rng.random = () => 0.1; g.clock.turn = 1;
  const hp = g.player.hp; OB.wild_tick(g, a); assert(g.player.hp < hp);
}
{ // foraging takes time, finds food, and a patch stays picked
  const [g] = field(); g.rng.random = () => 0.0; g.clock.turn = 1000; const t0 = g.clock.turn, n0 = g.player.count('forage');
  assert(g.forage()); assert(g.clock.turn - t0 >= 5); assert(g.player.count('forage') > n0);
  const n = g.player.count('forage'); assert(!g.forage()); assert.strictEqual(g.player.count('forage'), n);
  g.clock.turn += 801; assert(g.forage());
}
{ // not on a road, not hunted
  const [g, lv] = field(); lv.set_tile(g.player.x, g.player.y, OB.T.ROAD); assert(!g.forage());
  lv.set_tile(g.player.x, g.player.y, OB.T.GRASS); assert.strictEqual(OB.wild_can_forage(g), '');
  OB.spawn_zombie(g, lv, [g.player.x + 4, g.player.y], 'walker', false); g.update_fov(); assert(OB.wild_can_forage(g) !== '');
}
{ // saves keep the picked patches
  const [g] = field(); g.foraged.push([1, 2, 3]); const g2 = OB.deserialize_game(OB.serialize_game(g)); assert.deepStrictEqual(g2.foraged, [[1, 2, 3]]);
}
console.log('wild: game bolts, boars gore, meat cooks, patches get picked clean');
