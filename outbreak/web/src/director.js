// ---------------------------------------------------------------- the Director: the hero's journey as a pacing chart (mirror of engine/director.py)
const DIR_STAGES = CONTENT.director.stages;
const DIR_SAMPLE_EVERY = 5, DIR_TELEGRAPH = 10, DIR_MERCY_HP = 0.35, DIR_PEAK_MAX = 130;

function dir_state(game) {
  if (!game.director) {
    game.director = { stage: 0, tension: 0, phase: 'build', phase_until: 0, hp_last: game.player.hp, damage: 0, pending: [], done: [], threats: 0, last_threat: -999, mercy: 0 };
    game.director.phase_until = game.clock.turn + game.rng.randint(DIR_STAGES[0].wait[0], DIR_STAGES[0].wait[1]);
  }
  return game.director;
}

function dir_progress(game) {
  const sc = game.scenario;
  if (sc.escalates) return (((game.clock.turn / 240.0) % 9.0) / 9.0) * 0.95;
  const reqs = game.requirements(), r = reqs.length ? reqs.filter((q) => q[1]).length / reqs.length : 0.0;
  const horizon = 240.0 * (game.deadline_days || 10), c = Math.min(1.0, game.clock.turn / horizon);
  let s = 0.65 * r + 0.35 * c;
  const site = game.pois[game.final_site_id];
  if (site && site.revealed) s += 0.04;
  if (game.final) s = Math.max(s, 0.92);
  return Math.min(1.0, s);
}

function dir_stage_index(s) { let idx = 0; DIR_STAGES.forEach((st, i) => { if (s >= st.start) idx = i; }); return idx; }

function dir_power(game) {
  const p = game.player, w = p.weapon ? game.item_def(p.weapon.id) : null;
  return 1.0 + 0.12 * (p.level - 1) + (p.armor ? 0.3 : 0.0) + (w && (w.dmg[0] + w.dmg[1]) >= 9 ? 0.2 : 0.0) + (comp_current(game) ? 0.35 : 0.0);
}

function dir_sample(game, d) {
  const p = game.player;
  d.damage = d.damage * 0.9 + Math.max(0, d.hp_last - p.hp) * 2.0;
  d.hp_last = p.hp;
  const raw = 10.0 * Math.min(4, game.visible_hostiles().length) + p.panic * 0.4 + game.heat * 0.25 + d.damage;
  d.tension = Math.min(100.0, Math.max(raw, d.tension * 0.95));
}

function dir_in_trouble(game) {
  const p = game.player, meds = ['medkit', 'bandage'].filter((i) => game.items[i]).reduce((s, i) => s + p.count(i), 0);
  return p.hp < p.max_hp * DIR_MERCY_HP || (p.bleeding && meds === 0 && p.hp < p.max_hp * 0.6);
}

// multiplier on the world's own threat generation (wanderers, random events)
function dir_scale(game) {
  const d = game.director;
  if (!d) return 1.0;
  const st = DIR_STAGES[d.stage];
  let base = { build: 1.0, peak: 1.35, release: 0.2 }[d.phase] * (0.5 + st.peak / 100.0);
  if (d.stage <= 3) base = Math.min(base, 0.6);
  return Math.max(0.1, base);
}

function dir_event_bias(game, id) {
  const d = game.director;
  if (!d) return 1.0;
  if (CONTENT.director.relief_events.includes(id)) return { release: 2.5, build: 1.0, peak: 0.4 }[d.phase];
  if (CONTENT.director.threat_events.includes(id)) return { release: 0.2, build: 1.0, peak: 1.8 }[d.phase];
  return 1.0;
}

function dir_status(game) {
  const d = game.director;
  if (!d) return '';
  const st = DIR_STAGES[d.stage], n = Math.floor(d.tension / 20);
  return `Act ${d.stage + 1}/${DIR_STAGES.length} ${st.title}  [${'#'.repeat(n)}${'.'.repeat(5 - n)}] ${d.phase}`;
}

function dir_tick(game) {
  const t = game.clock.turn, d = dir_state(game);
  if (t % DIR_SAMPLE_EVERY) return;
  dir_sample(game, d); dir_stage(game, d, t); dir_due(game, d, t);
  if (game.level !== game.world.level || game.final || game.pending_event) return;
  const st = DIR_STAGES[d.stage];
  if (dir_in_trouble(game) && d.phase !== 'release') {
    d.phase = 'release'; d.phase_until = t + Math.floor(st.release / 2); d.mercy += 1;
    game.msg('A lull falls. Whatever was after you has lost the scent.', 'dir');
    return;
  }
  if (d.phase === 'build' && t >= d.phase_until && d.tension < Math.max(12, st.peak * 0.45) && !d.pending.length) dir_threat(game, d, st, t);
  else if (d.phase === 'peak' && !d.pending.length && (t >= d.phase_until || (d.tension < 25 && t - d.last_threat > 50))) {
    d.phase = 'release'; d.phase_until = t + st.release; game.msg('It passes. For now, the road is yours.', 'dir');
  } else if (d.phase === 'release' && t >= d.phase_until) { d.phase = 'build'; d.phase_until = t + game.rng.randint(st.wait[0], st.wait[1]); }
}

function dir_stage(game, d, t) {
  let idx = dir_stage_index(dir_progress(game));
  if (game.scenario.escalates) idx = Math.min(idx, DIR_STAGES.length - 2);
  else if (idx < d.stage) idx = d.stage;                      // a story does not run backwards
  if (d.done.length && idx === d.stage) return;
  const first = !d.done.length;
  d.stage = idx;
  const st = DIR_STAGES[idx];
  if (d.done.includes(st.id) && !game.scenario.escalates) return;
  if (!d.done.includes(st.id)) d.done.push(st.id);
  const goal = (game.objectives().find((o) => !o[1]) || ['see it through'])[0];
  if (!first) {
    game.msg(`ACT ${idx + 1}: ${st.title}.`, 'dir', true);
    game.msg(st.cue.replace('{goal}', goal).replace('{refuge}', game.era.refuge), 'dir');
  }
  const c = comp_current(game), lines = CONTENT.director.act_lines[st.id];
  if (c && lines && t > 30) comp_say(game, c, lines[0]);
  d.phase = 'build'; d.phase_until = t + game.rng.randint(st.wait[0], st.wait[1]);
  dir_beat(game, d, st, t);
}

function dir_beat(game, d, st, t) {
  if (st.beat === 'call') game.reveal_random_lead();
  else if (st.beat === 'mentor') { if (game.reveal_random_lead()) game.msg('A scrap of knowledge from the road: someone tells you where to look.', 'dir'); }
  else if (st.beat === 'allies') pets_stray_beat(game);
  else if (st.beat === 'threshold') { d.pending.push([t + 15, 'horde', 3]); game.msg('The first test is on its way. Be ready.', 'dir'); }
  else if (st.beat === 'approach') {
    const site = game.pois[game.final_site_id];
    if (site && !site.revealed) { site.revealed = true; game.msg(`You learn where it is: ${site.name} is marked on your map.`, 'dir'); }
  } else if (st.beat === 'ordeal') { d.pending.push([t + DIR_TELEGRAPH + 10, 'boss', 1]); game.msg('Something large is coming. You can feel it before you see it.', 'dir'); }
  else if (st.beat === 'reward') {
    for (const [iid, n] of [['medkit', 1], ['food', 2], ['bandage', 2]]) if (game.items[iid]) game.give_item(make_item(iid, n));
    game.msg('In what it left behind: supplies enough to keep going.', 'dir');
    d.phase = 'release'; d.phase_until = t + st.release;
  } else if (st.beat === 'chase') d.pending.push([t + 20, 'horde', 5]);
}

function dir_threat(game, d, st, t) {
  const rng = game.rng, power = dir_power(game);
  const size = Math.max(2, Math.round((2 + st.peak / 22.0) * (0.6 + 0.4 * power)));
  let kind = d.stage >= 4 ? rng.choice(['horde', 'horde', 'raiders', 'special']) : 'horde';
  if (kind === 'raiders' && game.era.id === 'scifi' && rng.random() < 0.3) kind = 'horde';
  d.pending.push([t + DIR_TELEGRAPH, kind, size]);
  d.phase = 'peak'; d.phase_until = t + DIR_PEAK_MAX; d.threats += 1; d.last_threat = t;
  game.msg({ horde: 'A restlessness runs through the dead. Something is coming this way.', raiders: 'Voices, off the road. People who are not friendly.', special: 'A sound you have not heard before, far off.' }[kind], 'dir');
}

function dir_due(game, d, t) {
  for (const item of d.pending.slice()) {
    const [due, kind, size] = item;
    if (t < due || game.level !== game.world.level) continue;
    d.pending.splice(d.pending.indexOf(item), 1);
    dir_land(game, d, kind, size);
  }
}

function dir_strongest(game) {
  let best = 'walker', hp = 0;
  for (const [sid, , first_day] of game.profile.specials) {
    const sp = CONTENT.specials[sid];
    if (first_day <= game_day(game) + 2 && sp.hp > hp && !sp.flags.includes('boss')) { best = sid; hp = sp.hp; }
  }
  return best;
}

function dir_land(game, d, kind, size) {
  const p = game.player, lv = game.world.level, rng = game.rng;
  if (kind === 'raiders') { game.spawn_raiders_near_player(Math.max(2, Math.min(5, size))); game.msg('Raiders step out of the cover!', 'dir'); return; }
  let pos = null;
  for (let k = 0; k < 40; k++) {
    const ang = rng.uniform(0, TAU), r = rng.randint(15, 21), q = [Math.trunc(p.x + Math.cos(ang) * r), Math.trunc(p.y + Math.sin(ang) * r)];
    if (q[0] > 2 && q[0] < lv.w - 2 && q[1] > 2 && q[1] < lv.h - 2 && lv.free(q[0], q[1])) { pos = q; break; }
  }
  if (!pos) return;
  const where = compass(pos[0] - p.x, pos[1] - p.y);
  if (kind === 'horde') { spawn_horde(game, pos, size * 2, apos(p)); game.msg(`The dead are coming from the ${where}.`, 'dir'); }
  else if (kind === 'special' || kind === 'boss') {
    const sid = dir_strongest(game), z = spawn_zombie(game, lv, pos, sid, false);
    if (kind === 'boss') { z.hp = z.max_hp = Math.trunc(z.max_hp * 1.3); }
    z.state = 'hunt'; z.target = apos(p); z.stimulus_turn = game.clock.turn;
    if (kind === 'boss') { spawn_horde(game, pos, 3, apos(p)); game.msg(`It comes from the ${where}: a ${profile_name_of(game.profile, sid).toLowerCase()}, and it has not come alone.`, 'dir', true); }
    else game.msg(`A ${profile_name_of(game.profile, sid).toLowerCase()} is hunting you, from the ${where}.`, 'dir');
  }
}
