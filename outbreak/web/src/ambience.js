// ---------------------------------------------------------------- the world makes noise too (see engine/ambience.py)
const WEATHER = ['clear', 'rain', 'fog', 'storm'];
const WEATHER_HEARING = { clear: 1.0, rain: 0.7, fog: 0.9, storm: 0.55 };
const WEATHER_SIGHT = { clear: 1.0, rain: 0.8, fog: 0.5, storm: 0.65 };
const WEATHER_PLAYER_SIGHT = { clear: 0, rain: -1, fog: -3, storm: -2 };
const WEATHER_EVERY = 120;
const WEATHER_NEXT = {
  clear: [['clear', 6], ['rain', 2], ['fog', 1]],
  rain: [['clear', 3], ['rain', 4], ['storm', 2], ['fog', 1]],
  fog: [['clear', 4], ['fog', 3], ['rain', 2]],
  storm: [['rain', 4], ['clear', 2], ['storm', 2]],
};
const WEATHER_ARRIVES = {
  rain: 'It starts to rain. Footsteps and voices will not carry far now.',
  fog: 'A thick fog rolls in. You can see little, and so can they.',
  storm: 'The sky goes black. A storm is breaking.',
  clear: 'The weather clears.',
};
const SURFACE_EXTRA = { [T.STAIRS_UP]: 2, [T.STAIRS_DOWN]: 2, [T.DOOR_OPEN]: 1 };
const PLACE_EXTRA = { market: 1, medical: 0, lab: 1, industry: 2, transit: 2, faith: 1, house: 1, guard: 0, military: 0, camp: 0 };
const PLACE_WHY = {
  market: 'Broken glass crunches underfoot.', lab: 'Glass and spilled equipment crunch underfoot.', industry: 'Loose metal rings under your boots.',
  transit: 'Your steps echo off the platforms.', faith: 'Your steps echo in the empty hall.', house: 'The old boards creak.',
};
const STEP_NOTICE_GAP = 40;

const outdoors = (game) => game.level.kind === 'overworld';
const hearing_scale = (game) => outdoors(game) ? (WEATHER_HEARING[game.weather] || 1.0) : 1.0;
const sight_scale = (game) => outdoors(game) ? (WEATHER_SIGHT[game.weather] || 1.0) : 1.0;

function weather_tick(game) {
  const t = game.clock.turn;
  if (t % WEATHER_EVERY === 0 && t > 0) {
    const options = WEATHER_NEXT[game.weather];
    let pick = game.rng.random() * options.reduce((s, o) => s + o[1], 0), nw = options[options.length - 1][0];
    for (const [name, w] of options) { pick -= w; if (pick <= 0) { nw = name; break; } }
    if (nw !== game.weather) { game.weather = nw; if (outdoors(game)) game.msg(WEATHER_ARRIVES[nw], 'info'); }
  }
  if ((game.weather === 'rain' || game.weather === 'storm') && t % 10 === 0) {         // rain washes the trail away
    for (const k of Object.keys(game.scent)) if (t - game.scent[k] >= 40) delete game.scent[k];
  }
  if (game.weather === 'storm' && outdoors(game) && t % 30 === 0 && game.rng.random() < 0.5) _thunder(game);
}

function _thunder(game) {
  const p = game.player, lv = game.level;
  const pos = [Math.max(2, Math.min(lv.w - 3, p.x + game.rng.randint(-26, 26))), Math.max(2, Math.min(lv.h - 3, p.y + game.rng.randint(-26, 26)))];
  game.msg('Thunder cracks overhead.', 'info');
  emit_on(game, lv, pos, 16, 'world');
}

function step_extra(game, tile) {
  let extra = SURFACE_EXTRA[tile] || 0;
  const lv = game.level;
  if (lv.kind === 'interior') extra += PLACE_EXTRA[game.poi_kind_of(lv)] || 0;
  return extra;
}

function explain_step(game, tile) {
  const lv = game.level;
  let why = '';
  if (lv.kind === 'interior') why = PLACE_WHY[game.poi_kind_of(lv)] || '';
  else if (tile === T.SHALLOW) why = 'You splash through the shallows.';
  if (why && game.clock.turn - game.last_step_note >= STEP_NOTICE_GAP && !game.player.sneaking) { game.last_step_note = game.clock.turn; game.msg(why, 'info'); }
}

function exposure_of_ground(game) {
  const t = game.level.tile(game.player.x, game.player.y);
  return t === T.ROAD ? 1.2 : t === T.SHALLOW ? 1.25 : 1.0;
}

function emit_on(game, level, pos, radius, source = 'world') {              // noise on any level: an alarm in a building is heard in the street
  const prev = game.level;
  game.level = level;
  try { game.emit_noise(pos, radius, source); } finally { game.level = prev; }
}

function _say_direction(game, pos, text) {
  const p = game.player;
  if (game.level.kind === 'overworld' && cheb(pos, [p.x, p.y]) <= 16 * 1.3) game.msg(`${text} (${compass(pos[0] - p.x, pos[1] - p.y)})`, 'warn');
}

function _random_spot(game, lo, hi) {
  const p = game.player, lv = game.world.level;
  for (let i = 0; i < 30; i++) {
    const x = p.x + game.rng.randint(-hi, hi), y = p.y + game.rng.randint(-hi, hi), d = cheb([x, y], [p.x, p.y]);
    if (d >= lo && d <= hi && x > 2 && x < lv.w - 2 && y > 2 && y < lv.h - 2 && lv.walkable(x, y)) return [x, y];
  }
  return null;
}

function world_tick(game) {
  const t = game.clock.turn;
  for (const s of game.sources.slice()) {
    if (t % s.every === 0) emit_on(game, game.world.level, s.pos, s.radius, 'world');
    s.left -= 1;
    if (s.left <= 0) game.sources.splice(game.sources.indexOf(s), 1);
  }
  if (game.level.kind !== 'overworld' || t % 20 !== 0 || t < 100) return;
  if (game.rng.random() >= 0.18 + 0.05 * Math.min(6.0, game.pressure)) return;
  const pos = _random_spot(game, 12, 34);
  if (!pos) return;
  if (game.rng.random() < 0.55) {
    game.sources.push({ pos, radius: 15, every: 3, left: 24, kind: 'car alarm' });
    _say_direction(game, pos, 'A car alarm starts to wail somewhere out there.');
  } else {
    emit_on(game, game.world.level, pos, 14, 'world');
    _say_direction(game, pos, 'Something heavy collapses in the distance.');
  }
}

function building_alarm(game, poi) {
  if (game.alarmed.includes(poi.id) || !['market', 'guard', 'military', 'lab'].includes(poi.kind)) return;
  game.alarmed.push(poi.id);
  if (game.rng.random() >= 0.3) return;
  game.msg('An alarm shrieks through the building. They will hear that outside!', 'bad', true);
  const pos = poi_pos(poi);
  game.sources.push({ pos, radius: 20, every: 3, left: 21, kind: 'building alarm' });
  emit_on(game, game.world.level, pos, 20, 'world');
}

function startle(game, tile) {
  if (tile !== T.BRUSH || game.player.sneaking || game.clock.is_night) return;
  if (game.rng.random() < 0.06) { game.msg('A flock of crows bursts out of the brush!', 'warn'); game.emit_noise([game.player.x, game.player.y], 9, 'world'); }
}
