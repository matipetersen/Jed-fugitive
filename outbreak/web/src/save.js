// ---------------------------------------------------------------- saving: the whole game as JSON
const SAVE_VERSION = 1, SAVE_KEY = 'outbreak.save.v1';

function bytes_to_b64(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}
function b64_to_bytes(b64) {
  const s = atob(b64), out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

function _serialize_level(lv) {
  return { id: lv.id, name: lv.name, w: lv.w, h: lv.h, kind: lv.kind, tiles: bytes_to_b64(lv.tiles), seen: bytes_to_b64(lv.seen),
           actors: lv.actors, items: lv.items, containers: lv.containers, portals: lv.portals, corpses: lv.corpses,
           hazards: lv.hazards, door_hp: lv.door_hp, docs: lv.docs, entry: lv.entry, arrivals: lv.arrivals,
           vault_lock: lv.vault_lock, bench: lv.bench, dark: lv.dark, safe: lv.safe, poi_id: lv.poi_id };
}
function _deserialize_level(d) {
  const lv = new Level(d.id, d.name, d.w, d.h, d.kind);
  lv.tiles = b64_to_bytes(d.tiles); lv.seen = b64_to_bytes(d.seen);
  for (const k of ['actors', 'items', 'containers', 'portals', 'corpses', 'hazards', 'door_hp', 'docs', 'entry', 'arrivals',
                   'vault_lock', 'bench', 'dark', 'safe', 'poi_id']) lv[k] = d[k];
  lv.rebuild_occ();
  return lv;
}

function serialize_game(game) {
  const levels = {};
  for (const [id, lv] of Object.entries(game.levels)) levels[id] = _serialize_level(lv);
  const data = {
    v: SAVE_VERSION, cfg: game.cfg, seed: game.seed, uid: game._uid, log: game.log.slice(-200), over: game.over,
    pending_event: game.pending_event, recent_events: game.recent_events, hordes: game.hordes, ring: game.ring, heat: game.heat,
    stalker_uid: game.stalker ? game.stalker.uid : 0, stalker_ready: game.stalker_ready, last_moan: game.last_moan,
    followers: game.followers, final: game.final, formula_found: game.formula_found, applied_docs: Array.from(game.applied_docs),
    scent: game.scent, step_parity: game._step_parity, force_progress: game._force_progress, clock: game.clock.turn,
    rng: game.rng.state, refuge_id: game.refuge_id, pad_id: game.pad_id, final_site_id: game.final_site_id, rep: game.rep,
    docs: game.docs, know: { known: Array.from(game.know.known), exposure: game.know.exposure },
    player: Object.assign({}, game.player), pois: game.pois,
    world: { start: game.world.start, camps: game.world.camps, zone: bytes_to_b64(game.world.zone) },
    levels, current: game.level.id,
    patrol_goals: game.patrol_goals, patrol_nodes: game.patrol_nodes, opening_id: game.opening_id, intro_pages: game.intro_pages,
  };
  return JSON.stringify(data);
}

function deserialize_game(json) {
  const d = typeof json === 'string' ? JSON.parse(json) : json;
  if (d.v !== SAVE_VERSION) throw new Error(`save version ${d.v} is not supported`);
  const g = new Game(null, true);
  g._init_state();
  g.cfg = d.cfg; g.seed = d.seed; g._uid = d.uid; g.log = d.log; g.over = d.over; g.pending_event = d.pending_event;
  g.recent_events = d.recent_events; g.hordes = d.hordes; g.ring = d.ring; g.heat = d.heat; g.stalker_ready = d.stalker_ready;
  g.last_moan = d.last_moan; g.followers = d.followers; g.final = d.final; g.formula_found = d.formula_found;
  g.applied_docs = new Set(d.applied_docs); g.scent = d.scent; g._step_parity = d.step_parity; g._force_progress = d.force_progress;
  g.clock = new Clock(d.clock);
  g.rng = new RNG(1); g.rng.state = d.rng;
  g.patrol_goals = d.patrol_goals || {}; g.patrol_nodes = d.patrol_nodes || []; g.opening_id = d.opening_id || ''; g.intro_pages = d.intro_pages || [];
  g.refuge_id = d.refuge_id; g.pad_id = d.pad_id; g.final_site_id = d.final_site_id; g.rep = d.rep; g.docs = d.docs;
  g.era = CONTENT.eras[g.cfg.era]; g.profile = CONTENT.presets[g.cfg.zombies]; g.scenario = CONTENT.scenarios[g.cfg.scenario];
  g.diff = CONTENT.difficulties[g.cfg.difficulty];
  g.items = Object.assign({}, g.era.items);
  register_components(g);
  g.know = new Knowledge(era_vocabulary(g.era), g.era.glyphs);
  g.know.known = new Set(d.know.known); g.know.exposure = d.know.exposure;
  g.player = Object.assign(Object.create(Player.prototype), d.player);
  g.pois = d.pois;
  g.levels = {};
  for (const [id, ld] of Object.entries(d.levels)) g.levels[id] = _deserialize_level(ld);
  g.world = { level: g.levels.world, pois: g.pois, start: d.world.start, camps: d.world.camps, zone: b64_to_bytes(d.world.zone) };
  g.level = g.levels[d.current];
  g.level.occ.set(g.level.idx(g.player.x, g.player.y), g.player);
  if (d.stalker_uid) {
    for (const lv of Object.values(g.levels)) for (const a of lv.actors) if (a.uid === d.stalker_uid) g.stalker = a;
    for (const f of g.followers) if (f.z.uid === d.stalker_uid) g.stalker = f.z;
  }
  g.update_fov();
  return g;
}

function save_game(game, store) {
  store = store || (typeof localStorage !== 'undefined' ? localStorage : null);
  if (!store) throw new Error('no storage available');
  store.setItem(SAVE_KEY, serialize_game(game));
}
function load_game(store) {
  store = store || (typeof localStorage !== 'undefined' ? localStorage : null);
  const raw = store && store.getItem(SAVE_KEY);
  if (!raw) throw new Error('no save found');
  return deserialize_game(raw);
}
function has_save(store) {
  try { store = store || (typeof localStorage !== 'undefined' ? localStorage : null); return !!(store && store.getItem(SAVE_KEY)); } catch (e) { return false; }
}
function delete_save(store) {
  try { store = store || (typeof localStorage !== 'undefined' ? localStorage : null); if (store) store.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
}
