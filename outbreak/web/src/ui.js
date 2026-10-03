// ================================================================ OUTBREAK: touch front-end
(() => {
'use strict';
const $ = (s) => document.querySelector(s);
function el(tag, cls, content) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (content !== undefined && content !== null) {
    for (const c of (Array.isArray(content) ? content : [content])) if (c !== null && c !== undefined && c !== false) e.append(c instanceof Node ? c : String(c));
  }
  return e;
}
const btn = (cls, label, onclick) => { const b = el('button', cls, label); b.type = 'button'; if (onclick) b.addEventListener('click', onclick); return b; };
const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
const MONO = '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace';

// ---------------------------------------------------------------- preferences and state
const prefs = Object.assign({ zoom: 26, haptics: true, lefty: false, travel: true }, lsGet('outbreak.prefs.v1', {}));
const savePrefs = () => lsSet('outbreak.prefs.v1', prefs);
let game = null, aim = null, travel = null, lastHp = 0, endingShown = false, modal = 0, sheetCloseCb = null, storageOk = true;
let camX = 0, camY = 0, dirty = true, view = { ox: 0, oy: 0, ts: 26 }, W = 0, H = 0, dpr = 1, pathPreview = null;
const cv = $('#map'), ctx = cv.getContext('2d');

// ---------------------------------------------------------------- map drawing
const TS = {};
const _t = (id, bg, deco) => { TS[id] = { bg, deco }; };
_t(T.FLOOR, '#1b2225'); _t(T.GRASS, '#16241a'); _t(T.ROAD, '#262d30'); _t(T.BRUSH, '#12271a', 'brush'); _t(T.TREE, '#0f2016', 'tree');
_t(T.WATER, '#0d2a40', 'water'); _t(T.SHALLOW, '#134058', 'water'); _t(T.RUBBLE, '#2a2724', 'rubble'); _t(T.WALL, '#394249', 'wall');
_t(T.DOOR, '#1b2225', 'door'); _t(T.DOOR_OPEN, '#1b2225', 'dooropen'); _t(T.LOCKED, '#1b2225', 'locked'); _t(T.STAIRS_UP, '#232c30', '<');
_t(T.STAIRS_DOWN, '#232c30', '>'); _t(T.CRATE, '#1b2225', 'crate'); _t(T.CRATE_OPEN, '#1b2225', 'cratex'); _t(T.PORTAL, '#2e363b', 'portal');
_t(T.FENCE, '#16241a', 'fence'); _t(T.BED, '#1b2225', 'bed'); _t(T.BENCH, '#1b2225', 'bench'); _t(T.CAMPFIRE, '#16241a', 'fire');
const ZCOL = { walker: '#b94a3c', crawler: '#9b5a3a', brute: '#8e3f9e', bloater: '#6a9a32', screamer: '#d4a52a', leaper: '#cf5a2a',
               clicker: '#3f9aa8', stalker: '#9b2f9b', alpha: '#c43fa6' };
const POI_LETTER = { medical: 'M', market: '$', guard: 'P', lab: 'L', transit: 'U', military: 'A', faith: 'C', industry: 'F', refuge: 'R', pad: 'E', house: 'h' };

function deco(kind, x, y, s, vis) {
  const c = ctx;
  switch (kind) {
    case 'wall': c.fillStyle = '#2d353b'; c.fillRect(x + 2, y + 2, s - 4, s - 4); c.fillStyle = '#4a555d'; c.fillRect(x, y, s, 2); break;
    case 'tree': c.fillStyle = '#1e5a33'; c.beginPath(); c.arc(x + s / 2, y + s / 2, s * 0.42, 0, 7); c.fill();
      c.fillStyle = '#2b7a46'; c.beginPath(); c.arc(x + s * 0.42, y + s * 0.4, s * 0.2, 0, 7); c.fill(); break;
    case 'brush': c.fillStyle = '#2a6b3d'; for (const [a, b] of [[.25, .3], [.6, .25], [.45, .6], [.75, .7], [.2, .75]]) c.fillRect(x + a * s, y + b * s, s * .14, s * .14); break;
    case 'water': c.strokeStyle = 'rgba(120,180,220,.35)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x + s * .2, y + s * .5); c.quadraticCurveTo(x + s * .4, y + s * .3, x + s * .5, y + s * .5);
      c.quadraticCurveTo(x + s * .6, y + s * .7, x + s * .8, y + s * .5); c.stroke(); break;
    case 'rubble': c.fillStyle = '#4a443e'; c.fillRect(x + s * .15, y + s * .5, s * .3, s * .3); c.fillRect(x + s * .5, y + s * .3, s * .3, s * .35); break;
    case 'door': c.fillStyle = '#7a5528'; c.fillRect(x + s * .15, y + s * .1, s * .7, s * .8); c.fillStyle = '#d9a23a'; c.fillRect(x + s * .68, y + s * .5, s * .08, s * .08); break;
    case 'dooropen': c.fillStyle = '#5b4020'; c.fillRect(x + s * .1, y + s * .1, s * .14, s * .8); break;
    case 'locked': c.fillStyle = '#7a2b22'; c.fillRect(x + s * .15, y + s * .1, s * .7, s * .8); c.fillStyle = '#e2573f'; c.fillRect(x + s * .4, y + s * .4, s * .2, s * .2); break;
    case 'crate': c.fillStyle = '#9a7228'; c.fillRect(x + s * .15, y + s * .2, s * .7, s * .6); c.strokeStyle = '#d9a23a'; c.lineWidth = 1.5; c.strokeRect(x + s * .15, y + s * .2, s * .7, s * .6);
      c.beginPath(); c.moveTo(x + s * .15, y + s * .2); c.lineTo(x + s * .85, y + s * .8); c.stroke(); break;
    case 'cratex': c.strokeStyle = '#5b5238'; c.lineWidth = 1.5; c.strokeRect(x + s * .15, y + s * .25, s * .7, s * .5); break;
    case 'bed': c.fillStyle = '#2f5b66'; c.fillRect(x + s * .12, y + s * .22, s * .76, s * .56); c.fillStyle = '#cfc8b4'; c.fillRect(x + s * .16, y + s * .27, s * .22, s * .2); break;
    case 'bench': c.fillStyle = '#2e6f7c'; c.fillRect(x + s * .1, y + s * .3, s * .8, s * .45); c.fillStyle = '#55b3c4'; c.fillRect(x + s * .2, y + s * .2, s * .2, s * .2); break;
    case 'fence': c.strokeStyle = '#8a8f8a'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(x, y + s * .35); c.lineTo(x + s, y + s * .35); c.moveTo(x, y + s * .65); c.lineTo(x + s, y + s * .65); c.stroke(); break;
    case 'fire': c.fillStyle = '#e2573f'; c.beginPath(); c.arc(x + s / 2, y + s / 2, s * .28, 0, 7); c.fill(); c.fillStyle = '#f0b445'; c.beginPath(); c.arc(x + s / 2, y + s * .55, s * .14, 0, 7); c.fill(); break;
    case '<': case '>': c.fillStyle = '#cfc8b4'; c.font = `bold ${Math.floor(s * .8)}px ${MONO}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(kind, x + s / 2, y + s / 2 + 1); break;
    default: break;
  }
}

function portal_letter(game, k) {
  const portal = game.level.portals[k];
  if (!portal) return null;
  if (portal.target === 'world') return '^';
  const poi = game.pois[portal.target.slice(0, portal.target.lastIndexOf(':'))];
  return poi ? (POI_LETTER[poi.kind] || 'H') : 'H';
}

function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 3);
  const r = $('#app').getBoundingClientRect();
  W = r.width; H = r.height;
  cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  layoutOverlays(); dirty = true;
}
function freeRect() {
  const top = $('#hud').hidden ? 0 : $('#hud').offsetHeight - 6;
  const bottom = $('#controls').hidden ? H : H - $('#controls').offsetHeight - 36;
  return { top, bottom: Math.max(top + 120, bottom) };
}
function layoutOverlays() {
  const ch = $('#controls').hidden ? 0 : $('#controls').offsetHeight;
  const hh = $('#hud').hidden ? 0 : $('#hud').offsetHeight;
  $('#log').style.bottom = (ch + 6) + 'px';
  $('#alert').style.bottom = (ch + 6 + $('#log').offsetHeight + 8) + 'px';
  $('#aim').style.top = (hh + 6) + 'px';
  $('#toast').style.top = (hh + 8) + 'px';
}

function draw() {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#0a0e0f'; ctx.fillRect(0, 0, W, H);
  if (!game) return;
  const lv = game.level, p = game.player, ts = prefs.zoom;
  const fr = freeRect();
  const cyPx = (fr.top + fr.bottom) / 2;
  const ox = W / 2 - camX * ts, oy = cyPx - camY * ts;
  view = { ox, oy, ts };
  const x0 = Math.max(0, Math.floor(-ox / ts)), x1 = Math.min(lv.w - 1, Math.ceil((W - ox) / ts));
  const y0 = Math.max(0, Math.floor(-oy / ts)), y1 = Math.min(lv.h - 1, Math.ceil((H - oy) / ts));
  const t_ms = performance.now();
  const dark = game.is_dark();
  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      const k = y * lv.w + x, vis = game.visible.has(k);
      if (!vis && !lv.seen[k]) continue;
      const t = lv.tiles[k], st = TS[t], px = ox + x * ts, py = oy + y * ts;
      ctx.fillStyle = st.bg; ctx.fillRect(px, py, ts + 0.5, ts + 0.5);
      if (st.deco && st.deco !== 'portal') deco(st.deco, px, py, ts, vis);
      if (t === T.PORTAL) {
        ctx.fillStyle = '#4a5860'; ctx.fillRect(px + 1, py + 1, ts - 2, ts - 2);
        ctx.fillStyle = '#f0e8d0'; ctx.font = `bold ${Math.floor(ts * .62)}px ${MONO}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(portal_letter(game, k) || 'H', px + ts / 2, py + ts / 2 + 1);
      }
      if (vis) {
        const hz = lv.hazards[k];
        if (hz) { ctx.fillStyle = hz.kind === 'fire' ? `rgba(240,120,40,${0.45 + 0.2 * Math.sin(t_ms / 120 + x)})` : 'rgba(110,200,80,.35)'; ctx.fillRect(px, py, ts, ts); }
        if (lv.corpses[k]) { ctx.fillStyle = '#6a6a62'; ctx.font = `${Math.floor(ts * .6)}px ${MONO}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('x', px + ts / 2, py + ts / 2); }
        if (lv.docs[k]) { ctx.fillStyle = '#55b3c4'; ctx.fillRect(px + ts * .3, py + ts * .25, ts * .4, ts * .5); }
        if (lv.items[k]) { ctx.fillStyle = '#e8b948'; ctx.beginPath(); ctx.moveTo(px + ts / 2, py + ts * .22); ctx.lineTo(px + ts * .74, py + ts / 2); ctx.lineTo(px + ts / 2, py + ts * .78); ctx.lineTo(px + ts * .26, py + ts / 2); ctx.closePath(); ctx.fill(); }
      } else { ctx.fillStyle = 'rgba(6,9,10,.55)'; ctx.fillRect(px, py, ts + 0.5, ts + 0.5); }
    }
  }
  // known buildings you cannot see right now
  if (lv.kind === 'overworld') {
    for (const poi of Object.values(game.pois)) {
      if (poi.kind === 'breach' || !(poi.revealed || poi.visited)) continue;
      const k = lv.idx(poi.x, poi.y);
      if (game.visible.has(k)) continue;
      const px = ox + poi.x * ts, py = oy + poi.y * ts;
      ctx.fillStyle = poi.id === game.final_site_id ? '#b87ad0' : (poi.lead && poi.component && game.player.count(poi.component) === 0 ? '#55b3c4' : '#8a6f9c');
      ctx.fillRect(px + 1, py + 1, ts - 2, ts - 2);
      ctx.fillStyle = '#0d1214'; ctx.font = `bold ${Math.floor(ts * .62)}px ${MONO}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(POI_LETTER[poi.kind] || 'H', px + ts / 2, py + ts / 2 + 1);
    }
  }
  if (pathPreview) {
    ctx.fillStyle = 'rgba(217,154,43,.7)';
    for (const [x, y] of pathPreview) { ctx.beginPath(); ctx.arc(ox + (x + .5) * ts, oy + (y + .5) * ts, ts * .12, 0, 7); ctx.fill(); }
  }
  // actors
  for (const a of lv.actors) {
    if (!game.visible.has(lv.idx(a.x, a.y))) continue;
    drawActor(a, ox + a.x * ts, oy + a.y * ts, ts);
  }
  drawActor(p, ox + p.x * ts, oy + p.y * ts, ts);
  // light: night tint and a pool of light around the player
  if (dark) {
    const night = lv.kind === 'overworld' ? (1 - game.clock.light) : 0.35;
    const r = Math.max(4, game.vision_radius()) * ts;
    const cx = ox + (p.x + .5) * ts, cy = oy + (p.y + .5) * ts;
    const g = ctx.createRadialGradient(cx, cy, r * 0.35, cx, cy, r * 1.15);
    g.addColorStop(0, 'rgba(4,8,14,0)'); g.addColorStop(1, `rgba(4,8,14,${0.2 + night * 0.5})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  if (aim) {
    ctx.lineWidth = 2; ctx.strokeStyle = '#d99a2b';
    if (aim.kind === 'fire') for (const t of game.targets_in_range()) { ctx.beginPath(); ctx.arc(ox + (t.x + .5) * ts, oy + (t.y + .5) * ts, ts * .62, 0, 7); ctx.stroke(); }
    else { ctx.beginPath(); ctx.arc(ox + (p.x + .5) * ts, oy + (p.y + .5) * ts, 8.5 * ts, 0, 7); ctx.setLineDash([6, 6]); ctx.stroke(); ctx.setLineDash([]); }
  }
  drawMarkers(fr);
}

function drawActor(a, px, py, ts) {
  const c = ctx, cx = px + ts / 2, cy = py + ts / 2;
  let fill, ink = '#fff', ring = null;
  if (a.kind === 'player') { fill = '#efe8d2'; ink = '#0d1214'; ring = '#d99a2b'; }
  else if (a.kind === 'zombie') { fill = ZCOL[a.special] || '#b94a3c'; if (a.flags.includes('boss')) ring = '#fff'; if (a.state === 'dormant') c.globalAlpha = 0.7; }
  else { fill = a.hostile ? '#c9992a' : '#55b3c4'; ink = '#0d1214'; }
  c.fillStyle = fill; c.beginPath(); c.arc(cx, cy, ts * .42, 0, 7); c.fill();
  if (ring) { c.strokeStyle = ring; c.lineWidth = 2; c.stroke(); }
  c.globalAlpha = 1;
  c.fillStyle = ink; c.font = `bold ${Math.floor(ts * .56)}px ${MONO}`; c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillText(a.glyph, cx, cy + 1);
  if (a.kind === 'zombie' && a.state !== 'hunt' && a.facing) {         // where it is looking: sneak up on the other side
    const ang = Math.atan2(a.facing[1], a.facing[0]), r = ts * .42;
    c.fillStyle = 'rgba(255,230,160,.9)'; c.beginPath();
    c.moveTo(cx + Math.cos(ang) * (r + 4), cy + Math.sin(ang) * (r + 4));
    c.lineTo(cx + Math.cos(ang + 2.4) * (r - 1), cy + Math.sin(ang + 2.4) * (r - 1));
    c.lineTo(cx + Math.cos(ang - 2.4) * (r - 1), cy + Math.sin(ang - 2.4) * (r - 1)); c.closePath(); c.fill();
  }
  if (a.kind === 'zombie') {                                           // awareness: ! hunting, ? it heard or half noticed you
    const al = a.alert || 0;
    if (a.state === 'hunt') { c.fillStyle = '#e2573f'; c.font = `bold ${Math.floor(ts * .5)}px ${MONO}`; c.fillText('!', cx + ts * .36, cy - ts * .38); }
    else if (al >= 25 || a.state === 'investigate') {
      c.fillStyle = al >= 70 ? '#e2573f' : '#d99a2b'; c.font = `bold ${Math.floor(ts * .5)}px ${MONO}`; c.fillText('?', cx + ts * .36, cy - ts * .38);
      if (al > 0) { c.fillStyle = '#000'; c.fillRect(px + 3, py + 1, ts - 6, 3); c.fillStyle = al >= 70 ? '#e2573f' : '#d99a2b'; c.fillRect(px + 3, py + 1, (ts - 6) * Math.min(1, al / 100), 3); }
    }
  }
  if (a.kind !== 'player' && a.hp < a.max_hp) {
    c.fillStyle = '#000'; c.fillRect(px + 3, py + ts - 5, ts - 6, 3);
    c.fillStyle = '#e2573f'; c.fillRect(px + 3, py + ts - 5, (ts - 6) * Math.max(0, a.hp / a.max_hp), 3);
  }
}

function drawThreats(fr) {
  // enemies you can see but that sit under the HUD or the controls: point at them from the edge of the free area
  const { ox, oy, ts } = view, m = 16, p = game.player;
  for (const a of game.visible_hostiles()) {
    const px = ox + (a.x + .5) * ts, py = oy + (a.y + .5) * ts;
    if (px > 0 && px < W && py > fr.top && py < fr.bottom) continue;
    const cx = Math.min(W - m, Math.max(m, px)), cy = Math.min(fr.bottom - m, Math.max(fr.top + m, py));
    const ang = Math.atan2(py - cy, px - cx);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang);
    ctx.fillStyle = a.kind === 'zombie' ? (ZCOL[a.special] || '#e2573f') : '#d9a23a';
    ctx.beginPath(); ctx.moveTo(11, 0); ctx.lineTo(-6, -7); ctx.lineTo(-6, 7); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
}

function drawMarkers(fr) {
  drawThreats(fr);
  if (game.level.kind !== 'overworld') return;
  const { ox, oy, ts } = view, m = 22;
  for (const poi of Object.values(game.pois)) {
    if (!poi.revealed || poi.kind === 'breach') continue;
    let col = null;
    if (poi.lead && poi.component && game.player.count(poi.component) === 0) col = '#55b3c4';
    else if (poi.id === game.final_site_id) col = '#b87ad0';
    if (!col) continue;
    const px = ox + (poi.x + .5) * ts, py = oy + (poi.y + .5) * ts;
    if (px > m && px < W - m && py > fr.top + m && py < fr.bottom - m) continue;
    const cx = Math.min(W - m, Math.max(m, px)), cy = Math.min(fr.bottom - m, Math.max(fr.top + m, py));
    const ang = Math.atan2(py - cy, px - cx);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang);
    ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(14, 0); ctx.lineTo(-8, -9); ctx.lineTo(-8, 9); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.fillStyle = col; ctx.font = `bold 11px ${MONO}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(POI_LETTER[poi.kind] || 'H', cx - Math.cos(ang) * 20, cy - Math.sin(ang) * 20);
  }
}

function frame() {
  if (game && game.live) liveFrame();
  if (game) {
    const p = game.player;
    const k = 0.32;
    camX += (p.x + .5 - camX) * k; camY += (p.y + .5 - camY) * k;
    if (Math.abs(p.x + .5 - camX) < 0.01 && Math.abs(p.y + .5 - camY) < 0.01) { camX = p.x + .5; camY = p.y + .5; }
    else dirty = true;
    if (game.level.hazards && Object.keys(game.level.hazards).length) dirty = true;
  }
  if (dirty) { dirty = false; draw(); }
  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------- real time (hardcore worlds)
let queued = null;
function liveFrame() {
  const g = game;
  const n = g.live_update(Date.now());
  if (queued && g.ready() && !modal && !g.over) { const fn = queued; queued = null; doAction(fn); }
  else if (n) { dirty = true; afterAction(); }
}
function startLive() { if (game && game.cfg.mode !== 'normal') { game.start_live(Date.now()); queued = null; } }

// ---------------------------------------------------------------- HUD, log, alerts
// in the shared world the calendar day is real time; the hour is still your own clock
function stampOf(g) {
  const c = g.clock;
  if (!g.shared) return c.stamp();
  const h = Math.floor(c.hour), m = Math.floor((c.hour - h) * 60);
  return `Day ${game_day(g)} ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

const pct = (v, m) => Math.max(0, Math.min(100, (v / Math.max(1, m)) * 100));
const setBar = (id, v, m, color) => { const f = $(id); f.style.width = pct(v, m) + '%'; f.style.background = color; };
function updateHud() {
  const g = game, p = g.player, c = g.clock;
  $('#h-place').innerHTML = ''; $('#h-place').append(el('b', null, g.level.name));
  $('#h-time').textContent = `${stampOf(g)} · ${c.phase}`;
  $('#v-hp').textContent = p.hp;
  setBar('#b-hp', p.hp, p.max_hp, p.hp > p.max_hp * .5 ? '#58b878' : p.hp > p.max_hp * .25 ? '#d99a2b' : '#e2573f');
  setBar('#b-sta', p.stamina, p.max_stamina, '#55b3c4');
  setBar('#b-pan', p.panic, p.max_panic, p.panic < 40 ? '#58b878' : p.panic < 75 ? '#d99a2b' : '#e2573f');
  setBar('#b-noi', g.heat, 100, g.heat > 60 ? '#e2573f' : g.heat > 30 ? '#d99a2b' : '#6b7a74');
  const chips = $('#chips'); chips.innerHTML = '';
  const add = (t, cls) => chips.append(el('span', 'chip ' + (cls || ''), t));
  if (p.infected) add(`INFECTED ${p.infection_timer >= 20 ? Math.round(p.infection_timer / 10) + 'h' : p.infection_timer + ' turns'}`, 'danger');
  if (p.bleeding) add('Bleeding', 'danger');
  if (p.fracture) add('Broken leg', 'warn');
  if (p.lost.length) add('No ' + p.lost.join('/'), 'warn');
  if (p.disguise_turns) add('Disguised', 'info');
  if (p.filter_turns) add('Filtered', 'info');
  if (p.sneaking) add('Sneaking', 'info');
  { const sb = document.querySelector('.act.sneak'); if (sb) { sb.classList.toggle('on', !!p.sneaking); $('#sneak-sub').textContent = p.sneaking ? 'on' : 'off'; } }
  if (p.sprinting) add('Running', 'info');
  if (g.cfg.mode !== 'normal') add(`Survivor #${g.generation}`, 'info');
  if (g.paused) add('PAUSED', 'warn');
  if (g.live && g.rest_left > 0) add('Resting', 'info');
  if (g.live && g.sleep_left > 0) add('Asleep', 'info');
  if (g.cfg.needs && p.hunger > 50) add('Hungry', p.hunger > 80 ? 'danger' : 'warn');
  if (g.final) add(`HOLD OUT ${g.final.turns_left}`, 'danger');
  if (g.ring && g.ring.active) add('Tide closing', 'warn');
  const objs = g.objectives(), next = objs.find((o) => !o[1]) || objs[objs.length - 1];
  $('#goal').innerHTML = ''; $('#goal').append(el('b', null, 'Goal '), next ? next[0] : '');
  layoutOverlays();
}

function renderLog() {
  const box = $('#log'); box.innerHTML = '';
  const recent = game.log.slice(-3);
  recent.forEach((m, i) => { const d = el('div', 't-' + m[2], m[1]); d.style.opacity = String(0.45 + 0.275 * (i + (3 - recent.length))); box.append(d); });
  layoutOverlays();
}

function updateControls() {
  const g = game, p = g.player;
  const ctxa = contextAction();
  $('#act-label').textContent = ctxa.label; $('#act-sub').textContent = ctxa.sub || '';
  const w = weapon_def(g);
  $('#fire-sub').textContent = is_ranged(w) ? (w.ammo ? `${p.count(w.ammo)} ammo` : w.name) : (w.name || 'fists');
  const alert = $('#alert'); alert.innerHTML = '';
  if (p.infected && can_amputate(g) === null) {
    alert.append(btn('big red', `CUT IT OFF (${p.bite_window})`, () => confirmAmputate()));
  }
  const heal = (p.hp < p.max_hp * 0.5 || p.bleeding) ? ['medkit', 'bandage'].find((id) => p.count(id) > 0) : null;
  if (heal) alert.append(btn('big', `Use ${g.item_def(heal).name.toLowerCase()}`, () => { doAction(() => g.use(p.inventory.findIndex((i) => i.id === heal))); }));
  alert.hidden = !alert.children.length;
  layoutOverlays();
}

let toastTimer = null;
function toast(text) {
  const t = $('#toast'); t.textContent = text; t.classList.add('on');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('on'), 1900);
}
function vibrate(ms) { if (prefs.haptics) { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { /* unsupported */ } } }
function flash() { const f = $('#flash'); f.classList.add('on'); requestAnimationFrame(() => requestAnimationFrame(() => f.classList.remove('on'))); }

// ---------------------------------------------------------------- the action pipeline
function refresh() { updateHud(); updateControls(); renderLog(); dirty = true; }
function afterAction() {
  const g = game, p = g.player;
  if (p.hp < lastHp) { flash(); vibrate(p.hp <= p.max_hp * .3 ? [40, 30, 40] : 25); }
  lastHp = p.hp;
  refresh();
  if (g.over) { cancelTravel(); if (!endingShown) showEnding(); return; }
  if (g.death_notice && !modal) { cancelTravel(); showDeathNotice(); return; }
  if (g.pending_event && !modal) { cancelTravel(); showEvent(); }
}
function doAction(fn) {
  if (!game || game.over || modal) return;
  if (game.live && !game.ready()) { queued = fn; return; }        // the world does not wait: the latest input runs when you are free
  queued = null;
  cancelTravel();
  try { fn(); } catch (e) { console.error(e); toast('Something went wrong'); }
  afterAction();
}

function adjacentUnaware() {
  const g = game, p = g.player;
  for (const [dx, dy] of DIRS8) {
    const a = g.level.occ.get(g.level.idx(p.x + dx, p.y + dy));
    if (a && a.kind === 'zombie' && a.state !== 'hunt' && (a.alert || 0) < 70) return a;
  }
  return null;
}
function contextAction() {
  const g = game, p = g.player, lv = g.level, k = lv.idx(p.x, p.y);
  const sneak = adjacentUnaware();
  if (sneak && !is_ranged(weapon_def(g))) return { label: 'Strike', sub: 'it has not seen you', run: () => g.attack(sneak) };
  if (lv.items[k] || lv.docs[k]) return { label: 'Pick up', sub: lv.docs[k] ? 'document' : 'items here', run: () => g.pickup() };
  const npc = g.adjacent_npc();
  if (npc) return { label: 'Talk', sub: npc.name, run: () => openNpc(npc) };
  if (g.adjacent_tile(T.BED)) return { label: 'Sleep', sub: 'until morning', run: () => confirmSleep() };
  if (g.adjacent_tile(T.BENCH)) return { label: cap(g.scenario.final_verb), sub: 'final stand', run: () => g.use_bench() };
  if (g.adjacent_tile(T.CRATE)) return { label: 'Search', sub: 'crate', run: () => g.interact() };
  if (g.adjacent_tile(T.LOCKED)) return { label: 'Unlock', sub: g.poi_of_level(lv) && g.poi_of_level(lv).code_known ? 'code known' : 'force it', run: () => g.interact() };
  return { label: 'Rest', sub: 'catch breath', run: () => g.rest() };
}

// ---------------------------------------------------------------- aiming and travelling
function startAim(kind, itemId) {
  const g = game;
  if (kind === 'fire') {
    const w = weapon_def(g);
    if (!is_ranged(w)) { toast('Equip a ranged weapon in the Bag'); return; }
    const t = g.targets_in_range();
    if (!t.length) { toast('Nothing in range'); return; }
    if (t.length === 1) { doAction(() => g.fire(t[0])); return; }
    aim = { kind };
    $('#aim').textContent = 'Tap a target to fire. Tap elsewhere to cancel.';
  } else {
    aim = { kind, itemId };
    $('#aim').textContent = 'Tap where to throw it (range 8). Tap the player to cancel.';
  }
  $('#aim').hidden = false; dirty = true;
}
function endAim() { aim = null; $('#aim').hidden = true; dirty = true; }
function aimTap(tx, ty) {
  const g = game, p = g.player, a = aim;
  endAim();
  if (a.kind === 'fire') {
    const t = g.targets_in_range().find((z) => z.x === tx && z.y === ty);
    if (t) doAction(() => g.fire(t));
  } else if (!(tx === p.x && ty === p.y)) doAction(() => g.throw_at(a.itemId, [tx, ty]));
}

function cancelTravel() { if (travel) { clearTimeout(travel.timer); travel = null; pathPreview = null; dirty = true; } }
function startTravel(path) {
  travel = { path, i: 0, timer: 0 }; pathPreview = path; stepTravel();
}
function stepTravel() {
  if (!travel) return;
  const g = game, p = g.player;
  if (g.over || g.pending_event || modal) { cancelTravel(); return; }
  if (g.visible_hostiles().length) { toast('Enemy in view'); cancelTravel(); return; }
  if (g.live && !g.ready()) { travel.timer = setTimeout(stepTravel, 40); return; }
  const next = travel.path[travel.i];
  const dx = next[0] - p.x, dy = next[1] - p.y;
  if (Math.max(Math.abs(dx), Math.abs(dy)) !== 1) { cancelTravel(); return; }
  const logN = g.log.length, hp = p.hp, lvl = g.level.id;
  const ok = g.move(dx, dy);
  afterAction();
  if (!travel) return;
  if (!ok) { cancelTravel(); return; }
  travel.i++;
  pathPreview = travel.path.slice(travel.i);
  const alarming = g.log.slice(logN).some((m) => m[2] === 'bad' || m[2] === 'warn');
  if (travel.i >= travel.path.length || p.hp < hp || alarming || g.level.id !== lvl) { cancelTravel(); return; }
  travel.timer = setTimeout(stepTravel, 75);
}
function route(tx, ty) {
  const g = game, lv = g.level, p = g.player;
  const t = lv.tile(tx, ty);
  const special = [T.CRATE, T.CRATE_OPEN, T.LOCKED, T.BED, T.BENCH].includes(t);
  let path = special ? null : g.travel_path(tx, ty);
  if (special) {
    let best = null;
    for (const [dx, dy] of DIRS8) {
      const q = g.travel_path(tx + dx, ty + dy);
      const here = (p.x === tx + dx && p.y === ty + dy) ? [] : q;
      if (here && (!best || here.length < best.length)) best = here;
    }
    if (best) path = best.concat([[tx, ty]]);
  }
  return path;
}

function onTap(sx, sy) {
  if (!game || game.over || modal) return;
  const g = game, p = g.player, lv = g.level;
  const tx = Math.floor((sx - view.ox) / view.ts), ty = Math.floor((sy - view.oy) / view.ts);
  if (travel) { cancelTravel(); return; }
  if (!lv.in_bounds(tx, ty)) return;
  if (aim) { aimTap(tx, ty); return; }
  const dx = tx - p.x, dy = ty - p.y, d = Math.max(Math.abs(dx), Math.abs(dy));
  if (d === 0) { const c = contextAction(); doAction(c.run); return; }
  const a = lv.actor_at(tx, ty);
  if (a && g.is_visible(tx, ty) && a.kind !== 'player') {
    if (a.kind === 'human' && !a.hostile) {
      if (d <= 1) doAction(() => openNpc(a)); else toast('Walk next to them to talk');
      return;
    }
    const w = weapon_def(g);
    if (d <= 1) doAction(() => g.move(dx, dy));
    else if (is_ranged(w) && d <= w.reach) doAction(() => g.fire(a));
    else if (w.reach > 1 && d <= w.reach) doAction(() => g.attack(a));
    else toast('Out of reach');
    return;
  }
  if (d === 1) { doAction(() => g.move(dx, dy)); return; }
  if (!prefs.travel) { toast('Tap-to-travel is off'); return; }
  if (g.visible_hostiles().length) { toast('Enemies nearby: move with the pad'); return; }
  const path = route(tx, ty);
  if (!path || !path.length) { toast(lv.seen[lv.idx(tx, ty)] ? 'No route there' : 'Unexplored'); return; }
  startTravel(path);
}
function onLongPress(sx, sy) {
  if (!game || modal) return;
  const tx = Math.floor((sx - view.ox) / view.ts), ty = Math.floor((sy - view.oy) / view.ts);
  vibrate(12);
  toast(game.describe_at(tx, ty) || '');
}

// ---------------------------------------------------------------- touch input on the map
const pts = new Map();
let pinch = null, press = null, moved = false;
cv.addEventListener('pointerdown', (e) => {
  cv.setPointerCapture(e.pointerId);
  pts.set(e.pointerId, { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY });
  if (pts.size === 1) {
    moved = false; press = setTimeout(() => { if (!moved && pts.size === 1) { const q = pts.values().next().value; press = null; moved = true; onLongPress(q.x, q.y); } }, 450);
  } else if (pts.size === 2) {
    const [a, b] = [...pts.values()]; pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), zoom: prefs.zoom }; moved = true; clearTimeout(press);
  }
});
cv.addEventListener('pointermove', (e) => {
  const q = pts.get(e.pointerId); if (!q) return;
  q.x = e.clientX; q.y = e.clientY;
  if (pts.size === 2 && pinch) {
    const [a, b] = [...pts.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
    prefs.zoom = Math.max(16, Math.min(46, Math.round(pinch.zoom * d / pinch.d))); dirty = true;
  } else if (Math.hypot(q.x - q.sx, q.y - q.sy) > 12) { moved = true; clearTimeout(press); }
});
function pointerEnd(e) {
  const q = pts.get(e.pointerId); if (!q) return;
  pts.delete(e.pointerId);
  clearTimeout(press);
  if (pinch && pts.size < 2) { pinch = null; savePrefs(); }
  if (!moved && e.type === 'pointerup' && pts.size === 0) onTap(q.x, q.y);
}
cv.addEventListener('pointerup', pointerEnd);
cv.addEventListener('pointercancel', pointerEnd);
cv.addEventListener('contextmenu', (e) => e.preventDefault());
cv.addEventListener('wheel', (e) => { prefs.zoom = Math.max(16, Math.min(46, prefs.zoom + (e.deltaY < 0 ? 2 : -2))); dirty = true; savePrefs(); e.preventDefault(); }, { passive: false });

// ---------------------------------------------------------------- on-screen controls
const ARROWS = [[-1, -1, 315], [0, -1, 0], [1, -1, 45], [-1, 0, 270], [0, 0, 0], [1, 0, 90], [-1, 1, 225], [0, 1, 180], [1, 1, 135]];
function buildControls() {
  const dpad = $('#dpad'); dpad.innerHTML = '';
  for (const [dx, dy, rot] of ARROWS) {
    const b = el('button', 'pad'); b.type = 'button'; b.setAttribute('aria-label', dx || dy ? `move ${dx},${dy}` : 'wait');
    b.innerHTML = dx || dy ? `<svg viewBox="0 0 24 24" style="transform:rotate(${rot}deg)"><path d="M12 20V5M6 11l6-6 6 6"/></svg>`
                           : '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/></svg>';
    let rep = null, held = false;
    const stop = () => { clearTimeout(rep); clearInterval(rep); rep = null; b.classList.remove('held'); };
    b.addEventListener('pointerdown', (e) => {
      e.preventDefault(); b.setPointerCapture(e.pointerId); b.classList.add('held'); held = false;
      if (!game || game.over || modal) return;
      if (dx || dy) {
        doAction(() => game.move(dx, dy));
        rep = setTimeout(() => { rep = setInterval(() => { if (modal || game.over) return stop(); doAction(() => game.move(dx, dy)); }, 120); }, 260);
      } else rep = setTimeout(() => { held = true; doAction(() => game.rest()); }, 450);
    });
    const up = (e) => { const was = rep !== null; stop(); if (!dx && !dy && was && !held && game && !game.over && !modal) doAction(() => game.wait(1)); };
    b.addEventListener('pointerup', up); b.addEventListener('pointercancel', stop); b.addEventListener('contextmenu', (e) => e.preventDefault());
    dpad.append(b);
  }
  const act = $('#actions'); act.innerHTML = '';
  const mk = (cls, html, fn) => { const b = el('button', 'pad act ' + cls); b.type = 'button'; b.innerHTML = html; b.addEventListener('click', fn); act.append(b); return b; };
  mk('primary', '<span id="act-label">Rest</span><small id="act-sub"></small>', () => { if (game && !game.over && !modal) { const c = contextAction(); doAction(c.run); } });
  mk('', '<span>Fire</span><small id="fire-sub"></small>', () => { if (game && !game.over && !modal) startAim('fire'); });
  mk('', '<span>Bag</span><small>items</small>', () => { if (game && !modal) openInventory(); });
  mk('', '<span>Menu</span><small>more</small>', () => { if (game && !modal) openMenu(); });
  mk('sneak', '<span id="sneak-label">Sneak</span><small id="sneak-sub">off</small>', () => { if (game && !game.over && !modal) { game.toggle_sneak(); afterAction(); } });
  $('#controls').classList.toggle('lefty', prefs.lefty);
}

window.addEventListener('keydown', (e) => {
  if (!game || modal || e.metaKey || e.ctrlKey) return;
  const k = e.key, map = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0], w: [0, -1], s: [0, 1], a: [-1, 0], d: [1, 0],
                           q: [-1, -1], e: [1, -1], z: [-1, 1], c: [1, 1] };
  if (map[k]) { doAction(() => game.move(...map[k])); e.preventDefault(); }
  else if (k === '.' || k === ' ') { doAction(() => game.wait(1)); e.preventDefault(); }
  else if (k === 'r') doAction(() => game.rest());
  else if (k === 'g') { const c = contextAction(); doAction(c.run); }
  else if (k === 'f') startAim('fire');
  else if (k === 'i' || k === 'b') openInventory();
  else if (k === 'm') openMenu();
  else if (k === 'Escape') { endAim(); cancelTravel(); }
});

// ---------------------------------------------------------------- sheets (bottom panels)
function openSheet(title, build, opts = {}) {
  modal = 1; cancelTravel();
  $('#overlay').hidden = false;
  $('#sheet-title').textContent = title;
  $('#sheet-close').hidden = !!opts.locked;
  $('#scrim').onclick = opts.locked ? null : () => closeSheet();
  sheetCloseCb = opts.onClose || null;
  const body = $('#sheet-body'); body.innerHTML = '';
  build(body);
  body.scrollTop = opts.keepScroll || 0;
}
function closeSheet() {
  if ($('#overlay').hidden) return;
  $('#overlay').hidden = true; modal = 0;
  const cb = sheetCloseCb; sheetCloseCb = null; if (cb) cb();
  dirty = true; if (game) refresh();
  if (game && game.over && !endingShown) showEnding();
  else if (game && game.death_notice) showDeathNotice();
  else if (game && game.pending_event) showEvent();
}
$('#sheet-close').addEventListener('click', () => closeSheet());

// run an engine action from inside a sheet, then refresh the world view
function sheetAct(fn) {
  if (!game || game.over) return;
  const hp = game.player.hp;
  try { fn(); } catch (e) { console.error(e); toast('Something went wrong'); }
  if (game.player.hp < hp) { flash(); vibrate(25); }
  lastHp = game.player.hp;
  refresh();
  if (game.over || game.pending_event || game.death_notice) { closeSheet(); }
}

const itemName = (it) => game.item_def(it.id).name;
function itemStats(it) {
  const d = game.item_def(it.id), bits = [];
  if (d.kind === 'weapon') bits.push(`${d.style} ${d.dmg[0]}-${d.dmg[1]}` + (d.reach > 1 ? `, reach ${d.reach}` : '') + (d.ammo ? `, uses ${game.item_def(d.ammo).name.toLowerCase()}` : '') + `, noise ${d.noise}`);
  else if (d.kind === 'armor') bits.push(`defence ${d.defense}, bite guard ${Math.round(d.bite_guard * 100)}%` + (d.stealth ? `, noisy +${d.stealth}` : ''));
  else if (d.kind === 'light') bits.push(`light radius ${d.light}`);
  else bits.push(d.desc);
  if (d.durability && it.dur !== null) bits.push(`${d.kind === 'light' ? 'fuel' : 'condition'} ${it.dur}/${d.durability}`);
  return bits.filter(Boolean).join(' · ');
}

function openInventory(sel = -1) {
  openSheet(`Pack ${game.player.slots_used()}/${INVENTORY_SLOTS}`, (body) => {
    const p = game.player;
    body.append(el('h3', 'sec', 'Carried now'));
    for (const [slot, label] of [['weapon', 'Hand'], ['armor', 'Body'], ['light', 'Light']]) {
      const it = p[slot];
      const row = el('div', 'row');
      row.append(el('div', 'badge', label[0]), el('div', 'main', [el('div', 'name', it ? itemName(it) : (slot === 'weapon' ? 'Bare fists' : 'Nothing')), el('div', 'sub', it ? itemStats(it) : label)]));
      if (it) {
        if (slot === 'light') row.append(btn('btn', p.light_on ? 'Switch off' : 'Switch on', () => { sheetAct(() => game.toggle_light()); openInventory(sel); }));
        row.append(btn('btn', 'Stow', () => { sheetAct(() => game.unequip(slot)); openInventory(sel); }));
      }
      body.append(row);
    }
    body.append(el('h3', 'sec', 'Pack'));
    if (!p.inventory.length) body.append(el('p', 'note', 'Empty. Search crates, shelves and the fallen.'));
    p.inventory.forEach((it, i) => {
      const d = game.item_def(it.id);
      const row = el('div', 'row tap' + (i === sel ? '' : ''));
      row.append(el('div', 'badge', d.kind[0].toUpperCase()), el('div', 'main', [el('div', 'name', itemName(it) + (it.qty > 1 ? ` x${it.qty}` : '')), el('div', 'sub', itemStats(it))]));
      row.addEventListener('click', () => openInventory(i === sel ? -1 : i));
      body.append(row);
      if (i === sel) {
        const acts = el('div', 'actionrow');
        const use = { weapon: 'Equip', armor: 'Equip', light: 'Equip', food: 'Eat', med: 'Use', tool: 'Use', throw: 'Throw' }[d.kind] || (d.effect.refuel ? 'Refuel light' : null);
        if (use) acts.append(btn('btn main', use, () => {
          if (d.kind === 'throw') { closeSheet(); startAim('throw', d.id); return; }
          sheetAct(() => game.use(i)); openInventory(Math.min(sel, game.player.inventory.length - 1));
        }));
        if (d.kind !== 'component') acts.append(btn('btn', 'Drop', () => { sheetAct(() => game.drop(i)); openInventory(-1); }));
        body.append(acts);
      }
    });
  });
}

function openCraft() {
  openSheet(`Craft · fluency ${Math.floor(game.know.fluency * 100)}%`, (body) => {
    body.append(el('p', 'note', `Better recipes need more of the ${game.era.cipher_name.toLowerCase()}. Crafting takes a few turns.`));
    for (const r of CONTENT.recipes) {
      const out = recipe_output(game, r);
      if (!out) continue;
      const [ok, why] = recipe_status(game, r);
      const need = r.inputs.map(([i, q]) => `${q}x ${game.item_def(i).name.toLowerCase()}`).join(', ');
      const row = el('div', 'row tap' + (ok ? '' : ' off'));
      row.append(el('div', 'main', [el('div', 'name', `${game.item_def(out).name}${r.qty > 1 ? ' x' + r.qty : ''}`), el('div', 'sub', need + (ok ? '' : ' · ' + why))]));
      if (ok) row.append(el('div', 'tag', `${r.turns} turns`));
      row.addEventListener('click', () => { if (ok) { const top = $('#sheet-body').scrollTop; sheetAct(() => game.craft(r.id)); if (!game.over) openSheetKeep(openCraft, top); } else toast(why); });
      body.append(row);
    }
  });
}
function openSheetKeep(fn, top) { fn(); $('#sheet-body').scrollTop = top; }

function openDocs() {
  const p = game.player;
  openSheet(`Documents · ${Math.floor(game.know.fluency * 100)}% fluent`, (body) => {
    body.append(el('p', 'note', `Written in ${game.era.cipher_name.toLowerCase()}. ${game.know.known.size} of ${game.know.vocab.length} words known. Decipher a page to learn what it holds.`));
    if (!p.documents.length) body.append(el('p', 'note', 'You have not found any documents yet. They hide in crates, houses and vaults.'));
    for (const id of p.documents) {
      const doc = game.docs[id], frac = Math.floor(decoded_fraction(doc, game.know) * 100), done = is_decoded(doc, game.know);
      const row = el('div', 'row tap');
      row.append(el('div', 'badge', done ? 'ok' : '?'), el('div', 'main', [el('div', 'name', doc.title), el('div', 'sub', done ? 'Deciphered' : `${frac}% readable`)]));
      row.addEventListener('click', () => openDoc(id));
      body.append(row);
    }
  });
}
function openDoc(id, note) {
  const doc = game.docs[id];
  openSheet(doc.title, (body) => {
    const done = is_decoded(doc, game.know);
    body.append(el('p', 'note', done ? 'Deciphered.' : `${Math.floor(decoded_fraction(doc, game.know) * 100)}% of the key words are known. Reading again and studying both teach words.`));
    body.append(el('div', 'paper', render_document(doc, game.know)));
    if (note) body.append(el('p', 'note t-good', note));
    const acts = el('div', 'actionrow');
    acts.append(btn('btn main', 'Read closely (2 turns)', () => { let r; sheetAct(() => { r = game.read_document(id); }); if (!game.over) openDoc(id, r && r[1].length ? 'You learn: ' + r[1].join(', ') : 'Nothing new sinks in.'); }));
    acts.append(btn('btn', doc.studies >= STUDY_LIMIT ? 'Studied out' : `Study (5 turns, ${STUDY_LIMIT - doc.studies} left)`, () => {
      let r; sheetAct(() => { r = game.study_document(id); }); if (!game.over) openDoc(id, r && r[1].length ? 'You work out: ' + r[1].join(', ') : 'The page keeps its secrets this time.');
    }));
    acts.append(btn('btn', 'All documents', () => openDocs()));
    body.append(acts);
  });
}

function openSkills() {
  const p = game.player;
  openSheet(`Skills · ${p.perk_points} point${p.perk_points === 1 ? '' : 's'}`, (body) => {
    const styles = ['blunt', 'blade', 'polearm', 'bow', 'firearm', 'energy'].filter((s) => p.style_xp[s]).map((s) => `${s} ${p.style_rank(s)}`);
    body.append(el('p', 'note', `Level ${p.level}, ${p.xp}/${xp_for(p.level)} xp. Weapon mastery: ${styles.join(', ') || 'none yet'}. Perks cost one point each; you earn a point per level.`));
    for (const b of CONTENT.branches) {
      body.append(el('h3', 'sec', CONTENT.branch_names[b]));
      for (const perk of Object.values(CONTENT.perks).filter((q) => q.branch === b)) {
        const rank = p.perks[perk.id] || 0;
        const row = el('div', 'row tap');
        row.append(el('div', 'main', [el('div', 'name', perk.name), el('div', 'sub', perk.desc)]), el('div', 'pips', '●'.repeat(rank) + '○'.repeat(perk.max_rank - rank)));
        row.addEventListener('click', () => { const top = $('#sheet-body').scrollTop; if (!game.learn_perk(perk.id)) toast(rank >= perk.max_rank ? 'Already at maximum' : 'No perk points'); refresh(); openSheetKeep(openSkills, top); });
        body.append(row);
      }
    }
  });
}

function openPlaces() {
  const g = game, p = g.player;
  openSheet('Known places', (body) => {
    const list = Object.values(g.pois).filter((q) => q.kind !== 'breach' && (q.revealed || q.visited)).sort((a, b) => cheb(poi_pos(a), [p.x, p.y]) - cheb(poi_pos(b), [p.x, p.y]));
    if (!list.length) body.append(el('p', 'note', 'Nothing marked yet. Explore, read documents, or ask around.'));
    for (const q of list) {
      const row = el('div', 'row tap');
      const goal = q.id === g.final_site_id;
      row.append(el('div', 'badge', POI_LETTER[q.kind] || 'H'), el('div', 'main', [el('div', 'name', q.name + (goal ? ' (goal)' : '')),
        el('div', 'sub', `${compass(q.x - p.x, q.y - p.y)} · ${cheb(poi_pos(q), [p.x, p.y])} tiles · ${q.visited ? 'visited' : 'unvisited'}${q.lead && q.component && p.count(q.component) === 0 ? ' · holds a component' : ''}`)]));
      row.addEventListener('click', () => {
        if (g.level.kind !== 'overworld') { toast('Go outside first'); return; }
        const path = player_path(g.level, [p.x, p.y], [q.x, q.y], () => true);
        closeSheet();
        if (!path || !path.length) toast('No route'); else if (g.visible_hostiles().length) toast('Enemies nearby'); else startTravel(path);
      });
      body.append(row);
    }
    body.append(el('p', 'note', 'Tap a place to head there. You stop when something dangerous shows up.'));
  });
}

function openStatus() {
  const g = game, p = g.player;
  openSheet('Field report', (body) => {
    body.append(el('h3', 'sec', 'Objectives'));
    for (const [text, done] of g.objectives()) body.append(el('div', 'row', [el('div', 'badge', done ? 'ok' : '·'), el('div', 'main', el('div', done ? 'name t-good' : 'name', text))]));
    body.append(el('h3', 'sec', 'You'));
    const kv = el('dl', 'kv');
    const add = (k, v) => kv.append(el('dt', null, k), el('dd', null, v));
    add('Origin', g.era.origin_names[g.cfg.origin]); add('Level', `${p.level} (${p.xp}/${xp_for(p.level)} xp)`);
    add('Humanity', `${p.humanity}/100: ${p.humanity >= 75 ? 'trusted' : p.humanity >= 40 ? 'ordinary' : p.humanity >= 15 ? 'cold' : 'feared'}`);
    add('Panic', `${Math.round(p.panic)}/100${p.panic >= 50 ? ' (aim suffers)' : ''}`);
    add('Noise', `${Math.round(g.heat)}/100${g.heat >= g.profile.stalker_heat * 0.7 ? ' (something will come)' : ''}`);
    add('Kills', `${p.stats.zombies || 0} dead, ${p.stats.humans || 0} people`);
    add('Time', `${stampOf(g)} (${g.clock.phase})`);
    if (p.infected) add('Infection', `${p.infection_timer} turns left (about ${Math.round(p.infection_timer / 10)} hours)`);
    if (g.deadline_days) add('Deadline', `the way out closes after day ${g.deadline_days}` + (g.lost_turns ? ` (the road has cost ${Math.round(g.lost_turns / 10)} hours)` : ''));
    add('The dead', `${g.profile.name}. ${profile_phase(g.profile, game_day(g)).name}.`);
    add('Seed', String(g.seed));
    body.append(kv);
  });
}

function openLog() {
  openSheet('Journal', (body) => {
    for (const [turn, text, tag] of game.log.slice(-120).reverse()) body.append(el('div', 'row', [el('div', 'main', el('div', 't-' + tag, text)), el('div', 'tag', 'T' + turn)]));
  });
}

function openHelp() {
  openSheet('How to play', (body) => {
    const li = (t, d) => body.append(el('div', 'row', el('div', 'main', [el('div', 'name', t), el('div', 'sub', d)])));
    li('Move', 'Hold the pad, or tap a tile to walk there. Walking stops when an enemy appears. Tap an adjacent enemy to hit it.');
    li('ACT button', 'It changes with what is next to you: pick up, search a crate, talk, sleep, unlock, rest. Tap yourself for the same.');
    li('Fire', 'With a ranged weapon equipped: one target fires at once; with several, tap the one you want.');
    li('Sneak up on them', 'Zombies look where they walk (the pale wedge on them). Toggle SNEAK, come from behind or from the side, and hit them before the ? bar fills: an unaware zombie dies to one blow. In front of it, or running, it notices you fast. A red ! means it hunts you. Sneaking costs half your speed and you cannot run; it ends the moment you fight a zombie that has noticed you, or get hit. Fights are loud (heavy blunt weapons the loudest) and bring the dead from far away.');
    li('Noise is the game', 'Every action makes noise. Guns are loud; blades, bows and sneaking are quiet. Too much noise brings a Stalker.');
    li('Bitten?', 'On an arm or leg, cut it off (red button) within the window, with a blade. Torso bites only buy time with suppressants.');
    li('Documents', 'They are written in a cipher. Read and study them to learn words. Deciphering reveals vault locations, codes and the formula.');
    li('Vaults', 'Components lie in locked vaults on the lowest floor. Use the code, or force the door (loud).');
    li('Long press', 'Hold on a tile to see what it is. Pinch to zoom.');
    li('Humanity', 'Your choices on the road decide who trades with you and who you face at the end.');
  });
}

function openMenu() {
  const g = game, p = g.player;
  openSheet('Menu', (body) => {
    const grid = el('div', 'grid2'); body.append(grid);
    const tile = (title, sub, fn, on) => { const b = el('button', 'tile' + (on ? ' on' : ''), [el('b', null, title), el('span', null, sub)]); b.type = 'button'; b.addEventListener('click', fn); grid.append(b); };
    tile('Pack', 'items and gear', () => openInventory());
    tile('Craft', 'make supplies', () => openCraft());
    tile('Documents', `${p.documents.length} found`, () => openDocs());
    tile('Skills', p.perk_points ? `${p.perk_points} point(s) to spend` : 'perks and mastery', () => openSkills());
    tile('Places', 'known buildings', () => openPlaces());
    tile('Throw', 'bombs and decoys', () => { closeSheet(); const t = p.inventory.find((i) => g.item_def(i.id).kind === 'throw'); if (t) startAim('throw', t.id); else toast('Nothing to throw'); });
    tile('Sneak', p.sneaking ? 'on: quieter, slower' : 'off', () => { sheetAct(() => g.toggle_sneak()); openMenu(); }, p.sneaking);
    tile('Run', p.sprinting ? 'on: uses stamina' : 'off', () => { sheetAct(() => g.toggle_sprint()); openMenu(); }, p.sprinting);
    tile('Light', p.light ? (p.light_on ? 'on: you are visible' : 'off') : 'none carried', () => { sheetAct(() => g.toggle_light()); openMenu(); }, p.light && p.light_on);
    tile('Gore disguise', 'smear with a corpse', () => { closeSheet(); doAction(() => g.smear()); });
    tile('Field report', 'goals and stats', () => openStatus());
    if (g.shared) tile('World', 'the shared season', () => openWorld());
    tile('Briefing', 'the story so far', () => showBriefing(0));
    tile('Journal', 'message history', () => openLog());
    tile('Settings', 'zoom, layout, save', () => openSettings());
    tile('How to play', 'controls', () => openHelp());
  });
}

// A survivor fell and the world went on: shown once, then the new survivor takes over.
function showDeathNotice() {
  const g = game, text = g.death_notice;
  g.death_notice = ''; lastHp = g.player.hp; camX = g.player.x + .5; camY = g.player.y + .5; flash(); vibrate([60, 40, 60]);
  openSheet(`Survivor #${g.generation - 1} has fallen`, (body) => {
    for (const para of text.split('\n\n')) body.append(el('p', 'event-text story', para));
    body.append(btn('btn main', 'Continue', () => closeSheet()));
  }, { locked: true });
  trySave();
}

// The story pages: the scene you started in, the world, and what you must do.
function showBriefing(i, first) {
  const pages = (game && game.intro_pages) || [];
  if (!pages.length) return;
  const [title, text] = pages[i], last = i === pages.length - 1;
  openSheet(title, (body) => {
    for (const para of text.split('\n\n')) body.append(el('p', 'event-text story', para));
    const acts = el('div', 'actionrow');
    acts.append(btn('btn main', last ? (first ? 'Begin' : 'Close') : 'Continue', () => { if (last) closeSheet(); else showBriefing(i + 1, first); }));
    if (!last) acts.append(btn('btn', 'Skip', () => closeSheet()));
    body.append(acts, el('p', 'note', `${i + 1} / ${pages.length}`));
  }, { locked: true, onClose: first ? startLive : null });
}

function openSettings(msg) {
  openSheet('Settings', (body) => {
    const tg = (label, key, sub) => { const r = el('button', 'toggle', [el('div', null, [el('b', null, label), el('div', 'sub', sub)]), el('span', 'sw' + (prefs[key] ? ' on' : ''))]); r.type = 'button';
      r.style.cssText = 'width:100%;text-align:left;margin-top:8px';
      r.addEventListener('click', () => { prefs[key] = !prefs[key]; savePrefs(); $('#controls').classList.toggle('lefty', prefs.lefty); openSettings(); }); body.append(r); };
    const z = el('div', 'row', [el('div', 'main', [el('div', 'name', 'Map zoom'), el('div', 'sub', `${prefs.zoom}px tiles. You can also pinch the map.`)]),
      btn('btn', '-', () => { prefs.zoom = Math.max(16, prefs.zoom - 3); savePrefs(); dirty = true; openSettings(); }), btn('btn', '+', () => { prefs.zoom = Math.min(46, prefs.zoom + 3); savePrefs(); dirty = true; openSettings(); })]);
    body.append(z);
    const tg2 = (label, sub, on, fn) => { const r = el('button', 'toggle', [el('div', null, [el('b', null, label), el('div', 'sub', sub)]), el('span', 'sw' + (on ? ' on' : ''))]); r.type = 'button'; r.style.cssText = 'width:100%;text-align:left;margin-top:8px'; r.addEventListener('click', fn); body.append(r); };
    tg('Left-handed layout', 'lefty', 'Swap the pad and the buttons.');
    tg('Tap to travel', 'travel', 'Tap a far tile to walk there.');
    tg('Vibration', 'haptics', 'Buzz when you are hurt.');
    if (game && game.live && game.cfg.mode === 'living') tg2('Pause the world', 'The shared world cannot be paused; a private one can.', game.paused, () => { game.paused = !game.paused; openSettings(); });
    const acts = el('div', 'actionrow'); acts.style.marginTop = '14px';
    acts.append(btn('btn main', 'Save now', () => { openSettings(trySave() ? 'Saved on this device.' : 'This browser would not let the page store a save.'); }));
    acts.append(btn('btn danger', 'Save and quit to title', () => { trySave(); quitToTitle(); }));
    body.append(acts);
    if (msg) body.append(el('p', 'note', msg));
    if (!storageOk) body.append(el('p', 'note t-warn', 'Saving is unavailable here, so progress is lost when you close the page.'));
  });
}

// ---------------------------------------------------------------- people, rest and events
function openNpc(npc) {
  const g = game;
  if (npc.role === 'scout' || npc.role === 'soldier') {
    const show = (line) => openSheet(npc.name, (b) => {
      if (line) b.append(el('p', 'event-text', line));
      const follows = npc.state === 'follow';
      const acts = el('div', 'actionrow');
      acts.append(btn('btn main', 'Talk', () => { const l = talk_patrol(g, npc); refresh(); show(l); }));
      acts.append(btn('btn', follows ? 'Go your way' : 'Come with me', () => { const l = follows ? dismiss(g, npc) : ask_join(g, npc); refresh(); show(l); }));
      b.append(acts);
    });
    show('');
    return;
  }
  const why = refuses(g);
  if (why) { openSheet(npc.name, (b) => b.append(el('p', 'event-text', why))); return; }
  if (npc.role === 'trader') return openTrade();
  openSheet(npc.name, (body) => {
    const say = (msg) => { body.querySelector('.say') && body.querySelector('.say').remove(); body.append(el('p', 'note say', msg)); refresh(); };
    if (npc.role === 'healer') {
      body.append(el('p', 'event-text', `"I can patch you up for ${HEAL_COST} ${g.era.coin}."`));
      body.append(btn('btn main', 'Patch me up', () => say(heal_service(g))));
    } else {
      body.append(el('p', 'event-text', `"I can teach you the ${g.era.cipher_name.toLowerCase()}, or sell what I know."`));
      const acts = el('div', 'actionrow');
      acts.append(btn('btn main', `Teach me (${TEACH_COST} ${g.era.coin})`, () => say(teach(g))));
      acts.append(btn('btn', `Buy a lead (${LEAD_COST})`, () => say(buy_lead(g))));
      body.append(acts);
    }
    body.append(el('p', 'note', `You have ${g.player.coins} ${g.era.coin}.`));
  });
}

function openTrade(msg) {
  const g = game, p = g.player;
  openSheet(`Trader · ${p.coins} ${g.era.coin}`, (body) => {
    if (msg) body.append(el('p', 'note t-good', msg));
    body.append(el('h3', 'sec', 'Buy'));
    for (const [id, price] of stock(g)) {
      const row = el('div', 'row tap');
      row.append(el('div', 'main', [el('div', 'name', g.item_def(id).name), el('div', 'sub', g.item_def(id).desc)]), el('div', 'tag', `${price} ${g.era.coin}`));
      row.addEventListener('click', () => { const t = $('#sheet-body').scrollTop; const r = buy(g, id); refresh(); openTrade(r); $('#sheet-body').scrollTop = t; });
      body.append(row);
    }
    body.append(el('h3', 'sec', 'Sell'));
    p.inventory.forEach((it, i) => {
      const price = sell_price(g, it);
      if (g.item_def(it.id).kind === 'component' || price <= 0) return;
      const row = el('div', 'row tap');
      row.append(el('div', 'main', el('div', 'name', itemName(it) + (it.qty > 1 ? ` x${it.qty}` : ''))), el('div', 'tag', `${price} ${g.era.coin}`));
      row.addEventListener('click', () => { const t = $('#sheet-body').scrollTop; const r = sell(g, i); refresh(); openTrade(r); $('#sheet-body').scrollTop = t; });
      body.append(row);
    });
  });
}

function confirmAmputate() {
  const g = game, p = g.player, shock = amputation_shock(g);
  const bandages = p.count('bandage') + p.count('medkit');
  const verdict = p.hp <= shock - 5 ? 'You will not survive it.' : p.hp <= shock + 5 ? 'It could kill you.' : 'You should survive it.';
  openSheet(`Cut off your ${p.bite_limb}?`, (body) => {
    body.append(el('p', 'event-text', `It costs about ${shock} health and a permanent loss of strength. The stump bleeds until you bind it: a bandage only slows it, a medkit closes it. You carry ${bandages}. ${p.lost.length ? 'You have already lost a limb: this one is far worse.' : ''}`));
    body.append(el('p', 'event-text t-' + (p.hp <= shock + 5 ? 'bad' : 'warn'), verdict));
    body.append(el('div', 'actionrow', [btn('btn danger', 'Cut it off', () => { closeSheet(); doAction(() => g.amputate()); }), btn('btn', 'Not yet', () => closeSheet())]));
  });
}

function confirmSleep() {
  const g = game;
  openSheet('Sleep', (body) => {
    body.append(el('p', 'event-text', 'Sleep until morning. You heal and calm down, but time passes' + (g.player.infected ? ' and the infection clock keeps running.' : '.')));
    body.append(el('div', 'actionrow', [btn('btn main', 'Sleep', () => { closeSheet(); doAction(() => g.sleep()); }), btn('btn', 'Not now', () => closeSheet())]));
  });
}

function showEvent() {
  const g = game, ev = g.pending_event, def = EVENT_BY_ID[ev.event_id];
  openSheet(def.title, (body) => {
    body.append(el('p', 'event-text', ev.text));
    def.choices.forEach((c, i) => {
      const ok = can_afford(g, c);
      const b = el('button', 'choice', fmt(c.label, event_context(g))); b.type = 'button'; b.disabled = !ok;
      if (!ok) b.append(el('small', null, 'You cannot afford that'));
      b.addEventListener('click', () => {
        const text = g.resolve_event(i);
        if (text === 'You cannot afford that.') { toast(text); return; }
        refresh();
        openSheet(def.title, (bd) => { bd.append(el('p', 'event-text', text), btn('btn main', 'Continue', () => closeSheet())); }, { locked: true });
      });
      body.append(b);
    });
  }, { locked: true });
}

// ---------------------------------------------------------------- screens: title, new game, ending
function hideAll() { for (const id of ['#title', '#newgame', '#ending']) $(id).hidden = true; for (const id of ['#hud', '#log', '#controls', '#alert', '#aim']) $(id).hidden = true; }
function showGameUi() { hideAll(); $('#hud').hidden = false; $('#log').hidden = false; $('#controls').hidden = false; resize(); refresh(); }

function trySave() {
  if (!game || game.over) return false;
  try { save_game(game); storageOk = true; return true; } catch (e) { storageOk = false; return false; }
}
function quitToTitle() { if (!$('#overlay').hidden) { $('#overlay').hidden = true; modal = 0; } game = null; if (sharedWorld) { sharedWorld.flush(); sharedWorld.detach(); sharedWorld = null; } cancelTravel(); endAim(); showTitle(); }

function showTitle() {
  hideAll(); const s = $('#title'); s.hidden = false; s.innerHTML = '';
  const w = el('div', 'wrap');
  w.append(el('div', 'fileno', ['File 0417 · quarantine zone · ', el('span', 'redact', 'CLASSIFIED')]));
  w.append(el('h1', 'logo', 'OUTBREAK'));
  w.append(el('p', 'tag-line', 'Pick the era. Pick the plague. Find what you need before it finds you.'));
  const m = el('div', 'menu');
  if (has_save()) m.append(btn('btn main', 'Continue', () => {
    try { startGame(null, load_game()); } catch (e) { toast('That save could not be loaded'); delete_save(); showTitle(); }
  }));
  m.append(btn('btn', 'New game', showNewGame), btn('btn', 'Shared world', showSharedWorld), btn('btn', 'How to play', () => openHelp()));
  w.append(m);
  w.append(el('p', 'note', 'A zombie survival roguelike. Turn based, one run, one life.'));
  if (!lsSet('outbreak.probe', 1)) w.append(el('p', 'note t-warn', 'This browser blocks storage, so saving will not work here.'));
  s.append(w);
}
let sharedWorld = null, sharedCtx = null;
let newCfg = null;
function showNewGame() {
  hideAll(); const s = $('#newgame'); s.hidden = false;
  newCfg = newCfg || Object.assign(default_config(), lsGet('outbreak.lastcfg', {}), { seed: null });
  const render = () => {
    s.innerHTML = '';
    const w = el('div', 'wrap form');
    const head = el('h2', 'logo', 'Brief'); head.style.fontSize = '40px';
    w.append(el('div', 'fileno', 'New case file'), head);
    const era = CONTENT.eras[newCfg.era];
    const group = (title, key, items, blurbOf, cols) => {
      w.append(el('h3', null, title));
      const box = el('div', 'opts' + (cols ? ' cols' : ''));
      for (const [id, name, sub] of items) {
        const o = el('button', 'opt' + (newCfg[key] === id ? ' on' : ''), [el('b', null, name), sub ? el('small', null, sub) : null]); o.type = 'button';
        o.addEventListener('click', () => { newCfg[key] = id; if (key === 'era') { /* origin names change */ } render(); });
        box.append(o);
      }
      w.append(box);
      if (blurbOf) w.append(el('div', 'blurb', blurbOf()));
    };
    group('When the collapse happens', 'era', Object.values(CONTENT.eras).map((e) => [e.id, `${e.year} · ${cap(e.name.split(' - ')[1] || e.name)}`, null]), () => era.blurb);
    const pz = CONTENT.presets[newCfg.zombies];
    group('What the dead are', 'zombies', Object.values(CONTENT.presets).map((z) => [z.id, z.name.split(' - ')[0], z.inspired_by]), () => `${pz.blurb}`);
    const sc = CONTENT.scenarios[newCfg.scenario];
    group('What you must do', 'scenario', Object.values(CONTENT.scenarios).map((c) => [c.id, c.name.split(' - ')[0], null]), () => sc.blurb);
    group('Who you are', 'origin', Object.values(CONTENT.origins).map((o) => [o.id, era.origin_names[o.id], null]), () => CONTENT.origins[newCfg.origin].blurb, true);
    group('Mode', 'mode', [['normal', 'Normal', 'one life'], ['living', 'Hardcore', 'the world goes on']],
      () => (newCfg.mode === 'living' ? 'You die, the world does not. A new survivor walks out of the refuge into the same world; what killed you levels up and keeps its name; your body rises. Infinite lives. The cure is for the world: nobody starts bitten.'
        : 'One survivor, one life. Permadeath deletes the save.'), true);
    group('How it starts', 'opening', [['random', 'Surprise me', null]].concat(Object.values(CONTENT.openings).map((o) => [o.id, o.name, null])),
      () => (newCfg.opening === 'random' ? 'The scene you wake up in is picked for who you are: scholars start studying, medics on their rounds.'
        : `${CONTENT.openings[newCfg.opening].scenes[newCfg.era]} [${CONTENT.openings[newCfg.opening].perk}]`), true);
    group('Difficulty', 'difficulty', ['easy', 'normal', 'hard'].map((d) => [d, cap(d), null]), () => ({ easy: 'Fewer dead, more loot, gentler hits, longer fuse.', normal: 'The intended experience.', hard: 'More dead, scarce loot, brutal hits, a short fuse.' })[newCfg.difficulty], true);
    w.append(el('h3', null, 'Rules'));
    for (const [key, label, sub] of [['needs', 'Hunger', 'Eat or weaken and starve.'], ['permadeath', 'Permadeath', 'Death deletes the save.']]) {
      const t = el('button', 'toggle', [el('div', null, [el('b', null, label), el('div', 'sub', sub)]), el('span', 'sw' + (newCfg[key] ? ' on' : ''))]); t.type = 'button';
      t.style.cssText = 'width:100%;text-align:left;margin-bottom:8px';
      t.addEventListener('click', () => { newCfg[key] = !newCfg[key]; render(); }); w.append(t);
    }
    w.append(el('h3', null, 'Seed (optional)'));
    const seedRow = el('div', 'seed'); const inp = el('input'); inp.id = 'seed'; inp.type = 'number'; inp.placeholder = 'random'; inp.inputMode = 'numeric'; inp.value = newCfg.seed === null ? '' : newCfg.seed;
    inp.addEventListener('input', () => { newCfg.seed = inp.value === '' ? null : Math.abs(parseInt(inp.value, 10)) % 1073741824; });
    seedRow.append(inp, btn('btn', 'Roll', () => { newCfg.seed = Math.floor(Math.random() * 1000000); render(); }));
    w.append(seedRow);
    const go = el('div', 'sticky'); const start = btn('btn main', 'BEGIN', () => {
      start.textContent = 'Generating the world...'; start.disabled = true;
      setTimeout(() => { try { lsSet('outbreak.lastcfg', newCfg); startGame(Object.assign({}, newCfg)); } catch (e) { console.error(e); start.textContent = 'Failed: ' + e.message; } }, 30);
    });
    go.append(start, el('p', 'note', ''));
    w.append(go, btn('btn', 'Back', showTitle));
    s.append(w);
  };
  render(); s.scrollTop = 0;
}

function startGame(cfg, loaded, shared) {
  if (sharedWorld) { sharedWorld.detach(); sharedWorld = null; }
  game = loaded || new Game(cfg);
  if (shared) {
    sharedWorld = new SharedWorld(shared.env.db, shared.env.uid, shared.season);
    sharedWorld.onclose = () => { if (game && game.over) afterAction(); };
    sharedWorld.attach(game);
  }
  game.on_autosave = () => { trySave(); };
  endingShown = false; aim = null; travel = null; pathPreview = null; modal = 0;
  lastHp = game.player.hp; camX = game.player.x + .5; camY = game.player.y + .5;
  showGameUi();
  trySave();
  if (!loaded) showBriefing(0, true);
  else if (game.cfg.mode !== 'normal') openSheet('Back in the world', (b) => { b.append(el('p', 'event-text story', game.cfg.mode === 'shared' ? 'The world kept going while you were away. Time runs on its own here.' : 'The world runs in real time. Nothing waits for you once you continue.'), btn('btn main', 'Continue', () => closeSheet())); }, { locked: true, onClose: startLive });
}

function showEnding() {
  const g = game, e = g.over; endingShown = true; cancelTravel(); endAim();
  const isShared = g.cfg.mode === 'shared';
  if (isShared) { delete_save(null, true); if (sharedWorld) { sharedWorld.flush(); sharedWorld.detach(); sharedWorld = null; } }
  else if (g.cfg.mode === 'normal' ? (g.cfg.permadeath || e.victory) : e.victory) delete_save();
  if (!$('#overlay').hidden) { $('#overlay').hidden = true; modal = 0; }
  hideAll(); const s = $('#ending'); s.hidden = false; s.innerHTML = '';
  const w = el('div', 'wrap');
  w.append(el('div', 'fileno', e.victory ? 'Case closed' : e.kind === 'closed' ? 'The world is closed' : 'Case file: terminated'), el('h2', 'end-title ' + (e.victory ? 'win' : 'lose'), e.title), el('p', 'end-text', e.text));
  w.append(el('div', 'sum', e.summary.map((l) => el('div', null, l))));
  w.append(el('div', 'fileno', 'Score'), el('div', 'score', String(e.score)));
  const m = el('div', 'menu'); m.style.marginTop = '20px';
  if (isShared) m.append(btn('btn main', 'Back to the shared world', () => { game = null; showSharedWorld(); }), btn('btn', 'Title screen', () => { game = null; showTitle(); }));
  else m.append(btn('btn main', 'New game', () => { game = null; showNewGame(); }), btn('btn', 'Title screen', () => { game = null; showTitle(); }));
  w.append(m); s.append(w); s.scrollTop = 0;
}

// ---------------------------------------------------------------- the shared world: season, keeper, join
async function sharedEnv() {
  if (sharedCtx) return sharedCtx;
  try {
    if (typeof claude === 'undefined' || !claude.use) return null;
    const db = await claude.use('db'); if (!db) return null;
    const user = await claude.use('user');
    sharedCtx = { db, uid: user ? await user.id() : null, canWrite: user ? await user.can('data.write') : null, isAdmin: user ? await user.canEdit() : false };
    return sharedCtx;
  } catch (e) { return null; }
}
const fmtLeft = (sec) => { const d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60); return d ? `${d}d ${h}h` : h ? `${h}h ${m}m` : `${m}m`; };

async function showSharedWorld(msg) {
  hideAll(); const s = $('#newgame'); s.hidden = false; s.innerHTML = '';
  const w = el('div', 'wrap form');
  w.append(el('div', 'fileno', 'Hardcore · one world for everyone'), el('h2', 'logo', 'Shared world'));
  w.firstChild.nextSibling.style.fontSize = '36px';
  s.append(w);
  const note = (t, cls) => w.append(el('p', 'note ' + (cls || ''), t));
  note('Loading the world...');
  const env = await sharedEnv();
  w.querySelector('p.note').remove();
  const back = () => w.append(btn('btn', 'Back', showTitle));
  if (!env) { note('The shared world needs this page to be opened from claude.ai, signed in, with the owner\'s sharing on. In a plain browser it cannot reach the shared database.', 't-warn'); back(); return; }
  let season = null, outcome = null;
  try {
    const sd = await env.db.doc('season/current').get(); season = sd.exists ? sd.data() : null;
    const od = await env.db.doc('play/outcome').get(); outcome = od.exists ? od.data() : null;
  } catch (e) { note('The shared database did not answer. Try again in a moment.', 't-warn'); back(); return; }
  if (msg) note(msg, 't-good');
  const now = Date.now();
  if (outcome && season && outcome.season !== season.n) outcome = null;
  const over = season && (now >= season.endsAt || outcome);
  if (!season) note(env.isAdmin ? 'There is no world yet. You are the keeper: create the first season.' : 'There is no world yet. The keeper has not created one.');
  else {
    const dayN = season_day(season, now), cfg = season.cfg;
    w.append(el('h3', null, `Season ${season.n}`));
    const kv = el('dl', 'kv');
    const add = (k, v) => kv.append(el('dt', null, k), el('dd', null, v));
    add('Calendar', `day ${dayN} (${season.dayMs / 3600000} real hours per day)`);
    add('Real time', `live: a step every ${season.tickMs || 700} ms, a sun cycle every ${Math.round(240 * (season.tickMs || 700) / 1000 / 60 * 10) / 10} min`);
    add('Resets in', over ? 'over' : fmtLeft(Math.max(0, Math.floor((season.endsAt - now) / 1000))));
    add('The world', `${CONTENT.eras[cfg.era].year} · ${CONTENT.presets[cfg.zombies].name.split(' - ')[0]} · ${CONTENT.scenarios[cfg.scenario].name.split(' - ')[0]} · ${cfg.difficulty}`);
    if (outcome) add('Outcome', outcome.kind === 'won' ? `The cure was made on day ${outcome.day}.` : 'The way out closed. Nobody made it.');
    w.append(kv);
    if (over) note(outcome ? 'This season is decided. The keeper will reset the world.' : 'This season has ended. The keeper will reset the world.');
    else {
      note('Every survivor shares one seeded world. The dead you destroy stay dead for everyone, your tomb keeps your gear for the next, whatever killed you gets a name and a level, and enemies keep levelling while nobody plays. It runs in real time, with no turns and no pause, but you do not see other players move.');
      if (env.canWrite === false) note('You can read this world but not play in it: ask the owner for contributor access.', 't-warn');
      else {
        w.append(btn('btn main', 'Join the world', () => showSharedJoin(env, season)));
        if (has_save(null, true)) w.append(btn('btn', 'Continue my survivor', () => {
          try { const g = load_game(null, true); if (g.season_n !== season.n) { delete_save(null, true); showSharedWorld('That survivor belonged to an earlier season.'); return; } startGame(null, g, { env, season }); }
          catch (e) { delete_save(null, true); showSharedWorld('That save could not be loaded.'); }
        }));
      }
    }
  }
  if (env.isAdmin) w.append(btn('btn', season ? 'Keeper: reset or reconfigure' : 'Keeper: create the world', () => showKeeper(env, season)));
  back();
}

function showSharedJoin(env, season) {
  hideAll(); const s = $('#newgame'); s.hidden = false; s.innerHTML = '';
  const cfg = season.cfg, era = CONTENT.eras[cfg.era], pick = { origin: 'medic', opening: 'random' };
  const render = () => {
    s.innerHTML = '';
    const w = el('div', 'wrap form');
    w.append(el('div', 'fileno', `Season ${season.n}`), el('h2', 'logo', 'Arrive'));
    w.querySelector('h2').style.fontSize = '36px';
    const group = (title, key, items, blurb) => {
      w.append(el('h3', null, title));
      const box = el('div', 'opts cols');
      for (const [id, name] of items) { const o = el('button', 'opt' + (pick[key] === id ? ' on' : ''), [el('b', null, name)]); o.type = 'button'; o.addEventListener('click', () => { pick[key] = id; render(); }); box.append(o); }
      w.append(box, el('div', 'blurb', blurb()));
    };
    group('Who you are', 'origin', Object.values(CONTENT.origins).map((o) => [o.id, era.origin_names[o.id]]), () => CONTENT.origins[pick.origin].blurb);
    group('How you arrive', 'opening', [['random', 'Surprise me']].concat(Object.values(CONTENT.openings).map((o) => [o.id, o.name])),
      () => (pick.opening === 'random' ? 'Picked from who you are.' : CONTENT.openings[pick.opening].scenes[cfg.era]));
    const go = el('div', 'sticky'); const start = btn('btn main', 'BEGIN', () => {
      start.textContent = 'Generating the world...'; start.disabled = true;
      setTimeout(() => { try { startGame(Object.assign({}, cfg, { mode: 'shared', seed: season.seed, origin: pick.origin, opening: pick.opening, season_n: season.n, clock_turn: season_turn(season, Date.now()) }), null, { env, season }); }
        catch (e) { console.error(e); start.textContent = 'Failed: ' + e.message; } }, 30);
    });
    go.append(start); w.append(go, btn('btn', 'Back', () => showSharedWorld()));
    s.append(w);
  };
  render(); s.scrollTop = 0;
}

function showKeeper(env, season) {
  hideAll(); const s = $('#newgame'); s.hidden = false; s.innerHTML = '';
  const base = season ? Object.assign({}, season.cfg) : { era: 'modern', zombies: 'classic', scenario: 'cure', difficulty: 'normal', needs: false, map_w: 360, map_h: 240 };
  const num = { days: season ? Math.round((season.endsAt - season.startedAt) / 86400000) : 7, hours: season ? season.dayMs / 3600000 : 3, tick: season ? (season.tickMs || 700) : 700 };
  let armed = false;
  const render = (msg) => {
    s.innerHTML = '';
    const w = el('div', 'wrap form');
    w.append(el('div', 'fileno', 'Keeper'), el('h2', 'logo', 'The world'));
    w.querySelector('h2').style.fontSize = '36px';
    w.append(el('p', 'note', 'These rules apply to the next season. Resetting ends the current one for everyone, clears its tombs, named enemies and kills, and picks a new seed.'));
    const group = (title, key, items) => {
      w.append(el('h3', null, title));
      const box = el('div', 'opts cols');
      for (const [id, name] of items) { const o = el('button', 'opt' + (base[key] === id ? ' on' : ''), [el('b', null, name)]); o.type = 'button'; o.addEventListener('click', () => { base[key] = id; armed = false; render(); }); box.append(o); }
      w.append(box);
    };
    group('Era', 'era', Object.values(CONTENT.eras).map((e) => [e.id, e.year]));
    group('The dead', 'zombies', Object.values(CONTENT.presets).map((z) => [z.id, z.name.split(' - ')[0]]));
    group('Goal', 'scenario', Object.values(CONTENT.scenarios).map((c) => [c.id, c.name.split(' - ')[0]]));
    group('Difficulty', 'difficulty', ['easy', 'normal', 'hard'].map((d) => [d, cap(d)]));
    const numRow = (label, key, min, max, sub) => {
      w.append(el('h3', null, label));
      const row = el('div', 'seed'); const inp = el('input'); inp.type = 'number'; inp.value = num[key]; inp.min = min; inp.max = max; inp.inputMode = 'decimal';
      inp.addEventListener('input', () => { const v = parseFloat(inp.value); if (v >= min && v <= max) { num[key] = v; armed = false; } });
      row.append(inp, el('span', 'note', sub)); w.append(row);
    };
    numRow('Season length (real days)', 'days', 0.1, 90, 'days until the world resets');
    numRow('Calendar day (real hours)', 'hours', 0.1, 48, 'real hours per calendar day: enemy level cap, zombie phases, the deadline');
    numRow('Tick (milliseconds)', 'tick', 200, 3000, 'the world runs live: one step every tick. Day and night turn every 240 ticks');
    if (msg) w.append(el('p', 'note t-good', msg));
    const label = season ? (armed ? 'Tap again: reset the world now' : `Reset the world (end season ${season.n})`) : 'Create the world';
    w.append(btn('btn ' + (armed ? 'danger' : 'main'), label, async () => {
      if (season && !armed) { armed = true; render(); return; }
      try { const next = await reset_world(env.db, season, base, Date.now(), { dayMs: num.hours * 3600000, seasonMs: num.days * 86400000, tickMs: num.tick }); showSharedWorld(`Season ${next.n} has begun.`); }
      catch (e) { render('Could not write: ' + (e && e.code || e)); }
    }));
    w.append(btn('btn', 'Back', () => showSharedWorld()));
    s.append(w);
  };
  render(); s.scrollTop = 0;
}

// in-game: how the season is going
function openWorld() {
  const g = game, sw = g.shared; if (!sw) return;
  const sm = sw.summary();
  openSheet(`Season ${sm.n}`, (body) => {
    const kv = el('dl', 'kv');
    const add = (k, v) => kv.append(el('dt', null, k), el('dd', null, v));
    add('Calendar day', String(sm.day)); add('Resets in', fmtLeft(sm.seconds_left)); add('Survivors fallen', String(sm.fallen));
    add('Enemy level cap', String(level_cap(g)));
    body.append(kv);
    if (sm.outcome) body.append(el('p', 'note', sm.outcome.kind === 'won' ? 'The cure has been made.' : 'The way out has closed.'));
    body.append(el('h3', 'sec', 'Named enemies still out there'));
    if (!sm.named.length) body.append(el('p', 'note', 'None yet.'));
    for (const d of sm.named) body.append(el('div', 'row', [el('div', 'main', [el('div', 'name', `${d.name}`), el('div', 'sub', d.title)])]));
    body.append(el('h3', 'sec', 'Hall of the fallen'));
    if (!sm.hall.length) body.append(el('p', 'note', 'Nobody has fallen yet.'));
    for (const h of sm.hall.slice(0, 12)) body.append(el('div', 'row', [el('div', 'main', [el('div', 'name', `${h.label} · level ${h.level}`), el('div', 'sub', `day ${h.day}: ${h.cause}`)])]));
  });
}

// ---------------------------------------------------------------- boot
function boot() {
  buildControls();
  resize();
  window.addEventListener('resize', resize);
  window.addEventListener('orientationchange', () => setTimeout(resize, 120));
  document.addEventListener('visibilitychange', () => { if (document.hidden) trySave(); });
  window.addEventListener('pagehide', () => { trySave(); });
  document.addEventListener('contextmenu', (e) => e.preventDefault());
  showTitle();
  requestAnimationFrame(frame);
  window.OB_DEBUG = { get game() { return game; }, get view() { return view; }, showEvent, showEnding, refresh, openDoc, afterAction, start: (cfg) => startGame(Object.assign(default_config(), cfg)), prefs, openMenu, openInventory, openDocs, openSkills, openPlaces, openCraft, openStatus };
}
boot();
})();
