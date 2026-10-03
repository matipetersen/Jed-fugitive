// ---------------------------------------------------------------- behaviour of the living and the dead
const ACTIVE_RADIUS = 45, FIELD_RADIUS = 28, DOOR_HP = 8, LOST_AFTER = 14, FOE_SIGHT = 5, HUMAN_SIGHT = 8;
const FIGHTERS = ['raider', 'scout', 'soldier'];
const same = (a, b) => !!a && !!b && a[0] === b[0] && a[1] === b[1];

function sight_range(game, z) {
  if (z.flags.includes('blind')) return 0.0;
  const prof = game.profile, p = game.player;
  let r = z.sight;
  if (game.is_dark()) {
    r *= 0.6 * prof.night_sight;
    if (player_lit(game)) r = Math.max(r, 6.0) * 1.7;
  }
  if (p.sneaking) r *= 0.5;
  if (game.level.tile(p.x, p.y) === T.BRUSH) r *= 0.5;
  if (p.disguise_turns > 0 && prof.intel < 2 && (z.uid * 37) % 100 < prof.disguise * 100) r = Math.min(r, 1.5);
  return r;
}

function sees_player(game, z) {
  const p = game.player, r = sight_range(game, z);
  if (r <= 0 || dist(apos(z), apos(p)) > r) return false;
  return has_los(game.level, apos(z), apos(p));
}

function speed_now(game, z) {
  let s = z.speed;
  if (game.is_dark()) s *= game.profile.night_speed;
  else if (game.clock.is_day) s *= game.profile.day_speed;
  if (z.state === 'idle') s *= 0.5;
  return s;
}

function ai_run(game) {
  const level = game.level, p = game.player;
  const humans = level.actors.filter((a) => a.kind === 'human' && a.hp > 0 && FIGHTERS.includes(a.role));
  for (const a of level.actors.slice()) {
    if (a.hp <= 0 || level.occ.get(level.idx(a.x, a.y)) !== a || cheb(apos(a), apos(p)) > ACTIVE_RADIUS) continue;
    if (a.kind === 'zombie') _zombie(game, a, humans);
    else if (a.kind === 'human') _human(game, a, humans);
  }
}

function _zombie(game, z, humans) {
  const prof = game.profile, level = game.level;
  if (z.cooldown > 0) z.cooldown -= 1;
  if (prof.sun_burn && level.kind === 'overworld' && game.clock.is_day) {
    z.hp -= 2;
    if (z.hp <= 0) { kill_zombie(game, z, false, false); return; }
  }
  z.energy += speed_now(game, z);
  let steps = 0;
  while (z.energy >= 1.0 && steps < 3 && z.hp > 0 && level.occ.get(level.idx(z.x, z.y)) === z) {
    z.energy -= 1.0; steps++;
    _zombie_step(game, z, humans);
  }
}

// The closest living foe of `a` within `limit` that it can see, or null.
function nearest_foe(game, a, foes, limit) {
  const level = game.level;
  let best = null, best_d = limit + 1;
  for (const f of foes) {
    if (f === a || f.hp <= 0) continue;
    const d = cheb(apos(a), apos(f));
    if (d < best_d && has_los(level, apos(a), apos(f))) { best = f; best_d = d; }
  }
  return best;
}

function _zombie_fight(game, z, foe) {
  z.state = 'hunt'; z.target = apos(foe); z.stimulus_turn = game.clock.turn;
  if (cheb(apos(z), apos(foe)) === 1) { attack_actor(game, z, foe); return; }
  const nxt = greedy_step(game.level, apos(z), apos(foe), game.rng, (n) => _passable(game, z, n));
  if (nxt !== null) _move_or_bash(game, z, nxt);
}

function _zombie_step(game, z, humans) {
  const p = game.player, prof = game.profile, turn = game.clock.turn;
  const d = cheb(apos(z), apos(p));
  const seen = sees_player(game, z);
  if (humans && humans.length && z.state !== 'dormant') {
    const foe = nearest_foe(game, z, humans, FOE_SIGHT);
    if (foe !== null && (!seen || cheb(apos(z), apos(foe)) < d)) { _zombie_fight(game, z, foe); return; }
  }
  if (z.state === 'dormant') {
    if (seen && d <= Math.max(2.0, sight_range(game, z) * 0.5)) z.state = 'hunt'; else return;
  }
  if (seen) {
    if (z.state !== 'hunt') _spotted(game, z);
    z.state = 'hunt'; z.target = apos(p); z.stimulus_turn = turn;
  } else if (z.state === 'hunt') _lost_sight(game, z, d);
  if (prof.dormant_after && (z.state === 'hunt' || z.state === 'investigate') && turn - z.stimulus_turn > prof.dormant_after) {
    z.state = 'dormant'; z.target = null; return;
  }
  if ((z.state === 'hunt' || z.state === 'investigate') && z.target !== null) _pursue(game, z, d, seen);
  else if (z.state === 'idle' && game.level.kind === 'overworld' && game.rng.random() < 0.35) _wander(game, z);
}

function _spotted(game, z) {
  if (z.flags.includes('screams') && z.cooldown <= 0) {
    z.cooldown = 40;
    game.msg(`The ${z.name.toLowerCase()} screams!`, 'warn');
    game.emit_noise(apos(z), 22, 'zombie');
    game.add_heat(6);
  }
}

function _lost_sight(game, z, d) {
  const p = game.player, prof = game.profile;
  if (z.flags.includes('relentless') && d <= 45) { z.target = apos(p); return; }
  if (prof.smell && game.clock.turn - z.stimulus_turn < 25) {
    const spot = game.scent_near(apos(z), prof.smell);
    if (spot) { z.target = spot; return; }
  }
  if (game.clock.turn - z.stimulus_turn > LOST_AFTER) { z.state = 'idle'; z.target = null; }
}

function _pursue(game, z, d, seen) {
  const p = game.player, level = game.level;
  if (d === 1 && (seen || same(z.target, apos(p)))) { zombie_attack(game, z); return; }
  if (z.flags.includes('leaps') && seen && d >= 2 && d <= 4 && z.cooldown <= 0) {
    const spot = level.free_spot_near(p.x, p.y, 1);
    if (spot && cheb(spot, apos(z)) <= 4) {
      level.move_actor(z, spot[0], spot[1]);
      z.cooldown = 8;
      game.msg(`The ${z.name.toLowerCase()} leaps at you!`, 'bad');
      zombie_attack(game, z);
      return;
    }
  }
  if (z.target !== null && cheb(apos(z), z.target) === 0) {
    if (z.state === 'investigate') { z.state = 'idle'; z.target = null; }
    return;
  }
  let nxt = null;
  if (same(z.target, apos(p))) {
    const field = game.get_field();
    if (field[level.idx(z.x, z.y)] >= 0) nxt = descend(level, field, apos(z), game.rng, _hazard_tiles(game, z));
  }
  if (nxt === null && z.target !== null) nxt = greedy_step(level, apos(z), z.target, game.rng, (n) => _passable(game, z, n));
  if (nxt === null) { if (z.state === 'investigate') { z.state = 'idle'; z.target = null; } return; }
  _move_or_bash(game, z, nxt);
}

function _passable(game, z, pos) {
  const t = game.level.tile(pos[0], pos[1]);
  if (NO_ENTRY.has(t)) return false;
  if (t === T.FENCE) return !!game.profile.swarm;
  const hz = game.level.hazards[game.level.idx(pos[0], pos[1])];
  return !(hz && hz.kind === 'fire' && game.profile.intel >= 1);
}

function _hazard_tiles(game, z) {
  if (game.profile.intel < 1) return null;
  const out = new Set();
  for (const [k, hz] of Object.entries(game.level.hazards)) if (hz.kind === 'fire') out.add(+k);
  return out;
}

function _move_or_bash(game, z, nxt) {
  const level = game.level, t = level.tile(nxt[0], nxt[1]);
  if (NO_ENTRY.has(t)) return;
  if (t === T.DOOR) {
    if (game.profile.intel >= 1) { level.set_tile(nxt[0], nxt[1], T.DOOR_OPEN); return; }
    _bash_door(game, z, nxt);
    return;
  }
  if (level.occ.has(level.idx(nxt[0], nxt[1]))) return;
  level.move_actor(z, nxt[0], nxt[1]);
}

function _bash_door(game, z, pos) {
  const level = game.level, k = level.idx(pos[0], pos[1]);
  let power = z.flags.includes('breaker') ? 6 : 2;
  if (game.profile.swarm) {
    let n = 0;
    for (const [dx, dy] of DIRS8) { const o = level.occ.get(level.idx(pos[0] + dx, pos[1] + dy)); if (o && o.kind === 'zombie') n++; }
    power *= 1 + n;
  }
  const hp = (level.door_hp[k] === undefined ? DOOR_HP : level.door_hp[k]) - power;
  level.door_hp[k] = hp;
  game.emit_noise(pos, 6, 'zombie');
  if (hp <= 0) {
    level.set_tile(pos[0], pos[1], T.FLOOR);
    delete level.door_hp[k];
    if (cheb(pos, apos(game.player)) <= 12) game.msg('A door splinters and gives way.', 'warn');
  }
}

function _wander(game, z) {
  const [dx, dy] = game.rng.choice(DIRS8);
  const n = [z.x + dx, z.y + dy], level = game.level;
  if (level.walkable(n[0], n[1]) && _passable(game, z, n) && !level.occ.has(level.idx(n[0], n[1])) && level.tile(n[0], n[1]) !== T.DOOR) {
    level.move_actor(z, n[0], n[1]);
  }
}

// Everything this human will shoot at that is not the player: the dead, and the other side.
function _foes_of(h, game, humans) {
  const out = game.level.actors.filter((z) => z.kind === 'zombie' && z.hp > 0);
  const mine = h.faction === 'raiders';
  for (const o of humans) if (o !== h && (o.faction === 'raiders') !== mine) out.push(o);
  return out;
}

function _human(game, h, humans) {
  if (!FIGHTERS.includes(h.role)) return;                       // shopkeepers and healers keep out of it
  const p = game.player, level = game.level;
  const d = cheb(apos(h), apos(p));
  const seen = h.hostile && d <= 11 && has_los(level, apos(h), apos(p));
  const foe = nearest_foe(game, h, _foes_of(h, game, humans), h.reach > 1 ? HUMAN_SIGHT : FOE_SIGHT);
  if (foe !== null && !(seen && d < cheb(apos(h), apos(foe)))) { _human_fight(game, h, foe); return; }
  if (seen) { h.state = 'hunt'; h.target = apos(p); }
  if (h.state === 'patrol') { _patrol_step(game, h); return; }
  if (h.state !== 'hunt' || !h.hostile) return;
  if (h.hp < h.max_hp * 0.3 && seen) { _flee(game, h, apos(p)); return; }
  if (h.reach > 1 && seen && d >= 2 && d <= h.reach) { human_attack(game, h); return; }
  if (d === 1) { human_attack(game, h); return; }
  const field = game.get_field();
  let nxt = field[level.idx(h.x, h.y)] >= 0 ? descend(level, field, apos(h), game.rng) : null;
  if (nxt === null) nxt = greedy_step(level, apos(h), apos(p), game.rng, (n) => !NO_ENTRY.has(level.tile(n[0], n[1])));
  _human_move(game, h, nxt);
}

function _human_move(game, h, nxt) {
  const level = game.level;
  if (nxt && !level.occ.has(level.idx(nxt[0], nxt[1])) && !NO_ENTRY.has(level.tile(nxt[0], nxt[1]))) {
    if (level.tile(nxt[0], nxt[1]) === T.DOOR) level.set_tile(nxt[0], nxt[1], T.DOOR_OPEN);
    else level.move_actor(h, nxt[0], nxt[1]);
    return true;
  }
  return false;
}

function _human_fight(game, h, foe) {
  const level = game.level, d = cheb(apos(h), apos(foe));
  if (h.hp < h.max_hp * 0.3 && foe.kind === 'zombie' && d <= 2) { _flee(game, h, apos(foe)); return; }
  if (h.reach > 1 && d >= 2 && d <= h.reach) attack_actor(game, h, foe, true);
  else if (d === 1) attack_actor(game, h, foe, false);
  else _human_move(game, h, greedy_step(level, apos(h), apos(foe), game.rng, (n) => !NO_ENTRY.has(level.tile(n[0], n[1]))));
}

// Walk to the group's current waypoint, every other tick; pick a new one on arrival.
function _patrol_step(game, h) {
  if (game.clock.turn % 2) return;
  const goals = game.patrol_goals;
  let goal = goals[h.group];
  if (!goal || cheb(apos(h), goal) <= 2 || h.stuck > 8) {
    const nodes = game.patrol_nodes;
    if (!nodes.length) return;
    goal = game.rng.choice(nodes); goals[h.group] = goal; h.stuck = 0;
  }
  const level = game.level;
  const nxt = greedy_step(level, apos(h), goal, game.rng, (n) => !NO_ENTRY.has(level.tile(n[0], n[1])));
  if (nxt === null || !_human_move(game, h, nxt)) h.stuck += 1;
}

function _flee(game, h, away_from) {
  const level = game.level;
  let best = null, best_d = cheb(apos(h), away_from);
  for (const [dx, dy] of DIRS8) {
    const n = [h.x + dx, h.y + dy];
    if (level.free(n[0], n[1]) && !NO_ENTRY.has(level.tile(n[0], n[1])) && cheb(n, away_from) > best_d) { best = n; best_d = cheb(n, away_from); }
  }
  if (best) level.move_actor(h, best[0], best[1]);
}
