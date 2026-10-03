// ---------------------------------------------------------------- moral encounters (data comes from Python)
const EVENTS = CONTENT.events;
const EVENT_BY_ID = Object.fromEntries(EVENTS.map((e) => [e.id, e]));

function fmt(text, ctx) { return text.replace(/\{(\w+)\}/g, (m, k) => (ctx[k] !== undefined ? ctx[k] : m)); }

function event_context(game) {
  const f = game.era.factions;
  return { coin: game.era.coin, radio: cap(game.era.radio), raiders: f.raiders[0], cult: f.cult[0],
           military: f.military[0], enclave: f.enclave[0], science: f.science[0] };
}

function can_afford(game, choice) {
  const p = game.player, need = choice.needs || {};
  if (p.coins < (need.coins || 0)) return false;
  return Object.entries(need.items || {}).every(([i, q]) => p.count(i) >= q);
}

function pick_event(game) {
  const pairs = [];
  for (const ev of EVENTS) {
    if (game.clock.day < ev.min_day || (game.recent_events[ev.id] !== undefined ? game.recent_events[ev.id] : -999) > game.clock.turn - 600) continue;
    const w = ['toll', 'prisoner', 'bait'].includes(ev.id) ? ev.weight * game.profile.human_threat : ev.weight;
    if (ev.id === 'radio' && !game.era.electricity && game.era.tech > 0) continue;
    pairs.push([ev, w]);
  }
  return pairs.length ? weighted_choice(game.rng, pairs) : null;
}

function start_event(game, ev) {
  game.recent_events[ev.id] = game.clock.turn;
  return { event_id: ev.id, text: fmt(ev.text, event_context(game)), result: '', resolved: false };
}

function resolve_event(game, active, index) {
  const choice = EVENT_BY_ID[active.event_id].choices[index];
  if (!can_afford(game, choice)) return 'You cannot afford that.';
  const outcome = weighted_choice(game.rng, choice.outcomes.map((o) => [o, o.weight]));
  const text = fmt(outcome.text, event_context(game));
  apply_fx(game, outcome.fx);
  active.result = text; active.resolved = true;
  game.msg(text, 'lore');
  return text;
}

function apply_fx(game, fx) {
  const p = game.player;
  if ('humanity' in fx) game.adjust_humanity(Math.trunc(fx.humanity), '');
  if ('panic' in fx) game.add_panic(fx.panic, true);
  if ('hp' in fx) p.hp = Math.max(1, Math.min(p.max_hp, p.hp + Math.trunc(fx.hp)));
  if ('coins' in fx) p.coins = Math.max(0, p.coins + Math.trunc(fx.coins));
  if ('xp' in fx && fx.xp > 0) p.gain_xp(Math.trunc(fx.xp));
  if ('words' in fx) {
    const learned = game.know.learn_random(game.rng, Math.trunc(fx.words));
    if (learned.length) game.msg(`You pick up the meaning of: ${learned.join(', ')}.`, 'good');
  }
  if ('heat' in fx) game.add_heat(fx.heat, true);
  for (const [item_id, qty] of Object.entries(fx.items || {})) {
    if (qty > 0) game.give_item(make_item(item_id, qty)); else if (qty < 0) p.take(item_id, -qty);
  }
  for (const [role, delta] of Object.entries(fx.rep || {})) game.rep[role] = Math.max(-100, Math.min(100, (game.rep[role] || 0) + Math.trunc(delta)));
  if (fx.horde) game.spawn_horde_near_player();
  if (fx.raiders) game.spawn_raiders_near_player(Math.trunc(fx.raiders));
  if (fx.reveal) game.reveal_random_lead();
}
