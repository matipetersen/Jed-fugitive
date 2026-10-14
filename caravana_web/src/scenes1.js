/* Escenas de menú: título, instrucciones, preparación, origen, reclutamiento, tienda y final. */
(function (CV) {
'use strict';
const UI = CV.ui, C = UI.C, D = CV.data, R = CV.render, W = UI.W, H = UI.H;
const Scene = UI.Scene, Button = UI.Button, T = (...a) => UI.text(...a);
const S1 = CV.scenes1 = {};
let ctx = null; const g2 = () => (ctx = UI.app.ctx);
CV.nameInput = {
  el: null,
  show(x, y, w, h, value, onChange) {
    if (!this.el) this.el = document.getElementById('nameInput');
    const cv = UI.app.canvas, r = cv.getBoundingClientRect(), k = r.width / W, e = this.el;
    e.style.display = 'block'; e.style.left = (r.left + x * k + window.scrollX) + 'px'; e.style.top = (r.top + y * k + window.scrollY) + 'px';
    e.style.width = (w * k) + 'px'; e.style.height = (h * k) + 'px'; e.style.fontSize = (22 * k) + 'px';
    if (e.value !== value && document.activeElement !== e) e.value = value;
    e.oninput = () => onChange(e.value.slice(0, 16));
  },
  focus() { if (this.el) { this.el.focus(); this.el.select(); } },
  hide() { if (!this.el) this.el = document.getElementById('nameInput'); if (this.el) { this.el.style.display = 'none'; this.el.blur(); } },
};
function backdrop(terrain, seed, veil) {
  const g = UI.app.ctx; g.drawImage(R.ground(W + 40, H + 40, terrain, seed), -20, -20); UI.veil(0, `rgba(14,10,6,${veil === undefined ? .78 : veil})`);
}
S1.backdrop = backdrop;

// ============================================================== título
class TitleScene extends Scene {
  constructor(app) {
    super(app); this.t = 0; this.parts = new R.Particles(); this.cx = 880; this.cy = 372; this.R = 200;
    this.riders = Array.from({length: 7}, () => [Math.random() * 6.28, 330 + Math.random() * 110, (Math.random() < .5 ? -1 : 1) * (.07 + Math.random() * .07)]);
    this.build();
  }
  build() {
    const x = 70, y = 330, w = 300; this.btns = [new Button(x, y, w, 46, 'Nueva partida', () => this.app.push(new SetupScene(this.app)), {size: 22})];
    let yy = y + 56;
    if (this.app.saveExists()) { this.btns.push(new Button(x, yy, w, 46, 'Continuar viaje', () => this.cont(), {size: 22})); yy += 56; }
    this.btns.push(new Button(x, yy, w, 46, 'Cómo se juega', () => this.app.push(new HowToScene(this.app)), {size: 22}));
  }
  resume() { this.build(); }
  cont() { const g = this.app.loadSave(); if (!g) return; this.app.game = g; this.app.replace(new CV.scenes2.TravelScene(this.app)); }
  handle(ev) { CV.sfx.unlock(); UI.handleButtons(this.btns, ev); }
  update(dt) { this.t += dt; if (Math.random() < .5) this.parts.add('ember', 0, 0, 1); this.parts.update(dt); for (const r of this.riders) r[0] += r[2] * dt; }
  draw() {
    const g = this.app.ctx, cx = this.cx, cy = this.cy;
    g.drawImage(R.ground(W + 40, H + 40, 'pradera', 3), -20, -20);
    const n = 9;
    for (let i = 0; i < n; i++) { const a = -Math.PI / 2 + Math.PI * 2 * i / n; R.drawWagon(g, cx + Math.cos(a) * this.R, cy + Math.sin(a) * this.R, a + Math.PI / 2, i % 3 ? 1 : .6, i % 4 === 0 ? 1 : 0, i === 2, false, i % 2 === 0, false, 1.35); }
    for (const [tx, ty] of [[-60, -50], [70, -30], [-30, 70], [60, 60]]) R.drawTent(g, cx + tx, cy + ty, 1.6);
    R.drawFire(g, cx, cy, this.t, 2);
    for (const [a, r, w] of this.riders) R.drawFoe(g, {kind: 'jinete', face: a + Math.PI / 2 * (w > 0 ? 1 : -1)}, cx + Math.cos(a) * r, cy + Math.sin(a) * r, 1.9, '#463c46');
    this.parts.draw(g, {x: x => cx + x, y: y => cy + y, s: 1});
    nightOverlay(g, [[cx, cy, 520 * (1 + .03 * Math.sin(this.t * 9))]], 'rgba(5,8,26,.8)');
    const gr = g.createLinearGradient(0, 0, 520, 0); gr.addColorStop(0, 'rgba(10,7,5,.92)'); gr.addColorStop(1, 'rgba(10,7,5,0)'); g.fillStyle = gr; g.fillRect(0, 0, 520, H);
    T('LA CARAVANA', 64, 82, {size: 62, color: C.gold, bold: true, serif: true, shadow: true});
    T('Hacia el Oeste · 1848', 68, 156, {size: 26, color: C.parch, serif: true, shadow: true});
    UI.para('2.000 millas. Carretas en círculo. Comerciar, parlamentar… y resistir cuando todo lo demás falla.', 68, 205, 330, 17, C.dim);
    for (const b of this.btns) b.draw();
    const sc = this.app.scores();
    if (sc.length) { T('Mejores crónicas', 70, 592, {size: 15, color: C.gold, bold: true}); sc.slice(0, 3).forEach((s, i) => T(`${i + 1}. ${s.name} — ${s.score} (${s.rank})`, 70, 616 + i * 20, {size: 14, color: C.dim})); }
  }
}
function nightOverlay(g, lights, color) {
  const o = nightOverlay.c || (nightOverlay.c = R.mk(W, H)), og = o.getContext('2d');
  og.globalCompositeOperation = 'source-over'; og.clearRect(0, 0, W, H); og.fillStyle = color; og.fillRect(0, 0, W, H);
  og.globalCompositeOperation = 'destination-out';
  for (const [x, y, r] of lights) { const gr = og.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(.35, 'rgba(0,0,0,.7)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); og.fillStyle = gr; og.fillRect(x - r, y - r, r * 2, r * 2); }
  g.drawImage(o, 0, 0);
}
S1.nightOverlay = nightOverlay;

class HowToScene extends Scene {
  constructor(app) { super(app); this.overlay = true; this.page = 0; this.btns = [
    new Button(400, 560, 120, 40, 'Anterior', () => this.page = Math.max(0, this.page - 1)), new Button(760, 560, 120, 40, 'Siguiente', () => this.page = Math.min(this.PAGES.length - 1, this.page + 1)),
    new Button(570, 560, 140, 40, 'Cerrar', () => this.app.pop())]; }
  get PAGES() { return [
    ['El viaje', 'Guías a un grupo de colonos 1.950 millas desde Independence hasta el Columbia, con carretas, bueyes y provisiones. Cada día se avanza, se come y se enferma. Controla el ritmo, las raciones y la guardia nocturna. Compra y vende en los fuertes, caza y descansa en el campamento. Si el invierno os alcanza (15 de diciembre), tendréis que fundar el asentamiento donde estéis.'],
    ['Familia, seguidores y cutscenes', 'Antes de partir eliges por qué os vais (motivo) y qué pretendéis al llegar (propósito); y reclutas hasta cuatro seguidores en la plaza de Independence, cada uno con su carácter. Por el camino, escenas con tu familia plantean decisiones: su lealtad cambia la moral, la puntería y la diplomacia. Un Director de IA vigila la presión que soportáis y ajusta el ritmo de ataques y eventos (tecla F3 muestra su panel).'],
    ['Diplomacia y comercio', 'Cada territorio tiene su pueblo: Pawnee, Cheyenne, Lakota, Shoshone, Cayuse. Su trato hacia ti (-100 a 100) decide si te dejan pasar o te atacan. Saluda con respeto, haz regalos (lo que más valoran vale más), pacta un paso seguro, contrata un guía, o intercambia por bueyes, medicinas y comida. Dar munición gana amistad, pero los arma. Cada muerte que causes se recuerda.'],
    ['Defensa 360°', 'Cuando falla la diplomacia, se cierra el círculo. Asigna tiradores (T) y ayudantes (A) a cada carreta (toca un colono y luego la plaza), marca objetivos tocando un enemigo, controla el fuego (libre, contenido, alto) para ahorrar balas, levanta barricadas en los huecos tocando la carreta caída, y si hace falta, parlamenta en plena batalla. Las flechas rojas del borde avisan por dónde llega cada oleada. De noche, los faroles son vida.'],
    ['Teclado (opcional)', 'Espacio: pausa · 1/2/3: velocidad · Enter: empezar ya · A: auto-asignar · F: política de fuego · P: parlamento · M: fundir utensilios en balas · F3: panel del Director. Todo se puede hacer también tocando la pantalla.'],
  ]; }
  handle(ev) { if (UI.handleButtons(this.btns, ev)) return; if (ev.type === 'key' && ev.key === 'Escape') this.app.pop(); }
  draw() {
    UI.veil(.66); UI.panel(300, 110, 680, 500, C.panel, C.gold, 12, undefined, 3);
    const [t, b] = this.PAGES[this.page]; T(t, 640, 130, {size: 32, color: C.gold, serif: true, bold: true, align: 'center'});
    UI.para(b, 340, 190, 600, 19, C.text, {gap: 5}); T(`${this.page + 1}/${this.PAGES.length}`, 640, 536, {size: 15, color: C.dim, align: 'center'});
    for (const bt of this.btns) bt.draw();
  }
}
S1.HowToScene = HowToScene;

// ============================================================== preparación: oficio, nombre, dificultad
class SetupScene extends Scene {
  constructor(app) {
    super(app); this.name = 'Jed'; this.prof = 'granjero'; this.diff = 'normal'; this.t = 0;
    this.go = new Button(W - 360, H - 76, 300, 50, 'Elegir vuestra historia →', () => this.next(), {size: 21, color: '#624a28'});
    this.back = new Button(60, H - 76, 160, 50, 'Volver', () => this.app.pop(), {size: 19});
    this.rnd = new Button(230, 168, 380, 28, 'Otro nombre', () => { const N = ['Jed', 'Abel', 'Nora', 'Caleb', 'Lydia', 'Gideon', 'Tess', 'Amos', 'Ada', 'Isaac']; this.name = N[(N.indexOf(this.name) + 1) % N.length]; }, {size: 14});
  }
  next() {
    CV.nameInput.hide();
    const g = CV.Game.create(this.name.trim() || 'Jed', this.prof, Math.floor(Math.random() * 1e6) + 1, this.diff);
    this.app.game = g; this.app.replace(new OriginScene(this.app));
  }
  card(i) { return {x: 60 + (i % 3) * 400, y: 250 + Math.floor(i / 3) * 190, w: 380, h: 170}; }
  handle(ev) {
    if (UI.handleButtons([this.go, this.back, this.rnd], ev)) return;
    if (ev.type === 'down') {
      if (ev.x >= 230 && ev.x <= 610 && ev.y >= 120 && ev.y <= 164) { CV.nameInput.focus(); return; }
      Object.keys(D.PROFESSIONS).forEach((k, i) => { const c = this.card(i); if (ev.x >= c.x && ev.x <= c.x + c.w && ev.y >= c.y && ev.y <= c.y + c.h) this.prof = k; });
      Object.keys(D.DIFFICULTY).forEach((k, i) => { const x = 690 + i * 180; if (ev.x >= x && ev.x <= x + 170 && ev.y >= 120 && ev.y <= 164) this.diff = k; });
    }
  }
  update(dt) { this.t += dt; CV.nameInput.show(236, 124, 368, 36, this.name, v => { this.name = v; }); }
  leave() { CV.nameInput.hide(); }
  draw() {
    backdrop('pradera', 11, .75);
    T('El líder de la caravana', 60, 36, {size: 40, color: C.gold, bold: true, serif: true});
    T('Tu nombre:', 60, 132, {size: 20}); UI.panel(230, 120, 380, 44, '#1e1610', C.edge, 6);
    this.rnd.draw();
    T('Dificultad:', 660, 100, {size: 15, color: C.dim});
    Object.entries(D.DIFFICULTY).forEach(([k, d], i) => { const sel = k === this.diff, x = 690 + i * 180; UI.panel(x, 120, 170, 44, sel ? '#543a24' : C.panel, sel ? C.gold : C.edge, 8, undefined, sel ? 3 : 2); T(d.name, x + 85, 142, {size: 19, color: sel ? C.gold : C.text, bold: sel, align: 'center', base: 'middle'}); });
    T(D.DIFFICULTY[this.diff].desc, 690, 170, {size: 14, color: C.dim});
    T('Elige tu oficio:', 60, 206, {size: 22, color: C.parch, serif: true});
    Object.entries(D.PROFESSIONS).forEach(([k, p], i) => {
      const c = this.card(i), sel = k === this.prof; UI.panel(c.x, c.y, c.w, c.h, sel ? '#503a24' : C.panel, sel ? C.gold : C.edge, 10, undefined, sel ? 3 : 2);
      T(p.name, c.x + 16, c.y + 12, {size: 26, color: sel ? C.gold : C.text, serif: true, bold: true}); T('$' + p.money, c.x + c.w - 16, c.y + 16, {size: 22, color: C.gold, align: 'right'});
      UI.para(p.desc, c.x + 16, c.y + 52, c.w - 32, 16, sel ? C.text : C.dim, {maxLines: 3});
      [['Puntería', 'shoot'], ['Medicina', 'medic'], ['Construir', 'build'], ['Labia', 'talk'], ['Caza', 'hunt']].forEach(([lb, key], j) => { const x = c.x + 16 + j * 70, v = p.skills[key]; T(lb, x, c.y + 112, {size: 11, color: C.dim}); UI.bar(x, c.y + 130, 62, 7, v / 10, v >= 7 ? C.green : v >= 4 ? C.gold : C.red); });
    });
    const c = this.card(5); UI.panel(c.x, c.y, c.w, c.h, '#241c14', C.edge, 10);
    T('Tu compañía', c.x + 16, c.y + 12, {size: 22, color: C.parch, serif: true, bold: true});
    UI.para('Dos familias y cuatro peones: 14 almas, siete carretas y catorce bueyes. Los niños y ancianos no disparan, pero recargan, curan y apagan fuegos. Cada colono tiene sus propias habilidades.', c.x + 16, c.y + 48, c.w - 32, 15, C.dim);
    this.go.draw(); this.back.draw();
  }
}
S1.SetupScene = SetupScene;
const _setupLeave = SetupScene.prototype;

// ============================================================== motivo y propósito
class OriginScene extends Scene {
  constructor(app) { super(app); this.g = app.game; this.motive = 'tierra'; this.purpose = 'granja'; this.go = new Button(W - 400, H - 70, 360, 52, 'Reclutar seguidores →', () => { CV.story.applyOrigin(this.g, this.motive, this.purpose); this.app.replace(new RecruitScene(this.app)); }, {size: 21, color: '#624a28'}); }
  rects(row) { const w = 295, gap = 20, x0 = (W - (4 * w + 3 * gap)) / 2, y = row === 0 ? 118 : 388, h = row === 0 ? 205 : 175; return [0, 1, 2, 3].map(i => ({x: x0 + i * (w + gap), y, w, h})); }
  handle(ev) {
    if (UI.handleButtons([this.go], ev)) return;
    if (ev.type === 'down') {
      Object.keys(CV.story.MOTIVES).forEach((k, i) => { const r = this.rects(0)[i]; if (ev.x >= r.x && ev.x <= r.x + r.w && ev.y >= r.y && ev.y <= r.y + r.h) this.motive = k; });
      Object.keys(CV.story.PURPOSES).forEach((k, i) => { const r = this.rects(1)[i]; if (ev.x >= r.x && ev.x <= r.x + r.w && ev.y >= r.y && ev.y <= r.y + r.h) this.purpose = k; });
    }
  }
  cards(items, rects, sel, perk) {
    Object.entries(items).forEach(([k, d], i) => { const r = rects[i], s = k === sel; UI.panel(r.x, r.y, r.w, r.h, s ? '#543e26' : C.panel, s ? C.gold : C.edge, 10, undefined, s ? 3 : 2);
      T(d.name, r.x + 14, r.y + 10, {size: 21, color: s ? C.gold : C.text, serif: true, bold: true}); UI.para(d.text, r.x + 14, r.y + 44, r.w - 28, 14, s ? C.text : C.dim, {maxLines: 5, gap: 2}); UI.para(d.perks, r.x + 14, r.y + r.h - 52, r.w - 28, 13, perk, {maxLines: 3, gap: 1}); });
  }
  draw() {
    backdrop('pradera', 17, .78);
    T('Vuestra historia', 40, 20, {size: 40, color: C.gold, serif: true, bold: true}); T('¿Por qué dejáis todo atrás?', 44, 82, {size: 21, color: C.parch, serif: true});
    this.cards(CV.story.MOTIVES, this.rects(0), this.motive, C.green);
    T('¿Qué pretendéis al llegar?', 44, 352, {size: 21, color: C.parch, serif: true});
    this.cards(CV.story.PURPOSES, this.rects(1), this.purpose, C.blue);
    T('El motivo cambia cómo parte la caravana; el propósito decide qué cuenta como éxito al fundar.', 44, H - 62, {size: 14, color: C.dim});
    T(`Compañía: ${this.g.leaderName} y su familia.`, 44, H - 40, {size: 14, color: C.dim});
    this.go.draw();
  }
}
S1.OriginScene = OriginScene;

// ============================================================== reclutar seguidores
class RecruitScene extends Scene {
  constructor(app) {
    super(app); this.g = app.game; this.r = new CV.story.Recruitment(this.g); this.t = 0; this.msg = 'Independence al amanecer. Varios viajeros sin carreta esperan en la plaza.'; this.msgCol = C.parch;
    this.done = new Button(W - 360, H - 62, 330, 48, 'Ir a la tienda →', () => this.app.replace(new ShopScene(this.app, {name: 'Independence, Misuri', mult: 1}, true)), {size: 20, color: '#624a28'});
    this.build();
  }
  cards() { const w = 400, h = 238, gap = 16, x0 = (W - (3 * w + 2 * gap)) / 2; return this.r.cands.map((c, i) => ({x: x0 + (i % 3) * (w + gap), y: 92 + Math.floor(i / 3) * (h + gap), w, h})); }
  build() {
    this.btns = []; const r = this.r;
    this.cards().forEach((rc, i) => {
      const c = r.cands[i], tpl = c.tpl, free = c.state === 'libre', [okk] = r.canAct(i);
      this.btns.push(new Button(rc.x + 130, rc.y + rc.h - 48, 120, 38, `Persuadir ${Math.round(r.chance(i) * 100)}%`, () => this.act(i, false), {enabled: free && okk && r.approaches > 0, size: 14}));
      this.btns.push(new Button(rc.x + 258, rc.y + rc.h - 48, 130, 38, tpl.fee > 0 ? `Contratar $${tpl.fee}` : 'Se une gratis', () => this.act(i, true), {enabled: free && okk && tpl.fee <= this.g.sup.money, size: 14}));
    });
  }
  act(i, hire) { const [ok, msg] = hire ? this.r.hire(i) : this.r.persuade(i); this.msg = msg; this.msgCol = ok ? C.green : C.red; this.build(); }
  handle(ev) { if (UI.handleButtons([this.done], ev)) return; UI.handleButtons(this.btns, ev); }
  update(dt) { this.t += dt; }
  draw() {
    const g = this.app.ctx, G = this.g, r = this.r;
    S1.backdrop('pradera', 18, .75);
    T('Reclutar seguidores', 40, 16, {size: 38, color: C.gold, serif: true, bold: true});
    UI.icon('money', W - 340, 36, 26); T('$' + Math.floor(G.sup.money).toLocaleString('es'), W - 318, 22, {size: 26, color: C.gold, bold: true});
    T(`Compañía ${G.living().length}/${CV.story.MAX_PARTY}`, W - 220, 16, {size: 18}); T(`Conversaciones: ${r.approaches}`, W - 220, 42, {size: 16, color: r.approaches ? C.gold : C.red});
    this.cards().forEach((rc, i) => {
      const c = r.cands[i], tpl = c.tpl, st = c.state;
      UI.panel(rc.x, rc.y, rc.w, rc.h, st === 'unido' ? '#3c4228' : st === 'rechazo' ? '#3e221e' : C.panel, st === 'unido' ? C.green : st === 'rechazo' ? C.red : C.edge, 10);
      g.save(); g.beginPath(); g.rect(rc.x + 6, rc.y + 10, 120, 200); g.clip(); R.drawPortrait(g, rc.x + 66, rc.y + 206, 230, tpl.id, tpl.groups[0], i + 3, st === 'unido' ? 'alegre' : st === 'rechazo' ? 'triste' : 'neutral', false, this.t + i, st === 'rechazo', false); g.restore();
      const gem = tpl.id === 'gemelos', nm = gem ? tpl.names.join(' y ') : tpl.names[0], multi = tpl.names.length > 1 && !gem;
      T(nm, rc.x + 130, rc.y + 10, {size: gem ? 15 : 19, color: C.gold, serif: true, bold: true});
      if (multi) T('y su hijo/a', rc.x + 130, rc.y + 32, {size: 12, color: C.dim});
      T(`${D.ROLE_NAMES[tpl.id] || ''} · ${tpl.trait}`, rc.x + 130, rc.y + 32 + (multi ? 12 : 0), {size: 13, color: C.parch});
      UI.para(tpl.pitch, rc.x + 130, rc.y + 62, rc.w - 142, 13, C.text, {maxLines: 3, gap: 1});
      [['Punt.', 'shoot'], ['Med.', 'medic'], ['Const.', 'build'], ['Labia', 'talk'], ['Caza', 'hunt']].forEach(([lb, key], j) => { const x = rc.x + 130 + (j % 3) * 88, y = rc.y + 142 + Math.floor(j / 3) * 22, v = tpl.skills[key]; T(lb, x, y, {size: 11, color: C.dim}); UI.bar(x + 32, y + 3, 48, 7, v / 10, v >= 7 ? C.green : v >= 4 ? C.gold : C.red); });
      if (st !== 'libre') T(st === 'unido' ? 'SE UNE' : 'RECHAZÓ', rc.x + rc.w - 14, rc.y + 10, {size: 15, color: st === 'unido' ? C.green : C.red, bold: true, align: 'right'});
      const tags = {land: 'tierra', faith: 'fe', gold: 'fortuna', escape: 'huida'};
      T('Le mueve: ' + tpl.likes.map(t => tags[t]).sort().join(', '), rc.x + 130, rc.y + 120, {size: 11, color: C.dim});
    });
    for (const b of this.btns) b.draw();
    UI.para(this.msg, 40, H - 62, W - 440, 16, this.msgCol, {maxLines: 2}); this.done.draw();
  }
}
S1.RecruitScene = RecruitScene;

// ============================================================== tienda y trueque
class ShopScene extends Scene {
  constructor(app, spec, initial) {
    super(app); this.spec = spec; this.initial = !!initial; this.g = app.game; this.msg = ''; this.msgCol = C.dim; this.bulk = false; this.used = [];
    this.offers = spec.barterTribe ? CV.tribeOffers(this.g, spec.barterTribe) : [];
    this.items = ['food', 'ammo', 'goods', 'parts', 'medicine', 'oxen', 'wagon', 'cannon'].filter(k => !(k === 'cannon' && !spec.cannon) && !(k === 'wagon' && spec.wagons === false));
    this.bulkBtn = new Button(620, 30, 220, 40, '', () => { this.bulk = !this.bulk; }, {size: 16});
    this.doneBtn = new Button(W - 330, H - 74, 270, 50, this.initial ? '¡Partir hacia Oregón!' : 'Terminar', () => this.finish(), {size: 21, color: '#624a28'});
    this.build();
  }
  mult() { return this.spec.mult; }
  qty() { return this.bulk ? 5 : 1; }
  build() {
    this.btns = [];
    if (this.spec.barterTribe) this.offers.forEach((o, i) => this.btns.push(new Button(700, 142 + i * 84, 140, 46, 'Aceptar', () => { const [ok, m] = CV.applyOffer(this.g, o); if (ok) this.used.push(i); this.msg = m; this.msgCol = ok ? C.green : C.red; this.build(); }, {enabled: !this.used.includes(i) && this.g.sup[o.take[0]] >= o.take[1], size: 18})));
    else this.items.forEach((k, i) => {
      const y = 120 + i * 60;
      this.btns.push(new Button(620, y + 8, 100, 40, 'Comprar', () => { const [ok, m] = this.g.buy(k, this.mult(), this.qty()); this.msg = m; this.msgCol = ok ? C.green : C.red; if (ok) CV.sfx.play('coin', .6, .05); }, {size: 17}));
      this.btns.push(new Button(730, y + 8, 100, 40, 'Vender', () => { const [ok, m] = this.g.sell(k, this.mult(), this.qty()); this.msg = m; this.msgCol = ok ? C.green : C.red; }, {size: 17}));
    });
  }
  finish() { if (this.initial) this.app.replace(new CV.scenes2.TravelScene(this.app, true)); else this.app.pop(); }
  handle(ev) {
    if (UI.handleButtons([this.doneBtn], ev)) return;
    if (!this.spec.barterTribe && UI.handleButtons([this.bulkBtn], ev)) return;
    UI.handleButtons(this.btns, ev);
  }
  have(k) { const s = this.g.sup; return {food: `Tienes ${Math.floor(s.food)} lb`, ammo: `Tienes ${s.ammo} balas`, goods: `Tienes ${s.goods}`, parts: `Tienes ${s.parts}`, medicine: `Tienes ${s.medicine}`, oxen: `Tienes ${s.oxen} bueyes`, wagon: `Tienes ${this.g.wagons.length} carretas`, cannon: `En almacén: ${this.g.cannonStock}`}[k]; }
  draw() {
    const g = this.g, s = g.sup;
    S1.backdrop(this.initial ? 'pradera' : g.terrain(), 21, .8);
    if (this.spec.barterTribe) {
      const t = D.TRIBES[this.spec.barterTribe]; T(`Trueque con los ${t.name}`, 50, 36, {size: 38, color: C.gold, serif: true, bold: true});
      T(`Valoran sobre todo: ${{food: 'comida', goods: 'mercancías', ammo: 'munición', medicine: 'medicinas'}[t.wants]}. Cada trato se puede aceptar una vez.`, 52, 86, {size: 17, color: C.dim});
      this.offers.forEach((o, i) => { const y = 130 + i * 84; UI.panel(50, y, 800, 74, C.panel, C.edge, 8); UI.para(o.text, 70, y + 14, 600, 19, C.text); T(`Recibes ${o.give[1]} · Entregas ${o.take[1]}`, 70, y + 46, {size: 14, color: C.dim}); if (this.used.includes(i)) T('Hecho', 780, y + 26, {size: 18, color: C.green, align: 'right'}); });
    } else {
      T(this.spec.name, 50, 30, {size: 38, color: C.gold, serif: true, bold: true});
      T(this.spec.mult > 1.05 ? 'Precios con recargo por la distancia' : 'Los precios más baratos de todo el camino', 52, 80, {size: 16, color: C.dim});
      this.bulkBtn.label = this.bulk ? 'Cantidad: ×5' : 'Cantidad: ×1'; this.bulkBtn.selected = this.bulk; this.bulkBtn.draw();
      this.items.forEach((k, i) => { const y = 120 + i * 60, it = D.ITEMS[k]; UI.panel(50, y, 790, 54, C.panel, C.edge, 8); UI.icon(k, 82, y + 24, 28);
        T(it.name, 110, y + 6, {size: 22, bold: true}); T(`${it.unit} · $${Math.round(g.price(k, this.mult()))} (vende a $${Math.round(g.price(k, this.mult(), true))})`, 110, y + 32, {size: 14, color: C.dim}); T(this.have(k), 440, y + 16, {size: 17, color: C.gold}); });
    }
    for (const b of this.btns) b.draw();
    const x = 880; UI.panel(x, 30, 360, H - 130, C.panel, C.gold, 10); UI.icon('money', x + 30, 62, 30); T('$' + Math.floor(s.money).toLocaleString('es'), x + 56, 44, {size: 32, color: C.gold, bold: true});
    let y = 100; [['food', 'Comida', Math.floor(s.food) + ' lb'], ['ammo', 'Munición', s.ammo], ['goods', 'Mercancías', s.goods], ['parts', 'Repuestos', s.parts], ['medicine', 'Medicinas', s.medicine], ['oxen', 'Bueyes', s.oxen], ['wagon', 'Carretas', g.wagons.length]].forEach(([ico, nm, v]) => { UI.icon(ico, x + 28, y + 11, 20); T(nm, x + 54, y, {size: 17}); T(String(v), x + 330, y, {size: 17, color: C.gold, align: 'right'}); y += 27; });
    y += 12; const days = s.food / Math.max(.1, g.dailyNeed()), need = 2 * g.wagons.length;
    const adv = [[`Comida para unos ${Math.floor(days)} días a raciones normales. El viaje dura 110–160.`, days > 90 ? C.green : days > 45 ? C.gold : C.red], [`Bueyes: ${s.oxen}/${need}. Con menos, las carretas se frenan.`, s.oxen >= need ? C.green : C.red], ['Munición: un combate grande gasta 50–100 balas.', s.ammo >= 100 ? C.green : s.ammo >= 40 ? C.gold : C.red]];
    if (s.goods < 12) adv.push(['Mercancías: son tus regalos y tributos. Sin ellas, la diplomacia es imposible.', s.goods >= 6 ? C.gold : C.red]);
    if (g.mile > 1000) adv.push(['Guarda repuestos, mercancías y comida: el asentamiento los necesita para construir.', C.parch]);
    for (const [t, col] of adv) y = UI.para(t, x + 16, y, 330, 15, col, {gap: 2}) + 6;
    this.doneBtn.draw(); if (this.msg) T(this.msg, 50, H - 60, {size: 18, color: this.msgCol});
  }
}
S1.ShopScene = ShopScene;

// ============================================================== final de partida (derrota)
class EndScene extends Scene {
  constructor(app, title, body) {
    super(app); this.title = title; this.body = body; app.clearSave();
    this.btns = [new Button(W / 2 - 270, H - 90, 250, 50, 'Volver al menú', () => { app.travel = null; app.replace(new TitleScene(app)); }, {size: 20}),
      new Button(W / 2 + 20, H - 90, 250, 50, 'Nueva partida', () => { app.travel = null; app.replace(new TitleScene(app)); app.push(new SetupScene(app)); }, {size: 20, color: '#624a28'})];
  }
  handle(ev) { UI.handleButtons(this.btns, ev); }
  draw() {
    S1.backdrop('estepa', 5, .8); const g = this.app.game;
    T(this.title, W / 2, 50, {size: 52, color: C.red, serif: true, bold: true, align: 'center', shadow: true});
    let y = UI.para(this.body, W / 2 - 360, 130, 720, 20, C.text, {gap: 5});
    if (g) { y += 14; T(`${g.dateText()} · ${Math.floor(g.mile)} millas recorridas · ${g.day} días`, W / 2, y, {size: 18, color: C.parch, align: 'center'}); y += 40;
      T('Quienes no llegaron', W / 2, y, {size: 22, color: C.gold, serif: true, align: 'center'}); y += 36;
      g.dead().slice(0, 16).forEach((c, i) => T(`† ${c.name} — ${c.cause}`, W / 2 - 340 + (i % 2) * 360, y + Math.floor(i / 2) * 24, {size: 17, color: C.dim})); }
    for (const b of this.btns) b.draw();
  }
}
S1.EndScene = EndScene;
S1.TitleScene = TitleScene;
CV.scenes1 = Object.assign(S1, {TitleScene, SetupScene, OriginScene, RecruitScene, ShopScene, EndScene, HowToScene});
})(globalThis.CV = globalThis.CV || {});
