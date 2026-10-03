// ---------------------------------------------------------------- world time
class Clock {
  constructor(turn) { this.turn = turn; }
  get tpd() { return CONTENT.clock.turns_per_day; }
  get tph() { return CONTENT.clock.turns_per_hour; }
  get day() { return Math.floor(this.turn / this.tpd) + 1; }
  get hour() { return (this.turn % this.tpd) / this.tph; }
  get light() {
    const h = this.hour;
    if (h >= 7 && h < 19) return 1.0;
    if (h >= 5 && h < 7) return (h - 5) / 2;
    if (h >= 19 && h < 21) return 1 - (h - 19) / 2;
    return 0.0;
  }
  get is_night() { return this.light < 0.35; }
  get is_day() { return this.light > 0.7; }
  get phase() { const h = this.hour; return h >= 5 && h < 7 ? 'dawn' : h >= 7 && h < 19 ? 'day' : h >= 19 && h < 21 ? 'dusk' : 'night'; }
  stamp() {
    const h = Math.floor(this.hour), m = Math.floor((this.hour - h) * 60);
    return `Day ${this.day} ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  }
  until_hour(hour) {
    const target = Math.floor(hour * this.tph), now = this.turn % this.tpd;
    return (((target - now) % this.tpd) + this.tpd) % this.tpd || this.tpd;
  }
}

const LOG_LIMIT = 600, SCENT_KEEP = 60, FORCE_TURNS = 6;

function default_config() {
  return { era: 'modern', zombies: 'classic', scenario: 'cure', origin: 'medic', mode: 'normal', difficulty: 'normal', seed: null,
           needs: false, permadeath: true, map_w: 120, map_h: 76, opening: 'random' };
}

class Game {
  constructor(cfg, _blank = false) {
    if (_blank) return;                                   // used by deserialize_game
    this.cfg = Object.assign(default_config(), cfg);
    const c = this.cfg;
    if (!CONTENT.eras[c.era]) throw new Error('unknown era ' + c.era);
    if (!CONTENT.presets[c.zombies]) throw new Error('unknown zombie preset ' + c.zombies);
    if (!CONTENT.scenarios[c.scenario]) throw new Error('unknown scenario ' + c.scenario);
    if (!CONTENT.origins[c.origin]) throw new Error('unknown origin ' + c.origin);
    if (c.opening !== 'random' && !CONTENT.openings[c.opening]) throw new Error('unknown opening ' + c.opening);
    if (c.mode !== 'normal' && c.mode !== 'living') throw new Error('unknown mode ' + c.mode);
    if (!CONTENT.difficulties[c.difficulty]) throw new Error('unknown difficulty ' + c.difficulty);
    if (c.map_w < 100 || c.map_h < 64) throw new Error('map too small (minimum 100x64)');
    this._init_state();
    setup_game(this);
    this.update_fov();
  }

  _init_state() {
    this._uid = 0; this.log = []; this.over = null; this.pending_event = null; this.recent_events = {};
    this.hordes = []; this.ring = null; this.heat = 0.0; this.stalker = null; this.stalker_ready = 0; this.last_moan = -999;
    this.patrol_goals = {}; this.distress = {}; this.aided = {};
    this.generation = 1; this.current_origin = 'medic'; this.fallen = []; this.fallen_bodies = {}; this.killer = null; this.death_notice = ''; this.patrol_nodes = []; this.opening_id = ''; this.intro_pages = [];
    this.followers = []; this.final = null; this.formula_found = false; this.applied_docs = new Set(); this.scent = {};
    this.visible = new Set(); this.on_autosave = null; this._field = null; this._field_key = ''; this._step_parity = 0;
    this._force_progress = {};
  }

  // ------------------------------------------------------------- basics
  next_uid() { return ++this._uid; }
  msg(text, tag = 'info') {
    if (!text) return;
    this.log.push([this.clock.turn, text, tag]);
    if (this.log.length > LOG_LIMIT) this.log.splice(0, 100);
  }
  item_def(id) { return this.items[id]; }
  is_dark() { return this.level.dark || this.clock.is_night; }
  get turn() { return this.clock.turn; }
  poi_of_level(level) { return this.pois[level.poi_id] || null; }
  poi_kind_of(level) { const p = this.poi_of_level(level); return p ? p.kind : 'camp'; }
  vault_component(level) { const p = this.poi_of_level(level); return p ? p.component : ''; }

  // ------------------------------------------------------------- state changes
  add_panic(amount, raw = false) {
    const p = this.player;
    if (amount > 0 && !raw) {
      amount *= Math.max(0.1, 1.0 - p.mod('panic_resist'));
      if (p.humanity < 25) amount *= 0.6;
    }
    p.panic = Math.max(0, Math.min(p.max_panic, p.panic + amount));
  }
  add_heat(amount, raw = false) { this.heat = Math.max(0, Math.min(100, this.heat + (raw ? amount : amount * this.diff.noise))); }
  adjust_humanity(delta, why) {
    const p = this.player, before = p.humanity;
    p.humanity = Math.max(0, Math.min(100, p.humanity + delta));
    if (why) this.msg(why, delta < 0 ? 'bad' : 'good');
    if (before >= 25 && p.humanity < 25) this.msg('Something in you goes quiet. The fear dulls. So does everything else.', 'warn');
    else if (before >= 75 && p.humanity < 75) this.msg('The people who trusted you would not recognise you now.', 'warn');
  }
  give_item(item) {
    const d = this.item_def(item.id);
    if (d.durability && (item.dur === null || item.dur === undefined)) item.dur = d.durability;
    item.key = d.kind === 'component';
    if (!this.player.add_item(item, d.stackable)) {
      this.level.drop([this.player.x, this.player.y], item);
      this.msg(`Your pack is full; the ${d.name.toLowerCase()} falls at your feet.`, 'warn');
    }
  }
  end(kind, cause = '') {
    if (this.over) return;
    if ((kind === 'dead' || kind === 'turned') && this.cfg.mode === 'living') { player_died(this, kind, cause); return; }   // the world goes on
    this.over = build_ending(this, kind, cause);
  }
  make_hostile(h) {
    if (h.hostile) return;
    h.hostile = true;
    const f = h.faction || 'enclave';
    this.rep[f] = (this.rep[f] || 0) - 20;
    this.msg(`The ${h.name.toLowerCase()} turns on you!`, 'bad');
    if (['trader', 'healer', 'scholar'].includes(h.role)) this.rep.enclave = (this.rep.enclave || 0) - 40;
  }

  // ------------------------------------------------------------- perception and noise
  vision_radius() {
    const p = this.player, lv = this.level;
    let r;
    if (lv.kind === 'haven' && !this.final) r = 12;
    else if (lv.dark) r = 7;
    else { const light = this.clock.light; r = light > 0.7 ? 14 : light > 0.35 ? 10 : 5; }
    if (this.is_dark()) {
      r += Math.floor(p.mod('night_vision'));
      if (player_lit(this)) r = Math.max(r, this.item_def(p.light.id).light);
    }
    return r;
  }
  update_fov() {
    const lv = this.level, p = this.player;
    this.visible = visible_tiles(lv, [p.x, p.y], this.vision_radius());
    for (const k of this.visible) lv.seen[k] = 1;
    if (lv.kind === 'overworld') {
      const sense = 12 + Math.floor(p.mod('poi_sense'));
      for (const poi of Object.values(this.pois)) {
        if (!poi.revealed && poi.kind !== 'breach' && poi.kind !== 'house' && cheb(poi_pos(poi), [p.x, p.y]) <= sense) {
          poi.revealed = true;
          this.msg(`You notice a building ahead: ${poi.name}.`, 'info');
        }
      }
    }
  }
  is_visible(x, y) { return this.visible.has(this.level.idx(x, y)); }
  visible_actors() { return this.level.actors.filter((a) => this.is_visible(a.x, a.y)); }
  visible_hostiles() { return this.visible_actors().filter((a) => a.kind === 'zombie' || (a.kind === 'human' && a.hostile)); }
  zombie_sees_player(z) { return sees_player(this, z); }

  emit_noise(pos, radius, source = 'player') {
    if (radius < 1) return;
    const turn = this.clock.turn;
    for (const a of this.level.actors) {
      if (a.kind !== 'zombie' || a.state === 'hunt') continue;
      const reach = radius * a.hearing;
      if ((a.x - pos[0]) ** 2 + (a.y - pos[1]) ** 2 > reach * reach) continue;
      a.state = 'investigate'; a.target = [pos[0], pos[1]]; a.stimulus_turn = turn;
    }
    if (this.level === this.world.level) noise_attracts(this, pos, radius);
    if (source === 'player' && radius >= 8) this.add_heat(radius * 0.12);
  }
  scent_near(pos, radius) {
    let best = null, best_t = -1;
    const w = this.level.w;
    for (const [k, t] of Object.entries(this.scent)) {
      const spot = [k % w, Math.floor(k / w)];
      if (t > best_t && cheb(spot, pos) <= radius) { best = spot; best_t = t; }
    }
    return best;
  }
  get_field() {
    const p = this.player, key = `${this.clock.turn}:${p.x},${p.y}:${this.level.id}`;
    if (this._field_key !== key) {
      this._field = distance_field(this.level, [p.x, p.y], FIELD_RADIUS, !!this.profile.swarm);
      this._field_key = key;
    }
    return this._field;
  }

  // ------------------------------------------------------------- the world tick
  _spend(turns) {
    for (let i = 0; i < Math.max(0, turns); i++) { if (this.over) break; this._tick(); }
    if (!this.over) this.update_fov();
  }

  _tick() {
    this.clock.turn += 1;
    const t = this.clock.turn;
    this._player_conditions(); if (this.over) return;
    this._hazards(); if (this.over) return;
    ai_run(this); if (this.over) return;
    abstract_run(this);
    hordes_tick(this);
    wanderers(this);
    this._followers();
    this._rising_dead();
    this._heat();
    this._time_events();
    if (this.final) this._final_tick();
    if (t % 40 === 0) this._maybe_event();
    if (t % 30 === 0) {
      for (const k of Object.keys(this.scent)) if (t - this.scent[k] >= SCENT_KEEP) delete this.scent[k];
    }
    if (t % 100 === 0 && this.on_autosave) { try { this.on_autosave(this); } catch (e) { /* storage unavailable */ } }
  }

  _infection_total() {
    if (this.scenario.start_infected && this.cfg.mode === 'normal') return Math.max(1, Math.floor(this.scenario.timer_turns * this.diff.timer));
    return Math.max(1, Math.floor(this.profile.incubation * this.diff.timer));
  }

  _player_conditions() {
    const p = this.player, t = this.clock.turn;
    if (p.bleeding) {
      if (t % 4 === 0) {
        p.hp -= p.bleeding; this.add_panic(1.5);
        if (p.hp <= 0) { this.end('dead', 'bled out'); return; }
      }
      if (this.rng.random() < 0.03) {
        p.bleeding -= 1;
        if (!p.bleeding) this.msg('The bleeding stops on its own.', 'good');
      }
    }
    if (p.infected) {
      p.infection_timer -= 1;
      if (p.bite_window > 0) {
        p.bite_window -= 1;
        if (p.bite_window === 0 && (p.bite_limb === 'arm' || p.bite_limb === 'leg')) this.msg('It is too late to cut it off. The infection has spread.', 'bad');
      }
      const left = p.infection_timer, total = this._infection_total();
      if ((left === Math.floor(total / 2) || left === Math.floor(total / 4) || left === 30 || left === 10) && left > 0) {
        this.msg(`Fever. Your hands shake. About ${Math.max(1, Math.floor(left / 10))} hours left.`, 'warn');
        this.add_panic(5);
      }
      if (left <= 0) { this.end('turned', ''); return; }
    }
    if (this.cfg.needs) {
      p.hunger = Math.min(100, p.hunger + 0.12);
      if (p.hunger >= 100 && t % 5 === 0) { p.hp -= 1; if (p.hp <= 0) { this.end('dead', 'starved'); return; } }
    }
    if (p.hp < p.max_hp && !p.bleeding && p.hunger < 75 && t % 12 === 0) p.hp += 1;
    p.stamina = Math.min(p.max_stamina, p.stamina + (p.sprinting ? 0.3 : 0.9));
    const near = this.level.actors.some((a) => a.kind === 'zombie' && a.state === 'hunt' && cheb([a.x, a.y], [p.x, p.y]) < 9);
    if (near) {
      this.add_panic(0.15);
      const adj = this.level.actors.filter((a) => a.kind === 'zombie' && cheb([a.x, a.y], [p.x, p.y]) === 1).length;
      if (adj >= 3) this.add_panic(3.0 * (adj - 2));
    } else p.panic = Math.max(0, p.panic - (this.level.safe ? 2.0 : 0.35));
    if (this.is_dark() && !player_lit(this)) this.add_panic(0.1);
    if (p.filter_turns) p.filter_turns -= 1;
    if (p.disguise_turns) p.disguise_turns -= 1;
    if (p.light && p.light_on && this.is_dark() && p.light.dur) {
      p.light.dur -= 1;
      if (p.light.dur === 0) this.msg(`Your ${this.item_def(p.light.id).name.toLowerCase()} flickers out.`, 'warn');
    }
  }

  _hazards() {
    const lv = this.level, p = this.player;
    for (const k of Object.keys(lv.hazards)) {
      const hz = lv.hazards[k];
      if (hz.ttl < 1e8) { hz.ttl -= 1; if (hz.ttl <= 0) { delete lv.hazards[k]; continue; } }
      const victim = lv.occ.get(+k);
      if (hz.kind === 'fire') {
        if (victim && victim.kind === 'zombie') { victim.hp -= 4; if (victim.hp <= 0) kill_zombie(this, victim, false, true); }
        else if (victim === p) {
          this.msg('You are burning!', 'bad');
          damage_player(this, 4, 'burned alive');
          if (this.over) return;
        }
      } else if (hz.kind === 'spore' && victim === p && !p.filter_turns) {
        if (this.profile.vector === 'spore') {
          if (this.rng.random() < 0.12 * (1.0 - p.mod('infect_resist'))) infect(this, 'spore');
        } else { damage_player(this, 2, 'choked on the fumes'); if (this.over) return; }
        this.add_panic(1.0);
      }
    }
  }

  _heat() {
    const prof = this.profile;
    if (this.heat >= prof.stalker_heat && !this.stalker && this.clock.turn >= this.stalker_ready &&
        this.level === this.world.level && !this.final) this._spawn_stalker();
    this.heat = Math.max(0, this.heat - (this.level.safe ? 1.5 : 0.4));
  }

  _spawn_stalker() {
    const p = this.player, lv = this.level;
    for (let i = 0; i < 60; i++) {
      const ang = this.rng.uniform(0, Math.PI * 2), r = this.rng.randint(14, 20);
      const pos = [Math.trunc(p.x + Math.cos(ang) * r), Math.trunc(p.y + Math.sin(ang) * r)];
      if (lv.free(pos[0], pos[1]) && !this.is_visible(pos[0], pos[1])) {
        const z = spawn_zombie(this, lv, pos, 'stalker', false, true);
        z.state = 'hunt'; z.target = [p.x, p.y]; z.stimulus_turn = this.clock.turn;
        this.stalker = z; this.heat = 55.0;
        this.msg(`Something is hunting you. A ${z.name.toLowerCase()}, and it does not stop.`, 'bad');
        this.add_panic(15);
        return;
      }
    }
  }
  on_stalker_killed() {
    this.stalker = null; this.stalker_ready = this.clock.turn + 500; this.heat = 20.0;
    this.player.gain_xp(60);
    this.msg('The Stalker is dead. For now.', 'good');
  }
  on_ring_escaped() { this.stalker_ready = Math.max(this.stalker_ready, this.clock.turn + 120); }

  _followers() {
    for (const entry of this.followers.slice()) {
      if (this.clock.turn < entry.due) continue;
      this.followers.splice(this.followers.indexOf(entry), 1);
      if (this.level.id !== entry.level_id) continue;
      const p = this.player, z = entry.z;
      const spot = this.level.free_spot_near(p.x, p.y, 5);
      if (spot && cheb(spot, [p.x, p.y]) >= 2) {
        z.x = spot[0]; z.y = spot[1];
        this.level.add_actor(z);
        z.state = 'hunt'; z.target = [p.x, p.y];
        this.msg(`The ${z.name.toLowerCase()} followed you in!`, 'bad');
      }
    }
  }

  _rising_dead() {
    const lv = this.level, t = this.clock.turn, w = lv.w;
    for (const k of Object.keys(lv.corpses)) {
      const [died, human] = lv.corpses[k];
      const x = k % w, y = Math.floor(k / w);
      if (t - died > 800) delete lv.corpses[k];
      else if (human && (human === 2 || this.profile.turn_on_death) && t - died > 55 && lv.free(x, y) &&
               cheb([x, y], [this.player.x, this.player.y]) > 1 && !lv.safe) {
        delete lv.corpses[k];
        const fk = `${lv.id}|${k}`, fallen = this.fallen_bodies[fk];
        if (fallen) delete this.fallen_bodies[fk];
        const z = fallen ? make_fallen(this, lv, [x, y], fallen) : spawn_zombie(this, lv, [x, y], 'walker', false, true);
        z.fresh_human = false; z.state = 'hunt'; z.target = [this.player.x, this.player.y]; z.stimulus_turn = t;
        if (this.is_visible(x, y)) this.msg('A body twitches, and rises.', 'warn');
      }
    }
  }

  _time_events() {
    const c = this.clock, sc = this.scenario;
    if (this.profile.sun_burn && c.turn % 240 === 200 && this.world.level.kind === 'overworld') this._dusk_wave();
    if (sc.deadline_days && c.day > sc.deadline_days && !this.final) this.end('left_behind', '');
    else if (sc.deadline_days && c.turn % 240 === 0 && c.day === sc.deadline_days) this.msg('The last day. By nightfall the way out will be gone.', 'warn');
    if (c.turn % 240 === 0) {
      const ph = profile_phase(this.profile, c.day), prev = profile_phase(this.profile, c.day - 1);
      if (ph !== prev && ph.blurb) this.msg(`Day ${c.day}: ${ph.name}. ${ph.blurb}`, 'lore');
    }
  }

  _dusk_wave() {
    const lv = this.world.level, p = this.player;
    let n = Math.floor(34 * this.profile.density * this.diff.zombies);
    for (let i = 0; i < n * 4; i++) {
      if (n <= 0) break;
      const pos = [this.rng.randint(3, lv.w - 4), this.rng.randint(3, lv.h - 4)];
      const t = lv.tile(pos[0], pos[1]);
      if (lv.free(pos[0], pos[1]) && (t === T.GRASS || t === T.ROAD) && cheb(pos, [p.x, p.y]) > 12) {
        spawn_zombie(this, lv, pos, null, false);
        n--;
      }
    }
    if (this.level === lv) this.msg('The sun is gone. Shapes begin to move in the streets.', 'warn');
  }

  _maybe_event() {
    if (this.pending_event || this.final || this.level !== this.world.level) return;
    if ((this.ring && this.ring.active) || this.clock.turn < 160 || this.rng.random() > 0.3) return;
    const p = this.player;
    if (this.level.actors.some((a) => a.kind === 'zombie' && cheb([a.x, a.y], [p.x, p.y]) < 11)) return;
    const ev = pick_event(this);
    if (ev) this.pending_event = start_event(this, ev);
  }

  resolve_event(index) {
    const ev = this.pending_event;
    if (!ev) return '';
    const text = resolve_event(this, ev, index);
    if (text === 'You cannot afford that.') return text;
    this.pending_event = null;
    this.update_fov();
    return text;
  }

  // ------------------------------------------------------------- hostiles from events
  spawn_horde_near_player() {
    const p = this.player, lv = this.world.level;
    for (let i = 0; i < 40; i++) {
      const ang = this.rng.uniform(0, Math.PI * 2), r = this.rng.randint(16, 22);
      const pos = [Math.trunc(p.x + Math.cos(ang) * r), Math.trunc(p.y + Math.sin(ang) * r)];
      if (pos[0] > 2 && pos[0] < lv.w - 2 && pos[1] > 2 && pos[1] < lv.h - 2 && lv.free(pos[0], pos[1])) {
        spawn_horde(this, pos, null, [p.x, p.y]);
        return;
      }
    }
  }
  spawn_raiders_near_player(n) {
    const p = this.player, lv = this.level;
    for (let i = 0; i < n; i++) {
      const spot = lv.free_spot_near(p.x + this.rng.randint(-6, 6), p.y + this.rng.randint(-6, 6), 4);
      if (spot && cheb(spot, [p.x, p.y]) >= 3) {
        const r = make_raider(this, spot[0], spot[1]);
        r.state = 'hunt';
        lv.add_actor(r);
      }
    }
  }
  // You killed something near a patrol that had called for help: they will remember.
  note_assist(pos) {
    for (const a of this.level.actors) {
      if (a.kind === 'human' && a.group && (a.role === 'scout' || a.role === 'soldier') && cheb(apos(a), pos) <= 7 &&
          this.clock.turn - (this.distress[a.group] !== undefined ? this.distress[a.group] : -999) < 300) {
        if (this.aided[a.group] === undefined) this.aided[a.group] = false;
      }
    }
  }
  reveal_random_lead() {
    const all = Object.values(this.pois);
    let pois = all.filter((q) => q.component && !q.lead);
    if (!pois.length) {
      const site = this.pois[this.final_site_id];
      pois = !site.revealed ? [site] : all.filter((q) => !q.revealed && q.kind !== 'house' && q.kind !== 'breach');
    }
    if (!pois.length) return false;
    const poi = this.rng.choice(pois);
    poi.revealed = true; poi.lead = true;
    this.msg(`A lead: ${poi.name} is marked on your map.`, 'good');
    return true;
  }

  // ------------------------------------------------------------- level handling
  ensure_level(level_id) {
    if (this.levels[level_id]) return this.levels[level_id];
    const cut = level_id.lastIndexOf(':');
    const poi = this.pois[level_id.slice(0, cut)], floor = parseInt(level_id.slice(cut + 1), 10);
    const ctx = { era: this.era, profile: this.profile, loot_mult: this.diff.loot, zombie_mult: this.diff.zombies,
                  spawn: (lv, pos, special = null, dormant = true) => spawn_zombie(this, lv, pos, special, dormant), day: this.clock.day };
    const n = Math.max(1, poi.floors);
    const docs = poi.docs.filter((d, i) => i % n === floor % n);
    const lv = generate_interior(poi, floor, this.seed, ctx, docs);
    lv.poi_id = poi.id;
    this.levels[level_id] = lv;
    for (const z of lv.actors) z.birth_day = this.clock.day;
    if (poi.kind === 'refuge') this._populate_refuge(lv);
    return lv;
  }

  _populate_refuge(lv) {
    if (!lv.bench) return;
    const [bx, by] = lv.bench;
    const defs = [['trader', 'Trader', bx - 6, by + 3, 'T'], ['healer', 'Healer', bx - 10, by + 3, 'H'], ['scholar', 'Archivist', bx - 14, by + 3, 'S']];
    for (const [role, name, x, y, glyph] of defs) {
      const spot = lv.free_spot_near(x, y, 3);
      if (spot) lv.add_actor({ kind: 'human', uid: this.next_uid(), name, glyph, x: spot[0], y: spot[1], hp: 30, max_hp: 30, level_id: lv.id,
                               role, faction: 'enclave', hostile: false, dmg: [3, 7], acc: 55, reach: 1, energy: 0, state: 'idle',
                               target: null, loot: [], talked: false });
    }
  }

  _use_portal(x, y) {
    const lv = this.level, p = this.player, old = lv;
    const portal = lv.portals[lv.idx(x, y)];
    const target = portal.target === 'world' ? this.world.level : this.ensure_level(portal.target);
    let dest;
    if (!(portal.pos[0] === -1 && portal.pos[1] === -1)) {
      dest = portal.pos.slice();
      if (target.kind === 'overworld') dest = target.free_spot_near(dest[0], dest[1] + 1, 3) || dest;
    } else dest = (target.arrivals[portal.arrive] || target.entry).slice();
    const occ = target.occ.get(target.idx(dest[0], dest[1]));
    if (!target.walkable(dest[0], dest[1]) || (occ && occ !== p)) dest = target.free_spot_near(dest[0], dest[1], 4) || dest;
    const st = this.stalker;
    if (st && st.hp > 0 && old.actors.includes(st) && cheb([st.x, st.y], [p.x, p.y]) <= 10 && st.state === 'hunt') {
      old.remove_actor(st);
      this.followers.push({ due: this.clock.turn + 4, level_id: target.id, z: st });
    }
    if (old.occ.get(old.idx(p.x, p.y)) === p) old.occ.delete(old.idx(p.x, p.y));
    this.level = target;
    p.x = dest[0]; p.y = dest[1];
    target.occ.set(target.idx(p.x, p.y), p);
    p.level_id = target.id;
    this.scent = {};
    const poi = this.poi_of_level(target);
    if (portal.target !== 'world' && poi && !poi.visited) {
      poi.visited = true; poi.revealed = true;
      p.gain_xp(poi.kind === 'house' ? 6 : 15);
    }
    this.msg(portal.target !== 'world' ? `You enter ${target.name}.` : 'You step back outside.', 'info');
    this._spend(1);
    return true;
  }

  // ------------------------------------------------------------- movement and interaction
  _begin_action() {
    if (this.over) return false;
    if (this.player.panic >= 95 && this.rng.random() < 0.12) {
      this.msg('You freeze, unable to move!', 'bad');
      this._spend(1);
      return false;
    }
    return true;
  }

  move(dx, dy) {
    if (!this._begin_action()) return false;
    const p = this.player, lv = this.level, nx = p.x + dx, ny = p.y + dy;
    if (!lv.in_bounds(nx, ny)) return false;
    const target = lv.occ.get(lv.idx(nx, ny));
    if (target && target !== p) return this._bump_actor(target);
    const tile = lv.tile(nx, ny), k = lv.idx(nx, ny);
    if (tile === T.DOOR) {
      lv.set_tile(nx, ny, T.DOOR_OPEN); delete lv.door_hp[k];
      this.emit_noise([p.x, p.y], 2);
      this._spend(1);
      return true;
    }
    if (tile === T.LOCKED) return this.try_unlock([nx, ny]);
    if (tile === T.CRATE || tile === T.CRATE_OPEN) {
      const turns = search_container(this, [nx, ny]);
      this._spend(turns);
      return turns > 0;
    }
    if (tile === T.BENCH) return this.use_bench();
    if (tile === T.BED) { this.msg('A bed. Use the SLEEP action beside it.', 'info'); return false; }
    if (lv.portals[k] && (tile === T.PORTAL || tile === T.STAIRS_UP || tile === T.STAIRS_DOWN)) return this._use_portal(nx, ny);
    if (!lv.walkable(nx, ny)) return false;
    lv.move_actor(p, nx, ny);
    this._after_step(tile);
    return true;
  }

  _bump_actor(target) {
    if (target.kind === 'human' && !target.hostile) { this.msg(`${target.name} is here. Use TALK.`, 'info'); return false; }
    const turns = player_attack(this, target) ? 1 : 0;
    this._spend(turns);
    return turns > 0;
  }

  _after_step(tile) {
    const p = this.player, lv = this.level, k = lv.idx(p.x, p.y);
    let noise = { [T.ROAD]: 3, [T.BRUSH]: 3, [T.SHALLOW]: 5 }[tile] || 2;
    if (p.sneaking) noise = 1;
    else if (p.sprinting && p.stamina > 5) noise += 4;
    if (p.armor) noise += this.item_def(p.armor.id).stealth;
    noise = Math.max(0, noise + Math.trunc(p.mod('move_noise')));
    this.emit_noise([p.x, p.y], noise);
    if (!TILES[tile].masks_scent) this.scent[k] = this.clock.turn;
    let cost = 1;
    if (p.sneaking) cost = 2;
    else if (p.sprinting && p.stamina > 5) { p.stamina -= 3; this._step_parity ^= 1; cost = this._step_parity; }
    else p.sprinting = false;
    if (p.fracture) { this._step_parity ^= 1; cost += this._step_parity; }
    if (p.lost.includes('leg')) cost += this.clock.turn % 3 ? 0 : 1;
    const stack = lv.items[k];
    if (stack) this.msg(`You see here: ${stack.slice(0, 3).map((i) => this.item_def(i.id).name.toLowerCase()).join(', ')}. (PICK UP)`, 'info');
    if (lv.docs[k]) this.msg('A document lies here. (PICK UP)', 'info');
    if (lv.hazards[k] && lv.hazards[k].kind === 'spore' && !p.filter_turns) this.msg('The air is thick with spores!', 'warn');
    this._spend(cost);
  }

  try_unlock(pos) {
    const lv = this.level, p = this.player, poi = this.poi_of_level(lv);
    if (poi && poi.code_known) {
      lv.set_tile(pos[0], pos[1], T.DOOR_OPEN);
      this.msg('You key in the code you deciphered. The vault door opens.', 'good');
      this._spend(1);
      return true;
    }
    const carried = (p.weapon ? [p.weapon] : []).concat(p.inventory);
    const tools = carried.filter((i) => { const d = this.item_def(i.id); return d.kind === 'weapon' && ['blunt', 'blade', 'polearm'].includes(d.style); });
    if (!tools.length) { this.msg('The door is locked. Find its code, or something to force it with.', 'warn'); return false; }
    const key = `${lv.id}:${lv.idx(pos[0], pos[1])}`;
    const progress = (this._force_progress[key] || 0) + 1;
    this._force_progress[key] = progress;
    this.emit_noise([p.x, p.y], 14);
    this._spend(progress === 1 ? FORCE_TURNS : 2);
    if (this.over) return true;
    if (this.rng.random() < 0.35 + 0.15 * progress) {
      lv.set_tile(pos[0], pos[1], T.DOOR_OPEN);
      this.msg('The lock gives with a crack that carries through the whole building.', 'good');
    } else this.msg('You hammer at the lock. It holds. (try again)', 'info');
    return true;
  }

  wait(turns = 1) { if (this.over) return false; this._spend(turns); return true; }

  rest(max_turns = 20) {
    if (this.over) return 0;
    if (this.visible_hostiles().length) { this.msg('You cannot rest with enemies in sight.', 'warn'); return 0; }
    const p = this.player;
    let rested = 0;
    for (let i = 0; i < max_turns; i++) {
      const hp0 = p.hp;
      this._spend(1); rested++;
      if (this.over || p.hp < hp0 || this.visible_hostiles().length || this.pending_event) break;
      if (p.hp < p.max_hp && !p.bleeding && this.clock.turn % 3 === 0) p.hp += 1;
      p.stamina = Math.min(p.max_stamina, p.stamina + 1.5);
      if (p.hp >= p.max_hp && p.stamina >= p.max_stamina && p.panic < 5) break;
    }
    return rested;
  }

  toggle_sneak() {
    const p = this.player;
    p.sneaking = !p.sneaking;
    if (p.sneaking) p.sprinting = false;
    this.msg(p.sneaking ? 'You creep.' : 'You stand up straight.', 'info');
  }
  toggle_sprint() {
    const p = this.player;
    p.sprinting = !p.sprinting && p.stamina > 10;
    if (p.sprinting) p.sneaking = false;
    this.msg(p.sprinting ? 'You break into a run.' : 'You slow down.', 'info');
  }
  toggle_light() {
    const p = this.player;
    if (!p.light) { this.msg('You have no light.', 'warn'); return; }
    p.light_on = !p.light_on;
    this.msg(p.light_on ? 'You switch the light on.' : 'You douse the light.', 'info');
    this.update_fov();
  }

  // ------------------------------------------------------------- items
  pickup() { const t = pickup_here(this); this._spend(t); return t > 0; }
  use(index) { if (!this._begin_action()) return false; const t = use_item(this, index); this._spend(t); return t > 0; }
  equip(index) { const t = equip(this, index); this._spend(t); return t > 0; }
  unequip(slot) { const t = unequip(this, slot); this._spend(t); return t > 0; }
  drop(index) { const t = drop_item(this, index); this._spend(t); return t > 0; }
  craft(recipe_id) { const t = craft_item(this, recipe_id); this._spend(t); return t > 0; }

  targets_in_range() {
    const w = weapon_def(this);
    const reach = Math.max(1, (is_ranged(w) || w.reach > 1) ? w.reach : 1);
    const p = this.player;
    return this.visible_hostiles().filter((a) => cheb([a.x, a.y], [p.x, p.y]) <= reach)
      .sort((a, b) => cheb([a.x, a.y], [p.x, p.y]) - cheb([b.x, b.y], [p.x, p.y]));
  }
  fire(target) { if (!this._begin_action()) return false; const s = player_fire(this, target); this._spend(s ? 1 : 0); return s; }
  attack(target) { if (!this._begin_action()) return false; const s = player_attack(this, target); this._spend(s ? 1 : 0); return s; }
  throw_at(item_id, pos) { if (!this._begin_action()) return false; const s = throw_item(this, item_id, pos); this._spend(s ? 1 : 0); return s; }
  amputate() {
    const reason = can_amputate(this);
    if (reason) { this.msg(reason, 'warn'); return false; }
    amputate(this);
    this._spend(3);
    return true;
  }
  smear() {
    const p = this.player, lv = this.level, w = lv.w;
    const near = Object.keys(lv.corpses).some((k) => cheb([k % w, Math.floor(k / w)], [p.x, p.y]) <= 1);
    if (!near) { this.msg('You need a corpse within reach.', 'warn'); return false; }
    p.disguise_turns = 120;
    this.add_panic(8);
    this.msg('You smear yourself with gore. You reek of the dead.', 'info');
    this._spend(3);
    return true;
  }

  // ------------------------------------------------------------- documents
  collect_document(doc_id) {
    if (this.player.documents.includes(doc_id)) return;
    this.player.documents.push(doc_id);
    this.msg(`You find a document: ${this.docs[doc_id].title}.`, 'lore');
  }
  read_document(doc_id) {
    const doc = this.docs[doc_id];
    const learned = expose(doc, this.know, EXPOSURE_TO_LEARN - (this.player.mod('study_bonus') >= 0.3 ? 1 : 0));
    if (learned.length) this.msg(`The meaning of '${learned.join(', ')}' sinks in.`, 'good');
    this._apply_payload(doc);
    this._spend(2);
    return [render_document(doc, this.know), learned];
  }
  study_document(doc_id) {
    const doc = this.docs[doc_id];
    const words = 1 + (this.know.fluency >= 0.15 ? 1 : 0) + (this.know.fluency >= 0.3 ? 1 : 0);
    const learned = study(this.rng, doc, this.know, this.player.mod('study_bonus'), words);
    if (learned.length) { this.msg(`After long effort you work out: ${learned.join(', ')}.`, 'good'); this.player.gain_xp(3 * learned.length); }
    else if (doc.studies >= STUDY_LIMIT) this.msg('You have wrung everything you can out of this page for now.', 'info');
    else this.msg('The page will not give up its secrets. Try again.', 'info');
    this._apply_payload(doc);
    this._spend(5);
    return [render_document(doc, this.know), learned];
  }
  _apply_payload(doc) {
    if (this.applied_docs.has(doc.id) || !is_decoded(doc, this.know)) return;
    this.applied_docs.add(doc.id);
    this.player.gain_xp(10);
    if (doc.payload.reveal) { const poi = this.pois[doc.payload.reveal]; poi.revealed = true; poi.lead = true; this.msg(`Deciphered: ${poi.name} is now marked on your map.`, 'good'); }
    if (doc.payload.code) { const poi = this.pois[doc.payload.code]; poi.code_known = true; this.msg(`Deciphered: you now know the vault code for ${poi.name}.`, 'good'); }
    if (doc.payload.formula) { this.formula_found = true; this.msg('Deciphered: you now hold the formula.', 'good'); }
  }

  // ------------------------------------------------------------- havens
  adjacent_npc() {
    const p = this.player;
    for (const [dx, dy] of DIRS8) {
      const a = this.level.occ.get(this.level.idx(p.x + dx, p.y + dy));
      if (a && a.kind === 'human' && !a.hostile) return a;
    }
    return null;
  }
  adjacent_tile(tile) {
    const p = this.player, lv = this.level;
    for (const [dx, dy] of DIRS8) if (lv.tile(p.x + dx, p.y + dy) === tile) return [p.x + dx, p.y + dy];
    return null;
  }
  // Context action. Returns 'npc' or 'bed' when the UI must open a menu, else ''.
  interact() {
    if (this.adjacent_npc()) return 'npc';
    if (this.adjacent_tile(T.BED)) return 'bed';
    if (this.adjacent_tile(T.BENCH)) { this.use_bench(); return ''; }
    const crate = this.adjacent_tile(T.CRATE);
    if (crate) { this._spend(search_container(this, crate)); return ''; }
    const lock = this.adjacent_tile(T.LOCKED);
    if (lock) { this.try_unlock(lock); return ''; }
    this.msg('Nothing to interact with.', 'info');
    return '';
  }
  sleep() {
    const lv = this.level, p = this.player;
    if (!lv.safe) { this.msg('It is not safe to sleep here.', 'warn'); return 0; }
    const turns = Math.min(80, this.clock.until_hour(6.0));
    this._spend(turns);
    if (!this.over) {
      p.hp = Math.min(p.max_hp, p.hp + Math.floor(p.max_hp * 0.6));
      p.stamina = p.max_stamina; p.panic = 0;
      this.msg(`You sleep for ${Math.floor(turns / 10)} hours.`, 'info');
      if (p.infected) this.msg('You wake in a sweat. The fever has not broken.', 'warn');
    }
    return turns;
  }

  requirements() {
    const sc = this.scenario, p = this.player, out = [];
    for (const req of sc.requirements) {
      const have = p.count(req.id) > 0;
      const poi = Object.values(this.pois).find((q) => q.component === req.id);
      const hint = have ? 'in your pack' : (poi && poi.lead ? `lead: ${poi.name}` : 'location unknown');
      out.push([this.item_def(req.id).name, have, hint]);
    }
    if (sc.needs_formula) {
      const ok = this.formula_found && this.know.fluency >= sc.formula_fluency;
      let hint;
      if (ok) hint = 'ready';
      else if (this.formula_found) hint = `need ${Math.floor(sc.formula_fluency * 100)}% fluency (you have ${Math.floor(this.know.fluency * 100)}%)`;
      else hint = 'not found';
      out.push(['The formula', ok, hint]);
    }
    return out;
  }
  requirements_met() { return this.requirements().every((r) => r[1]); }

  use_bench() {
    const lv = this.level, site = this.pois[this.final_site_id];
    if (lv.poi_id !== site.id) { this.msg('It is idle. This is not where you need to be.', 'info'); return false; }
    if (this.final) { this.msg('You are already working. Hold out!', 'warn'); return false; }
    if (!this.requirements_met()) {
      const missing = this.requirements().filter((r) => !r[1]).map((r) => `${r[0]} (${r[2]})`);
      this.msg('You are not ready: ' + missing.join('; ') + '.', 'warn');
      return false;
    }
    const sc = this.scenario;
    this.final = { turns_left: sc.final_turns, next_wave: 4, boss_done: false };
    lv.safe = false;
    this.msg(`You begin to ${sc.final_verb}. The noise carries. Hold out for ${sc.final_turns} turns!`, 'bad');
    this.emit_noise([this.player.x, this.player.y], 30);
    this.add_heat(30, true);
    this._spend(1);
    return true;
  }

  _final_tick() {
    const f = this.final, lv = this.level, p = this.player;
    if (lv.poi_id !== this.final_site_id) return;
    f.turns_left -= 1;
    if (f.turns_left <= 0) { this.final = null; this.end('won'); return; }
    f.next_wave -= 1;
    if (f.next_wave <= 0) {
      f.next_wave = 6;
      const n = 2 + Math.floor(p.level / 4) + (this.diff.zombies > 1 ? 1 : 0);
      for (let i = 0; i < n; i++) {
        const spot = lv.free_spot_near(lv.entry[0] + this.rng.randint(-2, 2), lv.entry[1], 3);
        if (spot && cheb(spot, [p.x, p.y]) > 2) {
          const z = spawn_zombie(this, lv, spot, null, false, true);
          z.state = 'hunt'; z.target = [p.x, p.y]; z.stimulus_turn = this.clock.turn;
        }
      }
      this.msg('The door shakes. More of them are coming in!', 'warn');
    }
    if (!f.boss_done && f.turns_left <= Math.floor(this.scenario.final_turns / 2)) {
      f.boss_done = true;
      if (p.humanity < 40) {
        this.msg("People step out of the dark with weapons. 'We have heard about you.'", 'bad');
        for (let i = 0; i < 3; i++) {
          const spot = lv.free_spot_near(lv.entry[0], lv.entry[1], 4);
          if (spot && cheb(spot, [p.x, p.y]) > 2) { const r = make_raider(this, spot[0], spot[1]); r.state = 'hunt'; lv.add_actor(r); }
        }
      } else {
        const spot = lv.free_spot_near(lv.entry[0], lv.entry[1], 4);
        if (spot) {
          const z = spawn_zombie(this, lv, spot, 'alpha', false, true);
          z.state = 'hunt'; z.target = [p.x, p.y];
          this.msg('Something enormous pushes through the dead. The Alpha has come for you.', 'bad');
        }
      }
    }
  }

  learn_perk(perk_id) { const ok = this.player.learn_perk(perk_id); if (ok) this.msg('You learn a new skill.', 'good'); return ok; }

  objectives() {
    const sc = this.scenario;
    const out = this.requirements().map(([n, done, h]) => [`${n}: ${h}`, done]);
    const site = this.pois[this.final_site_id];
    out.push([`${cap(sc.final_verb)} at ${site.revealed ? site.name : 'location unknown'}`, false]);
    return out;
  }

  describe_at(x, y) {
    const lv = this.level;
    if (!lv.in_bounds(x, y)) return '';
    if (!this.is_visible(x, y) && !lv.seen[lv.idx(x, y)]) return 'unexplored';
    const parts = [TILES[lv.tile(x, y)].name];
    const a = lv.occ.get(lv.idx(x, y));
    if (a && this.is_visible(x, y)) parts.unshift(a.kind === 'player' ? 'you' : a.name.toLowerCase() + (a.title ? ` - ${a.title}` : ''));
    if (this.is_visible(x, y) && lv.items[lv.idx(x, y)]) parts.push('items');
    return parts.join(', ');
  }

  // Path for tap-to-travel: through tiles you have seen, avoiding anything standing in the way.
  travel_path(x, y) {
    const lv = this.level, p = this.player;
    if (!lv.in_bounds(x, y) || (x === p.x && y === p.y)) return null;
    const allow = (nx, ny) => {
      const k = lv.idx(nx, ny);
      if (!lv.seen[k] && !this.visible.has(k)) return false;
      const t = lv.tiles[k];
      if (t === T.LOCKED || t === T.CRATE || t === T.CRATE_OPEN || t === T.BED || t === T.BENCH) return false;
      const occ = lv.occ.get(k);
      if (occ && occ !== p && !(nx === x && ny === y)) return false;
      const hz = lv.hazards[k];
      if (hz && hz.kind === 'fire') return false;
      return true;
    };
    return player_path(lv, [p.x, p.y], [x, y], allow);
  }
}

function make_game(cfg = {}) { return new Game(cfg); }
