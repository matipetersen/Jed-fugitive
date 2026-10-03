// ---------------------------------------------------------------- creating zombies and raiders
function profile_phase(profile, day) {
  let current = { from_day: 1, name: 'Outbreak', hp: 1, speed: 1, spawn: 1, special: 1, blurb: '' };
  for (const ph of profile.phases) if (day >= ph.from_day) current = ph;
  return current;
}
const profile_name_of = (profile, sid) => profile.names[sid] || CONTENT.specials[sid].name;

function pick_special(rng, profile, day) {
  const phase = profile_phase(profile, day);
  const pairs = [['walker', 10.0]];
  for (const [sid, weight, first_day] of profile.specials) if (day >= first_day) pairs.push([sid, weight * phase.special]);
  return weighted_choice(rng, pairs);
}

function make_zombie(game, special_id, x, y, fresh = false) {
  const profile = game.profile, sp = CONTENT.specials[special_id];
  const day = game_day(game), phase = profile_phase(profile, day);
  const age = fresh ? 0 : game.rng.randint(0, Math.max(0, day - 1));
  const decay = Math.max(0.4, 1.0 - profile.decay * age);
  const hp = Math.max(1, Math.floor(sp.hp * profile.hp_mult * phase.hp * decay));
  const z = {
    kind: 'zombie', uid: game.next_uid(), name: profile_name_of(profile, special_id), glyph: sp.glyph, x, y, hp, max_hp: hp,
    level_id: 'world', special: special_id, dmg: sp.dmg, acc: sp.acc,
    speed: profile.speed * sp.speed * phase.speed * (decay < 1 ? 0.85 : 1.0),
    sight: profile.sight * sp.sight, hearing: profile.hearing * sp.hearing, xp: sp.xp, flags: sp.flags,
    energy: 0, state: 'idle', target: null, stimulus_turn: 0, birth_day: day - age, cooldown: 0, horde: 0,
    carries: [], fresh_human: false, alert: 0, facing: null,
  };
  z.facing = DIRS8[z.uid % 8];                       // which way it looks (derived from the uid: the same for everyone)
  if (sp.flags.includes('boss') || sp.flags.includes('relentless')) z.speed = Math.max(z.speed, 1.0);
  return z;
}

function spawn_zombie(game, level, pos, special = null, dormant = true, fresh = false) {
  const sid = special || pick_special(game.rng, game.profile, game_day(game));
  const z = make_zombie(game, sid, pos[0], pos[1], fresh);
  z.state = dormant && level.kind !== 'overworld' ? 'dormant' : 'idle';
  level.add_actor(z);
  return z;
}

function make_raider(game, x, y) {
  const era = game.era;
  const reach = (era.firearms || era.tech === 0) ? 6 : 1;
  const hp = Math.floor(18 * (1.0 + 0.04 * (game.gen_day ? 1 : game.player.level)));
  const h = { kind: 'human', uid: game.next_uid(), name: 'Raider', glyph: 'R', x, y, hp, max_hp: hp, level_id: 'world',
              role: 'raider', faction: 'raiders', hostile: true, dmg: [3, 6], acc: 48, reach, energy: 0, state: 'idle',
              target: null, loot: [], talked: false };
  if (game.rng.random() < 0.7) h.loot = roll_items(game.rng, era, 'camp', 1.6, game.diff.loot);
  return h;
}

const PATROL_NAMES = {
  scout: { medieval: 'Abbey scout', eighties: 'Fort scout', modern: 'Survivor scout', scifi: 'Dome scout' },
  soldier: { medieval: 'Man-at-arms', eighties: 'Soldier', modern: 'Soldier', scifi: 'Marine' },
};

// A friendly-ish armed walker: an enclave scout or a military soldier.
function make_patrol(game, role, x, y, group) {
  const era = game.era, reach = (era.firearms || era.tech === 0) ? 6 : 1;
  const [hp, dmg, acc, faction] = role === 'scout' ? [24, [3, 6], 52, 'enclave'] : [32, [4, 8], 60, 'military'];
  return { kind: 'human', uid: game.next_uid(), name: PATROL_NAMES[role][era.id], glyph: 'f', x, y, hp, max_hp: hp, level_id: 'world',
           role, faction, hostile: false, dmg, acc, reach, energy: 0, state: 'patrol', target: null, loot: [], talked: false, group, stuck: 0 };
}
