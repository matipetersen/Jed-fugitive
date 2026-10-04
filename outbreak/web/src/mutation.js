// ---------------------------------------------------------------- the strain changes (see engine/mutation.py)
const MUTATION_MAX = 5, MUTATION_RAMP = 12;
const MUTATION_TRAITS = {
  fleet: ['They move faster than they did.', 'speed', 1.12],
  tough: ['They take more killing: the hides are tougher.', 'hp', 1.2],
  keen: ['They hear and see more than they did.', 'senses', 1.2],
  frenzied: ['They hit harder.', 'dmg', 1.2],
  swift: ['They close the distance faster still.', 'speed', 1.1],
};

function mutation_strength(game) {
  return game.profile.mutates * game.era.rules.lab * Math.min(1.0, Math.max(0, game_day(game) - 1) / MUTATION_RAMP);
}
const mutation_special_boost = (game) => 1.0 + 0.6 * mutation_strength(game);

function _mutate(z, trait) {
  const [, stat, k] = MUTATION_TRAITS[trait];
  if (stat === 'speed') z.speed *= k;
  else if (stat === 'hp') { z.hp = Math.floor(z.hp * k); z.max_hp = Math.floor(z.max_hp * k); }
  else if (stat === 'senses') { z.hearing *= k; z.sight *= 1.1; }
  else if (stat === 'dmg') z.dmg = [Math.floor(z.dmg[0] * k), Math.max(Math.floor(z.dmg[0] * k), Math.floor(z.dmg[1] * k))];
}
function mutation_apply(game, z) { for (const t of game.mutations) _mutate(z, t); }

function mutation_daily(game) {
  const s = mutation_strength(game);
  if (s <= 0 || game.mutations.length >= MUTATION_MAX) return;
  if (game.rng.random() >= Math.min(0.8, 0.5 * s)) return;
  const left = Object.keys(MUTATION_TRAITS).filter((t) => !game.mutations.includes(t));
  const trait = left[game.rng.randint(0, left.length - 1)];
  game.mutations.push(trait);
  for (const lv of Object.values(game.levels)) for (const a of lv.actors) if (a.kind === 'zombie') _mutate(a, trait);
  game.msg(`Day ${game_day(game)}: the strain has changed. ${MUTATION_TRAITS[trait][0]}`, 'lore');
}

function mutation_matchup(era, profile) {
  const m = profile.mutates * era.rules.lab;
  const how = m < 0.1 ? 'The strain hardly changes here: the dead of the last day are the dead of the first.'
    : m < 0.4 ? 'The strain changes slowly. Expect a new trait now and then.'
    : m < 0.8 ? 'The strain changes steadily; after a couple of weeks it is not what it was.'
    : 'The strain mutates fast here: expect a new trait every few days, and the strange ones to multiply.';
  return `${era.rules.feel} ${how}`.trim();
}
