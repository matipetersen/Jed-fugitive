/* Dibujo procedural: terreno, carretas, personas, retratos, fondos y partículas. */
(function (CV) {
'use strict';
const UI = CV.ui, D = CV.data;
const R = CV.render = {};
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
R.mk = mk;
const SHIRTS = ['#964638', '#466496', '#5a8250', '#96783c', '#78508a', '#3c7878', '#a05a6e', '#6e6e6e'];
const SKINS = ['#e0ba98', '#cea07c', '#ba8a68', '#e8c4a4'];
const hash = s => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return h; };
R.shirt = cid => SHIRTS[cid % SHIRTS.length];

// ------------------------------------------------------------ terreno
const groundCache = {};
R.ground = function (w, h, terrain, seed) {
  const key = `${w}x${h}${terrain}${seed}`; if (groundCache[key]) return groundCache[key];
  const c = mk(w, h), g = c.getContext('2d'), rng = new CV.RNG(seed * 7919 + hash(terrain));
  const base = D.TERRAIN_COLORS[terrain] || D.TERRAIN_COLORS.pradera;
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  const adj = (hex, d) => { const n = parseInt(hex.slice(1), 16); const f = x => Math.max(0, Math.min(255, x + d)); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; };
  for (let i = 0; i < w * h / 9000; i++) { const r = rng.int(30, 110); g.globalAlpha = .09; g.fillStyle = adj(base, rng.int(-14, 14)); g.beginPath(); g.arc(rng.int(-r, w), rng.int(-r, h), r, 0, 7); g.fill(); }
  g.globalAlpha = 1; g.lineWidth = 1;
  for (let i = 0; i < w * h / 700; i++) { const x = rng.int(0, w), y = rng.int(0, h), ln = rng.int(3, 7); g.strokeStyle = adj(base, rng.int(-34, 22)); g.beginPath(); g.moveTo(x, y); g.lineTo(x + rng.int(-2, 2), y - ln); g.stroke(); }
  for (let i = 0; i < w * h / 14000; i++) { const gg = rng.int(110, 150); g.fillStyle = `rgb(${gg},${gg - 4},${gg - 10})`; g.beginPath(); g.ellipse(rng.int(0, w), rng.int(0, h), rng.int(2, 5), rng.int(1, 3), 0, 0, 7); g.fill(); }
  if (['pradera', 'valle', 'llanura'].includes(terrain)) for (let i = 0; i < w * h / 22000; i++) { g.fillStyle = rng.choice(['#f0dc5a', '#e6e6f0', '#d278aa']); g.fillRect(rng.int(0, w), rng.int(0, h), 2, 2); }
  return groundCache[key] = c;
};

// ------------------------------------------------------------ carreta (vista cenital)
const wagonCache = {};
R.wagonBase = function (level, reinforced, platform, cannon, lantern, destroyed) {
  const key = [level, reinforced, platform, cannon, lantern, destroyed].join(); if (wagonCache[key]) return wagonCache[key];
  const W = 100, H = 54, c = mk(W, H), g = c.getContext('2d'), rng = new CV.RNG(5), cx = W / 2, cy = H / 2;
  const rect = (x, y, w, h, r, fill, stroke, lw) => { g.beginPath(); g.roundRect(x, y, w, h, r); if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.lineWidth = lw || 1; g.strokeStyle = stroke; g.stroke(); } };
  if (destroyed) {
    for (let i = 0; i < 16; i++) { const x = rng.int(14, W - 26), y = rng.int(10, H - 14), a = rng.uniform(0, Math.PI), ln = rng.int(10, 26); g.strokeStyle = rng.choice(['#46301e', '#5c3e26', '#281e18']); g.lineWidth = rng.int(2, 4); g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * ln, y + Math.sin(a) * ln); g.stroke(); }
    g.fillStyle = 'rgba(30,26,24,.6)'; g.beginPath(); g.ellipse(cx, cy, 24, 10, 0, 0, 7); g.fill();
    g.strokeStyle = '#3c322c'; g.lineWidth = 2; g.beginPath(); g.arc(cx - 28, cy + 10, 8, 0, 7); g.stroke();
    return wagonCache[key] = c;
  }
  for (const dx of [-27, 27]) for (const dy of [-1, 1]) { rect(cx + dx - 7, cy + dy * (H / 2 - 5) - 3.5, 14, 7, 2, '#221a14'); g.strokeStyle = '#564230'; g.beginPath(); g.moveTo(cx + dx - 5, cy + dy * (H / 2 - 5)); g.lineTo(cx + dx + 5, cy + dy * (H / 2 - 5)); g.stroke(); }
  rect(6, 7, W - 12, H - 14, 5, '#765230', '#4a321e', 2);
  for (let i = 0; i < reinforced; i++) rect(10 + i * 4, 9 + i * 2, W - 20 - i * 8, H - 18 - i * 4, 4, null, '#787c82', 2);
  if (reinforced) for (let x = 14; x < W - 12; x += 18) { g.fillStyle = '#969aa0'; g.beginPath(); g.arc(x, 10, 2, 0, 7); g.arc(x, H - 11, 2, 0, 7); g.fill(); }
  rect(12, 11, W - 24, H - 22, 14, '#e8deb e'.replace(' ', ''), '#b0a07e', 2);
  g.strokeStyle = '#cec2a0'; g.lineWidth = 1; for (let x = 20; x < W - 16; x += 11) { g.beginPath(); g.moveTo(x, 14); g.lineTo(x, H - 14); g.stroke(); }
  if (level >= 1) for (let i = 0; i < 3 * level; i++) { const x = rng.int(18, W - 18), y = rng.int(15, H - 15); g.fillStyle = '#463828'; g.beginPath(); g.arc(x, y, rng.int(2, 4), 0, 7); g.fill(); g.strokeStyle = '#3c3022'; g.beginPath(); g.moveTo(x, y); g.lineTo(x + rng.int(-8, 8), y + rng.int(-5, 5)); g.stroke(); }
  if (level >= 2) { g.fillStyle = 'rgba(60,50,40,.85)'; g.beginPath(); g.moveTo(cx - 6, 13); g.lineTo(cx + 12, 19); g.lineTo(cx + 2, 27); g.fill(); g.strokeStyle = '#281e18'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx - 22, H - 14); g.lineTo(cx - 10, 19); g.stroke(); }
  if (level >= 3) { g.fillStyle = 'rgba(36,30,26,.8)'; g.beginPath(); g.ellipse(cx + 17, cy + 5, 13, 7, 0, 0, 7); g.fill(); }
  if (platform) { rect(cx - 18, cy - 7, 36, 14, 2, '#966c42', '#503820', 2); g.strokeStyle = '#64482a'; for (let x = cx - 14; x < cx + 18; x += 6) { g.beginPath(); g.moveTo(x, cy - 5); g.lineTo(x, cy + 5); g.stroke(); } }
  if (cannon) { g.fillStyle = '#2e2c30'; g.beginPath(); g.arc(cx - 6, cy, 8, 0, 7); g.fill(); rect(cx - 6, cy - 4, 30, 8, 3, '#3e3e44'); g.fillStyle = '#1e1e22'; g.beginPath(); g.arc(cx + 24, cy, 5, 0, 7); g.fill(); }
  if (lantern) { g.fillStyle = '#ffd66e'; g.beginPath(); g.arc(W - 14, 12, 4, 0, 7); g.fill(); g.strokeStyle = '#78501e'; g.stroke(); }
  return wagonCache[key] = c;
};
R.drawWagon = function (g, x, y, tangent, hpFrac, reinforced, platform, cannon, lantern, destroyed, scale, flash) {
  const level = hpFrac > .75 ? 0 : hpFrac > .5 ? 1 : hpFrac > .25 ? 2 : 3;
  const b = R.wagonBase(level, reinforced, platform, cannon, lantern, destroyed);
  g.save(); g.translate(x, y); g.rotate(tangent); g.scale(scale || 1, scale || 1);
  g.drawImage(b, -b.width / 2, -b.height / 2);
  if (flash) { g.globalAlpha = .4; g.fillStyle = '#ff5a40'; g.globalCompositeOperation = 'source-atop'; }
  g.restore();
};

// ------------------------------------------------------------ personas
R.drawPerson = function (g, x, y, group, cid, scale, o) {
  o = o || {};
  const sz = ({adulto: 7.5, joven: 6.8, niño: 5, anciano: 7}[group] || 7) * scale;
  if (o.dead) { g.fillStyle = '#3c2824'; g.beginPath(); g.ellipse(x, y, sz, sz * .5, 0, 0, 7); g.fill(); return; }
  const shirt = R.shirt(cid);
  g.fillStyle = 'rgba(0,0,0,.24)'; g.beginPath(); g.ellipse(x, y + sz * .7, sz, sz * .45, 0, 0, 7); g.fill();
  if (o.aim !== undefined && o.aim !== null) {
    const a = o.aim; g.strokeStyle = '#3c2e22'; g.lineWidth = Math.max(1, 2 * scale); g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * (sz + 8 * scale), y + Math.sin(a) * (sz + 8 * scale)); g.stroke();
    g.strokeStyle = '#bebec8'; g.lineWidth = 1; g.beginPath(); g.moveTo(x + Math.cos(a) * (sz + 8 * scale), y + Math.sin(a) * (sz + 8 * scale)); g.lineTo(x + Math.cos(a) * (sz + 11 * scale), y + Math.sin(a) * (sz + 11 * scale)); g.stroke();
  }
  g.fillStyle = shirt; g.beginPath(); g.arc(x, y, sz, 0, 7); g.fill(); g.lineWidth = 1; g.strokeStyle = '#281e18'; g.stroke();
  const hy = y - sz * .25;
  g.fillStyle = SKINS[0]; g.beginPath(); g.arc(x, hy, Math.max(2, sz * .55), 0, 7); g.fill();
  if (group === 'adulto') { g.fillStyle = '#463424'; g.beginPath(); g.ellipse(x, hy - sz * .45, sz * .8, sz * .35, 0, 0, 7); g.fill(); }
  else if (group === 'anciano') { g.fillStyle = '#e1e1e1'; g.beginPath(); g.arc(x, hy - sz * .35, Math.max(1, sz * .4), 0, 7); g.fill(); }
  else if (group === 'joven') { g.strokeStyle = '#6e4c28'; g.lineWidth = 2; g.beginPath(); g.arc(x, hy, sz * .6, Math.PI, 2 * Math.PI); g.stroke(); }
  else { g.fillStyle = '#c89646'; g.beginPath(); g.arc(x, hy - sz * .35, Math.max(1, sz * .45), 0, 7); g.fill(); }
  if (o.wounded) { g.strokeStyle = '#dc2828'; g.lineWidth = 2; g.beginPath(); g.moveTo(x - 3, y - sz - 5); g.lineTo(x + 3, y - sz - 5); g.moveTo(x, y - sz - 8); g.lineTo(x, y - sz - 2); g.stroke(); }
};
R.drawFoe = function (g, f, x, y, s, tribeCol, flash, ghost) {
  const k = f.kind, col = flash ? '#f0f0f0' : tribeCol;
  if (ghost) { g.fillStyle = '#a02828'; g.beginPath(); g.arc(x, y, Math.max(2, 3 * s), 0, 7); g.fill(); return; }
  if (k === 'jinete' || k === 'jefe') {
    const L = 14 * s * (k === 'jefe' ? 1.25 : 1);
    g.save(); g.translate(x, y); g.fillStyle = 'rgba(0,0,0,.2)'; g.beginPath(); g.ellipse(0, 6 * s, L * .9, 3 * s, 0, 0, 7); g.fill();
    g.rotate(f.face); const horse = k === 'jinete' ? '#6e4a2c' : '#1e1816';
    g.fillStyle = horse; g.beginPath(); g.ellipse(0, 0, L * .95, L * .38, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(L * .95, -L * .05, L * .3, L * .2, 0, 0, 7); g.fill();
    g.strokeStyle = '#32241a'; g.lineWidth = 2; g.beginPath(); g.moveTo(-L * .9, 0); g.lineTo(-L * 1.2, L * .3); g.stroke();
    g.restore();
    g.fillStyle = col; g.beginPath(); g.arc(x, y - 2 * s, Math.max(3, 4.5 * s), 0, 7); g.fill();
    g.fillStyle = '#cda078'; g.beginPath(); g.arc(x, y - 5 * s, Math.max(2, 3 * s), 0, 7); g.fill();
    if (k === 'jefe') { for (let i = -3; i <= 3; i++) { g.strokeStyle = '#f0f0e6'; g.lineWidth = 2; g.beginPath(); g.moveTo(x, y - 6 * s); g.lineTo(x + i * 4 * s, y - 15 * s); g.stroke(); g.fillStyle = '#c82828'; g.beginPath(); g.arc(x + i * 4 * s, y - 15 * s, 2, 0, 7); g.fill(); } }
    else { g.strokeStyle = '#f0f0e6'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 1, y - 6 * s); g.lineTo(x + 3 * s, y - 11 * s); g.stroke(); }
    return;
  }
  const r = 6.2 * s;
  g.fillStyle = 'rgba(0,0,0,.2)'; g.beginPath(); g.ellipse(x, y + r * .6, r, r * .5, 0, 0, 7); g.fill();
  g.fillStyle = col; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.lineWidth = 1; g.strokeStyle = '#321e18'; g.stroke();
  g.fillStyle = '#cda078'; g.beginPath(); g.arc(x, y - r * .3, Math.max(2, r * .55), 0, 7); g.fill();
  if (k === 'guerrero') { g.strokeStyle = '#6e5032'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 3 * s, y + 6 * s); g.lineTo(x + 9 * s, y - 12 * s); g.stroke(); g.fillStyle = '#c8c8cd'; g.beginPath(); g.moveTo(x + 9 * s, y - 12 * s); g.lineTo(x + 11 * s, y - 16 * s); g.lineTo(x + 7 * s, y - 15 * s); g.fill(); g.strokeStyle = '#e6dcc8'; g.beginPath(); g.moveTo(x, y - r); g.lineTo(x - 1, y - r - 5 * s); g.stroke(); }
  else if (k === 'fuego') { g.strokeStyle = '#6e5032'; g.lineWidth = 2; g.beginPath(); g.arc(x + 2 * s, y, 10 * s, -1.2, 1.2); g.stroke(); g.fillStyle = '#ff8c28'; g.beginPath(); g.arc(x + 8 * s, y, Math.max(2, 3 * s), 0, 7); g.fill(); g.fillStyle = '#ffdc64'; g.beginPath(); g.arc(x + 8 * s, y, Math.max(1, 1.5 * s), 0, 7); g.fill(); }
  else if (k === 'bandido') { g.fillStyle = '#322824'; g.beginPath(); g.ellipse(x, y - r * .8, r, r * .4, 0, 0, 7); g.fill(); g.strokeStyle = '#3c322c'; g.lineWidth = 2; g.beginPath(); g.moveTo(x - 2 * s, y + 3 * s); g.lineTo(x + 12 * s, y - 3 * s); g.stroke(); }
};
R.drawTent = function (g, x, y, s) {
  const r = 15 * s; g.fillStyle = 'rgba(0,0,0,.16)'; g.beginPath(); g.arc(x + 3, y + 4, r, 0, 7); g.fill();
  g.fillStyle = '#d6c8a8'; g.beginPath(); g.moveTo(x, y - r * .9); g.lineTo(x + r, y + r * .7); g.lineTo(x - r, y + r * .7); g.closePath(); g.fill();
  g.strokeStyle = '#96866a'; g.lineWidth = 2; g.stroke(); g.beginPath(); g.moveTo(x, y - r * .9); g.lineTo(x, y + r * .7); g.stroke();
  g.fillStyle = '#463828'; g.beginPath(); g.moveTo(x, y + r * .7); g.lineTo(x - 4 * s, y + r * .7); g.lineTo(x, y - s); g.fill();
};
R.drawOx = function (g, x, y, s, a) {
  const c = Math.cos(a), sn = Math.sin(a);
  g.fillStyle = '#604630'; g.beginPath(); g.ellipse(x, y, 11 * s, 6 * s, 0, 0, 7); g.fill();
  g.fillStyle = '#503a28'; g.beginPath(); g.arc(x + c * 11 * s, y + sn * 11 * s, 5 * s, 0, 7); g.fill();
  g.strokeStyle = '#ebe6d7'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + c * 13 * s, y + sn * 13 * s - 3); g.lineTo(x + c * 17 * s, y + sn * 17 * s - 6); g.stroke();
};
R.drawFire = function (g, x, y, t, s) {
  const fl = 1 + .15 * Math.sin(t * 13) + .1 * Math.sin(t * 7.3);
  g.strokeStyle = '#422c1c'; g.lineWidth = Math.max(1, 3 * s);
  for (let i = 0; i < 7; i++) { const a = i * Math.PI * 2 / 7; g.beginPath(); g.moveTo(x + Math.cos(a) * 3 * s, y + Math.sin(a) * 3 * s); g.lineTo(x + Math.cos(a) * 11 * s, y + Math.sin(a) * 11 * s); g.stroke(); }
  for (const [r, c] of [[9, '#e65a1e'], [6.5, '#fa a028'.replace(' ', '')], [3.8, '#ffe678']]) { g.fillStyle = c; g.beginPath(); g.arc(x, y, Math.max(1, r * s * fl), 0, 7); g.fill(); }
};

// ------------------------------------------------------------ retratos (cutscenes)
const STY = {
  esposa: ['#60402a', 'bun', 'bonnet', null, '#607896'], hijo: ['#78502e', 'messy', 'cap', null, '#965a3c'], hija: ['#8c6036', 'braids', 'ribbon', null, '#be7882'],
  abuelo: ['#e2e2e2', 'white', 'hat', 'full', '#606068'], tomas: ['#28201c', 'short', 'hat', 'full', '#6e503c'], ruth: ['#785a3c', 'bun', 'bonnet', null, '#46465a'],
  ada: ['#c8a05a', 'braids', 'ribbon', null, '#aabe8c'], silas: ['#46382c', 'short', 'hat', 'stubble', '#505a46'], mary: ['#5a3c28', 'braids', 'hat', null, '#786e46'],
  josiah: ['#463224', 'short', 'none', 'stubble', '#82644a'], hannah: ['#6e4c32', 'bun', 'none', null, '#788c78'], lucas: ['#966e3c', 'messy', 'none', null, '#8c8ca0'],
  emma: ['#aa7846', 'braids', 'none', null, '#a07896'], medico: ['#3c322c', 'short', 'none', 'stubble', '#3c404c'], cazadora: ['#503828', 'braids', 'hat', null, '#6e603c'],
  herrero: ['#3c281e', 'bald', 'none', 'full', '#58463c'], predicador: ['#bebebe', 'white', 'none', null, '#1e1e24'], mercenario: ['#282422', 'short', 'hat', 'stubble', '#3c3232'],
  traductora: ['#32241e', 'braids', 'none', null, '#965a46'], gemelos: ['#6e4c2c', 'messy', 'cap', null, '#826e64'], partera: ['#463228', 'bun', 'bonnet', null, '#6e505a'],
  carretero: ['#64462a', 'short', 'hat', 'stubble', '#786446'], viuda: ['#3c322c', 'bun', 'bonnet', null, '#282830'],
};
const STYLES = ['short', 'bun', 'messy', 'braids'], HATS = ['hat', 'none', 'cap', 'bonnet'];
function styleFor(role, cid, group) {
  const b = role.split('_')[0]; if (STY[b]) return STY[b];
  const hair = ['#3c2c22', '#785432', '#aa824c', '#28221e'][cid % 4];
  return [hair, STYLES[cid % 4], HATS[cid % 4], (cid % 3 === 0 && group === 'adulto') ? 'stubble' : null, SHIRTS[cid % SHIRTS.length]];
}
const dark = (hex, k) => { const n = parseInt(hex.slice(1), 16); const f = x => Math.max(0, x - k); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; };
R.drawPortrait = function (g, cx, baseY, height, role, group, cid, mood, speaking, t, dim, back) {
  let sc = height / 360; if (group === 'niño') sc *= .74; else if (group === 'anciano') sc *= .94;
  const W = Math.ceil(380 * sc), H = Math.ceil(400 * sc), pic = mk(W, H), p = pic.getContext('2d'), mx = W / 2, by = H - 2, k = sc;
  const [hair, hstyle, hat, beard, shirt] = styleFor(role, cid, group);
  const skin = SKINS[(cid + role.length) % SKINS.length];
  const E = (x, y, w, h, fill, stroke, lw) => { p.beginPath(); p.ellipse(mx + x * k, by + y * k, Math.abs(w * k / 2), Math.abs(h * k / 2), 0, 0, 7); if (fill) { p.fillStyle = fill; p.fill(); } if (stroke) { p.lineWidth = (lw || 2) * k; p.strokeStyle = stroke; p.stroke(); } };
  const Rc = (x, y, w, h, fill, rad) => { p.beginPath(); p.roundRect(mx + x * k, by + y * k, w * k, h * k, (rad || 0) * k); p.fillStyle = fill; p.fill(); };
  const L = (x1, y1, x2, y2, col, w) => { p.strokeStyle = col; p.lineWidth = Math.max(1, (w || 2) * k); p.beginPath(); p.moveTo(mx + x1 * k, by + y1 * k); p.lineTo(mx + x2 * k, by + y2 * k); p.stroke(); };
  E(0, 10, 300, 190, dark(shirt, 28)); E(0, 6, 290, 175, shirt);
  const hy = -205;
  if (back) { E(0, hy, 120, 130, '#322824'); E(0, hy - 52, 150, 38, '#221a16'); E(0, hy - 70, 90, 60, '#281e1c'); E(0, 6, 290, 175, '#242834'); }
  else {
    Rc(-24, hy + 52, 48, 60, dark(skin, 22));
    if (hstyle === 'white' || hstyle === 'messy') E(0, hy - 4, 128, 140, hair);
    if (hstyle === 'braids') for (const sx of [-1, 1]) { L(sx * 46, hy + 20, sx * 52, hy + 100, hair, 12); E(sx * 52, hy + 104, 14, 14, '#c85a5a'); }
    if (hstyle === 'bun') E(0, hy - 66, 52, 44, hair);
    E(0, hy, 106, 126, skin); E(-52, hy + 6, 16, 28, skin); E(52, hy + 6, 16, 28, skin);
    if (['short', 'bun', 'braids'].includes(hstyle)) E(0, hy - 40, 106, 50, hair); else if (hstyle === 'messy' || hstyle === 'white') { E(-20, hy - 46, 54, 36, hair); E(24, hy - 44, 50, 34, hair); }
    if (beard === 'full') { E(0, hy + 55, 92, 82, hair); E(0, hy + 20, 70, 36, skin); }
    else if (beard === 'stubble') { p.save(); p.beginPath(); p.rect(0, by + (hy + 14) * k, W, 80 * k); p.clip(); E(0, hy, 106, 126, 'rgba(70,56,48,.55)'); p.restore(); }
    if (hat === 'hat') { E(0, hy - 50, 170, 28, '#42301f'); E(0, hy - 72, 90, 56, '#503a28'); Rc(-45, hy - 66, 90, 10, '#281c14'); }
    else if (hat === 'cap') { E(0, hy - 52, 112, 56, '#5a6478'); E(30, hy - 38, 60, 14, '#465060'); }
    else if (hat === 'bonnet') { E(0, hy - 22, 130, 118, '#ece4d0'); E(0, hy + 2, 100, 112, skin); E(0, hy - 40, 104, 44, hstyle === 'white' ? '#e6e6e6' : hair); }
    else if (hat === 'ribbon') E(0, hy - 62, 22, 18, '#c85a64');
    const blink = (Math.floor(t * 1.7 + cid) % 5 === 0) && (t * 1.7 % 1 < .12), ey = hy - 4;
    for (const sx of [-1, 1]) {
      if (blink) L(sx * 24 - 9, ey, sx * 24 + 9, ey, '#281c18', 3);
      else { E(sx * 24, ey, 20, 14, '#faf8f0'); E(sx * 24 + (mood !== 'miedo' ? 3 : 0), ey + (mood === 'triste' ? 1 : 0), 9, 9, '#32261e'); }
      const b0 = ey - 18, ex = sx * 24; let p1, p2;
      if (mood === 'enojado') [p1, p2] = sx < 0 ? [[ex - 12, b0 - 3], [ex + 12, b0 + 5]] : [[ex - 12, b0 + 5], [ex + 12, b0 - 3]];
      else if (mood === 'triste') [p1, p2] = sx < 0 ? [[ex - 12, b0 + 4], [ex + 12, b0 - 4]] : [[ex - 12, b0 - 4], [ex + 12, b0 + 4]];
      else if (mood === 'miedo') [p1, p2] = [[ex - 12, b0 - 6], [ex + 12, b0 - 6]];
      else if (mood === 'alegre' || mood === 'risa') [p1, p2] = sx > 0 ? [[ex - 12, b0 + 1], [ex + 12, b0 - 3]] : [[ex - 12, b0 - 3], [ex + 12, b0 + 1]];
      else [p1, p2] = [[ex - 12, b0], [ex + 12, b0]];
      L(p1[0], p1[1], p2[0], p2[1], '#32221a', mood === 'enojado' ? 4 : 3);
    }
    L(-2, ey + 6, 4, ey + 30, dark(skin, 40), 3);
    const my = hy + 40, opening = speaking && (Math.floor(t * 9) % 3 !== 0);
    if (mood === 'alegre' || mood === 'risa') { p.strokeStyle = '#6e322c'; p.lineWidth = 3 * k; p.beginPath(); p.arc(mx, by + (my - 2) * k, 18 * k, .15 * Math.PI, .85 * Math.PI); p.stroke(); if (mood === 'risa' || opening) E(0, my + 8, 22, 12, '#5a1e1e'); }
    else if (mood === 'triste') { p.strokeStyle = '#6e322c'; p.lineWidth = 3 * k; p.beginPath(); p.arc(mx, by + (my + 14) * k, 14 * k, 1.15 * Math.PI, 1.85 * Math.PI); p.stroke(); }
    else if (mood === 'miedo') E(0, my + 4, 18, 22, '#5a1e1e');
    else if (mood === 'enojado') L(-16, my + 2, 16, my - 2, '#6e322c', 4);
    else if (opening) E(0, my + 2, 22, 12, '#5a1e1e'); else L(-14, my + 2, 14, my + 2, '#6e322c', 3);
    const b = role.split('_')[0];
    if (b === 'silas' || b === 'mercenario') L(24, hy - 20, 38, hy + 18, '#aa5a50', 3);
    if (b === 'medico') { for (const sx of [-1, 1]) E(sx * 24, ey, 30, 24, null, '#3c3228', 3); L(-9, ey, 9, ey, '#3c3228', 2); }
    if (b === 'predicador') Rc(-18, hy + 62, 36, 14, '#f0f0f0', 3);
  }
  if (dim) { p.globalCompositeOperation = 'multiply'; p.fillStyle = '#78788c'; p.fillRect(0, 0, W, H); p.globalCompositeOperation = 'destination-in'; p.drawImage(pic, 0, 0); }
  const bob = Math.sin(t * 2.2 + cid) * 2 * k + (speaking && !dim ? 3 * k * (.5 + .5 * Math.sin(t * 8)) : 0);
  g.drawImage(pic, cx - W / 2, baseY - H + bob);
};

// ------------------------------------------------------------ fondos de cutscene
const BW = 1400, SH = 720;
function grad(g, top, bot) { const gr = g.createLinearGradient(0, 0, 0, SH); gr.addColorStop(0, top); gr.addColorStop(1, bot); g.fillStyle = gr; g.fillRect(0, 0, BW, SH); }
function hills(g, base, amp, freq, col, seed) { g.fillStyle = col; g.beginPath(); g.moveTo(0, SH); for (let x = 0; x <= BW + 8; x += 8) g.lineTo(x, base + Math.sin(x * freq + seed) * amp + Math.sin(x * freq * 2.3 + seed * 2) * amp * .4); g.lineTo(BW, SH); g.closePath(); g.fill(); }
function pine(g, x, y, h, col) { const w = h * .45; g.fillStyle = col || '#1a3828'; for (let i = 0; i < 4; i++) { const yy = y - h + i * h * .22, ww = w * (.35 + i * .22); g.beginPath(); g.moveTo(x, yy); g.lineTo(x - ww, yy + h * .32); g.lineTo(x + ww, yy + h * .32); g.fill(); } g.fillStyle = '#32241a'; g.fillRect(x - 3, y - 4, 6, 10); }
function wagonSil(g, x, y, sc, col) {
  g.fillStyle = col || '#181414'; g.beginPath(); g.roundRect(x - 40 * sc, y - 30 * sc, 80 * sc, 22 * sc, 3); g.fill();
  g.beginPath(); g.moveTo(x - 38 * sc, y - 30 * sc); for (let a = 0; a <= 180; a += 15) { const r = a * Math.PI / 180; g.lineTo(x - Math.cos(r) * 38 * sc, y - 30 * sc - Math.sin(r) * 30 * sc); } g.fill();
  g.beginPath(); g.arc(x - 20 * sc, y - 6 * sc, 13 * sc, 0, 7); g.arc(x + 20 * sc, y - 6 * sc, 11 * sc, 0, 7); g.fill();
}
function buildBackdrop(key) {
  const c = mk(BW, SH), g = c.getContext('2d'), rng = new CV.RNG(hash(key));
  const rect = (x, y, w, h, col) => { g.fillStyle = col; g.fillRect(x, y, w, h); };
  const poly = (pts, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (const q of pts.slice(1)) g.lineTo(q[0], q[1]); g.closePath(); g.fill(); };
  if (key === 'alba') {
    grad(g, '#262254', '#faaa68'); g.fillStyle = '#ffe296'; g.beginPath(); g.arc(780, 430, 70, 0, 7); g.fill(); hills(g, 470, 14, .004, '#563c50', 1);
    for (let i = 0; i < 14; i++) { const x = 120 + i * 46, h = rng.int(34, 80); rect(x, 520 - h, 36, h, '#322230'); poly([[x - 4, 520 - h], [x + 18, 520 - h - 20], [x + 40, 520 - h]], '#3c2832'); }
    rect(330, 360, 24, 160, '#2e1e2a'); poly([[324, 360], [342, 320], [360, 360]], '#2e1e2a'); hills(g, 540, 8, .006, '#2c3634', 3); rect(0, 560, BW, 160, '#222c2a'); rect(0, 640, BW, 40, '#604a38');
    for (let i = 0; i < 7; i++) wagonSil(g, 700 + i * 90, 650, 1);
  } else if (key === 'noche') {
    grad(g, '#06081a', '#161a38');
    for (let i = 0; i < 260; i++) { const b = rng.int(150, 255); g.fillStyle = `rgb(${b},${b},${b})`; g.fillRect(rng.int(0, BW), rng.int(0, 380), 1.5, 1.5); }
    g.fillStyle = '#e6e8d7'; g.beginPath(); g.arc(1040, 140, 32, 0, 7); g.fill(); g.fillStyle = '#0a0c1e'; g.beginPath(); g.arc(1054, 130, 28, 0, 7); g.fill();
    hills(g, 470, 22, .005, '#0e141c', 2); rect(0, 520, BW, 200, '#0e1616');
    [140, 330, 560, 880, 1110, 1290].forEach((x, i) => wagonSil(g, x, 560 + (i % 2) * 14, i % 2 ? 1.3 : 1.1, '#0a0c0e'));
    for (const x of [460, 1000]) poly([[x, 470], [x - 54, 560], [x + 54, 560]], '#0c0e12');
  } else if (key === 'dia') {
    grad(g, '#6096dc', '#b8cce0'); for (let i = 0; i < 6; i++) { const x = rng.int(0, BW), y = rng.int(40, 200); g.fillStyle = '#f6f8fc'; for (let j = 0; j < 4; j++) { g.beginPath(); g.ellipse(x + j * 34 + 50, y + (j % 2) * 8 + 18, 50, 18, 0, 0, 7); g.fill(); } }
    hills(g, 430, 26, .004, '#5c8264', 5); hills(g, 480, 18, .007, '#6e965c', 9); rect(0, 520, BW, 200, '#6e9654'); rect(0, 620, BW, 36, '#a0805a');
  } else if (key === 'rio') {
    grad(g, '#6ea0e0', '#d0e0ec'); hills(g, 410, 20, .004, '#608060', 4); rect(0, 440, BW, 280, '#608c5a');
    poly([[0, 520], [BW, 500], [BW, 600], [0, 640]], '#4278ba');
    for (let i = 0; i < 60; i++) { const x = rng.int(0, BW), y = rng.int(530, 620); g.strokeStyle = '#b4d6f4'; g.beginPath(); g.moveTo(x, y); g.lineTo(x + rng.int(14, 40), y); g.stroke(); }
    for (const x of [90, 1210, 1330]) { g.strokeStyle = '#463224'; g.lineWidth = 8; g.beginPath(); g.moveTo(x, 520); g.lineTo(x + 6, 380); g.stroke(); g.strokeStyle = '#3c6e3c'; g.lineWidth = 3; for (let k = 0; k < 7; k++) { g.beginPath(); g.moveTo(x + 6, 390); g.lineTo(x + 6 + rng.int(-110, 110), 500); g.stroke(); } }
  } else if (key === 'roca') {
    grad(g, '#d89a64', '#fad6a0'); hills(g, 470, 14, .004, '#967e5a', 3); rect(0, 520, BW, 200, '#9c865c');
    poly([[780, 540], [840, 160], [860, 150], [890, 300], [960, 540]], '#aa8c68'); poly([[840, 160], [860, 150], [890, 300], [846, 300]], '#82684c');
  } else if (key === 'montana') {
    grad(g, '#5478b8', '#d8e2f0'); poly([[0, 520], [260, 220], [460, 400], [700, 170], [980, 420], [1220, 240], [BW, 520]], '#7e8498');
    for (const [px, py] of [[260, 220], [700, 170], [1220, 240]]) poly([[px, py], [px - 60, py + 90], [px + 60, py + 90]], '#f4f6fc');
    rect(0, 520, BW, 200, '#3c5046'); for (let i = 0; i < 30; i++) pine(g, rng.int(0, BW), rng.int(560, 700), rng.int(70, 140));
  } else if (key === 'bosque') {
    grad(g, '#182c28', '#0e1e1c'); for (let i = 0; i < 60; i++) pine(g, rng.int(0, BW), rng.int(500, 700), rng.int(180, 340), `rgb(${14 + rng.int(0, 14)},${40 + rng.int(0, 20)},${34 + rng.int(0, 14)})`); rect(0, 640, BW, 80, '#1e2c1e');
  } else if (key === 'tienda') {
    grad(g, '#3e2c1e', '#241812'); g.strokeStyle = '#32241a'; g.lineWidth = 3; for (let i = 0; i < BW; i += 70) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i - 90, SH); g.stroke(); }
    rect(0, 560, BW, 160, '#5c4632'); g.fillStyle = '#beaa82'; g.beginPath(); g.roundRect(180, 520, 480, 90, 22); g.fill(); g.strokeStyle = '#786450'; g.lineWidth = 4; g.stroke(); g.fillStyle = '#502828'; g.beginPath(); g.roundRect(200, 510, 440, 40, 18); g.fill();
  } else if (key === 'fuerte') {
    grad(g, '#6ea0e0', '#d8e2ec'); hills(g, 420, 16, .004, '#608260', 6); rect(0, 500, BW, 220, '#6e925a'); rect(320, 280, 700, 240, '#705030');
    for (let i = 0; i < 700; i += 28) { g.strokeStyle = '#543a22'; g.lineWidth = 2; g.beginPath(); g.moveTo(320 + i, 280); g.lineTo(320 + i, 520); g.stroke(); poly([[318 + i, 280], [334 + i, 252], [350 + i, 280]], '#705030'); }
    g.fillStyle = '#241a14'; g.beginPath(); g.roundRect(630, 380, 80, 140, 40); g.fill(); g.strokeStyle = '#3c2818'; g.lineWidth = 5; g.beginPath(); g.moveTo(940, 280); g.lineTo(940, 140); g.stroke(); poly([[940, 140], [1000, 156], [940, 174]], '#c83c32');
  } else if (key === 'bifurcacion') {
    grad(g, '#82aae0', '#ece8d2'); hills(g, 430, 20, .004, '#608264', 7); hills(g, 470, 14, .008, '#466e50', 2); rect(0, 520, BW, 200, '#608c5a'); poly([[900, 470], [BW, 440], [BW, 520], [1040, 540]], '#4278ba');
    g.strokeStyle = '#5a3e24'; g.lineWidth = 10; g.beginPath(); g.moveTo(560, 640); g.lineTo(560, 330); g.stroke();
    [['Willamette', 0, 1], ['Walla Walla', 56, -1], ['Columbia', 112, 1]].forEach(([lbl, dy, dx]) => { poly([[560, 340 + dy], [560 + dx * 150, 340 + dy], [560 + dx * 172, 360 + dy], [560 + dx * 150, 380 + dy], [560, 380 + dy]], '#966c42'); });
    rect(0, 650, BW, 40, '#a0805a');
  } else grad(g, '#1e1e28', '#0a0a10');
  return c;
}
const bdCache = {};
R.drawBackdrop = function (g, key, t, progress) {
  if (!bdCache[key]) bdCache[key] = buildBackdrop(key);
  const pan = Math.max(-(BW - 1280), Math.min(0, Math.floor(-progress * 60 - Math.sin(t * .2) * 6)));
  g.drawImage(bdCache[key], pan, 0);
  const glow = (x, y, rad, a, col) => { const gr = g.createRadialGradient(x, y, 0, x, y, rad); gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(1, `rgba(${col},0)`); g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); };
  if (key === 'noche' || key === 'tienda') { const [x, y] = key === 'noche' ? [640, 600] : [730, 330]; const fl = 1 + .07 * Math.sin(t * 13) + .05 * Math.sin(t * 7.3); glow(x, y, 380 * fl, .5, '255,150,60'); R.drawFire(g, x, y, t, 3.2); }
  if (key === 'alba') glow(780 + pan, 430, 280, .35, '255,210,130');
  if (key === 'rio') for (let i = 0; i < 14; i++) { const x = (i * 117 + t * 30) % 1280; g.strokeStyle = '#c8e2fa'; g.lineWidth = 2; g.beginPath(); g.moveTo(x, 540 + (i % 5) * 18); g.lineTo(x + 26, 540 + (i % 5) * 18); g.stroke(); }
  if (key === 'montana') { g.fillStyle = `rgba(220,230,250,${.08 + .05 * Math.sin(t)})`; g.fillRect(0, 0, 1280, 720); }
};

// ------------------------------------------------------------ partículas
class Particles {
  constructor() { this.items = []; }
  add(kind, x, y, n, col) {
    n = n || 1;
    for (let i = 0; i < n; i++) {
      const r = Math.random;
      if (kind === 'smoke') this.items.push({kind, x, y, vx: (r() - .5) * 16, vy: -4 - r() * 10, t: 0, life: .8 + r() * .8, size: 4 + r() * 4, col: '210,210,210'});
      else if (kind === 'spark') { const a = r() * 6.28, v = 40 + r() * 80; this.items.push({kind, x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, life: .2 + r() * .3, size: 2, col: col || '255,220,120'}); }
      else if (kind === 'dust') this.items.push({kind, x, y, vx: (r() - .5) * 36, vy: (r() - .5) * 36, t: 0, life: .5 + r() * .6, size: 4 + r() * 5, col: '190,170,130'});
      else if (kind === 'fire') this.items.push({kind, x: x + (r() - .5) * 16, y: y + (r() - .5) * 12, vx: (r() - .5) * 12, vy: -18 - r() * 22, t: 0, life: .4 + r() * .5, size: 3 + r() * 3, col: '255,150,40'});
      else if (kind === 'ember') this.items.push({kind, x, y, vx: (r() - .5) * 40, vy: -20 - r() * 40, t: 0, life: .6 + r() * .8, size: 2, col: '255,190,90'});
      else if (kind === 'ring') this.items.push({kind, x, y, vx: 0, vy: 0, t: 0, life: .5, size: 6, col: col || '255,255,255'});
    }
  }
  update(dt) {
    for (const p of this.items) { p.t += dt; p.x += p.vx * dt; p.y += p.vy * dt; if (p.kind === 'smoke' || p.kind === 'dust') p.size += dt * 8; if (p.kind === 'ring') p.size += dt * 120; }
    this.items = this.items.filter(p => p.t < p.life).slice(-700);
  }
  draw(g, cam) {
    for (const p of this.items) {
      const k = 1 - p.t / p.life, sx = cam.x(p.x), sy = cam.y(p.y);
      if (p.kind === 'ring') { g.strokeStyle = `rgba(${p.col},${.85 * k})`; g.lineWidth = 2; g.beginPath(); g.arc(sx, sy, p.size * cam.s, 0, 7); g.stroke(); }
      else { g.fillStyle = `rgba(${p.col},${(p.kind === 'smoke' ? .47 : p.kind === 'dust' ? .33 : 1) * k})`; g.beginPath(); g.arc(sx, sy, Math.max(1, p.size * cam.s * ((p.kind === 'smoke' || p.kind === 'dust') ? 1 : .5 + k)), 0, 7); g.fill(); }
    }
  }
}
R.Particles = Particles;
})(globalThis.CV = globalThis.CV || {});
