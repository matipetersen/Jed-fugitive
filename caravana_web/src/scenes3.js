/* Combate 360°, elección de sitio, asentamiento y crónica. */
(function (CV) {
'use strict';
const UI = CV.ui, C = UI.C, D = CV.data, R = CV.render, W = UI.W, H = UI.H;
const Scene = UI.Scene, Button = UI.Button, T = (...a) => UI.text(...a);
const S3 = CV.scenes3 = {};
const inBox = (ev, x, y, w, h) => ev.x >= x && ev.x <= x + w && ev.y >= y && ev.y <= y + h;
const hpCol = f => f > .5 ? C.green : f > .25 ? C.orange : C.red;
const LEFT_W = 260, S = 1;

// ============================================================== combate
class BattleScene extends Scene {
  constructor(app, game, spec, onDone) {
    super(app); this.game = game; this.spec = spec; this.onDone = onDone; this.battle = new CV.Battle(game, spec);
    this.cx = LEFT_W + (W - LEFT_W) / 2; this.cy = H / 2 + 8; this.shake = 0;
    this.field = {x: LEFT_W, y: 0, w: W - LEFT_W, h: H}; this.speed = 1; this.paused = false; this.selected = null; this.parts = new R.Particles(); this.tracers = []; this.bodies = [];
    this.t = 0; this.tip = ''; this.tribeCol = D.TRIBES[spec.foe] ? D.TRIBES[spec.foe].color : '#605046'; this.parley = false; this.endTimer = 0; this.finished = false; this.rscroll = 0;
    const rr = new CV.RNG(game.day * 3 + 1), Rr = this.battle.R;
    this.tents = [[-.42, -.28, 1], [.36, -.34, .95], [-.34, .3, .9], [.4, .28, .85]].slice(0, 2 + Math.min(2, Math.floor(game.living().length / 5))).map(([a, b, s]) => [a * Rr, b * Rr, s]);
    this.crates = Array.from({length: 5}, () => [rr.uniform(-.5, .5) * Rr, rr.uniform(-.5, .5) * Rr]).filter(([x, y]) => Math.hypot(x, y) > 30);
    this.oxen = Array.from({length: Math.min(7, 3 + Math.floor(game.sup.oxen / 4))}, () => [rr.uniform(-.5, .5) * Rr * .9, rr.uniform(-.5, .5) * Rr * .9, rr.uniform(0, 6.28)]).filter(([x, y]) => Math.hypot(x, y) > 36);
    this.buildButtons();
  }
  X(x) { return this.cx + x * S + (this.shake ? (Math.random() - .5) * this.shake : 0); }
  Y(y) { return this.cy + y * S; }
  inv(sx, sy) { return [(sx - this.cx) / S, (sy - this.cy) / S]; }
  get cam() { return {x: x => this.cx + x * S, y: y => this.cy + y * S, s: S}; }
  buildButtons() {
    this.touch = UI.touch; const b = this.battle, x = 10, w = LEFT_W - 20, th = UI.touch ? 38 : 32, gp = th + 4, y = H - (UI.touch ? 252 : 236), h2 = w / 2 - 2, B = (...a) => new Button(...a);
    this.autoB = B(x, y, h2, th, 'Auto (A)', () => b.autoAssign(), {size: 15, key: 'KeyA'});
    this.unasB = B(x + w / 2 + 2, y, h2, th, 'Quitar puesto', () => { if (this.selected) { b.unassign(this.selected); this.selected = null; } }, {size: 15});
    this.polB = B(x, y + gp, w, th, '', () => { const o = ['libre', 'contenido', 'alto']; b.policy = o[(o.indexOf(b.policy) + 1) % 3]; }, {size: 15, key: 'KeyF'});
    this.parB = B(x, y + 2 * gp, h2, th, 'Parlamento (P)', () => { if (b.parleyAvailable) this.parley = !this.parley; }, {size: 15, key: 'KeyP'});
    this.meltB = B(x + w / 2 + 2, y + 2 * gp, h2, th, 'Fundir (M)', () => b.melt(), {size: 15, key: 'KeyM'});
    this.startB = B(x, y + 3 * gp, w, th, '', () => b.startFight(), {size: 15, key: 'Enter'});
    this.btns = [this.autoB, this.unasB, this.polB, this.parB, this.meltB, this.startB,
      B(x, y + 4 * gp, w / 3 - 2, th - 2, 'Pausa', () => { this.paused = !this.paused; }, {size: 14, key: 'Space'}),
      B(x + w / 3 + 1, y + 4 * gp, w / 3 - 2, th - 2, 'x1', () => { this.speed = 1; this.paused = false; }, {size: 14, key: 'Digit1'}),
      B(x + 2 * w / 3 + 2, y + 4 * gp, w / 3 - 2, th - 2, 'x2', () => { this.speed = 2; this.paused = false; }, {size: 14, key: 'Digit2'})];
    this.rosterBottom = y - 6;
  }
  rGeom() { const n = Math.max(1, this.battle.colonists.length), top = 60, avail = this.rosterBottom - top, rh = Math.max(UI.touch ? 28 : 21, Math.min(UI.touch ? 34 : 31, Math.floor(avail / n))); return [top, avail, rh]; }
  rRows() {
    const [top, avail, rh] = this.rGeom(), total = rh * this.battle.colonists.length; this.rscroll = Math.max(0, Math.min(this.rscroll, Math.max(0, total - avail)));
    let y = top - this.rscroll; return this.battle.colonists.map(bc => { const r = {bc, x: 8, y, w: LEFT_W - 16, h: rh - 2}; y += rh; return r; });
  }
  slotPositions() { const out = []; for (const w of this.battle.wagons) { if (w.destroyed) continue; for (const slot of ['tirador', 'ayuda']) { const [px, py] = this.battle.postPos(w.idx, slot); out.push([w.idx, slot, this.cam.x(px), this.cam.y(py)]); } } return out; }
  parleyButtons() {
    const b = this.battle, cx = this.field.x + this.field.w / 2, out = [];
    [[0, 'Parlamentar con las manos vacías'], [1, 'Ofrecer un regalo (3 mercancías)'], [2, 'Ofrecer un gran regalo (8 mercancías)']].forEach(([gift, l], i) => {
      const p = Math.round(b.parleyChance(gift) * 100), en = this.game.sup.goods >= [0, 3, 8][gift] && b.parleyCd <= 0 && b.fightTime >= 10;
      out.push(new Button(cx - 230, 250 + i * 54, 460, 44, `${l} — ${p}%`, () => { const [ok, msg] = b.parley(gift); b.say(msg, ok ? '#aaffaa' : '#ff9678'); this.parley = false; }, {enabled: en, size: 17}));
    });
    out.push(new Button(cx - 100, 250 + 3 * 54 + 6, 200, 36, 'Volver al combate', () => { this.parley = false; }, {size: 16})); return out;
  }
  click(ev) {
    const b = this.battle, T_ = UI.touch;
    for (const r of this.rRows()) if (inBox(ev, r.x, r.y, r.w, r.h)) { if (!r.bc.ref.alive || r.bc.ref.health <= 0) return; this.selected = this.selected === r.bc ? null : r.bc; return; }
    if (!inBox(ev, this.field.x, 0, this.field.w, H)) return;
    for (const [widx, slot, sx, sy] of this.slotPositions()) {
      if (Math.hypot(ev.x - sx, ev.y - sy) < (T_ ? 28 : 15)) {
        const occ = b.game.postOf(widx, slot);
        if (this.selected) { if (slot === 'tirador' && !b.game.canShoot(this.selected.ref)) { b.say('Sólo adultos y jóvenes sanos pueden disparar; ponlos de ayudantes.', '#ffaa78'); return; } b.assign(this.selected, widx, slot); this.selected = null; }
        else if (occ) { const bc = b.colonists.find(c => c.ref === occ); if (bc) this.selected = bc; }
        return;
      }
    }
    const [wx, wy] = this.inv(ev.x, ev.y); let best = null, bd = T_ ? 44 : 26;
    for (const f of b.aliveFoes()) { if (!b.isVisible(f)) continue; const d = Math.hypot(f.x - wx, f.y - wy) * S; if (d < bd) { best = f; bd = d; } }
    if (best) { b.setFocus(b.focus === best ? null : best); return; }
    for (const w of b.wagons) if (w.destroyed && w.barricade <= 0 && Math.hypot(w.x - wx, w.y - wy) * S < (T_ ? 56 : 40)) { b.orderBarricade(w.idx); return; }
    this.selected = null;
  }
  hover(ev) {
    const b = this.battle; this.tip = ''; this.tp = [ev.x, ev.y];
    for (const r of this.rRows()) if (inBox(ev, r.x, r.y, r.w, r.h)) { const c = r.bc.ref; this.tip = `${c.name} — ${this.game.roleLabel(c)}. Puntería ${c.shoot}, Medicina ${c.medic}, Construcción ${c.build}. Salud ${Math.round(c.health)}.` + (c.sick ? ` Enfermedad: ${c.sick}.` : ''); return; }
    const [wx, wy] = this.inv(ev.x, ev.y);
    for (const w of b.wagons) if (Math.hypot(w.x - wx, w.y - wy) * S < 36) { const r = w.ref; this.tip = w.destroyed ? `Carreta ${w.idx + 1} destruida.` + (w.barricade <= 0 ? ' Toca para levantar una barricada (1 repuesto).' : ' Barricada en pie.') : `Carreta ${w.idx + 1}: ${Math.round(r.hp)}/${Math.round(r.maxHp)} PV, refuerzos ${r.reinforced}` + (w.burning > 0 ? ' ¡ARDE!' : ''); return; }
    for (const f of b.aliveFoes()) if (b.isVisible(f) && Math.hypot(f.x - wx, f.y - wy) * S < 16) { this.tip = `${D.FOES[f.kind].name} — ${Math.round(f.hp)}/${Math.round(f.maxHp)} PV (toca para marcar objetivo)`; return; }
  }
  handle(ev) {
    const b = this.battle;
    if (b.done) { if ((ev.type === 'down' || (ev.type === 'key' && ['Enter', 'Space'].includes(ev.key))) && this.endTimer > .8) this.finish(); return; }
    if (this.parley) { if (UI.handleButtons(this.parleyButtons(), ev)) return; if (ev.type === 'key' && ['Escape', 'KeyP'].includes(ev.key)) this.parley = false; return; }
    if (UI.handleButtons(this.btns, ev)) return;
    if (ev.type === 'move') { this.hover(ev); if (this.rdown && ev.down) { const dy = ev.y - this.rdown.y; if (Math.abs(dy) > 8 || this.rdrag) { this.rdrag = true; this.rscroll -= ev.y - (this.rlast || ev.y); } this.rlast = ev.y; } }
    else if (ev.type === 'wheel') { if (ev.x < LEFT_W) this.rscroll += ev.dy * .5; }
    else if (ev.type === 'down') {
      if (ev.button === 2) { this.selected = null; b.setFocus(null); return; }
      this.hover(ev);
      if (ev.x < LEFT_W && ev.y > 60 && ev.y < this.rosterBottom) { this.rdown = {x: ev.x, y: ev.y}; this.rdrag = false; this.rlast = ev.y; } else this.click(ev);
    } else if (ev.type === 'up') { if (this.rdown && !this.rdrag) this.click(ev); this.rdown = null; this.rdrag = false; }
    else if (ev.type === 'key') { if (ev.key === 'F3') UI.debugDirector = !UI.debugDirector; if (ev.key === 'Escape') this.selected = null; if (ev.key === 'Digit3') { this.speed = 3; this.paused = false; } }
  }
  consumeFx() {
    const b = this.battle, P = this.parts, sfx = CV.sfx;
    for (const ev of b.fx) {
      const k = ev[0];
      if (k === 'shot') { sfx.play('shot', .45, .05); this.tracers.push([ev[1], ev[2], ev[3], ev[4], .1, ev[5]]); P.add('smoke', ev[1], ev[2], 2); P.add('spark', ev[1], ev[2], 2); }
      else if (k === 'hit') { sfx.play('hit', .5, .04); P.add('spark', ev[1], ev[2], 4, '255,120,90'); }
      else if (k === 'death') { sfx.play('death', .35, .08); P.add('dust', ev[1], ev[2], 5); P.add('ring', ev[1], ev[2], 1, '255,230,190'); this.bodies.push([ev[1], ev[2], 0]); }
      else if (k === 'wave') sfx.play('horn', .8, 1);
      else if (k === 'bow') sfx.play('bow', .3, .12);
      else if (k === 'death_col') { sfx.play('lose', .5); P.add('ring', ev[1], ev[2], 1, '255,120,120'); }
      else if (k === 'hurt') { sfx.play('hurt', .5, .1); P.add('spark', ev[1], ev[2], 5, '255,80,80'); }
      else if (k === 'rifle') { sfx.play('rifle', .5, .1); this.tracers.push([ev[1], ev[2], ev[3], ev[4], .1, false]); P.add('smoke', ev[1], ev[2], 2); }
      else if (k === 'chop') { sfx.play('chop', .35, .1); P.add('spark', ev[1], ev[2], 2, '190,140,80'); }
      else if (k === 'thunk') { sfx.play('thunk', .3, .1); P.add('dust', ev[1], ev[2], 1); }
      else if (k === 'boom') { sfx.play('boom', .8, .2); P.add('fire', ev[1], ev[2], 14); P.add('smoke', ev[1], ev[2], 14); P.add('dust', ev[1], ev[2], 10); this.shake = 7; }
      else if (k === 'cannon') { sfx.play('cannon', .9, .2); P.add('smoke', ev[1], ev[2], 10); P.add('spark', ev[1], ev[2], 8); P.add('fire', ev[3], ev[4], 8); P.add('smoke', ev[3], ev[4], 8); P.add('dust', ev[3], ev[4], 8); P.add('ring', ev[3], ev[4], 1, '255,200,120'); this.tracers.push([ev[1], ev[2], ev[3], ev[4], .25, true]); this.shake = 5; }
    }
    b.fx.length = 0;
  }
  update(dt) {
    this.t += dt; const b = this.battle; this.shake = Math.max(0, this.shake - dt * 14);
    if (!this.paused && !b.done) for (let i = 0; i < this.speed; i++) b.update(dt);
    this.consumeFx(); this.parts.update(this.paused ? 0 : dt);
    this.tracers = this.tracers.map(t => [t[0], t[1], t[2], t[3], t[4] - dt, t[5]]).filter(t => t[4] > 0);
    for (const bd of this.bodies) bd[2] += dt; this.bodies = this.bodies.filter(x => x[2] < 22).slice(-70);
    if (b.done) { if (this.endTimer === 0) CV.sfx.play(b.result.outcome === 'derrota' ? 'lose' : 'win', .7); this.endTimer += dt; }
    if (this.touch !== UI.touch) this.buildButtons();
    this.unasB.enabled = !!(this.selected && this.selected.ref.post);
    this.polB.label = {libre: 'Fuego libre (F)', contenido: 'Fuego contenido (F)', alto: 'Alto el fuego (F)'}[b.policy];
    this.startB.label = b.phase === 'prep' ? '¡Empezar ya! (Enter)' : 'Combate en curso'; this.startB.enabled = b.phase === 'prep';
    this.meltB.enabled = this.game.sup.goods >= 5; this.parB.enabled = b.parleyAvailable && b.phase === 'fight';
    if (!this.paused) for (const w of b.wagons) if (w.burning > 0 && Math.random() < .6) { this.parts.add('fire', w.x, w.y, 1); if (Math.random() < .3) this.parts.add('smoke', w.x, w.y, 1); }
    if (!this.paused && Math.random() < .4) { this.parts.add('ember', 0, 0, 1); if (Math.random() < .3) this.parts.add('smoke', 0, 0, 1); }
  }
  finish() { if (this.finished) return; this.finished = true; this.onDone(this.battle.result); }
  draw() {
    const g = this.app.ctx, b = this.battle, F = this.field;
    g.fillStyle = C.bg; g.fillRect(0, 0, W, H);
    g.save(); g.beginPath(); g.rect(F.x, 0, F.w, H); g.clip();
    g.drawImage(R.ground(F.w + 40, H + 40, this.game.terrain(), this.game.day % 5), F.x - 20, -20);
    const rg = g.createRadialGradient(this.cx, this.cy, 0, this.cx, this.cy, b.R * S + 60); rg.addColorStop(0, 'rgba(122,98,64,.55)'); rg.addColorStop(.85, 'rgba(122,98,64,.5)'); rg.addColorStop(1, 'rgba(122,98,64,0)'); g.fillStyle = rg; g.fillRect(F.x, 0, F.w, H);
    this.drawCamp(g); this.drawBodies(g); this.drawWagons(g); this.drawSlots(g); this.drawColonists(g); this.drawFoes(g); this.drawAllies(g); this.drawArrows(g);
    for (const [x1, y1, x2, y2, , ok] of this.tracers) { g.strokeStyle = ok ? '#fff0aa' : '#c8c8c8'; g.lineWidth = 1; g.beginPath(); g.moveTo(this.cam.x(x1), this.cam.y(y1)); g.lineTo(this.cam.x(x2), this.cam.y(y2)); g.stroke(); }
    this.parts.draw(g, this.cam);
    if (b.night) this.drawNight(g);
    this.drawWarnings(g); this.drawFocus(g);
    g.restore();
    this.drawHud(g);
    if (this.parley) this.drawParley(g);
    if (b.done) this.drawResult(g);
    if (UI.debugDirector) { CV.scenes2.drawDirector(this.game); T(`presión ${this.game.director.battlePressure(b).toFixed(2)} · oleadas pend. ${b.pending.length} · retrasos ${b.delaysUsed}`, LEFT_W + 10, 48, {size: 13, color: C.blue}); }
    if (this.tip && !b.done) UI.tooltip(this.tip, this.tp[0], this.tp[1]);
  }
  drawCamp(g) {
    const b = this.battle;
    for (const [x, y, s] of this.tents) R.drawTent(g, this.cam.x(x), this.cam.y(y), s);
    for (const [x, y] of this.crates) { const sx = this.cam.x(x), sy = this.cam.y(y); g.fillStyle = '#7c5a36'; g.fillRect(sx - 6, sy - 5, 12, 10); g.strokeStyle = '#46301c'; g.lineWidth = 1; g.strokeRect(sx - 6, sy - 5, 12, 10); }
    for (const [x, y, a] of this.oxen) R.drawOx(g, this.cam.x(x), this.cam.y(y), .9, a + Math.sin(this.t * .3 + x) * .1);
    const sx = this.cam.x(0), sy = this.cam.y(52); g.fillStyle = '#ebe8de'; g.beginPath(); g.roundRect(sx - 22, sy - 12, 44, 24, 3); g.fill(); g.fillStyle = '#c83232'; g.fillRect(sx - 2, sy - 8, 4, 16); g.fillRect(sx - 8, sy - 2, 16, 4);
    R.drawFire(g, this.cam.x(0), this.cam.y(0), this.t, 1);
  }
  drawBodies(g) { for (const [x, y, t] of this.bodies) { g.fillStyle = `rgba(60,36,30,${.6 * Math.max(0, 1 - t / 22)})`; g.beginPath(); g.ellipse(this.cam.x(x), this.cam.y(y), 13, 7, 0, 0, 7); g.fill(); } }
  drawWagons(g) {
    for (const w of this.battle.wagons) {
      const r = w.ref, frac = Math.max(0, r.hp / Math.max(1, r.maxHp)), sx = this.cam.x(w.x), sy = this.cam.y(w.y);
      R.drawWagon(g, sx, sy, w.angle + Math.PI / 2, frac, r.reinforced, r.platform, r.cannon, r.lantern, w.destroyed, S);
      if (w.flash > 0 && !w.destroyed) { g.fillStyle = 'rgba(200,60,40,.35)'; g.beginPath(); g.arc(sx, sy, 24, 0, 7); g.fill(); }
      if (w.destroyed && w.barricade > 0) { const a = w.angle + Math.PI / 2; g.strokeStyle = '#785432'; g.lineWidth = 3; for (let i = -2; i <= 2; i++) { const px = sx + Math.cos(a) * i * 14 * S, py = sy + Math.sin(a) * i * 14 * S; g.beginPath(); g.moveTo(px - 5, py - 8); g.lineTo(px + 5, py + 8); g.moveTo(px + 5, py - 8); g.lineTo(px - 5, py + 8); g.stroke(); } UI.bar(sx - 18, sy + 14, 36, 4, w.barricade / 90, '#c8a05a'); }
      if (w.destroyed && w.buildProgress > 0 && w.barricade <= 0) UI.bar(sx - 18, sy + 14, 36, 4, w.buildProgress, '#82c878');
      if (!w.destroyed && frac < .999) UI.bar(sx + Math.cos(w.angle) * 34 * S - 18, sy + Math.sin(w.angle) * 34 * S - 3, 36, 5, frac, hpCol(frac));
      if (!w.destroyed) T(w.idx + 1, sx - Math.cos(w.angle) * 33 * S, sy - Math.sin(w.angle) * 33 * S, {size: 13, color: '#fff5dc', bold: true, align: 'center', base: 'middle', shadow: true});
    }
  }
  drawSlots(g) {
    const b = this.battle, showAll = b.phase === 'prep' || this.selected;
    for (const [widx, slot, sx, sy] of this.slotPositions()) {
      const occ = b.game.postOf(widx, slot), col = slot === 'tirador' ? '#6ea0dc' : '#78b864';
      if (!occ && !showAll) continue;
      const rad = UI.touch ? 15 : 12; g.strokeStyle = col; g.lineWidth = 2; g.beginPath(); g.arc(sx, sy, rad, 0, 7); g.stroke();
      if (!occ) T(slot === 'tirador' ? 'T' : 'A', sx, sy, {size: 12, color: col, bold: true, align: 'center', base: 'middle'});
      if (this.selected && this.selected.ref === occ) { g.strokeStyle = C.gold; g.lineWidth = 3; g.beginPath(); g.arc(sx, sy, rad + 3, 0, 7); g.stroke(); }
    }
  }
  drawColonists(g) {
    for (const bc of this.battle.colonists.slice().sort((a, b) => a.y - b.y)) {
      const c = bc.ref, sx = this.cam.x(bc.x), sy = this.cam.y(bc.y);
      if (!c.alive) { R.drawPerson(g, sx, sy, c.group, c.cid, S * 1.5, {dead: true}); continue; }
      let aim = null; if (bc.aim && bc.flash > 0) aim = Math.atan2(bc.aim[1] - bc.y, bc.aim[0] - bc.x); else if (bc.task === 'post') aim = Math.atan2(bc.y, bc.x);
      R.drawPerson(g, sx, sy, c.group, c.cid, S * 1.6, {aim, wounded: c.health < 30});
      if (bc.flash > .2 && bc.task !== 'post') { g.strokeStyle = '#ff5050'; g.lineWidth = 1; g.beginPath(); g.arc(sx, sy, 10, 0, 7); g.stroke(); }
      if (this.selected === bc) { g.strokeStyle = C.gold; g.lineWidth = 2; g.beginPath(); g.arc(sx, sy, 13, 0, 7); g.stroke(); }
      if (c.health < 100 && c.health > 0) UI.bar(sx - 8, sy - 14, 16, 3, c.health / 100, hpCol(c.health / 100));
      const lb = {repair: 'reparando', extinguish: 'apagando', heal: 'curando', build: 'construyendo'}[bc.task]; if (lb) T(lb, sx, sy + 12, {size: 11, color: C.dim, align: 'center'});
    }
  }
  drawFoes(g) {
    const b = this.battle, F = this.field;
    for (const f of b.foes.slice().sort((a, c) => a.y - c.y)) {
      if (!f.alive || f.fled) continue; const sx = this.cam.x(f.x), sy = this.cam.y(f.y);
      if (sx < F.x - 60 || sx > F.x + F.w + 60 || sy < -60 || sy > H + 60) continue;
      if (b.night && !b.isVisible(f)) { if (Math.hypot(f.x, f.y) < 520) { g.fillStyle = '#962828'; g.beginPath(); g.arc(sx, sy, 2, 0, 7); g.fill(); } continue; }
      R.drawFoe(g, f, sx, sy, S * 1.75, this.tribeCol, f.flash > 0);
      if (f.mounted && f.state !== 'stand' && Math.random() < .18 && !this.paused) this.parts.add('dust', f.x, f.y, 1);
      if (f.hp < f.maxHp) UI.bar(sx - 9, sy - 16, 18, 3, f.hp / f.maxHp, C.red);
      if (f.state === 'flee') T('huye', sx, sy - 22, {size: 11, color: C.dim, align: 'center', base: 'bottom'});
    }
  }
  drawAllies(g) { for (const al of this.battle.allies) if (al.alive) R.drawFoe(g, {kind: 'jinete', face: al.face}, this.cam.x(al.x), this.cam.y(al.y), S * 1.75, '#5abe78'); }
  drawArrows(g) {
    for (const a of this.battle.arrows) {
      const sx = this.cam.x(a.x), sy = this.cam.y(a.y), dx = a.tx - a.x, dy = a.ty - a.y, d = Math.max(1, Math.hypot(dx, dy));
      g.strokeStyle = a.fire ? '#ffa032' : '#e6dcbe'; g.lineWidth = 2; g.beginPath(); g.moveTo(sx - dx / d * 12, sy - dy / d * 12); g.lineTo(sx, sy); g.stroke();
      if (a.fire && Math.random() < .5) this.parts.add('fire', a.x, a.y, 1);
    }
  }
  drawFocus(g) { const f = this.battle.focus; if (f && f.alive && !f.fled) { const sx = this.cam.x(f.x), sy = this.cam.y(f.y), r = 16 + 2 * Math.sin(this.t * 8); g.strokeStyle = C.red; g.lineWidth = 2; g.beginPath(); g.arc(sx, sy, r, 0, 7); g.stroke(); for (let a = 0; a < 4; a++) { const an = a * Math.PI / 2; g.beginPath(); g.moveTo(sx + Math.cos(an) * (r - 4), sy + Math.sin(an) * (r - 4)); g.lineTo(sx + Math.cos(an) * (r + 5), sy + Math.sin(an) * (r + 5)); g.stroke(); } } }
  drawNight(g) {
    const b = this.battle, fl = 1 + .03 * Math.sin(this.t * 9), L = [[this.cam.x(0), this.cam.y(0), (b.R + 190) * S * fl]];
    for (const w of b.wagons) { if (w.ref.lantern && !w.destroyed) L.push([this.cam.x(w.x), this.cam.y(w.y), 300 * S * fl]); if (w.burning > 0) L.push([this.cam.x(w.x), this.cam.y(w.y), 170 * S * fl]); }
    for (const f of b.foes) if (f.alive && f.revealed > 0 && !f.fled) L.push([this.cam.x(f.x), this.cam.y(f.y), 70 * S]);
    CV.scenes1.nightOverlay(g, L, 'rgba(6,10,30,.84)');
  }
  drawWarnings(g) {
    const F = this.field, x0 = F.x + 35, x1 = F.x + F.w - 35, y0 = 35, y1 = H - 35, cx = this.cam.x(0), cy = this.cam.y(0);
    for (const [ang, secs, comp] of this.battle.warnings()) {
      const dx = Math.cos(ang), dy = Math.sin(ang), tx = dx > 0 ? (x1 - cx) / dx : dx < 0 ? (x0 - cx) / dx : 1e9, ty = dy > 0 ? (y1 - cy) / dy : dy < 0 ? (y0 - cy) / dy : 1e9, t = Math.min(tx, ty), px = cx + dx * t, py = cy + dy * t;
      const pulse = .6 + .4 * Math.sin(this.t * 7), col = `rgb(255,${Math.floor(80 + 100 * pulse)},60)`;
      g.fillStyle = col; g.beginPath(); g.moveTo(px + dx * 14, py + dy * 14); g.lineTo(px - dx * 6 - dy * 12, py - dy * 6 + dx * 12); g.lineTo(px - dx * 6 + dy * 12, py - dy * 6 - dx * 12); g.fill();
      const n = Object.values(comp).reduce((a, c) => a + c, 0); T(`${n} · ${Math.max(0, secs).toFixed(0)}s`, px - dx * 30, py - dy * 30, {size: 14, color: col, bold: true, align: 'center', base: 'middle', shadow: true});
    }
  }
  drawHud(g) {
    const b = this.battle, G = this.game, F = this.field;
    g.fillStyle = '#281e16'; g.fillRect(0, 0, LEFT_W, H);
    T('DEFENSA DEL CÍRCULO', LEFT_W / 2, 12, {size: 16, color: C.gold, bold: true, serif: true, align: 'center'}); T('toca un colono → toca una plaza T/A', LEFT_W / 2, 36, {size: 12, color: C.dim, align: 'center'});
    g.save(); g.beginPath(); g.rect(0, 58, LEFT_W, this.rosterBottom - 58); g.clip();
    for (const r of this.rRows()) {
      const c = r.bc.ref, sel = this.selected === r.bc; g.fillStyle = sel ? '#5c462e' : '#3a2c1e'; g.beginPath(); g.roundRect(r.x, r.y, r.w, r.h, 5); g.fill(); if (sel) { g.strokeStyle = C.gold; g.lineWidth = 2; g.stroke(); }
      if (!c.alive) { T('† ' + c.name, r.x + 8, r.y + 3, {size: 14, color: '#82645a'}); continue; }
      R.drawPerson(g, r.x + 13, r.y + r.h / 2, c.group, c.cid, .9); T(c.name.slice(0, 16), r.x + 28, r.y + Math.max(1, (r.h - 17) / 2 - 3), {size: 14});
      UI.bar(r.x + 28, r.y + r.h - 5, 96, 3, c.health / 100, hpCol(c.health / 100));
      let lbl = '—', col = C.dim;
      if (c.post) { lbl = `C${c.post[0] + 1} ` + (c.post[1] === 'tirador' ? 'tirador' : 'ayuda'); col = c.post[1] === 'tirador' ? '#8cbef0' : '#96d282'; }
      else if (['repair', 'extinguish', 'heal', 'build', 'melee'].includes(r.bc.task)) lbl = {repair: 'repara', extinguish: 'apaga', heal: 'cura', build: 'construye', melee: 'lucha'}[r.bc.task];
      else if (r.bc.task === 'wounded') { lbl = 'herido'; col = C.red; }
      T(lbl, r.x + r.w - 6, r.y + r.h / 2, {size: 12, color: col, align: 'right', base: 'middle'});
    }
    g.restore();
    for (const bt of this.btns) bt.draw();
    g.fillStyle = 'rgba(30,22,16,.8)'; g.fillRect(F.x, 0, F.w, 40);
    const left = b.aliveFoes().length + b.pending.reduce((a, p) => a + Object.values(p[2]).reduce((x, y) => x + y, 0), 0);
    UI.icon('ammo', LEFT_W + 20, 20, 20); T(G.sup.ammo, LEFT_W + 36, 9, {size: 20, color: G.sup.ammo > 15 ? C.gold : C.red, bold: true});
    T(`Enemigos: ${left}`, LEFT_W + 110, 11, {size: 18}); T(`Abatidos: ${b.killed}`, LEFT_W + 235, 11, {size: 18, color: C.green}); T(`Bajas: ${b.deadNames.length}`, LEFT_W + 360, 11, {size: 18, color: b.deadNames.length ? C.red : C.dim});
    T({libre: 'Fuego: libre', contenido: 'Fuego: contenido', alto: 'Fuego: alto'}[b.policy], LEFT_W + 470, 12, {size: 16, color: C.dim});
    if (b.phase === 'prep') T(`PREPARACIÓN  ${Math.max(0, b.prep).toFixed(0)}s`, W - 14, 11, {size: 18, color: C.gold, bold: true, align: 'right'});
    else T(`${Math.floor(b.fightTime / 60)}:${String(Math.floor(b.fightTime) % 60).padStart(2, '0')}`, W - 14, 11, {size: 18, bold: true, align: 'right'});
    if (this.paused) T('PAUSA', F.x + F.w / 2, 70, {size: 34, color: C.gold, bold: true, align: 'center', shadow: true});
    if (b.phase === 'prep') { UI.panel(F.x + F.w / 2 - 290, 48, 580, 52, '#1e1610', C.gold, 6, .85, 1); T('Cierra el círculo: pon a tus mejores tiradores (T) en las carretas por donde vendrá el ataque.', F.x + F.w / 2, 54, {size: 14, align: 'center'}); T('Las flechas rojas del borde indican por dónde llegará cada oleada.', F.x + F.w / 2, 75, {size: 14, color: C.gold, align: 'center'}); }
    let y = H - 24; for (const [t0, msg, col] of b.msgs.slice().reverse().slice(0, 6)) { const age = b.time - t0, a = age < 8 ? 1 : Math.max(0, 1 - (age - 8) * .25); if (a <= 0) continue; const w = UI.measure(msg, 15) + 12; g.fillStyle = `rgba(0,0,0,${.5 * a})`; g.fillRect(LEFT_W + 8, y - 1, w, 20); T(msg, LEFT_W + 14, y, {size: 15, color: col, alpha: a}); y -= 22; }
  }
  drawParley(g) {
    const F = this.field, cx = F.x + F.w / 2; g.fillStyle = 'rgba(0,0,0,.55)'; g.fillRect(F.x, 0, F.w, H);
    UI.panel(cx - 270, 190, 540, 330, C.panel, C.gold, 10); T('Parlamento a mitad de la batalla', cx, 204, {size: 24, color: C.gold, serif: true, align: 'center'});
    T('Bandera blanca e intérprete. Depende de su trato hacia ti, tu labia y el regalo.', cx, 236, {size: 13, color: C.dim, align: 'center'});
    for (const b of this.parleyButtons()) b.draw(); T('(espera 10 s de combate; si fracasan, no podrás intentarlo durante 28 s)', cx, 495, {size: 12, color: C.dim, align: 'center'});
  }
  drawResult(g) {
    const res = this.battle.result, F = this.field, cx = F.x + F.w / 2; g.fillStyle = 'rgba(0,0,0,.47)'; g.fillRect(0, 0, W, H);
    UI.panel(cx - 250, 220, 500, 230, C.panel, C.gold, 12);
    T({victoria: '¡VICTORIA!', huida: 'EL ENEMIGO SE RETIRA', paz: 'SE HA PACTADO LA PAZ', derrota: 'DERROTA'}[res.outcome], cx, 238, {size: 36, color: res.outcome === 'derrota' ? C.red : C.gold, bold: true, serif: true, align: 'center', shadow: true});
    T(`Enemigos abatidos: ${res.killed}/${res.total}`, cx, 298, {size: 20, align: 'center'}); T(`Colonos caídos: ${res.dead.length}  ·  Carretas perdidas: ${res.wagonsLost}`, cx, 326, {size: 20, align: 'center'}); T(`Munición gastada: ${res.ammoUsed}`, cx, 354, {size: 20, align: 'center'});
    if (this.endTimer > .8) T('Toca para continuar', cx, 410, {size: 17, color: C.dim, align: 'center'});
  }
}
S3.BattleScene = BattleScene;

// ============================================================== elegir sitio
const PREFS = {esposa: 'willamette', hannah: 'willamette', hija: 'willamette', abuelo: 'walla', ruth: 'walla', hijo: 'columbia', tomas: 'columbia', silas: 'columbia', mary: 'columbia'};
const moodOf = a => a < -30 ? 'hostiles' : a < -5 ? 'recelosos' : a < 20 ? 'cautos' : a < 50 ? 'amistosos' : 'aliados';
class SiteScene extends Scene {
  constructor(app) {
    super(app); this.g = app.game; this.keys = this.g.forcedWinter ? ['improvisado'] : Object.keys(D.SITES); const n = this.keys.length, w = 380, x0 = (W - (n * w + (n - 1) * 30)) / 2;
    this.cards = this.keys.map((k, i) => ({k, x: x0 + i * (w + 30), y: 150, w, h: 480}));
    this.btns = this.cards.map(c => new Button(c.x + 40, c.y + c.h - 52, c.w - 80, 44, 'Fundar aquí', () => this.choose(c.k), {size: 19, color: '#624a28'}));
  }
  choose(key) {
    const g = this.g, app = this.app;
    for (const role in PREFS) { const c = g.member(role); if (c && key !== 'improvisado') c.loyalty = Math.max(0, Math.min(100, c.loyalty + (PREFS[role] === key ? 4 : -1))); }
    const notes = key !== 'improvisado' ? g.travelToSite(key) : [];
    if (!g.living().length) { app.replace(new CV.scenes1.EndScene(app, 'El último tramo fue el definitivo', 'Los últimos supervivientes no resisten el tramo final.')); return; }
    app.replace(new SettlementScene(app, new CV.Settlement(g, key)));
    if (notes.length) app.push(new CV.scenes2.PromptScene(app, CV.info('El último tramo', notes.join('\n'), 'danger')));
  }
  handle(ev) { UI.handleButtons(this.btns, ev); }
  draw() {
    const g = this.app.ctx, G = this.g; g.drawImage(R.ground(W + 40, H + 40, 'valle', 71), -20, -20); UI.veil(0, 'rgba(12,9,6,.72)');
    if (G.forcedWinter) { T('El invierno os ha detenido', W / 2, 40, {size: 44, color: C.red, serif: true, bold: true, align: 'center', shadow: true}); T('No hay más camino: fundaréis donde estáis.', W / 2, 98, {size: 20, color: C.parch, align: 'center'}); }
    else { T('Bifurcación del Columbia', W / 2, 40, {size: 44, color: C.gold, serif: true, bold: true, align: 'center', shadow: true}); T('¿Dónde fundaréis vuestro hogar?', W / 2, 98, {size: 22, color: C.parch, align: 'center'}); T(`Quedan ${Math.max(0, D.FORCED_WINTER_DAY - G.day)} días para el invierno · ${G.living().length} colonos · comida ${Math.floor(G.sup.food)} lb`, W / 2, 126, {size: 16, color: C.dim, align: 'center'}); }
    for (const c of this.cards) {
      const k = c.k, site = k === 'improvisado' ? D.MAKESHIFT : D.SITES[k]; UI.panel(c.x, c.y, c.w, c.h, C.panel, C.gold, 12, undefined, 3);
      T(site.name, c.x + c.w / 2, c.y + 14, {size: k === 'improvisado' ? 20 : 26, color: C.gold, serif: true, bold: true, align: 'center'});
      const px = c.x + 20, py = c.y + 56, pw = c.w - 40; g.fillStyle = k === 'columbia' ? '#6e8278' : '#609a5a'; g.beginPath(); g.roundRect(px, py, pw, 90, 8); g.fill();
      if (k === 'willamette') for (let i = 0; i < 6; i++) { g.fillStyle = '#285a38'; g.beginPath(); g.moveTo(px + 30 + i * 52, py + 84); g.lineTo(px + 44 + i * 52, py + 16); g.lineTo(px + 58 + i * 52, py + 84); g.fill(); }
      else if (k === 'walla') { g.fillStyle = '#aa9664'; g.fillRect(px, py + 50, pw, 40); g.fillStyle = '#827864'; g.beginPath(); g.moveTo(px, py + 50); g.lineTo(px + 90, py + 14); g.lineTo(px + 180, py + 50); g.fill(); }
      else if (k === 'columbia') { g.fillStyle = '#4678b4'; g.fillRect(px, py + 54, pw, 36); g.fillStyle = '#6e645a'; g.beginPath(); g.moveTo(px, py + 54); g.lineTo(px + 60, py + 8); g.lineTo(px + 160, py + 54); g.fill(); }
      else { g.fillStyle = '#e6ecf4'; g.beginPath(); g.moveTo(px, py + 90); g.lineTo(px + 100, py + 20); g.lineTo(px + 200, py + 90); g.fill(); }
      UI.para(site.text, c.x + 20, c.y + 158, c.w - 40, 15, C.text, {maxLines: 5});
      let y = c.y + 262; for (const [l, key] of [['Fertilidad', 'fertility'], ['Defensa', 'defense'], ['Agua', 'water'], ['Comercio', 'trade']]) { T(l, c.x + 22, y, {size: 15, color: C.dim}); const v = site[key]; UI.bar(c.x + 130, y + 3, 200, 10, v / 10, v >= 7 ? C.green : v >= 5 ? C.gold : C.red); y += 24; }
      const nb = site.neighbor || G.currentTribe() || 'cayuse', t = D.TRIBES[nb]; T(`Vecinos: ${t.name} (${moodOf(G.tribes[nb].attitude)})`, c.x + 22, y + 6, {size: 16, color: t.color, bold: true});
      if (k !== 'improvisado') {
        const fans = Object.entries(PREFS).filter(([r, p]) => p === k && G.member(r)).map(([r]) => G.member(r).name.split(' ')[0]); if (fans.length) T('Lo prefieren: ' + fans.slice(0, 4).join(', '), c.x + 22, c.y + 408, {size: 12, color: C.parch});
        T(site.extra ? `+${site.extra} millas · ~${Math.ceil(site.extra / 17)} días` : 'Sin viaje adicional', c.x + 22, y + 32, {size: 15, color: C.dim});
      }
    }
    for (const b of this.btns) b.draw();
  }
}
S3.SiteScene = SiteScene;

// ============================================================== construir el asentamiento
class SettlementScene extends Scene {
  constructor(app, st) {
    super(app); this.g = app.game; this.st = st; this.msg = ''; this.msgCol = C.dim; this.t = 0;
    this.go = new Button(W - 400, H - 70, 360, 52, 'Sobrevivir el primer año →', () => this.goOn(), {size: 21, color: '#624a28'}); this.build();
  }
  resume() { this.build(); }
  build() { this.btns = Object.keys(D.BUILDINGS).map((k, i) => new Button(640, 120 + i * 62 + 6, 120, 42, this.st.built.includes(k) ? 'Hecho' : 'Construir', () => { const [ok, m] = this.st.build(k); this.msg = m; this.msgCol = ok ? C.green : C.red; this.build(); }, {enabled: this.st.canBuild(k)[0], size: 16})); }
  goOn() { const ch = this.st.simulate(Math.floor(this.g.rng.random() * 1e6)); this.app.clearSave(); this.app.replace(new ChronicleScene(this.app, this.st, ch)); }
  handle(ev) { if (UI.handleButtons([this.go], ev)) return; UI.handleButtons(this.btns, ev); }
  update(dt) { this.t += dt; }
  draw() {
    const g = this.app.ctx, G = this.g, st = this.st, site = st.site; g.drawImage(R.ground(W + 40, H + 40, 'valle', 81), -20, -20); UI.veil(0, 'rgba(12,9,6,.7)');
    T(site.name, 40, 22, {size: 38, color: C.gold, serif: true, bold: true}); T('Gastad lo que traéis: lo que no se construya hoy, no os protegerá en invierno.', 42, 74, {size: 16, color: C.dim});
    Object.entries(D.BUILDINGS).forEach(([k, b], i) => {
      const y = 120 + i * 62, built = st.built.includes(k); UI.panel(30, y, 740, 56, built ? '#3a3e28' : C.panel, built ? C.green : C.edge, 8);
      T(b.name, 46, y + 6, {size: 19, bold: true}); T(b.desc, 46, y + 31, {size: 13, color: C.dim});
      let x = 440; for (const [res, n] of Object.entries(b.cost)) { UI.icon(res, x + 12, y + 28, 18); T(n, x + 28, y + 17, {size: 16, color: G.sup[res] >= n ? C.green : C.red, bold: true}); x += 66; }
    });
    for (const b of this.btns) b.draw();
    UI.panel(800, 110, 440, 400, C.panel, C.edge, 10); const s = G.sup; T('Almacén', 820, 122, {size: 22, color: C.gold, serif: true, bold: true});
    let y = 158; [['food', 'Comida', Math.floor(s.food) + ' lb'], ['ammo', 'Munición', s.ammo], ['goods', 'Mercancías', s.goods], ['parts', 'Repuestos', s.parts], ['medicine', 'Medicinas', s.medicine], ['money', 'Dinero', '$' + Math.floor(s.money)]].forEach(([ic, nm, v]) => { UI.icon(ic, 836, y + 10, 20); T(nm, 860, y, {size: 17}); T(v, 1220, y, {size: 17, color: C.gold, align: 'right'}); y += 27; });
    y += 10; T(`Colonos: ${G.living().length}`, 820, y, {size: 17}); y += 28;
    const nb = site.neighbor || 'cayuse', t = D.TRIBES[nb], att = G.tribes[nb].attitude; T(`Vecinos: ${t.name} — ${moodOf(att)} (${att >= 0 ? '+' : ''}${Math.round(att)})`, 820, y, {size: 17, color: t.color, bold: true}); y += 34;
    for (const [l, k] of [['Fertilidad', 'fertility'], ['Defensa', 'defense'], ['Agua', 'water'], ['Comercio', 'trade']]) { T(l, 820, y, {size: 14, color: C.dim}); UI.bar(920, y + 3, 200, 9, Math.min(10, site[k]) / 10, C.green); y += 21; }
    UI.para(`Un invierno largo exige ~${G.living().length * 36 * 4} lb de comida. Sin cabañas morirá gente por el frío; sin pozo, por fiebres; sin tratado, quizá por incursiones.`, 820, y + 8, 400, 14, C.parch);
    if (this.msg) T(this.msg, 40, H - 60, {size: 18, color: this.msgCol}); this.go.draw();
  }
}
S3.SettlementScene = SettlementScene;

// ============================================================== crónica final
class ChronicleScene extends Scene {
  constructor(app, st, ch) {
    super(app); this.g = app.game; this.st = st; this.ch = ch; this.t = 0; this.shown = 1; this.phase = 'story'; this.saved = false;
    this.btns = [new Button(W / 2 - 270, H - 76, 250, 50, 'Volver al menú', () => { app.travel = null; app.replace(new CV.scenes1.TitleScene(app)); }, {size: 20}),
      new Button(W / 2 + 20, H - 76, 250, 50, 'Nueva partida', () => { app.travel = null; app.replace(new CV.scenes1.TitleScene(app)); app.push(new CV.scenes1.SetupScene(app)); }, {size: 20, color: '#624a28'})];
    this.skip = new Button(W - 250, H - 60, 220, 44, 'Ver el resultado →', () => this.toResult(), {size: 17});
  }
  toResult() { if (this.phase === 'story') { this.shown = this.ch.lines.length; this.phase = 'result'; this.save(); } }
  save() { if (!this.saved) { this.saved = true; this.app.addScore(this.g.leaderName, this.ch.score, this.ch.rank); CV.sfx.play('win', .7); } }
  handle(ev) {
    if (this.phase === 'result') UI.handleButtons(this.btns, ev);
    else { if (UI.handleButtons([this.skip], ev)) return; if (ev.type === 'down') this.shown = Math.min(this.ch.lines.length, this.shown + 1); }
  }
  update(dt) { this.t += dt; if (this.phase === 'story') { this.shown = Math.max(this.shown, Math.min(this.ch.lines.length, Math.floor(this.t / 1.3))); if (this.shown >= this.ch.lines.length && this.t > this.ch.lines.length * 1.3 + 1.5) { this.phase = 'result'; this.save(); } } }
  draw() {
    const g = this.app.ctx, G = this.g, ch = this.ch; g.drawImage(R.ground(W + 40, H + 40, 'valle', 91), -20, -20); UI.veil(0, 'rgba(12,9,6,.78)');
    if (this.phase === 'story') {
      T('Crónica del primer año', W / 2, 30, {size: 42, color: C.gold, serif: true, bold: true, align: 'center'}); UI.panel(180, 100, W - 360, H - 190, '#e2d0a4', C.edge, 12, undefined, 3);
      let y = 124; for (const ln of ch.lines.slice(0, this.shown)) { y = UI.para(ln, 210, y, W - 420, 18, C.ink, {gap: 3}) + 8; if (y > H - 120) break; }
      this.skip.draw(); return;
    }
    T(ch.rank.toUpperCase(), W / 2, 24, {size: 50, color: ch.survivors ? C.gold : C.red, serif: true, bold: true, align: 'center', shadow: true});
    T(`${ch.survivors} de ${G.colonists.length} colonos pasaron el primer año en ${this.st.site.name}`, W / 2, 90, {size: 21, color: C.parch, align: 'center'});
    UI.panel(60, 130, 560, 440, C.panel, C.edge, 10); T('Puntuación', 80, 142, {size: 24, color: C.gold, serif: true, bold: true});
    let y = 182; for (const [l, v] of ch.breakdown) { T(l, 84, y, {size: 18}); T(v, 590, y, {size: 18, color: C.gold, align: 'right'}); y += 30; }
    g.strokeStyle = C.edge; g.lineWidth = 2; g.beginPath(); g.moveTo(84, y + 4); g.lineTo(590, y + 4); g.stroke(); T('TOTAL', 84, y + 14, {size: 26, color: C.gold, bold: true}); T(ch.score, 590, y + 14, {size: 26, color: C.gold, bold: true, align: 'right'});
    UI.panel(650, 130, 570, 440, C.panel, C.edge, 10); T('La compañía', 670, 142, {size: 24, color: C.gold, serif: true, bold: true});
    y = 182; for (const c of G.colonists) { R.drawPerson(g, 690, y + 11, c.group, c.cid, 1.1, {dead: !c.alive}); T(c.name + (c.isLeader ? '  (líder)' : ''), 710, y, {size: 16, color: c.alive ? C.text : '#8c6e64'}); T(c.alive ? 'vive' : '† ' + c.cause, 1200, y, {size: 15, color: c.alive ? C.green : C.dim, align: 'right'}); y += 24; if (y > 550) break; }
    T(`Edificios: ${this.st.built.length} · Días de viaje: ${G.day} · Millas: ${Math.floor(G.mile)}`, W / 2, 590, {size: 16, color: C.dim, align: 'center'});
    for (const b of this.btns) b.draw();
  }
}
S3.ChronicleScene = ChronicleScene;
})(globalThis.CV = globalThis.CV || {});
