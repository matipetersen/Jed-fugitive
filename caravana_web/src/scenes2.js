/* Escenas del viaje: avisos, diario, cutscenes, viaje, campamento, diplomacia y plan de defensa. */
(function (CV) {
'use strict';
const UI = CV.ui, C = UI.C, D = CV.data, R = CV.render, W = UI.W, H = UI.H;
const Scene = UI.Scene, Button = UI.Button, T = (...a) => UI.text(...a);
const S2 = CV.scenes2 = {};
const inBox = (ev, x, y, w, h) => ev.x >= x && ev.x <= x + w && ev.y >= y && ev.y <= y + h;
const hpCol = f => f > .5 ? C.green : f > .25 ? C.orange : C.red;
const dateOf = day => { const d = new Date(D.START.getTime() + day * 86400000); return `${d.getDate()} ${D.MONTHS[d.getMonth()].slice(0, 3)}`; };

// ============================================================== aviso con opciones
class PromptScene extends Scene {
  constructor(app, prompt) {
    super(app); this.overlay = true; this.p = prompt; this.layout();
  }
  layout() {
    const p = this.p, bodyH = UI.paraHeight(p.body, 19, 640);
    const h = 78 + bodyH + 20 + p.options.reduce((s, o) => s + (o.who && o.who.length ? 70 : 54), 0) + 20;
    this.rect = {x: (W - 700) / 2, y: Math.max(8, (H - h) / 2 - 10), w: 700, h};
    let y = this.rect.y + 78 + bodyH + 20; this.btns = [];
    p.options.forEach((o, i) => {
      const hh = o.who && o.who.length ? 62 : 46;
      this.btns.push(new Button(this.rect.x + 30, y, 640, hh, o.label + (o.hint ? `   ·   ${o.hint}` : ''), () => this.choose(o), {size: 18, key: i < 9 ? 'Digit' + (i + 1) : null}));
      y += hh + 8;
    });
  }
  choose(o) {
    const res = o.action();
    this.app.pop();
    if (res) this.app.handleInterrupt(res);
  }
  handle(ev) {
    if (UI.handleButtons(this.btns, ev)) return;
    if (ev.type === 'key' && (ev.key === 'Enter' || ev.key === 'Space') && this.p.options.length === 1) this.choose(this.p.options[0]);
  }
  draw() {
    const r = this.rect, p = this.p, col = {info: C.gold, good: C.green, danger: C.red}[p.tone] || C.gold;
    UI.veil(.65); UI.panel(r.x, r.y, r.w, r.h, C.panel, col, 12, undefined, 3);
    T(p.title, r.x + r.w / 2, r.y + 20, {size: 32, color: col, bold: true, serif: true, shadow: true, align: 'center'});
    UI.para(p.body, r.x + 30, r.y + 76, 640, 19, C.text);
    this.btns.forEach((b, i) => { b.draw(); const o = p.options[i]; if (o.who && o.who.length) T('Lo defienden: ' + o.who.join(', '), b.x + 14, b.y + b.h - 17, {size: 12, color: '#e6c882'}); });
  }
}
S2.PromptScene = PromptScene;

// ============================================================== diario y compañía
class JournalScene extends Scene {
  constructor(app) {
    super(app); this.overlay = true; this.g = app.game; this.scroll = 0; this.tab = 0;
    this.btns = [new Button(W / 2 - 80, H - 66, 160, 44, 'Cerrar', () => app.pop(), {size: 19, color: '#624a28', key: 'Escape'}),
      new Button(W / 2 - 300, H - 66, 90, 44, '▲', () => this.scroll -= 150, {size: 22}), new Button(W / 2 + 210, H - 66, 90, 44, '▼', () => this.scroll += 150, {size: 22}),
      new Button(70, 24, 180, 40, 'Diario', () => { this.tab = 0; this.scroll = 0; }, {size: 18}), new Button(260, 24, 180, 40, 'La compañía', () => { this.tab = 1; this.scroll = 0; }, {size: 18})];
  }
  lines() {
    const g = this.g;
    if (this.tab === 0) return g.journal.slice().reverse().map(([d, t]) => [`${dateOf(d)}  ·  ${t}`, C.text]);
    return g.colonists.map(c => [`${c.alive ? '' : '† '}${c.name} — ${g.roleLabel(c)}${c.alive ? `  · salud ${Math.round(c.health)}${c.sick ? ' · ' + c.sick : ''}${D.FAMILY_ROLES.includes(c.roleId) && !c.isLeader ? ' · lealtad ' + c.loyalty : ''}` : '  · ' + c.cause}`, c.alive ? (c.sick ? C.orange : C.text) : C.dim]);
  }
  handle(ev) {
    if (UI.handleButtons(this.btns, ev)) return;
    if (ev.type === 'wheel') this.scroll += ev.dy;
    if (ev.type === 'down') { this.drag = ev.y; }
    if (ev.type === 'move' && ev.down && this.drag !== undefined) { this.scroll -= ev.y - this.drag; this.drag = ev.y; }
    if (ev.type === 'up') this.drag = undefined;
  }
  draw() {
    UI.veil(.7); UI.panel(50, 76, W - 100, H - 160, '#2a2016', C.edge, 10);
    this.btns[3].selected = this.tab === 0; this.btns[4].selected = this.tab === 1;
    const g = this.app.ctx, ls = this.lines(); let total = 0;
    const wrapped = ls.map(([t, c]) => { const w = UI.wrap(t, 17, W - 160); total += w.length * 22 + 6; return [w, c]; });
    const avail = H - 190; this.scroll = Math.max(0, Math.min(this.scroll, Math.max(0, total - avail)));
    g.save(); g.beginPath(); g.rect(60, 88, W - 120, avail + 4); g.clip();
    let y = 94 - this.scroll;
    for (const [w, c] of wrapped) { for (const ln of w) { T(ln, 80, y, {size: 17, color: c}); y += 22; } y += 6; }
    g.restore();
    for (const b of this.btns) b.draw();
  }
}
S2.JournalScene = JournalScene;

// ============================================================== menú pausa
class MenuScene extends Scene {
  constructor(app) {
    super(app); this.overlay = true;
    this.btns = [new Button(W / 2 - 170, 290, 340, 50, 'Seguir jugando', () => app.pop(), {size: 20, key: 'Escape'}),
      new Button(W / 2 - 170, 350, 340, 50, '', () => { CV.sfx.enabled = !CV.sfx.enabled; }, {size: 18}),
      new Button(W / 2 - 170, 410, 340, 50, 'Guardar y volver al título', () => { app.autosave(); app.travel = null; app.replace(new CV.scenes1.TitleScene(app)); }, {size: 20, color: '#624a28'})];
  }
  handle(ev) { UI.handleButtons(this.btns, ev); }
  draw() {
    UI.veil(.7); UI.panel(W / 2 - 220, 240, 440, 250, C.panel, C.gold, 12, undefined, 3);
    T('Pausa', W / 2, 252, {size: 34, color: C.gold, serif: true, bold: true, align: 'center'});
    this.btns[1].label = CV.sfx.enabled ? 'Sonido: activado' : 'Sonido: silenciado';
    for (const b of this.btns) b.draw();
  }
}

// ============================================================== cutscene
let vig = null;
function vignette(g) {
  if (!vig) { vig = R.mk(W, H); const v = vig.getContext('2d'), gr = v.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, W * .62); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,.6)'); v.fillStyle = gr; v.fillRect(0, 0, W, H); }
  g.drawImage(vig, 0, 0);
}
class CutsceneScene extends Scene {
  constructor(app, spec) {
    super(app); this.g = app.game; this.spec = spec; this.i = 0; this.t = 0; this.tLine = 0; this.tBg = 0; this.shake = 0; this.flash = 0; this.finished = false;
    this.skip = new Button(W - 190, 12, 170, 40, 'Saltar', () => this.finish(), {size: 17});
    this.enterBeat();
  }
  get beat() { return this.spec.beats[this.i]; }
  enterBeat() {
    this.tLine = 0; const b = this.beat;
    if (b.fx === 'shake') this.shake = 14; if (b.fx === 'flash') this.flash = 1;
    const prev = this.i > 0 ? this.spec.beats[this.i - 1].bg : null; if (prev !== b.bg) this.tBg = 0;
  }
  lineDone() { return this.tLine * 46 >= this.beat.text.length; }
  advance() {
    if (this.finished) return;
    if (!this.lineDone()) { this.tLine = 999; return; }
    if (this.i + 1 >= this.spec.beats.length) { this.finish(); return; }
    this.i++; this.enterBeat();
  }
  finish() {
    if (this.finished) return; this.finished = true; this.app.pop();
    const res = this.spec.then ? this.spec.then() : null;
    if (res) this.app.handleInterrupt(res);
  }
  handle(ev) {
    if (UI.handleButtons([this.skip], ev)) return;
    if (ev.type === 'down') this.advance();
    else if (ev.type === 'key') { if (['Space', 'Enter', 'ArrowRight'].includes(ev.key)) this.advance(); else if (ev.key === 'Escape') this.finish(); }
  }
  update(dt) { this.t += dt; this.tLine += dt; this.tBg += dt; this.shake = Math.max(0, this.shake - dt * 30); this.flash = Math.max(0, this.flash - dt * 1.6); }
  nameOf(w) { if (w === 'tu') return 'Tú'; if (!w) return ''; const c = this.g.byRole(w); return c ? c.name.split(' ')[0] : w; }
  draw() {
    const g = this.app.ctx, b = this.beat, G = this.g, BT = 62, BB = 150;
    g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    g.save(); g.translate(Math.sin(this.t * 60) * this.shake, Math.cos(this.t * 47) * this.shake * .6);
    R.drawBackdrop(g, b.bg, this.t, this.i / Math.max(1, this.spec.beats.length - 1));
    const n = b.cast.length, baseY = H - BB + 40; let xs = [];
    if (n) { const span = n > 1 ? 800 : 0, x0 = W / 2 - span / 2 + (n < 3 ? 60 : 0); xs = b.cast.map((_, k) => x0 + (n > 1 ? span * k / (n - 1) : 0)); }
    b.cast.forEach((role, k) => {
      const c = G.byRole(role); if (!c) return;
      R.drawPortrait(g, xs[k], baseY, 470, role, c.group, c.cid, role === b.speaker ? b.mood : 'neutral', role === b.speaker && !this.lineDone(), this.t, !!b.speaker && role !== b.speaker, false);
    });
    if (b.speaker === 'tu') R.drawPortrait(g, 170, baseY + 30, 430, 'lider', 'adulto', 0, 'neutral', false, this.t, false, true);
    vignette(g);
    if (this.tBg < .5) { g.fillStyle = `rgba(0,0,0,${1 - this.tBg / .5})`; g.fillRect(0, 0, W, H); }
    g.restore();
    if (this.flash > 0) { g.fillStyle = `rgba(255,255,255,${.86 * this.flash})`; g.fillRect(0, 0, W, H); }
    g.fillStyle = '#000'; g.fillRect(0, 0, W, BT); g.fillRect(0, H - BB, W, BB);
    T(this.spec.title, 28, 16, {size: 28, color: C.gold, serif: true, bold: true}); this.skip.draw();
    const bx = 46, by = H - BB + 12, bw = W - 92, bh = BB - 26;
    UI.panel(bx, by, bw, bh, '#1c140e', C.gold, 10, .92);
    const name = this.nameOf(b.speaker);
    if (name) { const tw = UI.measure(name, 22, true) + 30; UI.panel(bx + 18, by - 16, tw, 32, '#5c4024', C.gold, 8); T(name, bx + 18 + tw / 2, by, {size: 22, color: C.gold, bold: true, align: 'center', base: 'middle'}); }
    const shown = b.text.slice(0, Math.floor(this.tLine * 46)), col = b.speaker === '' ? '#d6caaa' : C.text;
    let yy = by + 22; for (const ln of UI.wrap(shown || ' ', 23, bw - 90)) { T(ln, bx + 22, yy, {size: 23, color: col}); yy += 30; }
    if (this.lineDone()) { const p = .5 + .5 * Math.sin(this.t * 6); g.fillStyle = `rgb(${Math.floor(220 * p + 30)},${Math.floor(180 * p + 30)},70)`; g.beginPath(); g.moveTo(bx + bw - 36, by + bh - 30); g.lineTo(bx + bw - 20, by + bh - 22); g.lineTo(bx + bw - 36, by + bh - 14); g.fill(); }
    const nb = this.spec.beats.length;
    for (let k = 0; k < nb; k++) { g.fillStyle = k <= this.i ? C.gold : '#50422e'; g.beginPath(); g.arc(W / 2 - (nb - 1) * 7 + k * 14, 40, 3, 0, 7); g.fill(); }
  }
}
S2.CutsceneScene = CutsceneScene;

// ============================================================== viaje
const DAY_TIME = .75;
function sideWagon(g, x, y, s, t, hp, ox) {
  g.save(); g.translate(x, y); g.scale(s, s);
  const bob = Math.sin(t * 9 + x) * 1.2;
  if (ox) for (let i = 0; i < 2; i++) { const oy = 12 + i * 12; g.fillStyle = i ? '#4c3828' : '#604630'; g.beginPath(); g.ellipse(120 + 16 * i, oy - 6 + bob * (i ? -1 : 1) * .5, 26, 14, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(150 + 16 * i, oy - 12, 10, 8, 0, 0, 7); g.fill(); g.strokeStyle = '#ebe6d7'; g.lineWidth = 3; g.beginPath(); g.moveTo(154 + 16 * i, oy - 18); g.lineTo(160 + 16 * i, oy - 26); g.stroke(); g.strokeStyle = '#2e2218'; for (const lx of [-12, 10]) { g.beginPath(); g.moveTo(120 + 16 * i + lx, oy + 4); g.lineTo(120 + 16 * i + lx + Math.sin(t * 6 + i) * 4, oy + 22); g.stroke(); } }
  g.fillStyle = '#6e4c2c'; g.fillRect(-60, -24 + bob, 120, 26); g.strokeStyle = '#3a281a'; g.lineWidth = 3; g.strokeRect(-60, -24 + bob, 120, 26);
  g.fillStyle = hp < .4 ? '#c8bc9c' : '#eee4c8'; g.beginPath(); g.moveTo(-56, -24 + bob); g.bezierCurveTo(-56, -84 + bob, 56, -84 + bob, 56, -24 + bob); g.closePath(); g.fill(); g.strokeStyle = '#a89868'; g.lineWidth = 2; g.stroke();
  g.strokeStyle = '#c4b890'; g.lineWidth = 1; for (let k = -40; k <= 40; k += 20) { g.beginPath(); g.moveTo(k, -24 + bob); g.quadraticCurveTo(k * 1.1, -70 + bob, k * .9, -62 + bob); g.stroke(); }
  for (const wx of [-34, 34]) { g.save(); g.translate(wx, 6); g.rotate(t * 3.2 + wx); g.fillStyle = '#2a1e16'; g.beginPath(); g.arc(0, 0, 21, 0, 7); g.fill(); g.strokeStyle = '#b08a52'; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 18, 0, 7); g.stroke(); g.lineWidth = 2; for (let k = 0; k < 6; k++) { g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(k * 1.047) * 18, Math.sin(k * 1.047) * 18); g.stroke(); } g.restore(); }
  g.restore();
}
class TravelScene extends Scene {
  constructor(app, intro) {
    super(app); app.travel = this; this.g = app.game; this.moving = false; this.speed = 1; this.acc = 0; this.scroll = 0; this.t = 0; this.feed = []; this.parts = new R.Particles(); this.rain = [];
    this.tip = ''; this.intro = !!intro; this.lastSave = this.g.day; this.build(); this.labels();
  }
  build() {
    const x0 = 832, w = 180, h = 38, gap = 6, y0 = 530, B = (x, y, ww, hh, l, f, o) => new Button(x, y, ww, hh, l, f, o);
    this.go = B(x0, y0, 2 * w + gap, 46, '', () => this.toggle(), {size: 21, color: '#624a28', key: 'Space'});
    this.btns = [this.go,
      B(x0, y0 + 52, w, h, 'Acampar (C)', () => this.camp(), {size: 15, key: 'KeyC'}), B(x0 + w + gap, y0 + 52, w, h, 'Plan de defensa (D)', () => this.defense(), {size: 15, key: 'KeyD'}),
      this.paceB = B(x0, y0 + 52 + (h + gap), w, h, '', () => this.cycle('pace', Object.keys(D.PACES)), {size: 15, key: 'KeyR'}),
      this.ratB = B(x0 + w + gap, y0 + 52 + (h + gap), w, h, '', () => this.cycle('rations', Object.keys(D.RATIONS)), {size: 15, key: 'KeyT'}),
      this.watB = B(x0, y0 + 52 + 2 * (h + gap), w, h, '', () => this.cycle('watch', Object.keys(D.WATCH_LABEL)), {size: 15, key: 'KeyG'}),
      B(x0 + w + gap, y0 + 52 + 2 * (h + gap), w - 100, h, 'Diario', () => { this.moving = false; this.app.push(new JournalScene(this.app)); }, {size: 15, key: 'KeyJ'}),
      this.speedB = B(x0 + 2 * w + gap + 8, y0, 66, 46, 'x1', () => { this.speed = {1: 2, 2: 4, 4: 1}[this.speed]; }, {size: 18}),
      B(x0 + 2 * w + gap + 8, y0 + 52, 66, h, 'Menú', () => { this.moving = false; this.app.autosave(); this.app.push(new MenuScene(this.app)); }, {size: 14, key: 'Escape'})];
    this.btns.push(B(x0 + w + gap + (w - 94), y0 + 52 + 2 * (h + gap), 94, h, 'Familia', () => this.family(), {size: 15}));
  }
  family() { this.moving = false; const g = this.g, opts = []; for (const role of ['esposa', 'hijo', 'hija', 'abuelo']) { const c = g.member(role); if (c) opts.push(CV.opt(`Hablar con ${c.name.split(' ')[0]}`, () => CV.story.familyTalk(g, role), `lealtad ${c.loyalty}`)); } opts.push(CV.opt('Ahora no', () => null)); this.app.push(new PromptScene(this.app, CV.prompt('Consejo familiar', 'Un rato tranquilo junto a la carreta. ¿Con quién hablas?', opts, 'info'))); }
  cycle(key, order) { const g = this.g; g[key] = order[(order.indexOf(g[key]) + 1) % order.length]; }
  labels() {
    const g = this.g;
    this.paceB.label = `Ritmo: ${D.PACE_LABEL[g.pace]} (R)`; this.ratB.label = `Raciones: ${D.RATION_LABEL[g.rations]} (T)`; this.watB.label = `${D.WATCH_LABEL[g.watch]} (G)`;
    this.go.label = this.moving ? 'Detener la marcha (Espacio)' : 'Continuar el viaje (Espacio)'; this.speedB.label = 'x' + this.speed;
  }
  toggle() { this.moving = !this.moving; this.acc = DAY_TIME * .6; }
  camp() { this.moving = false; this.app.push(new CampScene(this.app, null)); }
  defense() { this.moving = false; this.app.push(new DefenseScene(this.app)); }
  enter() {
    if (!this.intro) return; this.intro = false; const g = this.g;
    this.pushFeed('La caravana parte de Independence.', C.gold);
    const cs = g.flags.cutscenes !== false ? CV.story.cutscenes.prologue(g) : null;
    if (cs) this.app.push(new CutsceneScene(this.app, cs));
    else this.app.push(new PromptScene(this.app, CV.info('Independence, 15 de abril de 1848', 'La caravana parte. Por delante: 1.950 millas.')));
  }
  resume() { this.build(); this.labels(); }
  pushFeed(s, col) { this.feed.push([s, col || C.text]); this.feed = this.feed.slice(-7); }
  consumeNotices() {
    const g = this.g;
    for (const n of g.notices) this.pushFeed(n, /muer|enferm|agot|Ladrones|Desastre|perd|roto|rompe/.test(n) ? C.orange : C.parch);
    g.notices.length = 0;
  }
  handleInterrupt(it) {
    const g = this.g, app = this.app; if (!it) return;
    switch (it.kind) {
      case 'prompt': app.push(new PromptScene(app, it)); break;
      case 'cutscene': this.moving = false; app.push(new CutsceneScene(app, it)); break;
      case 'contact': this.moving = false; app.push(new DiplomacyScene(app, new CV.Contact(g, it.tribe, it.ctype, it.opening))); break;
      case 'battle': this.moving = false; app.push(new CV.scenes3.BattleScene(app, g, it, res => this.battleDone(it, res))); break;
      case 'shop': this.moving = false; app.push(new CV.scenes1.ShopScene(app, it, false)); break;
      case 'arrival': this.moving = false; app.autosave(); app.push(new CampScene(app, it.waypoint)); break;
      case 'fork':
        this.moving = false;
        if (!g.flags.fork_seen && g.flags.cutscenes !== false && !g.forcedWinter) {
          g.flags.fork_seen = true; const cs = CV.story.cutscenes.fork(g);
          if (cs) { cs.then = () => ({kind: 'fork'}); app.push(new CutsceneScene(app, cs)); return; }
        }
        app.push(new CV.scenes3.SiteScene(app)); break;
      case 'end': this.moving = false; app.replace(new CV.scenes1.EndScene(app, it.title, it.body)); break;
    }
  }
  battleDone(spec, res) {
    const g = this.g, app = this.app;
    app.pop();
    const p = g.applyBattle(spec, res);
    if (!g.living().length) { g.over = true; app.replace(new CV.scenes1.EndScene(app, 'La caravana ha caído', 'El último defensor cae al pie de las carretas. El viento levanta ceniza sobre el camino a Oregón.')); return; }
    app.autosave(); app.push(new PromptScene(app, p));
  }
  handle(ev) {
    if (ev.type === 'move') { this.tip = ''; for (const [b, t] of [[this.paceB, 'Ritmo: lento ahorra a los bueyes y a la gente; rápido cansa y enferma.'], [this.ratB, 'Raciones: escasas ahorran comida pero debilitan; abundantes alimentan y suben la moral.'], [this.watB, 'Guardia: más vigilancia da más avisos antes de un ataque, a cambio de cansancio.']]) if (b.hit(ev.x, ev.y)) this.tip = t; this.tipPos = [ev.x, ev.y]; }
    if (UI.handleButtons(this.btns, ev)) return;
    if (ev.type === 'key' && ev.key === 'F3') UI.debugDirector = !UI.debugDirector;
  }
  update(dt) {
    this.t += dt; const g = this.g; this.labels();
    if (this.moving && !g.over) {
      this.scroll += dt * 90 * this.speed * (g.pace === 'lento' ? .6 : g.pace === 'rapido' ? 1.35 : 1);
      this.acc += dt * this.speed; let guard = 0;
      while (this.acc >= DAY_TIME && this.moving && guard < 8) {
        guard++; this.acc -= DAY_TIME;
        const it = g.advanceDay(); this.consumeNotices();
        if (g.day - this.lastSave >= 8) { this.lastSave = g.day; this.app.autosave(); }
        if (it) { this.handleInterrupt(it); break; }
      }
      if (Math.random() < .7) this.parts.add('dust', 140 + Math.random() * 900, 484 + Math.random() * 10, 1);
    }
    this.parts.update(dt);
    if (['lluvia', 'tormenta', 'nieve'].includes(g.weather) && this.rain.length < 160) for (let i = 0; i < 6; i++) this.rain.push([Math.random() * W, 250 + Math.random() * 50, .7 + Math.random() * .6]);
    const spd = {lluvia: 520, tormenta: 700, nieve: 90}[g.weather] || 0;
    for (const r of this.rain) { r[1] += spd * dt * r[2]; r[0] += (g.weather !== 'nieve' ? -60 : Math.sin(this.t * 2 + r[0]) * 20) * dt; }
    this.rain = this.rain.filter(r => r[1] < 520 && spd > 0);
  }
  draw() {
    const g = this.app.ctx, G = this.g;
    g.fillStyle = C.bg; g.fillRect(0, 0, W, H);
    this.drawHeader(g, G); this.drawMap(g, G); this.drawLand(g, G); this.drawBottom(g, G);
    if (this.tip) UI.tooltip(this.tip, this.tipPos[0], this.tipPos[1]);
    if (UI.debugDirector) S2.drawDirector(G);
  }
  drawHeader(g, G) {
    UI.panel(0, 0, W, 56, '#2a2016', C.edge, 0, undefined, 1);
    T(G.dateText(), 20, 8, {size: 22, color: C.gold, bold: true, serif: true});
    const tid = G.currentTribe(), tn = tid ? D.TRIBES[tid].name : '—';
    T(`${G.terrain().charAt(0).toUpperCase() + G.terrain().slice(1)} · territorio ${tn}`, 20, 34, {size: 14, color: C.dim});
    T(`${Math.floor(G.mile)} / ${D.TRAIL_END} millas`, W / 2, 8, {size: 22, align: 'center'});
    const nw = G.nextWaypoint(); T(nw ? `${nw.name} en ${Math.ceil(G.milesToNext())} millas` : 'Final del camino', W / 2, 34, {size: 14, color: C.parch, align: 'center'});
    const ico = {despejado: 'sun', calor: 'sun', lluvia: 'rain', tormenta: 'storm', nieve: 'snow', frío: 'snow'}[G.weather]; UI.icon(ico, W - 220, 28, 30);
    T(G.weather.charAt(0).toUpperCase() + G.weather.slice(1), W - 196, 18, {size: 18}); if (G.hasGuide()) T('Guía contigo', W - 20, 34, {size: 13, color: C.blue, align: 'right'});
  }
  drawMap(g, G) {
    UI.panel(0, 56, W, 196, '#1f1810', C.edge, 0, undefined, 1);
    const x0 = 50, x1 = W - 50, mx = m => x0 + (x1 - x0) * m / D.TRAIL_END, y = 150;
    for (const [a, b, t] of D.TERRITORIES) { g.globalAlpha = .38; g.fillStyle = D.TRIBES[t].color; g.fillRect(mx(a), y - 30, mx(Math.min(b, D.TRAIL_END)) - mx(a), 60); g.globalAlpha = 1; T(D.TRIBES[t].name, (mx(a) + mx(Math.min(b, D.TRAIL_END))) / 2, y - 52, {size: 13, color: D.TRIBES[t].color, align: 'center'}); }
    g.strokeStyle = '#8a6c42'; g.lineWidth = 4; g.setLineDash([10, 6]); g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); g.setLineDash([]);
    g.strokeStyle = C.gold; g.lineWidth = 5; g.beginPath(); g.moveTo(x0, y); g.lineTo(mx(G.mile), y); g.stroke();
    D.WAYPOINTS.forEach((w, i) => { const x = mx(w.mile), vis = G.visited.includes(w.name); g.fillStyle = vis ? C.gold : '#7a6a50'; g.beginPath(); g.arc(x, y, w.kind === 'post' ? 7 : 5, 0, 7); g.fill(); g.strokeStyle = '#1a140f'; g.lineWidth = 1; g.stroke(); T(w.name, Math.max(46, Math.min(W - 70, x)), y + (i % 2 ? 16 : 30), {size: 12, color: vis ? C.parch : C.dim, align: 'center'}); });
    const wx = mx(G.mile); g.fillStyle = '#eee4c8'; g.beginPath(); g.moveTo(wx, y - 20); g.lineTo(wx - 9, y - 34); g.lineTo(wx + 9, y - 34); g.fill(); g.strokeStyle = '#1a140f'; g.stroke();
    T(`Día ${G.day}`, W - 16, 64, {size: 14, color: C.dim, align: 'right'});
  }
  drawLand(g, G) {
    const y0 = 254, h = 262; g.save(); g.beginPath(); g.rect(0, y0, W, h); g.clip();
    const wet = ['lluvia', 'tormenta'].includes(G.weather), snow = G.weather === 'nieve' || G.weather === 'frío';
    const sk = g.createLinearGradient(0, y0, 0, y0 + 170); sk.addColorStop(0, wet ? '#5a6678' : snow ? '#9ab0c8' : '#5c94d4'); sk.addColorStop(1, wet ? '#8a96a4' : snow ? '#d4dee8' : '#c6d8e8'); g.fillStyle = sk; g.fillRect(0, y0, W, h);
    const tcol = D.TERRAIN_COLORS[G.terrain()] || '#608a44';
    const hill = (base, amp, fr, par, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(0, y0 + h); for (let x = 0; x <= W + 8; x += 8) g.lineTo(x, y0 + base + Math.sin((x + this.scroll * par) * fr) * amp + Math.sin((x + this.scroll * par) * fr * 2.3) * amp * .4); g.lineTo(W, y0 + h); g.fill(); };
    hill(120, 22, .006, .06, G.inMountains() ? '#6a7690' : '#7a9a8a'); hill(150, 16, .01, .2, tcol); g.globalAlpha = .55; g.fillStyle = '#000'; g.fillRect(0, y0 + 150, W, h); g.globalAlpha = 1;
    g.fillStyle = tcol; g.fillRect(0, y0 + 170, W, h); g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(0, y0 + 170, W, h);
    g.fillStyle = '#9a7a52'; g.fillRect(0, y0 + 214, W, 32); g.fillStyle = 'rgba(0,0,0,.14)'; for (let x = -((this.scroll * 1) % 60); x < W; x += 60) g.fillRect(x, y0 + 228, 28, 3);
    g.strokeStyle = 'rgba(30,60,20,.55)'; g.lineWidth = 2; for (let k = 0; k < 40; k++) { const x = ((k * 97 - this.scroll * 1.2) % (W + 100) + W + 100) % (W + 100) - 50, yy = y0 + 176 + (k * 37 % 30); g.beginPath(); g.moveTo(x, yy); g.lineTo(x + 3, yy - 9); g.stroke(); }
    const nW = Math.min(4, G.wagons.length);
    for (let i = nW - 1; i >= 0; i--) sideWagon(g, 330 + i * 190, y0 + 226, 1, this.moving ? this.t : 0, G.wagons[i].hp / G.wagons[i].maxHp, i === nW - 1);
    this.parts.draw(g, {x: x => x, y: y => y, s: 1});
    g.strokeStyle = wet ? 'rgba(170,200,240,.7)' : 'rgba(255,255,255,.85)'; g.lineWidth = wet ? 1.5 : 3; for (const r of this.rain) { g.beginPath(); g.moveTo(r[0], r[1] - y0 + y0); g.lineTo(r[0] + (wet ? -6 : 0.5), r[1] + (wet ? 12 : 1)); g.stroke(); }
    if (G.weather === 'tormenta' && Math.sin(this.t * 3) > .97) { g.fillStyle = 'rgba(255,255,255,.4)'; g.fillRect(0, y0, W, h); }
    g.restore();
  }
  drawBottom(g, G) {
    UI.panel(0, 516, W, 204, '#2a2016', C.edge, 0, undefined, 1);
    const s = G.sup; const vals = [['food', Math.floor(s.food) + ' lb'], ['ammo', s.ammo], ['goods', s.goods], ['parts', s.parts], ['medicine', s.medicine], ['oxen', s.oxen], ['money', '$' + Math.floor(s.money)], ['wagon', G.wagons.length]];
    vals.forEach(([ic, v], i) => { const cx = 20 + (i % 4) * 130, cy = 528 + Math.floor(i / 4) * 36; UI.icon(ic, cx + 12, cy + 12, 22); T(v, cx + 30, cy, {size: 19, color: C.gold, bold: true}); });
    UI.icon('morale', 32, 622, 22); UI.bar(52, 616, 180, 12, G.morale / 100, G.morale > 55 ? C.green : G.morale > 28 ? C.gold : C.red); T('moral', 240, 614, {size: 14, color: C.dim});
    const liv = G.living(), sick = liv.filter(c => c.sick).length, days = s.food / Math.max(.1, G.dailyNeed());
    T(`Colonos ${liv.length}${sick ? ` · enfermos ${sick}` : ''}`, 20, 648, {size: 16, color: sick ? C.orange : C.text});
    T(`Comida para ${Math.floor(days)} días`, 20, 672, {size: 16, color: days < 8 ? C.red : days < 18 ? C.gold : C.dim});
    T(`Lealtad familiar ${Math.round(G.familyLoyalty())}`, 20, 696, {size: 14, color: C.dim});
    const wf = G.wagons.reduce((a, w) => a + w.hp / w.maxHp, 0) / Math.max(1, G.wagons.length);
    T('carretas', 280, 648, {size: 14, color: C.dim}); UI.bar(350, 652, 110, 10, wf, hpCol(wf));
    T('bueyes', 280, 672, {size: 14, color: C.dim}); UI.bar(350, 676, 110, 10, G.oxenFactor(), hpCol(G.oxenFactor()));
    UI.panel(480, 524, 340, 188, '#1e1610', C.edge, 8, undefined, 1);
    let y = 530; for (const [t, col] of this.feed) { const ln = UI.wrap(t, 14, 318)[0]; T(ln, 490, y, {size: 14, color: col}); y += 25; }
    for (const b of this.btns) b.draw();
  }
}
S2.TravelScene = TravelScene;
S2.drawDirector = function (G) {
  const d = G.director, x = W - 330, y = 60; UI.panel(x, y, 320, 150, '#0e0e16', C.blue, 6, .9, 1);
  T('DIRECTOR DE IA' + (d.enabled ? '' : ' (apagado)'), x + 10, y + 6, {size: 14, color: C.blue, bold: true});
  UI.bar(x + 10, y + 28, 300, 10, d.tension, d.tension > .6 ? C.red : d.tension > .3 ? C.gold : C.green);
  T(`tensión ${d.tension.toFixed(2)} (cruda ${d.raw.toFixed(2)}) · ataques ×${d.raidMult(G).toFixed(2)} · fuerza ×${d.strengthMult(G).toFixed(2)}`, x + 10, y + 44, {size: 12});
  d.log.slice(-5).forEach(([dy, m], i) => T(`d${dy}: ${m}`.slice(0, 50), x + 10, y + 64 + i * 16, {size: 12, color: C.dim}));
};

// ============================================================== campamento
class CampScene extends Scene {
  constructor(app, wp) {
    super(app); this.g = app.game; this.wp = wp; this.chatted = false; this.t = 0; this.build();
  }
  resume() { this.build(); }
  build() {
    const g = this.g, wp = this.wp, x = 700, w = 230, y = 150, bx = [x, x + w + 10];
    this.btns = []; const add = (c, r, l, f, o) => { const b = new Button(bx[c], y + r * 56, w, 46, l, f, Object.assign({size: 17}, o)); this.btns.push(b); return b; };
    add(0, 0, 'Descansar 1 día', () => this.rest(1)); add(1, 0, 'Descansar 3 días', () => this.rest(3));
    add(0, 1, 'Salir de caza (1 día)', () => this.hunt()); add(1, 1, 'Reparar carretas', () => this.repairAll());
    add(0, 2, 'Plan de defensa', () => this.app.push(new DefenseScene(this.app)));
    const shop = wp && wp.kind === 'post'; add(1, 2, shop ? 'Comerciar' : 'Sin comercio aquí', () => this.app.push(new CV.scenes1.ShopScene(this.app, {name: wp.name, mult: wp.price || 1, cannon: !!wp.cannon}, false)), {enabled: !!shop});
    this.talkB = add(0, 3, 'Hablar con viajeros', () => this.talk(), {enabled: !!wp && !this.chatted}); add(1, 3, 'Tratar enfermos', () => this.treat());
    this.paceB = add(0, 4, '', () => this.cyc('pace', Object.keys(D.PACES))); this.ratB = add(1, 4, '', () => this.cyc('rations', Object.keys(D.RATIONS)));
    this.watB = add(0, 5, '', () => this.cyc('watch', Object.keys(D.WATCH_LABEL))); add(1, 5, 'Consejo familiar', () => this.family());
    this.btns.push(new Button(bx[0], y + 6 * 56 + 14, 2 * w + 10, 56, 'Levantar el campamento y seguir', () => this.leave(), {size: 22, color: '#624a28', key: 'Escape'}));
  }
  cyc(k, order) { const g = this.g; g[k] = order[(order.indexOf(g[k]) + 1) % order.length]; }
  afterDays(title, body, it) {
    const g = this.g;
    if (!it && g.living().length) this.app.push(new PromptScene(this.app, CV.info(title, body, 'good')));
    else this.app.push(new PromptScene(this.app, CV.info(title, body, 'info', () => it)));
  }
  rest(n) {
    const g = this.g, sb = g.living().filter(c => c.sick).length, [days, it] = g.rest(n), sa = g.living().filter(c => c.sick).length;
    let body = `Pasan ${days} día(s) de descanso. Los carros se remiendan y la gente se repone` + (sb > sa ? `; ${sb - sa} enfermo(s) mejoran` : '') + '. La comida, en cambio, no se estira sola.';
    if (g.sup.food <= 0) body += ' ¡La comida se ha acabado!';
    this.app.travel.consumeNotices(); this.afterDays('Descanso', body, it);
  }
  hunt() {
    const g = this.g, p = g.huntDay(); this.app.travel.consumeNotices();
    const it = g.living().length ? g.campEvent() : g.gameOver('El campamento queda en silencio: nadie ha sobrevivido.');
    if (it) p.options[0].action = () => it;
    this.app.push(new PromptScene(this.app, p));
  }
  repairAll() {
    const g = this.g; let done = 0;
    for (let i = 0; i < g.wagons.length; i++) while (g.wagons[i].hp < g.wagons[i].maxHp - 20 && g.sup.parts > 0) { const [ok] = g.repairWagon(i); if (!ok) break; done++; }
    this.app.push(new PromptScene(this.app, CV.info('Taller de campaña', done ? `Se hacen ${done} reparaciones.` : 'No hay nada que reparar o no quedan repuestos.', done ? 'good' : 'info')));
  }
  talk() {
    const g = this.g; this.chatted = true; this.talkB.enabled = false; const parts = [];
    for (const t of ['pawnee', 'cheyenne', 'lakota', 'shoshone', 'cayuse']) if (g.tribes[t].met || t === g.nextTribe()) { const a = g.tribes[t].attitude; parts.push(`Los ${g.tribeName(t)} andan ` + (a < -50 ? 'furiosos con los blancos.' : a < -20 ? 'hostiles.' : a < 5 ? 'recelosos.' : a < 30 ? 'tranquilos.' : 'amistosos.')); }
    let extra = ''; const r = g.rng.random();
    if (r < .33) { g.sup.goods++; extra = ' Un viajero te regala un lote de mercancías a cambio de tu compañía.'; } else if (r < .66) { g.morale = Math.min(100, g.morale + 6); extra = ' La charla anima al grupo.'; }
    this.app.push(new PromptScene(this.app, CV.info('Noticias del camino', 'Viajeros que vuelven al este y otros que van al oeste comparten noticias: ' + parts.slice(0, 4).join(' ') + extra)));
  }
  treat() {
    const g = this.g, sick = g.living().filter(c => c.sick);
    if (!sick.length) { this.app.push(new PromptScene(this.app, CV.info('Enfermería', 'Nadie necesita tratamiento ahora.'))); return; }
    let used = 0;
    for (const c of sick) if (g.sup.medicine > 0) { g.sup.medicine--; c.health = Math.min(100, c.health + 30); if (g.rng.random() < .6 + .04 * g.best('medic')) c.sick = ''; used++; }
    const left = g.living().filter(c => c.sick).length;
    this.app.push(new PromptScene(this.app, CV.info('Enfermería', used ? `Gastas ${used} medicinas. Siguen enfermos: ${left}.` : 'No quedan medicinas.', used ? 'good' : 'danger')));
  }
  family() {
    const g = this.g, opts = [];
    for (const role of ['esposa', 'hijo', 'hija', 'abuelo']) { const c = g.member(role); if (c) opts.push(CV.opt(`Hablar con ${c.name.split(' ')[0]}`, () => CV.story.familyTalk(g, role), `lealtad ${c.loyalty}`)); }
    opts.push(CV.opt('Ahora no', () => null));
    this.app.push(new PromptScene(this.app, CV.prompt('Consejo familiar', 'Es la hora tranquila de la noche. ¿Con quién te sientas?', opts, 'info')));
  }
  leave() { this.app.pop(); const t = this.app.travel; if (t) { t.moving = true; t.acc = 0; } }
  handle(ev) { UI.handleButtons(this.btns, ev); }
  update(dt) { this.t += dt; const g = this.g; this.paceB.label = `Ritmo: ${D.PACE_LABEL[g.pace]}`; this.ratB.label = `Raciones: ${D.RATION_LABEL[g.rations]}`; this.watB.label = D.WATCH_LABEL[g.watch]; this.talkB.enabled = !!this.wp && !this.chatted; }
  draw() {
    const g = this.app.ctx, G = this.g, wp = this.wp;
    g.drawImage(R.ground(W + 40, H + 40, G.terrain(), 41), -20, -20); UI.veil(0, 'rgba(16,11,7,.75)');
    T(wp ? wp.name : 'Campamento en el camino', 40, 24, {size: 42, color: C.gold, serif: true, bold: true});
    UI.para(wp ? wp.text : `${G.terrain().charAt(0).toUpperCase() + G.terrain().slice(1)}. Millas recorridas: ${Math.floor(G.mile)}.`, 42, 80, 600, 17, C.dim);
    T(G.dateText(), 42, 136, {size: 17, color: C.parch});
    UI.panel(30, 170, 640, H - 190, C.panel, C.edge, 10); T('La compañía', 48, 180, {size: 20, color: C.gold, serif: true, bold: true});
    let y = 212; const cols = G.living(), rh = Math.min(36, (H - 260) / Math.max(1, cols.length));
    for (const c of cols) {
      R.drawPerson(g, 64, y + 12, c.group, c.cid, 1.3); T(c.name, 88, y - 4, {size: 15}); T(G.roleLabel(c) + (c.sick ? ' · ' + c.sick : ''), 88, y + 12, {size: 11, color: c.sick ? C.red : C.dim});
      UI.bar(310, y + 8, 120, 9, c.health / 100, hpCol(c.health / 100)); T(`Punt. ${c.shoot} · Med. ${c.medic} · Lab. ${c.talk}`, 440, y + 4, {size: 13, color: C.dim});
      if (D.FAMILY_ROLES.includes(c.roleId) && !c.isLeader) T(`Lealtad ${c.loyalty}`, 590, y + 4, {size: 13, color: c.loyalty >= 60 ? C.green : c.loyalty >= 35 ? C.gold : C.red});
      y += rh;
    }
    UI.panel(690, 10, 550, 128, C.panel, C.edge, 10); const s = G.sup;
    [['food', Math.floor(s.food) + ' lb'], ['ammo', s.ammo], ['goods', s.goods], ['parts', s.parts], ['medicine', s.medicine], ['oxen', s.oxen], ['money', '$' + Math.floor(s.money)], ['wagon', G.wagons.length]].forEach(([ic, v], i) => { const cx = 708 + (i % 4) * 134, cy = 26 + Math.floor(i / 4) * 40; UI.icon(ic, cx + 12, cy + 10, 22); T(v, cx + 30, cy, {size: 19, color: C.gold, bold: true}); });
    UI.icon('morale', 716, 112, 18); UI.bar(736, 106, 180, 11, G.morale / 100, G.morale > 55 ? C.green : G.morale > 28 ? C.gold : C.red); T('moral', 924, 104, {size: 14, color: C.dim});
    for (const b of this.btns) b.draw();
  }
}
S2.CampScene = CampScene;

// ============================================================== diplomacia
const GIFT_UNITS = {goods: [1, 2, 4], food: [1, 2, 3], ammo: [10, 20, 40], medicine: [1, 2, 3]};
class DiplomacyScene extends Scene {
  constructor(app, contact) {
    super(app); this.c = contact; this.g = app.game; this.gift = false; this.t = 0; this.log = []; this.tip = '';
    if (contact.opening) this.log.push(['narr', contact.opening]);
    for (const h of contact.history) this.log.push(['narr', h]);
    this.shown = contact.history.length; this.build();
  }
  build() {
    const c = this.c, g = this.g, x = 880, w = 360; this.btns = [];
    if (c.ended) { this.btns.push(new Button(x, 560, w, 54, 'Terminar el encuentro', () => this.finish(), {size: 21, color: '#624a28'})); return; }
    if (this.gift) {
      let y = 150;
      for (const kind of ['goods', 'food', 'ammo', 'medicine']) { GIFT_UNITS[kind].forEach((u, j) => this.btns.push(new Button(x + 120 + j * 76, y, 70, 40, kind === 'food' ? `${u * 50} lb` : `${u}`, () => { this.doIt('regalo', [kind, u]); this.gift = false; this.build(); }, {size: 16}))); y += 56; }
      this.btns.push(new Button(x, 560, w, 46, 'Volver', () => { this.gift = false; this.build(); }, {size: 18})); return;
    }
    const defs = [['Saludar con respeto', 'saludo', 'Gratis. Quizá te cause buena impresión.'], ['Hacer un regalo…', null, 'Regalar mercancías, comida, munición o medicinas.'], ['Comerciar (trueque)', 'comerciar', 'Bueyes, medicinas, comida… no cuesta paciencia.'],
      ['Negociar paso seguro', 'paso', `Tributo ≈ ${3 + Math.floor(c.info.pride / 2)} mercancías. Tregua de unos 12+ días.`], ['Pedir información', 'info', '1 mercancía. Noticias y a veces un buen sitio de caza.'],
      ['Contratar guía e intérprete', 'guia', '8 mercancías. Requiere trato 10+. Dura ~450 millas.'], ['Proponer alianza', 'alianza', '10 mercancías. Requiere trato 55+ y un pacto previo.'], ['Mostrar fuerza', 'fuerza', 'Arriesgado: intimidar puede evitar o provocar una guerra.'], ['Despedirse', 'adios', 'Termina la reunión.']];
    if (g.flags.eli_friend && g.member('abuelo')) defs.splice(1, 0, ['Enviar a Eli como emisario', 'eli', 'Eli conoce a un hombre de esta gente… quizá sea suficiente.']);
    let y = 100; const step = defs.length <= 9 ? 52 : 47;
    for (const [l, k, h] of defs) { const b = new Button(x, y, w, 44, l, k === null ? () => { this.gift = true; this.build(); } : () => this.doIt(k), {size: 18, hint: h}); this.btns.push(b); y += step; }
  }
  doIt(key, arg) {
    const c = this.c, msg = c.do(key, arg), before = this.shown;
    if (c.history.length > before) { for (const h of c.history.slice(before)) this.log.push(['narr', h]); this.shown = c.history.length; } else this.log.push(['warn', msg]);
    if (c.shopRequested) { c.shopRequested = false; this.app.push(new CV.scenes1.ShopScene(this.app, {name: 'Trueque', mult: 1, barterTribe: c.tribe}, false)); }
    this.build();
  }
  finish() {
    const spec = this.c.finish(); this.app.pop(); const t = this.app.travel;
    if (t) { if (this.c.result === 'paz') t.pushFeed(`Paz con los ${this.c.info.name}.`, C.green); if (spec) t.handleInterrupt(spec); }
  }
  resume() { this.build(); }
  handle(ev) {
    if (ev.type === 'move') { this.tip = ''; for (const b of this.btns) if (b.hit(ev.x, ev.y) && b.hint) { this.tip = b.hint; this.tp = [ev.x, ev.y]; } }
    UI.handleButtons(this.btns, ev);
  }
  update(dt) { this.t += dt; }
  draw() {
    const g = this.app.ctx, c = this.c, G = this.g, info = c.info, tcol = info.color;
    g.drawImage(R.ground(W + 40, H + 40, G.terrain(), 61), -20, -20); UI.veil(0, 'rgba(14,10,6,.78)');
    UI.panel(30, 30, 330, H - 60, C.panel, tcol, 12, undefined, 3);
    g.fillStyle = tcol; g.beginPath(); g.roundRect(46, 46, 298, 120, 8); g.fill(); g.strokeStyle = '#140e0a'; g.lineWidth = 3; g.stroke();
    const bx = 195, by = 112; g.fillStyle = '#ece0be'; g.beginPath(); g.moveTo(bx, by - 46); g.lineTo(bx + 50, by + 40); g.lineTo(bx - 50, by + 40); g.fill(); g.fillStyle = '#3c2c1e'; g.beginPath(); g.moveTo(bx, by + 40); g.lineTo(bx - 12, by + 40); g.lineTo(bx, by - 2); g.fill();
    T(info.name.toUpperCase(), 195, 176, {size: 30, color: C.gold, serif: true, bold: true, align: 'center', shadow: true});
    UI.para(info.lore, 50, 216, 290, 14, C.dim, {maxLines: 4});
    const att = c.ts.attitude; T(`Trato: ${c.mood()}`, 50, 300, {size: 22, bold: true});
    const gr = g.createLinearGradient(50, 0, 340, 0); gr.addColorStop(0, '#d24a3c'); gr.addColorStop(.5, '#d2b43c'); gr.addColorStop(1, '#46b46a'); g.fillStyle = gr; g.fillRect(50, 336, 290, 14);
    const px = 50 + (att + 100) / 200 * 290; g.fillStyle = '#fff'; g.beginPath(); g.moveTo(px, 352); g.lineTo(px - 6, 362); g.lineTo(px + 6, 362); g.fill(); T((att >= 0 ? '+' : '') + Math.round(att), px, 364, {size: 14, align: 'center'});
    let y = 396; const chips = [];
    if (G.day <= c.ts.treatyUntil) chips.push([c.ts.treatyUntil < 9999 ? `Tregua hasta el día ${c.ts.treatyUntil}` : 'Paz permanente', C.green]);
    if (c.ts.allied) chips.push(['Alianza sellada', C.green]); if (G.hasGuide()) chips.push(['Guía/intérprete contigo', C.blue]); if (c.ts.arms > 2) chips.push(['Bien armados (con tu pólvora)', C.orange]);
    for (const [s, col] of chips) { T('• ' + s, 50, y, {size: 15, color: col}); y += 22; }
    T('Paciencia', 50, H - 160, {size: 16, color: C.dim});
    for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(150 + i * 24, H - 151, 8, 0, 7); if (i < c.patience) { g.fillStyle = C.gold; g.fill(); } else { g.strokeStyle = '#463626'; g.lineWidth = 2; g.stroke(); } }
    const s = G.sup; [['goods', 62, s.goods], ['food', 132, Math.floor(s.food)], ['ammo', 232, s.ammo], ['medicine', 302, s.medicine]].forEach(([ic, x, v]) => { UI.icon(ic, x, H - 108, 20); T(v, x + 18, H - 118, {size: 17, color: C.gold}); });
    T(`Tu labia: ${c.talkSkill().toFixed(0)}`, 50, H - 76, {size: 15, color: C.dim});
    UI.panel(380, 30, 480, H - 60, '#e2d0a4', C.edge, 12, undefined, 3);
    T({visit: 'Una visita', patrol: 'Una patrulla os sale al paso', tense: 'Parlamento a vida o muerte'}[c.kind], 620, 44, {size: 24, color: C.ink, serif: true, bold: true, align: 'center'});
    let yy = H - 60;
    for (const [who, msg] of this.log.slice().reverse()) {
      const lines = UI.wrap(msg, 16, 430), h = lines.length * 21 + 10; yy -= h + 6; if (yy < 90) break;
      g.fillStyle = who === 'narr' ? '#d6c08c' : '#ecd6be'; g.beginPath(); g.roundRect(396, yy, 448, h, 6); g.fill();
      lines.forEach((ln, i) => T(ln, 404, yy + 5 + i * 21, {size: 16, color: who === 'warn' ? '#502820' : C.ink}));
    }
    UI.panel(870, 30, 380, H - 60, C.panel, C.edge, 12);
    T(this.gift ? 'Elige el regalo' : '¿Qué haces?', 1060, 46, {size: 22, color: C.gold, serif: true, bold: true, align: 'center'});
    if (c.ended) T({paz: 'Hay paz.', hostil: '¡La guerra es inevitable!', neutral: 'El encuentro ha terminado.'}[c.result], 1060, 480, {size: 24, color: c.result === 'paz' ? C.green : c.result === 'hostil' ? C.red : C.parch, serif: true, align: 'center'});
    if (this.gift) { let y2 = 150; for (const [k, n] of [['goods', 'Mercancías'], ['food', 'Comida'], ['ammo', 'Munición'], ['medicine', 'Medicinas']]) { const star = info.wants === k; T((star ? '★ ' : '') + n, 890, y2 + 10, {size: 16, color: star ? C.gold : C.text}); y2 += 56; } T('★ = lo que más valoran', 890, 380, {size: 14, color: C.dim}); }
    for (const b of this.btns) b.draw();
    if (this.tip) UI.tooltip(this.tip, this.tp[0], this.tp[1]);
  }
}
S2.DiplomacyScene = DiplomacyScene;

// ============================================================== plan de defensa
class DefenseScene extends Scene {
  constructor(app) {
    super(app); this.g = app.game; this.sel = null; this.selW = 0; this.msg = ''; this.msgCol = C.dim; this.t = 0;
    this.close = new Button(W - 300, H - 60, 270, 46, 'Listo', () => app.pop(), {size: 20, color: '#624a28', key: 'Escape'});
    this.auto = new Button(30, H - 60, 200, 46, 'Auto-asignar', () => { this.g.autoAssign(); this.msg = 'Tiradores y ayudantes reasignados.'; this.msgCol = C.green; }, {size: 18});
    this.unas = new Button(240, H - 60, 200, 46, 'Quitar puesto', () => { if (this.sel) { this.sel.post = null; this.sel = null; } }, {size: 18});
    this.geom(); this.buildUp();
  }
  resume() { this.geom(); this.buildUp(); }
  geom() {
    const g = this.g; g.normalizePosts(); this.n = g.wagons.length; this.R = Math.max(118, this.n * 106 / (2 * Math.PI)); this.S = .95; this.CX = 600; this.CY = 372;
    this.wag = g.wagons.map((_, i) => { const a = -Math.PI / 2 + 2 * Math.PI * i / this.n; return {i, a, x: this.CX + Math.cos(a) * this.R * this.S, y: this.CY + Math.sin(a) * this.R * this.S}; });
    this.selW = Math.min(this.selW, Math.max(0, this.n - 1));
  }
  slotPos(i, slot) { const a = this.wag[i].a, r = (this.R - 30) * this.S, off = (slot === 'tirador' ? -.17 : .17) * 90 / Math.max(60, this.R) * 1.15; return [this.CX + Math.cos(a + off) * r, this.CY + Math.sin(a + off) * r]; }
  buildUp() {
    const g = this.g; this.up = []; if (!g.wagons.length) return; const i = this.selW, w = g.wagons[i];
    const defs = [['Reparar (+90 PV) · 1 repuesto', () => this.act(g.repairWagon(i)), w.hp < w.maxHp - 1], [`Reforzar con planchas · 2 repuestos (${w.reinforced}/2)`, () => this.act(g.upgrade(i, 'refuerzo')), w.reinforced < 2],
      ['Plataforma de tiro · 2 repuestos + 1 mercancía', () => this.act(g.upgrade(i, 'plataforma')), !w.platform], ['Farol de combate · 2 mercancías', () => this.act(g.upgrade(i, 'farol')), !w.lantern],
      [`Montar cañón (en almacén: ${g.cannonStock})`, () => this.act(g.upgrade(i, 'cañón')), !w.cannon && g.cannonStock > 0]];
    defs.forEach(([l, f, en], k) => this.up.push(new Button(920, 330 + k * 50, 330, 44, l, f, {enabled: en, size: 15})));
  }
  act([ok, msg]) { this.msg = msg; this.msgCol = ok ? C.green : C.red; this.buildUp(); }
  rows() { const cols = this.g.living(), rh = Math.max(UI.touch ? 30 : 24, Math.min(36, (H - 250) / Math.max(1, cols.length))); return cols.map((c, k) => [c, {x: 24, y: 92 + k * rh, w: 300, h: rh - 3}]); }
  handle(ev) {
    if (UI.handleButtons([this.close, this.auto, this.unas].concat(this.up), ev)) return;
    const g = this.g;
    if (ev.type === 'down') {
      for (const [c, r] of this.rows()) if (inBox(ev, r.x, r.y, r.w, r.h)) { this.sel = this.sel === c ? null : c; return; }
      for (let i = 0; i < this.n; i++) for (const slot of ['tirador', 'ayuda']) {
        const [sx, sy] = this.slotPos(i, slot);
        if (Math.hypot(ev.x - sx, ev.y - sy) < (UI.touch ? 28 : 16)) {
          if (this.sel) { if (slot === 'tirador' && !g.canShoot(this.sel)) { this.msg = 'Sólo adultos y jóvenes sanos pueden disparar: ponlos de ayudantes.'; this.msgCol = C.red; } else { g.assign(this.sel, i, slot); this.sel = null; this.msg = ''; } }
          else { const occ = g.postOf(i, slot); if (occ) this.sel = occ; }
          this.selW = i; this.buildUp(); return;
        }
      }
      for (const w of this.wag) if (Math.hypot(ev.x - w.x, ev.y - w.y) < 40) { this.selW = w.i; this.buildUp(); return; }
    }
  }
  update(dt) { this.t += dt; }
  draw() {
    const g = this.app.ctx, G = this.g, S = this.S, CX = this.CX, CY = this.CY;
    g.drawImage(R.ground(W + 40, H + 40, G.terrain(), 51), -20, -20); UI.veil(0, 'rgba(16,11,7,.6)');
    T('Plan de defensa', 30, 18, {size: 38, color: C.gold, serif: true, bold: true});
    T('Toca un colono y luego una plaza (T = tirador, A = ayudante). Toca una plaza ocupada para moverla.', 32, 64, {size: 14, color: C.dim});
    g.fillStyle = '#6e583a'; g.beginPath(); g.arc(CX, CY, this.R * S + 46, 0, 7); g.fill(); g.strokeStyle = '#7e6642'; g.lineWidth = 3; g.stroke();
    for (const [tx, ty] of [[-.4, -.25], [.35, -.3], [-.3, .3]]) R.drawTent(g, CX + tx * this.R * S, CY + ty * this.R * S, .9);
    R.drawFire(g, CX, CY, this.t, 1);
    for (const w of this.wag) {
      const wg = G.wagons[w.i]; R.drawWagon(g, w.x, w.y, w.a + Math.PI / 2, Math.max(0, wg.hp / wg.maxHp), wg.reinforced, wg.platform, wg.cannon, wg.lantern, false, S);
      if (w.i === this.selW) { g.strokeStyle = C.gold; g.lineWidth = 2; g.beginPath(); g.arc(w.x, w.y, 50, 0, 7); g.stroke(); }
      const f = wg.hp / wg.maxHp; UI.bar(w.x + Math.cos(w.a) * 52 * S - 18, w.y + Math.sin(w.a) * 52 * S - 3, 36, 5, f, hpCol(f));
      T(w.i + 1, w.x + Math.cos(w.a) * 66 * S, w.y + Math.sin(w.a) * 66 * S, {size: 16, color: C.gold, bold: true, align: 'center', base: 'middle', shadow: true});
    }
    for (let i = 0; i < this.n; i++) for (const slot of ['tirador', 'ayuda']) {
      const [sx, sy] = this.slotPos(i, slot), occ = G.postOf(i, slot), col = slot === 'tirador' ? '#6ea0dc' : '#78b864';
      g.fillStyle = '#1e1610'; g.beginPath(); g.arc(sx, sy, 13, 0, 7); g.fill(); g.strokeStyle = col; g.lineWidth = 2; g.stroke();
      if (!occ) T(slot === 'tirador' ? 'T' : 'A', sx, sy, {size: 13, color: col, bold: true, align: 'center', base: 'middle'});
      else { R.drawPerson(g, sx, sy, occ.group, occ.cid, 1.4); if (this.sel === occ) { g.strokeStyle = C.gold; g.lineWidth = 3; g.beginPath(); g.arc(sx, sy, 17, 0, 7); g.stroke(); } }
    }
    UI.panel(14, 84, 322, H - 160, C.panel, C.edge, 8);
    for (const [c, r] of this.rows()) {
      const sel = this.sel === c; UI.panel(r.x, r.y, r.w, r.h, sel ? '#5c462e' : '#3a2c1e', sel ? C.gold : '#3a2c1e', 5, undefined, sel ? 2 : 1);
      R.drawPerson(g, r.x + 14, r.y + r.h / 2, c.group, c.cid, 1); T(c.name.slice(0, 17), r.x + 30, r.y + 1, {size: 14, color: c.sick ? '#c8e696' : C.text});
      UI.bar(r.x + 30, r.y + r.h - 7, 100, 3, c.health / 100, c.health > 50 ? C.green : C.orange);
      let lbl = '—', col = C.dim; if (c.post) { lbl = `C${c.post[0] + 1} ` + (c.post[1] === 'tirador' ? 'tirador' : 'ayuda'); col = c.post[1] === 'tirador' ? '#8cbef0' : '#96d282'; }
      T(lbl, r.x + r.w - 8, r.y + r.h / 2, {size: 12, color: col, align: 'right', base: 'middle'}); if (G.canShoot(c)) T('P' + c.shoot, r.x + 150, r.y + 3, {size: 12, color: C.gold});
    }
    UI.panel(900, 70, 360, H - 150, C.panel, C.edge, 10);
    if (G.wagons.length) {
      const w = G.wagons[this.selW]; T(`Carreta ${this.selW + 1}`, 920, 80, {size: 26, color: C.gold, serif: true, bold: true});
      UI.bar(920, 124, 320, 12, w.hp / w.maxHp, hpCol(w.hp / w.maxHp)); T(`${Math.floor(w.hp)} / ${Math.floor(w.maxHp)} PV`, 920, 142, {size: 15});
      const ex = [['cañón', w.cannon], ['plataforma', w.platform], ['farol', w.lantern]].filter(x => x[1]).map(x => x[0]);
      T(`Refuerzos: ${w.reinforced}` + (ex.length ? ' · ' + ex.join(', ') : ''), 920, 164, {size: 14, color: C.dim});
      const t_ = G.postOf(this.selW, 'tirador'), a_ = G.postOf(this.selW, 'ayuda');
      T(`Tirador: ${t_ ? t_.name : '—'}`, 920, 188, {size: 15, color: '#8cbef0'}); T(`Ayudante: ${a_ ? a_.name : '—'}`, 920, 210, {size: 15, color: '#96d282'});
      UI.para('El ayudante recarga y apaga fuegos; con él el tirador dispara un 32 % más rápido.', 920, 236, 320, 13, C.dim);
      T(`Repuestos: ${G.sup.parts} · Mercancías: ${G.sup.goods}`, 920, 296, {size: 15, color: C.gold});
    }
    for (const b of this.up) b.draw();
    T(`Tiradores disponibles: ${G.shooters().length} · Plazas de tirador: ${this.n} · Munición: ${G.sup.ammo}`, 30, H - 100, {size: 15, color: C.parch});
    if (this.msg) T(this.msg, 460, H - 52, {size: 16, color: this.msgCol});
    this.unas.enabled = !!(this.sel && this.sel.post); this.close.draw(); this.auto.draw(); this.unas.draw();
  }
}
S2.DefenseScene = DefenseScene;
Object.assign(S2, {PromptScene, JournalScene, CutsceneScene, TravelScene, CampScene, DiplomacyScene, DefenseScene, MenuScene});
})(globalThis.CV = globalThis.CV || {});
