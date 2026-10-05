// ---------------------------------------------------------------- game to hunt and plants to gather (mirror of engine/wild.py)
const WILD_SPECIES = {                 // hp, glyph, meat [min, max], notice radius, dmg when cornered, spawn weight
  rabbit: [4, 'r', [1, 1], 5, [0, 0], 50],
  deer: [14, 'd', [2, 3], 7, [0, 0], 35],
  boar: [20, 'b', [2, 3], 4, [3, 7], 15],
};
const WILD_NAMES = { rabbit: 'Rabbit', deer: 'Deer', boar: 'Boar' };
const WILD_FORAGE_TURNS = 5, WILD_PATCH_TURNS = 800, WILD_SNEAK_BLOW = 3.0;
const wild_grazing = (t) => t === T.GRASS || t === T.BRUSH;

function wild_make(game, x, y, species) {
  const [hp, glyph] = WILD_SPECIES[species];
  return { kind: 'animal', uid: game.next_uid(), name: WILD_NAMES[species], glyph, x, y, hp, max_hp: hp, level_id: 'world', lvl: 1, lvl_xp: 0, title: '', stun: 0,
           species, state: 'graze', alert: false };
}

function wild_pick_species(rng) {
  let r = rng.random() * 100;
  for (const [k, v] of Object.entries(WILD_SPECIES)) { r -= v[5]; if (r < 0) return k; }
  return 'rabbit';
}

function wild_step_away(game, a) {
  const lv = game.level, p = game.player;
  let best = null, best_d = cheb(apos(a), apos(p));
  for (const [dx, dy] of DIRS8) {
    const n = [a.x + dx, a.y + dy];
    if (lv.free(n[0], n[1]) && (wild_grazing(lv.tile(n[0], n[1])) || lv.tile(n[0], n[1]) === T.ROAD) && cheb(n, apos(p)) > best_d) { best = n; best_d = cheb(n, apos(p)); }
  }
  return best;
}

function wild_tick(game, a) {
  const p = game.player, lv = game.level, t = game.clock.turn;
  if (lv.kind !== 'overworld') return;
  const d = cheb(apos(a), apos(p));
  let radius = WILD_SPECIES[a.species][3];
  if (p.sneaking) radius = Math.max(2, radius - 3);
  if (!a.alert && d <= radius && has_los(lv, apos(a), apos(p)) && (!p.sneaking || game.rng.random() < 0.4)) {
    a.alert = true; a.state = (a.species === 'boar' && d <= 3) ? 'charge' : 'flee';
  }
  if (a.alert && d > radius + 6) { a.alert = false; a.state = 'graze'; }
  if (a.state === 'flee') {
    if (t % 3) { const nxt = wild_step_away(game, a); if (nxt) lv.move_actor(a, nxt[0], nxt[1]); }
    return;
  }
  if (a.state === 'charge') {
    if (d === 1) {
      const [lo, hi] = WILD_SPECIES[a.species][4];
      if (game.rng.random() < 0.7) {
        const dmg = game.rng.randint(lo, hi);
        game.msg(`The ${a.name.toLowerCase()} gores you for ${dmg}.`, 'combat');
        p.hp -= dmg;
        if (p.hp <= 0) game.end('dead', 'gored by a boar');
      }
    } else if (d <= 8) {
      const nxt = greedy_step(lv, apos(a), apos(p), game.rng, (n) => wild_grazing(lv.tile(n[0], n[1])) || lv.tile(n[0], n[1]) === T.ROAD);
      if (nxt && lv.free(nxt[0], nxt[1])) lv.move_actor(a, nxt[0], nxt[1]);
    }
    return;
  }
  if (game.rng.random() < 0.18) {
    const [dx, dy] = game.rng.choice(DIRS8), n = [a.x + dx, a.y + dy];
    if (lv.free(n[0], n[1]) && wild_grazing(lv.tile(n[0], n[1]))) lv.move_actor(a, n[0], n[1]);
  }
}

function wild_attack(game, a, unaware, acc, dmg) {
  if (!unaware && game.rng.random() * 100 >= acc) {
    game.msg(`You swing at the ${a.name.toLowerCase()} and miss.`, 'combat');
    a.alert = true; a.state = a.species === 'boar' ? 'charge' : 'flee';
    return true;
  }
  const hurt = Math.max(1, Math.trunc(dmg * (unaware ? WILD_SNEAK_BLOW : 1.0)));
  a.hp -= hurt;
  if (a.hp <= 0) { wild_kill(game, a); return true; }
  a.alert = true; a.state = a.species === 'boar' ? 'charge' : 'flee';
  game.msg(`You hit the ${a.name.toLowerCase()} for ${hurt}.`, 'combat');
  return true;
}

function wild_kill(game, a) {
  const lv = game.level;
  lv.remove_actor(a);
  const [lo, hi] = WILD_SPECIES[a.species][2], n = game.rng.randint(lo, hi);
  lv.drop(apos(a), make_item('raw_meat', n));
  game.player.gain_xp(3);
  game.player.bump('game');
  game.msg(`The ${a.name.toLowerCase()} drops. ${n} cut${n !== 1 ? 's' : ''} of meat lie there: pick it up, and cook it.`, 'good');
}

function wild_can_forage(game) {
  const p = game.player, lv = game.level;
  if (lv.kind !== 'overworld') return 'There is nothing to gather indoors.';
  if (!wild_grazing(lv.tile(p.x, p.y))) return 'Nothing edible grows on this. Try grass or brush.';
  if (game.visible_hostiles().length) return 'Not with something hunting you.';
  return '';
}

function wild_forage(game) {
  if (!game._begin_action()) return false;
  const why = wild_can_forage(game);
  if (why) { game.msg(why, 'info'); return false; }
  const p = game.player, lv = game.level, t = game.clock.turn;
  const patches = game.foraged;
  if (patches.some(([x, y, when]) => cheb([x, y], apos(p)) <= 2 && t - when < WILD_PATCH_TURNS)) { game.msg('This patch is already picked over. Move on.', 'info'); return false; }
  for (let i = 0; i < WILD_FORAGE_TURNS; i++) {
    game._spend(1);
    if (game.over) return true;
    if (game.visible_hostiles().length) { game.msg('You stop gathering: something is coming.', 'warn'); return true; }
  }
  game.emit_noise(apos(p), 2, 'player');
  patches.push([p.x, p.y, t]);
  let chance = lv.tile(p.x, p.y) === T.BRUSH ? 0.8 : 0.5;
  if (game.weather === 'rain' || game.weather === 'fog') chance += 0.1;
  if (!game.clock.is_day) chance -= 0.25;
  if (game.rng.random() < chance) {
    const n = game.rng.randint(1, 3);
    game.give_item(make_item('forage', n));
    game.msg(`You gather wild greens and berries (${n}).`, 'good');
  } else game.msg('You find nothing worth eating here.', 'info');
  return true;
}

// ---------------------------------------------------------------- trees and water
const WILD_CHOP_TURNS = { blade: 6, blunt: 9, polearm: 9 }, WILD_CHOP_NOISE = 8;

function wild_tree_beside(game) {
  const p = game.player, lv = game.level;
  if (lv.kind !== 'overworld') return null;
  for (const [dx, dy] of DIRS8) {
    const x = p.x + dx, y = p.y + dy;
    if (lv.in_bounds(x, y) && lv.tile(x, y) === T.TREE && x > 0 && y > 0 && x < lv.w - 1 && y < lv.h - 1) return [x, y];      // the rim of the world is not for felling
  }
  return null;
}

function wild_water_beside(game) {
  const p = game.player, lv = game.level;
  if (lv.kind !== 'overworld') return null;
  if (lv.tile(p.x, p.y) === T.SHALLOW) return [p.x, p.y];
  for (const [dx, dy] of DIRS8) {
    const x = p.x + dx, y = p.y + dy;
    if (lv.in_bounds(x, y) && (lv.tile(x, y) === T.WATER || lv.tile(x, y) === T.SHALLOW)) return [x, y];
  }
  return null;
}

function wild_chop(game) {
  if (!game._begin_action()) return false;
  const tree = wild_tree_beside(game), p = game.player, lv = game.level;
  if (!tree) { game.msg('There is no tree within reach.', 'info'); return false; }
  const w = p.weapon ? game.item_def(p.weapon.id) : null, turns = w ? WILD_CHOP_TURNS[w.style] : undefined;
  if (turns === undefined) { game.msg('You need something with an edge or some weight to cut with.', 'info'); return false; }
  if (game.visible_hostiles().length) { game.msg('Not with something hunting you.', 'info'); return false; }
  for (let i = 0; i < turns; i++) {
    game._spend(1);
    if (game.over) return true;
    if (i % 3 === 0) game.emit_noise(apos(p), WILD_CHOP_NOISE, 'player');
    if (game.visible_hostiles().length) { game.msg('You stop chopping: something is coming.', 'warn'); return true; }
  }
  lv.set_tile(tree[0], tree[1], T.GRASS);
  const n = game.rng.randint(2, 4);
  game.give_item(make_item('wood', n));
  game.msg(`The tree comes down. ${n} planks, and a clearing where it stood.`, 'good');
  return true;
}

function wild_fish(game) {
  if (!game._begin_action()) return false;
  const p = game.player;
  const gear = p.inventory.find((i) => game.item_def(i.id).effect.fish);
  if (!gear) { game.msg('You have nothing to fish with. Craft a rod or a net.', 'info'); return false; }
  if (game.visible_hostiles().length) { game.msg('Not with something hunting you.', 'info'); return false; }
  const eff = game.item_def(gear.id).effect, most = eff.fish === 1 ? 1 : eff.fish, turns = most === 1 ? 8 : 12;
  for (let i = 0; i < turns; i++) {
    game._spend(1);
    if (game.over) return true;
    if (game.visible_hostiles().length) { game.msg('You stop fishing: something is coming.', 'warn'); return true; }
  }
  let chance = most === 1 ? 0.55 : 0.7;
  if (game.weather === 'rain' || game.weather === 'fog') chance += 0.1;
  if (!game.clock.is_day) chance -= 0.2;
  if (game.rng.random() < chance) {
    const n = game.rng.randint(1, most);
    game.give_item(make_item('fish', n));
    game.msg(n > 1 ? `You land ${n} fish.` : 'You land a fish.', 'good');
  } else game.msg('Nothing bites.', 'info');
  if (game.rng.random() < (eff.tear || 0)) {
    p.take(gear.id, 1);
    game.msg(`Your ${game.item_def(gear.id).name.toLowerCase()} ${most > 1 ? 'tears apart' : 'snaps'}.`, 'warn');
  }
  return true;
}

function wild_target(game) {
  if (wild_tree_beside(game) && game.player.weapon) return 'chop';
  if (wild_water_beside(game) && game.player.inventory.some((i) => game.item_def(i.id).effect.fish)) return 'fish';
  return wild_can_forage(game) ? '' : 'forage';
}

function wild_gather(game) {
  const what = wild_target(game);
  if (what === 'chop') return wild_chop(game);
  if (what === 'fish') return wild_fish(game);
  if (what === 'forage') return wild_forage(game);
  if (wild_tree_beside(game)) game.msg('You need a weapon with an edge or some weight to fell a tree.', 'info');
  else if (wild_water_beside(game)) game.msg('You have nothing to fish with. Craft a rod or a net.', 'info');
  else game.msg(wild_can_forage(game) || 'Nothing to gather here.', 'info');
  return false;
}
