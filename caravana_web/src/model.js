/* LA CARAVANA (web) — modelo: estado, viaje, eventos, tienda y diplomacia. Espejo de caravana/model.py */
(function (CV) {
'use strict';
const D = CV.data;
const clamp = CV.clamp;

class RNG {
  constructor(seed) { this.s = (seed >>> 0) || 1; }
  random() { // mulberry32
    this.s = (this.s + 0x6D2B79F5) >>> 0;
    let t = this.s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  uniform(a, b) { return a + (b - a) * this.random(); }
  int(a, b) { return a + Math.floor(this.random() * (b - a + 1)); }
  choice(arr) { return arr[Math.floor(this.random() * arr.length)]; }
  choices(items, weights) {
    const tot = weights.reduce((x, y) => x + y, 0);
    let r = this.random() * tot;
    for (let i = 0; i < items.length; i++) { r -= weights[i]; if (r <= 0) return items[i]; }
    return items[items.length - 1];
  }
  shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(this.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
}
CV.RNG = RNG;

const prompt = (title, body, options, tone) => ({kind: 'prompt', title, body, options: options || [], tone: tone || 'info'});
const info = (title, body, tone, then) => prompt(title, body, [{label: 'Continuar', action: then || (() => null)}], tone || 'info');
const opt = (label, action, hint, who) => ({label, action, hint: hint || '', who: who || []});
CV.prompt = prompt; CV.info = info; CV.opt = opt;

class Game {
  constructor(seed) {
    this.seed = seed || 1;
    this.rng = new RNG(this.seed);
    this.difficulty = 'normal';
    this.day = 0; this.mile = 0;
    this.colonists = []; this.wagons = [];
    this.sup = {food: 0, ammo: 0, goods: 0, parts: 0, medicine: 0, oxen: 0, money: 0};
    this.pace = 'normal'; this.rations = 'normales'; this.watch = 'normal';
    this.morale = 75; this.weather = 'despejado';
    this.leaderName = 'Jed'; this.profession = 'granjero';
    this.tribes = {};
    for (const k in D.TRIBES) this.tribes[k] = {attitude: 0, treatyUntil: -1, allied: false, arms: 0, met: false, kills: 0, lastRaid: -99, raids: 0, firstContactDone: false};
    this.journal = []; this.notices = [];
    this.visited = ['Independence']; this.nextWp = 1;
    this.guideUntil = -1; this.guideTribe = ''; this.lastBanditDay = -99;
    this.stats = {raids: 0, kills: 0, parleys: 0, gifts: 0, hunted: 0, lost: 0, treaties: 0};
    this.nextCid = 0; this.cannonStock = 0; this.over = false; this.arrivedSite = null; this.forcedWinter = false; this.starving = false;
    this.flags = {}; this.storyDone = []; this.talked = {};
    this.director = new CV.Director();
  }
  // ---------------------------------------------------------- creación
  static create(leaderName, profession, seed, difficulty) {
    const g = new Game(seed);
    g.difficulty = difficulty || 'normal';
    g.leaderName = leaderName || 'Jed'; g.profession = profession;
    const prof = D.PROFESSIONS[profession];
    g.sup.money = prof.money * D.DIFFICULTY[g.difficulty].money;
    const leader = g.make('adulto', g.leaderName, prof.skills);
    leader.isLeader = true; leader.roleId = 'lider';
    CV.story.populate(g);
    g.wagons = Array.from({length: 7}, () => ({hp: 240, maxHp: 240, reinforced: 0, platform: false, lantern: false, cannon: false}));
    g.sup.oxen = 14;
    if (profession === 'carpintero') for (let i = 0; i < 3; i++) g.reinforce(g.wagons[i]);
    g.sup.ammo = profession === 'soldado' ? 40 : 0;
    const starts = {pawnee: 5, cheyenne: 0, lakota: -10, shoshone: 10, cayuse: 8, kalapuya: 10, chinook: 10};
    for (const k in starts) g.tribes[k].attitude = starts[k];
    if (profession === 'soldado') for (const k of D.TERRITORY_TRIBES) g.tribes[k].attitude -= 8;
    if (profession === 'comerciante') for (const k in g.tribes) g.tribes[k].attitude += 5;
    g.autoAssign();
    g.log(`La caravana de ${g.leaderName} parte de Independence, Misuri.`);
    return g;
  }
  make(group, name, skills) {
    const c = {cid: this.nextCid++, name, group, shoot: 3, medic: 2, build: 3, talk: 3, hunt: 3, health: 100, sick: '', alive: true, post: null,
      isLeader: false, kills: 0, cause: '', roleId: '', loyalty: 50, trait: '', bio: ''};
    Object.assign(c, skills || {});
    this.colonists.push(c);
    return c;
  }
  reinforce(w) { w.reinforced++; w.maxHp += 120; w.hp += 120; }
  // ---------------------------------------------------------- utilidades
  log(t) { this.journal.push([this.day, t]); }
  note(t) { this.notices.push(t); this.log(t); }
  date() { return new Date(D.START.getTime() + this.day * 86400000); }
  dateText() { const d = this.date(); return `${d.getDate()} de ${D.MONTHS[d.getMonth()]} de ${d.getFullYear()}`; }
  living() { return this.colonists.filter(c => c.alive); }
  dead() { return this.colonists.filter(c => !c.alive); }
  byRole(r) { return this.colonists.find(c => c.roleId === r) || null; }
  member(r) { const c = this.byRole(r); return c && c.alive ? c : null; }
  familyLoyalty() { const f = this.living().filter(c => D.FAMILY_ROLES.includes(c.roleId)).map(c => c.loyalty); return f.length ? f.reduce((a, b) => a + b, 0) / f.length : 50; }
  canShoot(c) { return c.alive && (c.group === 'adulto' || c.group === 'joven') && c.health > 20; }
  shooters() { return this.living().filter(c => this.canShoot(c)); }
  roleLabel(c) {
    if (c.isLeader) return 'Líder';
    if (c.roleId && !c.roleId.includes('_') && D.ROLE_NAMES[c.roleId]) return D.ROLE_NAMES[c.roleId];
    return {adulto: 'Adulto', joven: 'Joven', niño: 'Niño/a', anciano: 'Anciano/a'}[c.group];
  }
  tribeAt(m) { for (const [a, b, t] of D.TERRITORIES) if (a <= m && m < b) return t; return null; }
  terrain(m) {
    m = m === undefined ? this.mile : m;
    return m < 280 ? 'pradera' : m < 640 ? 'llanura' : m < 900 ? 'estepa' : m < 1100 ? 'montaña' : m < 1500 ? 'desierto' : m < 1650 ? 'cañón' : m < 1900 ? 'bosque' : 'valle';
  }
  inMountains() { return (this.mile >= 900 && this.mile < 1100) || (this.mile >= 1650 && this.mile < 1900); }
  nextWaypoint() { return this.nextWp < D.WAYPOINTS.length ? D.WAYPOINTS[this.nextWp] : null; }
  milesToNext() { const w = this.nextWaypoint(); return w ? Math.max(0, w.mile - this.mile) : 0; }
  hasGuide() { return this.mile < this.guideUntil; }
  best(skill) { const v = this.living().filter(c => c.group !== 'niño').map(c => c[skill]); return v.length ? Math.max(...v) : 1; }
  currentTribe() { return this.tribeAt(this.mile); }
  tribeName(t) { return D.TRIBES[t].name; }
  nextTribe() { for (const [a, b, t] of D.TERRITORIES) if (a > this.mile) return t; return this.currentTribe(); }
  get diff() { return D.DIFFICULTY[this.difficulty]; }
  dailyNeed() { return this.living().reduce((s, c) => s + D.RATIONS[this.rations] * (c.group === 'niño' ? .6 : c.group === 'anciano' ? .8 : 1), 0); }
  // ---------------------------------------------------------- puestos
  normalizePosts() {
    const n = this.wagons.length, used = new Set();
    for (const c of this.colonists) {
      if (c.post) {
        const key = c.post[0] + ':' + c.post[1];
        if (!c.alive || c.post[0] >= n || used.has(key)) c.post = null; else used.add(key);
      }
    }
  }
  autoAssign(threat) {
    for (const c of this.colonists) c.post = null;
    threat = threat || {};
    const order = [];
    this.wagons.forEach((w, i) => { if (w.hp > 0) order.push(i); });
    if (!order.length) return;
    order.sort((a, b) => (threat[b] || 0) - (threat[a] || 0) || (this.wagons[b].cannon - this.wagons[a].cannon) || a - b);
    const sh = this.living().filter(c => this.canShoot(c)).sort((a, b) => b.shoot - a.shoot);
    const rest = this.living().filter(c => !sh.includes(c));
    for (const i of order) { const c = sh.shift(); if (c) c.post = [i, 'tirador']; }
    const helpers = sh.concat(rest.sort((a, b) => ((a.group === 'niño') - (b.group === 'niño')) || (b.build - a.build)));
    order.forEach((i, k) => { if (helpers[k]) helpers[k].post = [i, 'ayuda']; });
  }
  postOf(w, slot) { return this.living().find(c => c.post && c.post[0] === w && c.post[1] === slot) || null; }
  assign(c, w, slot) {
    if (w >= this.wagons.length) return false;
    if (slot === 'tirador' && !this.canShoot(c)) return false;
    const other = this.postOf(w, slot);
    if (other && other !== c) { other.post = c.post; if (other.post && other.post[1] === 'tirador' && !this.canShoot(other)) other.post = null; }
    c.post = [w, slot];
    return true;
  }
  // ---------------------------------------------------------- tienda
  price(item, mult, selling) {
    let p = D.ITEMS[item].price * (mult || 1);
    if (this.profession === 'comerciante') p *= .88;
    return selling ? Math.round(p * D.SELL * 100) / 100 : Math.round(p * 100) / 100;
  }
  stockOf(item) {
    if (item === 'wagon') return this.wagons.length;
    if (item === 'cannon') return this.cannonStock;
    return Math.floor(this.sup[item] / D.ITEMS[item].per);
  }
  buy(item, mult, qty) {
    qty = qty || 1;
    const cost = this.price(item, mult) * qty;
    if (cost > this.sup.money + 1e-6) return [false, 'No tienes dinero suficiente.'];
    if (item === 'wagon' && this.wagons.length + qty > 12) return [false, 'Un círculo de más de 12 carretas es inmanejable.'];
    this.sup.money -= cost;
    if (item === 'wagon') for (let i = 0; i < qty; i++) this.wagons.push({hp: 240, maxHp: 240, reinforced: 0, platform: false, lantern: false, cannon: false});
    else if (item === 'cannon') this.cannonStock += qty;
    else this.sup[item] += D.ITEMS[item].per * qty;
    return [true, `Compras ${qty} × ${D.ITEMS[item].name} por $${Math.round(cost)}.`];
  }
  sell(item, mult, qty) {
    qty = qty || 1;
    if (item === 'wagon') {
      if (this.wagons.length <= 3) return [false, 'No puedes quedarte con menos de 3 carretas.'];
      for (let i = 0; i < qty; i++) this.wagons.pop();
      this.normalizePosts();
    } else if (item === 'cannon') {
      if (this.cannonStock < qty) return [false, 'No tienes cañones en el almacén.'];
      this.cannonStock -= qty;
    } else {
      const per = D.ITEMS[item].per;
      if (this.sup[item] < per * qty) return [false, 'No tienes tanto para vender.'];
      this.sup[item] -= per * qty;
    }
    const gain = this.price(item, mult, true) * qty;
    this.sup.money += gain;
    return [true, `Vendes ${qty} × ${D.ITEMS[item].name} por $${Math.round(gain)}.`];
  }
  // ---------------------------------------------------------- viaje
  oxenFactor() { return Math.min(1, this.sup.oxen / Math.max(1, 2 * this.wagons.length)); }
  updateWeather() {
    const m = this.date().getMonth() + 1, r = this.rng.random();
    let w = 'despejado';
    if (m >= 4 && m <= 6) w = r < .08 ? 'tormenta' : r < .28 ? 'lluvia' : 'despejado';
    else if (m === 7 || m === 8) w = r < .22 ? 'calor' : r < .27 ? 'tormenta' : 'despejado';
    else if (m === 9 || m === 10) w = (r < .10 && this.inMountains()) ? 'nieve' : r < .25 ? 'lluvia' : 'despejado';
    else w = r < .40 ? 'nieve' : 'frío';
    this.weather = w;
  }
  travelSpeed() {
    const base = D.PACES[this.pace];
    const wf = {despejado: 1, lluvia: .8, tormenta: .5, calor: .9, nieve: .55, frío: .8}[this.weather];
    const tf = ['montaña', 'bosque', 'cañón'].includes(this.terrain()) ? .78 : 1;
    const sick = this.living().filter(c => c.sick).length;
    const sf = 1 - Math.min(.3, .04 * sick);
    const wag = this.wagons.every(w => w.hp > 40) ? 1 : .85;
    return base * wf * tf * sf * wag * this.oxenFactor();
  }
  advanceDay() {
    if (this.over) return null;
    this.day++;
    this.updateWeather();
    const end = this.checkWinter();
    if (end) return end;
    const wp = this.nextWaypoint();
    let miles = this.travelSpeed();
    if (miles < 1) { this.note('Sin bueyes suficientes, las carretas no pueden avanzar. Necesitas comprar o comerciar bueyes.'); miles = 0; }
    let arrived = null;
    if (wp && this.mile + miles >= wp.mile) { miles = wp.mile - this.mile; arrived = wp; }
    this.mile += miles;
    this.dailyUpkeep();
    const died = this.dailyHealth(false);
    this.director.update(this);
    this.desertions();
    this.wagonsWear(miles);
    if (!this.living().length) return this.gameOver('La caravana ha perecido por completo en el camino.');
    if (died.length) return info('Luto en la caravana', `${died.map(c => c.name).join(', ')} no sobrevivió. Se cava una tumba junto al camino y se reza en silencio.`, 'danger');
    if (arrived) { this.nextWp++; this.visited.push(arrived.name); return this.arrivalInterrupt(arrived); }
    let evt = CV.story.check(this, true);
    if (evt) return evt;
    evt = this.rollTribeEvents(); if (evt) return evt;
    evt = this.rollBandits(); if (evt) return evt;
    return this.rollRandomEvent();
  }
  arrivalInterrupt(wp) {
    this.log(`Se llega a ${wp.name}.`);
    if (wp.kind === 'river') return this.riverPrompt(wp);
    if (wp.kind === 'mountain') return this.mountainPrompt(wp);
    if (wp.kind === 'fork') return {kind: 'fork'};
    if (wp.kind === 'post') return {kind: 'arrival', waypoint: wp};
    this.morale = Math.min(100, this.morale + 5);
    return info(wp.name, wp.text + ' La moral sube al ver el hito.', 'good');
  }
  wagonsWear(miles) { for (const w of this.wagons) if (miles > 0 && this.rng.random() < .01) w.hp = Math.max(10, w.hp - this.rng.int(5, 20)); }
  checkWinter() {
    if (this.day >= D.FORCED_WINTER_DAY && !this.forcedWinter && this.mile < D.TRAIL_END) {
      this.forcedWinter = true;
      return prompt('El invierno os alcanza', 'Las primeras nevadas cierran los pasos. Es imposible continuar: hay que fundar aquí con lo que se tiene, en un lugar improvisado.',
        [opt('Fundar el asentamiento aquí', () => ({kind: 'fork'}))], 'danger');
    }
    return null;
  }
  dailyUpkeep() {
    const need = this.dailyNeed();
    if (this.sup.food >= need) { this.sup.food -= need; this.starving = false; }
    else { this.sup.food = 0; this.starving = true; this.note('¡La comida se ha agotado! Todos pasan hambre.'); this.morale = Math.max(0, this.morale - 4); }
    const target = this.starving ? 20 : 70 + (this.familyLoyalty() - 50) / 8 + (this.member('predicador') ? 3 : 0);
    this.morale += (target - this.morale) * .02;
    if (this.pace === 'rapido') this.morale -= .5;
    if (this.rations === 'abundantes') this.morale += .5;
    this.morale = clamp(this.morale, 0, 100);
  }
  dailyHealth(resting) {
    const died = [];
    const medic = this.living().length ? this.best('medic') : 1;
    const rd = {escasas: -1.6, normales: .4, abundantes: 1.4}[this.rations];
    let pd = {lento: .6, normal: 0, rapido: -1}[this.pace];
    const wd = {despejado: 0, lluvia: -.3, tormenta: -.8, calor: -.6, nieve: -1.2, frío: -.7}[this.weather];
    if (resting) pd = 1.5;
    for (const c of this.living()) {
      let d = rd + pd + wd;
      if (this.starving) d -= 4;
      if (c.sick) {
        d -= 3;
        if (this.sup.medicine > 0 && c.health < 45) { this.sup.medicine--; c.health += 25; this.note(`${c.name} recibe medicinas contra ${c.sick}.`); d += 2; }
        let pr = .10 + .02 * medic + (resting ? .08 : 0);
        if (this.profession === 'medico') pr += .08;
        if (this.rng.random() < pr) { this.note(`${c.name} se ha recuperado de ${c.sick}.`); c.sick = ''; }
      } else {
        let p = .004 + (this.rations === 'escasas' ? .006 : 0) + (this.pace === 'rapido' ? .003 : 0) + (['lluvia', 'tormenta', 'nieve'].includes(this.weather) ? .003 : 0);
        if (c.group === 'niño' || c.group === 'anciano') p *= 1.6;
        p *= Math.max(.4, 1 - medic / 18) * this.diff.disease;
        if (this.profession === 'medico') p *= .7;
        if (resting) p *= .5;
        if (this.rng.random() < p) { c.sick = this.rng.choice(D.DISEASES.slice(0, 6)); this.note(`${c.name} cae enfermo/a: ${c.sick}.`); }
      }
      c.health = clamp(c.health + d, 0, 100);
      if (c.health <= 0) {
        c.alive = false; c.post = null;
        c.cause = c.sick || (this.starving ? 'hambre' : 'agotamiento');
        this.stats.lost++; this.morale = Math.max(0, this.morale - 10);
        this.note(`${c.name} ha muerto (${c.cause}).`);
        died.push(c);
      }
    }
    if (died.length) this.normalizePosts();
    return died;
  }
  desertions() {
    for (const c of this.living()) {
      if (c.trait === 'mercenario' && c.loyalty < 25 && this.rng.random() < .05) {
        c.alive = false; c.cause = 'desertó'; c.post = null;
        const g = Math.min(this.sup.goods, 3); this.sup.goods -= g; this.sup.ammo = Math.max(0, this.sup.ammo - 15);
        this.stats.lost++; this.normalizePosts();
        this.note(`${c.name} desaparece de madrugada con 15 balas y ${g} mercancías.`);
      }
    }
  }
  gameOver(text) { this.over = true; return {kind: 'end', title: 'Fin del viaje', body: text, victory: false}; }
  // ---------------------------------------------------------- tribus y asaltos
  raidProbability(tid) {
    const ts = this.tribes[tid], t = D.TRIBES[tid];
    if (ts.allied) return 0;
    let p = t.aggression * Math.max(0, 25 - ts.attitude) / 100 * .22;
    if (this.day <= ts.treatyUntil) p *= .08;
    if (this.hasGuide() && this.guideTribe === tid) p *= .6;
    return p * this.director.raidMult(this);
  }
  rollTribeEvents() {
    const tid = this.currentTribe();
    if (!tid || this.mile < 20) return null;
    const ts = this.tribes[tid], t = D.TRIBES[tid], rng = this.rng;
    const start = D.TERRITORIES.find(x => x[2] === tid)[0];
    if (!ts.firstContactDone && this.mile >= start + 70) {
      ts.firstContactDone = true; ts.met = true;
      return {kind: 'contact', tribe: tid, ctype: ts.attitude >= 8 ? 'visit' : 'patrol', opening: t.greet};
    }
    if (rng.random() < .05 && this.day > ts.lastRaid + 4) { ts.met = true; return {kind: 'contact', tribe: tid, ctype: ts.attitude >= 15 ? 'visit' : 'patrol', opening: t.greet}; }
    if (this.day > ts.lastRaid + 3 && rng.random() < this.raidProbability(tid)) return this.raidWarning(tid);
    return null;
  }
  raidWarning(tid) {
    const ts = this.tribes[tid]; ts.lastRaid = this.day;
    let warn = {ninguna: .3, normal: .6, reforzada: .92}[this.watch];
    if (this.hasGuide()) warn += .2;
    const spec = this.makeRaid(tid);
    if (this.rng.random() < warn) {
      spec.tense = true;
      const name = this.tribeName(tid);
      const vs = CV.story.voices(this);
      let body = `Los vigías divisan una partida de guerra ${name} que se aproxima, unos ${Math.max(5, Math.floor(spec.strength * 1.1))} guerreros. Todavía hay tiempo de decidir.`;
      if (vs.length) body += '\n\n' + CV.story.voicesText(vs);
      return prompt(`¡${name} se acercan!`, body, [
        opt('Cerrar el círculo y prepararse', () => { CV.story.follow(this, vs, 'fight'); return spec; }, 'Combate (tendrás tiempo de organizar posiciones)', CV.story.backers(vs, 'fight')),
        opt('Salir a parlamentar', () => { CV.story.follow(this, vs, 'parley'); return {kind: 'contact', tribe: tid, ctype: 'tense', opening: 'Envías un emisario con las manos vacías hacia la partida de guerra.'}; }, 'Diplomacia: última oportunidad de evitar la sangre', CV.story.backers(vs, 'parley')),
        opt('Forzar la marcha y huir', () => { CV.story.follow(this, vs, 'flee'); return this.flee(spec); }, 'Arriesgado: bueyes y carretas pueden sufrir', CV.story.backers(vs, 'flee')),
      ], 'danger');
    }
    spec.night = this.rng.random() < .5; spec.prepTime = 6;
    spec.reason = '¡Ataque por sorpresa! Los vigías no vieron venir a la partida.';
    this.note(spec.reason);
    return spec;
  }
  flee(spec) {
    const rng = this.rng;
    let chance = .45 + .1 * (this.sup.oxen / Math.max(1, 2 * this.wagons.length)) - .02 * spec.strength / 4;
    if (this.pace === 'rapido') chance += .1;
    if (rng.random() < chance && this.oxenFactor() > .4) {
      const lost = [];
      if (rng.random() < .5 && this.sup.oxen > 2) { this.sup.oxen -= 2; lost.push('dos bueyes'); }
      if (rng.random() < .4) { this.sup.food = Math.max(0, this.sup.food - 80); lost.push('80 lb de comida'); }
      if (rng.random() < .4 && this.wagons.length) { const w = rng.choice(this.wagons); w.hp = Math.max(20, w.hp - 80); lost.push('daños en una carreta'); }
      this.mile += 8; this.morale -= 5;
      return info('¡Escapasteis!', 'A latigazos, la caravana se pierde entre el polvo y la partida desiste. ' + (lost.length ? 'Perdisteis: ' + lost.join(', ') + '.' : 'Sin pérdidas.'));
    }
    spec.prepTime = 4; spec.reason = 'La huida fracasa: los jinetes os alcanzan antes de cerrar el círculo.';
    return spec;
  }
  makeRaid(tid, extra) {
    const t = D.TRIBES[tid], ts = this.tribes[tid], rng = this.rng;
    const progress = this.mile / 2000;
    let strength = (7 + progress * 12 + ts.arms * 1.1 + rng.uniform(0, 3) + (extra || 0)) * t.strength;
    if (this.day <= ts.treatyUntil) strength *= .45;
    return this.composeBattle(tid, strength);
  }
  composeBattle(tid, strength) {
    const rng = this.rng;
    strength *= this.diff.raid * this.director.strengthMult(this);
    let style = D.TRIBES[tid] ? D.TRIBES[tid].style : {bandido: 6, guerrero: 2};
    if (tid === 'bandidos') style = {bandido: 6, guerrero: 3, jinete: 1};
    const kinds = Object.keys(style), weights = kinds.map(k => style[k]);
    const nWaves = strength < 8 ? 1 : strength < 15 ? 2 : strength < 24 ? 3 : 4;
    let budget = strength; const waves = [];
    const base = rng.uniform(0, Math.PI * 2); let t = 0;
    const boss = strength >= 16 && tid !== 'bandidos';
    for (let wi = 0; wi < nWaves; wi++) {
      let wb = budget / (nWaves - wi) * rng.uniform(.8, 1.2);
      const comp = {};
      while (wb > .8) {
        let k = rng.choices(kinds, weights), cost = D.FOES[k].cost;
        if (cost > wb + 1) { k = 'guerrero'; cost = D.FOES[k].cost; }
        comp[k] = (comp[k] || 0) + 1; wb -= cost; budget -= cost;
      }
      if (boss && wi === nWaves - 1) comp.jefe = 1;
      if (Object.keys(comp).length) {
        const angle = wi === 0 ? base : wi % 2 === 1 ? base + Math.PI + rng.uniform(-.5, .5) : base + rng.choice([-1, 1]) * Math.PI / 2 + rng.uniform(-.4, .4);
        waves.push([t, angle, comp]);
      }
      t += rng.uniform(22, 38);
    }
    if (strength > 12 && waves.length) {
      const [t0, a0, c0] = waves[0], split = {};
      for (const k of Object.keys(c0)) if (c0[k] >= 2) { const h = Math.floor(c0[k] / 2); c0[k] -= h; split[k] = h; }
      if (Object.keys(split).length) waves.splice(1, 0, [t0 + 1.5, a0 + rng.choice([-1, 1]) * rng.uniform(1.8, 2.6), split]);
    }
    const allies = 4 * D.TERRITORY_TRIBES.filter(k => this.tribes[k].allied && k !== tid).length;
    return {kind: 'battle', foe: tid, strength, waves, allies, night: rng.random() < .18, prepTime: 28, reason: tid === 'bandidos' ? 'Una banda de salteadores os ha tendido una emboscada.' : '', tense: false};
  }
  rollBandits() {
    if (this.mile < 300 || this.day - this.lastBanditDay < 14) return null;
    const p = .012 * (this.watch === 'ninguna' ? 1.8 : this.watch === 'reforzada' ? .6 : 1) * this.director.raidMult(this);
    if (this.rng.random() < p) {
      this.lastBanditDay = this.day;
      const spec = this.composeBattle('bandidos', 5 + this.mile / 2000 * 7 + this.rng.uniform(0, 2));
      spec.night = this.rng.random() < .4; spec.prepTime = this.watch !== 'reforzada' ? 10 : 25;
      spec.reason = 'Un grupo de salteadores aprovecha la oscuridad del camino y os asalta.';
      return prompt('¡Bandoleros!', 'Hombres armados salen de entre las rocas gritando que dejéis la carga y os marchéis.', [
        opt('¡Al círculo! Defendernos', () => spec),
        opt('Pagar el rescate (6 mercancías, 20 balas)', () => this.payBandits()),
      ], 'danger');
    }
    return null;
  }
  payBandits() {
    if (this.sup.goods >= 6 && this.sup.ammo >= 20) { this.sup.goods -= 6; this.sup.ammo -= 20; this.morale -= 8; return info('Un mal trato', 'Los bandidos toman el pago y se esfuman. La rabia pesa más que la pérdida.'); }
    const spec = this.composeBattle('bandidos', 5 + this.mile / 2000 * 7); spec.prepTime = 6; spec.reason = 'No podéis pagar. Los bandidos atacan de todos modos.';
    return spec;
  }
  // ---------------------------------------------------------- eventos aleatorios
  rollRandomEvent() {
    if (this.rng.random() > .17) return null;
    let table = [['wheel', 3], ['ox', 2], ['storm', 2], ['sick', 2], ['bison', 3], ['trader', 2], ['news', 1], ['lost', 1], ['road', 1], ['stranger', 2], ['music', 1], ['fire', 1], ['berries', 2], ['thieves', 1]];
    table = this.director.reweight(this, table);
    const k = this.rng.choices(table.map(t => t[0]), table.map(t => t[1]));
    return this['ev_' + k]();
  }
  ev_wheel() {
    if (this.sup.parts > 0) {
      if (this.profession === 'carpintero' && this.rng.random() < .5) this.note('Se rompe una rueda; con su oficio, reparas sin gastar repuestos.');
      else { this.sup.parts--; this.note('Se rompe una rueda. Gastas un juego de repuestos.'); }
    } else { this.day += 2; this.note('Se rompe un eje y no hay repuestos: perdéis dos días improvisando uno.'); }
    return null;
  }
  ev_ox() { if (this.sup.oxen > 2) { this.sup.oxen--; this.note('Un buey cae muerto de agotamiento.'); } return null; }
  ev_storm() { this.day++; for (const c of this.living()) c.health = Math.max(1, c.health - 3); this.note('Una tormenta eléctrica os obliga a detener todo un día.'); return null; }
  ev_sick() { const h = this.living().filter(c => !c.sick); if (h.length) { const c = this.rng.choice(h); c.sick = this.rng.choice(D.DISEASES); c.health -= 15; this.note(`${c.name} cae enfermo/a: ${c.sick}.`); } return null; }
  ev_berries() { const n = this.rng.int(25, 60); this.sup.food += n; this.note(`Los niños encuentran bayas y raíces comestibles: +${n} lb de comida.`); return null; }
  ev_bison() {
    const tid = this.currentTribe();
    if (this.mile < 200 || this.sup.ammo < 8) return null;
    const trespass = tid && this.day > this.tribes[tid].treatyUntil && !this.tribes[tid].allied;
    const hunt = () => {
      const skill = this.best('hunt'); let used = Math.min(this.rng.int(6, 10), this.sup.ammo);
      this.sup.ammo -= used;
      const gain = Math.floor(used * this.rng.uniform(25, 38) * (.7 + skill / 14));
      this.sup.food += gain; this.stats.hunted += gain;
      let txt = `La cacería da ${gain} lb de carne seca (${used} balas).`;
      if (trespass && this.rng.random() < .5) { this.tribes[tid].attitude -= 7; txt += ` Pero los ${this.tribeName(tid)} consideran esa manada suya… y lo han visto.`; }
      return info('Cacería de bisontes', txt, 'good');
    };
    return prompt('¡Una manada de bisontes!', 'Una manada enorme cruza el valle a media milla de la caravana.' + (trespass ? ' Cazarla en estas tierras puede ofender.' : ''),
      [opt('Cazar (6-10 balas)', hunt), opt('Dejarlos pasar', () => null)], 'good');
  }
  ev_trader() { return prompt('Comerciante ambulante', 'Un mulero con un carro cargado de mercancías os alcanza por el camino.',
    [opt('Comerciar', () => ({kind: 'shop', name: 'Comerciante ambulante', mult: 1.25, wagons: false})), opt('Seguir adelante', () => null)], 'info'); }
  ev_news() {
    const nxt = this.nextTribe();
    if (nxt) { const a = this.tribes[nxt].attitude; this.note(`Unos viajeros que vuelven al este cuentan que los ${this.tribeName(nxt)} andan ${a < -30 ? 'muy hostiles' : a < 0 ? 'recelosos' : a < 30 ? 'tranquilos' : 'amistosos'} con los blancos.`); }
    return null;
  }
  ev_lost() { this.day++; this.note('Os desorientáis en una bifurcación sin señales. Perdéis un día.'); return null; }
  ev_road() { this.mile += 12; this.note('Encontráis un atajo excelente: ganáis 12 millas.'); return null; }
  ev_music() { this.morale = Math.min(100, this.morale + 12); this.note('Esa noche suena el violín junto al fuego. La moral mejora.'); return null; }
  ev_fire() { if (this.sup.goods > 0) { const n = Math.min(this.sup.goods, this.rng.int(1, 3)); this.sup.goods -= n; this.note(`Una chispa quema parte de la carga: -${n} mercancías.`); } return null; }
  ev_thieves() {
    if (this.watch === 'reforzada' && this.rng.random() < .7) { this.note('La guardia reforzada sorprende a unos ladrones y los ahuyenta.'); return null; }
    const n = this.rng.int(1, 3); this.sup.goods = Math.max(0, this.sup.goods - n); this.sup.ammo = Math.max(0, this.sup.ammo - 8);
    this.note('Ladrones nocturnos se llevan mercancías y munición.'); return null;
  }
  ev_stranger() {
    if (this.mile < 200) return null;
    const deserter = this.rng.random() < .2;
    const take = () => {
      if (this.sup.food < 40) return info('Sin comida que ofrecer', 'No podéis alimentar a otra boca; el extraño sigue su camino.');
      this.sup.food -= 40;
      if (deserter) { this.sup.goods -= Math.min(this.sup.goods, 4); this.sup.ammo = Math.max(0, this.sup.ammo - 15); return info('Un desertor', 'Al amanecer, el «superviviente» ha desaparecido con parte de vuestras mercancías y munición.', 'danger'); }
      const c = this.make('joven', `${this.rng.choice(['Samuel','Ruth','Caleb','Nora','Abel','Lydia'])} Walker`, {shoot: this.rng.int(4, 8), build: this.rng.int(3, 6), hunt: this.rng.int(3, 6)});
      this.note(`${c.name} se une a la caravana.`);
      return info('Un nuevo colono', `${c.name} agradece la comida y se ofrece a trabajar. Se une a la caravana.`, 'good');
    };
    return prompt('Un superviviente', 'Un joven andrajoso, único sobreviviente de otra caravana, os pide comida y unirse al grupo.', [opt('Acogerlo (40 lb de comida)', take), opt('Seguir adelante', () => null)], 'info');
  }
  // ---------------------------------------------------------- cruces y pasos
  riverPrompt(wp) {
    const depth = wp.depth + (['lluvia', 'tormenta'].includes(this.weather) ? 1 : 0) + (this.date().getMonth() + 1 <= 5 ? 1 : 0);
    const guide = this.hasGuide() ? .7 : 1, fee = 25 + 8 * this.wagons.length;
    return prompt(`${wp.name} — profundidad ${depth}`, `${wp.text} El cauce ronda los ${depth} pies de profundidad.`, [
      opt('Vadear', () => this.riverResult('vadeas', (.06 + .07 * depth) * guide), 'Rápido pero arriesgado'),
      opt('Calafatear las carretas y flotar', () => { this.day++; return this.riverResult('calafateas y flotas', (.03 + .05 * depth) * guide); }, '1 día, riesgo medio'),
      opt(`Pagar la balsa ($${fee})`, () => {
        if (this.sup.money < fee) return info('Sin dinero', `El barquero pide $${fee} y no los tienes.`, 'danger');
        this.sup.money -= fee; this.day++; return info('Cruce seguro', `Pagas $${fee} y la balsa pasa carreta por carreta sin incidentes.`, 'good');
      }, 'Seguro'),
      opt('Esperar 2 días a que baje', () => { this.day += 2; this.dailyUpkeep(); this.dailyUpkeep(); return this.riverPrompt({...wp, depth: Math.max(1, wp.depth - 1)}); }, 'Consume comida'),
    ], 'info');
  }
  riverResult(how, risk) {
    const rng = this.rng;
    if (rng.random() < risk) {
      const lost = [];
      const f = Math.floor(this.sup.food * rng.uniform(.15, .3)); this.sup.food -= f; lost.push(`${f} lb de comida`);
      if (this.sup.oxen > 2) { this.sup.oxen -= 2; lost.push('2 bueyes'); }
      if (this.sup.ammo > 0) { const a = Math.floor(this.sup.ammo * .2); this.sup.ammo -= a; lost.push(`${a} balas`); }
      if (rng.random() < .35) {
        const vs = this.living().filter(c => ['niño', 'anciano', 'joven'].includes(c.group));
        if (vs.length) {
          const v = rng.choice(vs); v.health -= 45; lost.push(`${v.name} casi se ahoga`);
          if (v.health <= 0) { v.alive = false; v.cause = 'ahogado'; v.post = null; this.stats.lost++; lost[lost.length - 1] = `${v.name} se ahoga`; this.normalizePosts(); }
        }
      }
      this.morale -= 8;
      return info('Desastre en el cruce', `Al cruzar (${how}), la corriente arrastra la carga. Perdéis: ${lost.join(', ')}.`, 'danger');
    }
    this.log(`Cruzaste el río (${how}) sin problemas.`);
    return info('Cruce completado', `Cruzáis el río (${how}) y todos llegan a la otra orilla.`, 'good');
  }
  mountainPrompt(wp) {
    let danger = wp.danger + (this.date().getMonth() + 1 >= 10 ? .2 : 0);
    danger *= this.hasGuide() ? .65 : 1;
    if (this.flags.samuel_scout) danger *= .8;
    return prompt(wp.name, wp.text, [
      opt('Cruzar con cautela (+2 días)', () => { this.day += 2; this.dailyUpkeep(); this.dailyUpkeep(); return this.mountainResult(danger * .45); }, 'Riesgo bajo'),
      opt('Forzar el paso', () => this.mountainResult(danger), 'Riesgo alto'),
      opt('Aligerar la carga (-4 mercancías)', () => { const l = Math.min(this.sup.goods, 4); this.sup.goods -= l; return this.mountainResult(danger * .55, `Dejáis ${l} lotes de mercancías atrás. `); }, 'Riesgo medio'),
    ], 'info');
  }
  mountainResult(risk, pre) {
    pre = pre || '';
    if (this.rng.random() < risk) {
      const msgs = [];
      if (this.wagons.length) { const w = this.rng.choice(this.wagons); w.hp = Math.max(15, w.hp - this.rng.int(80, 160)); msgs.push('una carreta queda muy dañada'); }
      if (this.sup.oxen > 2) { this.sup.oxen -= 2; msgs.push('pierdes dos bueyes en un barranco'); }
      this.sup.food = Math.max(0, this.sup.food - 60); this.morale -= 6;
      return info('Paso accidentado', pre + 'El camino se cobra su peaje: ' + msgs.join('; ') + '.', 'danger');
    }
    return info('Paso superado', pre + 'La caravana cruza el paso y respira hondo.', 'good');
  }
  // ---------------------------------------------------------- campamento
  restDay(days) {
    for (let i = 0; i < (days || 1); i++) {
      this.day++; this.updateWeather(); this.dailyUpkeep(); this.dailyHealth(true); this.director.update(this);
      this.morale = Math.min(100, this.morale + 3);
      for (const w of this.wagons) w.hp = Math.min(w.maxHp, w.hp + 18);
    }
  }
  campEvent() { if (this.over) return null; return this.rollTribeEvents() || this.rollBandits(); }
  rest(days) {
    let done = 0;
    for (let i = 0; i < days; i++) {
      this.restDay(1); done++;
      if (!this.living().length) return [done, this.gameOver('El campamento queda en silencio: nadie ha sobrevivido.')];
      if (this.day >= D.FORCED_WINTER_DAY && !this.forcedWinter && this.mile < D.TRAIL_END) { const it = this.checkWinter(); if (it) return [done, it]; }
      const it = this.campEvent(); if (it) return [done, it];
    }
    return [done, null];
  }
  travelToSite(id) {
    const extra = D.SITES[id] ? D.SITES[id].extra : 0, days = Math.ceil(extra / 17), notes = [];
    for (let i = 0; i < days; i++) {
      this.day++; this.updateWeather(); this.dailyUpkeep();
      for (const c of this.dailyHealth(false)) notes.push(`${c.name} murió en el último tramo (${c.cause}).`);
    }
    this.mile += extra; this.arrivedSite = id;
    return notes;
  }
  repairWagon(i) {
    const w = this.wagons[i];
    if (w.hp >= w.maxHp - 1) return [false, 'Esa carreta está en perfecto estado.'];
    let cost = 1;
    if (this.profession === 'carpintero' || this.best('build') >= 8) cost = this.rng.random() < .5 ? 1 : 0;
    if (this.sup.parts < cost) return [false, 'Faltan repuestos.'];
    this.sup.parts -= cost; w.hp = Math.min(w.maxHp, w.hp + 90);
    return [true, `Carreta ${i + 1} reparada (${Math.floor(w.hp)}/${Math.floor(w.maxHp)}).`];
  }
  upgrade(i, kind) {
    const w = this.wagons[i], s = this.sup;
    if (kind === 'refuerzo') {
      if (w.reinforced >= 2) return [false, 'Ya tiene el máximo de refuerzos.'];
      if (s.parts < 2) return [false, 'Faltan repuestos (2).'];
      s.parts -= 2; this.reinforce(w); return [true, `Carreta ${i + 1}: planchas de refuerzo (+120 de resistencia).`];
    }
    if (kind === 'plataforma') {
      if (w.platform) return [false, 'Ya tiene plataforma.'];
      if (s.parts < 2 || s.goods < 1) return [false, 'Faltan repuestos (2) o mercancías (1).'];
      s.parts -= 2; s.goods -= 1; w.platform = true; return [true, `Carreta ${i + 1}: plataforma de tiro (más alcance y puntería).`];
    }
    if (kind === 'farol') {
      if (w.lantern) return [false, 'Ya tiene farol.'];
      if (s.goods < 2) return [false, 'Faltan mercancías (2).'];
      s.goods -= 2; w.lantern = true; return [true, `Carreta ${i + 1}: farol para combates nocturnos.`];
    }
    if (kind === 'cañón') {
      if (w.cannon) return [false, 'Ya tiene cañón.'];
      if (this.cannonStock < 1) return [false, 'No tienes ningún cañón en el almacén (cómpralo en Fort Laramie o Fort Hall).'];
      this.cannonStock--; w.cannon = true; return [true, `Carreta ${i + 1}: cañón montado.`];
    }
    return [false, 'Mejora desconocida.'];
  }
  huntDay() {
    this.day++; this.updateWeather(); this.dailyUpkeep(); this.dailyHealth(false);
    const hunters = this.living().filter(c => c.group === 'adulto' || c.group === 'joven').sort((a, b) => b.hunt - a.hunt).slice(0, 2);
    if (this.sup.ammo < 6 || !hunters.length) return info('Sin medios', 'No tienes munición o cazadores para salir.', 'danger');
    const used = Math.min(this.sup.ammo, this.rng.int(8, 14)); this.sup.ammo -= used;
    const skill = hunters.reduce((s, h) => s + h.hunt, 0) / hunters.length;
    const tf = {pradera: 1.2, llanura: 1.4, estepa: .9, montaña: .8, desierto: .5, cañón: .7, bosque: 1, valle: 1.3}[this.terrain()];
    const gain = Math.floor(used * this.rng.uniform(14, 30) * (.6 + skill / 8) * tf);
    this.sup.food += gain; this.stats.hunted += gain;
    let txt = `${hunters.map(h => h.name).join(' y ')} regresan con ${gain} lb de carne (${used} balas).`;
    const tid = this.currentTribe();
    if (tid && this.day > this.tribes[tid].treatyUntil && !this.tribes[tid].allied && this.rng.random() < .3) { this.tribes[tid].attitude -= 5; txt += ` Pero los ${this.tribeName(tid)} los vieron cazar en sus tierras.`; }
    return info('Cacería', txt, 'good');
  }
  // ---------------------------------------------------------- resultado de combate
  applyBattle(spec, res) {
    const lines = [], tid = spec.foe;
    this.director.onBattleEnd(this, res);
    this.stats.raids++; this.stats.kills += res.killed;
    const native = !!this.tribes[tid];
    const title = {victoria: '¡Victoria!', huida: 'El enemigo se retira', paz: 'Se acuerda la paz', derrota: 'Derrota'}[res.outcome];
    lines.push(`Enemigos abatidos: ${res.killed}/${res.total}. Munición gastada: ${res.ammoUsed}.`);
    if (res.dead.length) lines.push('Caídos: ' + res.dead.join(', ') + '.');
    if (res.wagonsLost) lines.push(`Carretas destruidas: ${res.wagonsLost} (con parte de la carga).`);
    if (native) {
      const ts = this.tribes[tid]; ts.kills += res.killed; ts.raids++;
      let delta;
      if (res.outcome === 'paz') { delta = 8 - res.killed * .6; this.stats.parleys++; ts.treatyUntil = Math.max(ts.treatyUntil, this.day + 8); lines.push(`El parlamento calma los ánimos de los ${this.tribeName(tid)}. Habrá una tregua.`); }
      else { delta = -4 - res.killed; lines.push(`Los ${this.tribeName(tid)} guardarán memoria de la sangre derramada (${Math.round(delta)} en su trato).`); }
      ts.attitude = clamp(ts.attitude + delta, -100, 100);
      for (const k of D.TERRITORY_TRIBES) if (k !== tid) this.tribes[k].attitude = clamp(this.tribes[k].attitude - res.killed * .15, -100, 100);
    } else if (res.outcome === 'victoria' || res.outcome === 'huida') {
      if (res.killed) {
        const la = this.rng.int(5, 8) * Math.max(1, Math.floor(res.killed / 3)), lg = this.rng.int(0, 3);
        this.sup.ammo += la; this.sup.goods += lg; lines.push(`Botín de los bandidos: +${la} balas, +${lg} mercancías.`);
      }
    }
    if ((res.outcome === 'victoria' || res.outcome === 'huida') && res.ammoUsed > 10) { const back = Math.floor(res.ammoUsed * .12); this.sup.ammo += back; lines.push(`Recoges balas y flechas aprovechables: +${back} balas.`); }
    if (res.outcome === 'victoria') this.morale = Math.min(100, this.morale + 6);
    else if (res.outcome === 'derrota') { this.morale = Math.max(0, this.morale - 25); this.sup.food *= .5; this.sup.goods = Math.floor(this.sup.goods / 2); lines.push('Los atacantes saquean la mitad de las provisiones antes de retirarse.'); }
    this.normalizePosts();
    for (const c of this.living()) if (c.health < 50 && !c.sick && this.rng.random() < .1) c.sick = 'herida infectada';
    this.log(`Combate contra ${native ? this.tribeName(tid) : 'bandidos'}: ${res.outcome}.`);
    return info(title, lines.join('\n'), res.outcome === 'derrota' ? 'danger' : 'good');
  }
}
CV.Game = Game;

// ============================================================== Diplomacia
class Contact {
  constructor(game, tribe, kind, opening) {
    this.g = game; this.tribe = tribe; this.kind = kind || 'visit'; this.opening = opening || '';
    this.patience = 4 + (game.hasGuide() ? 1 : 0) + (kind === 'visit' ? 1 : 0) - (kind === 'tense' ? 1 : 0);
    this.ended = false; this.result = 'neutral'; this.history = []; this.used = new Set(); this.shopRequested = false; this.specAfter = null;
    game.tribes[tribe].met = true;
    if (kind === 'patrol' && game.tribes[tribe].attitude < 10) {
      const lots = 2 + Math.floor(D.TRIBES[tribe].pride / 2);
      this.history.push(`Su portavoz exige un tributo por cruzar sus tierras: unos ${lots} lotes de mercancías.`);
    }
  }
  get ts() { return this.g.tribes[this.tribe]; }
  get info() { return D.TRIBES[this.tribe]; }
  mood() { const a = this.ts.attitude; return a < -60 ? 'Furiosos' : a < -30 ? 'Hostiles' : a < -5 ? 'Recelosos' : a < 20 ? 'Cautelosos' : a < 50 ? 'Amistosos' : 'Aliados'; }
  talkSkill() { return this.g.best('talk') + (this.g.hasGuide() ? 3 : 0) + CV.story.talkBonus(this.g); }
  chance(base, per) {
    let p = base + (per === undefined ? .04 : per) * this.talkSkill() + .004 * this.ts.attitude - .03 * this.info.pride;
    if (this.g.hasGuide()) p += .1;
    return clamp(p, .05, .95);
  }
  spend(kind, units) {
    const s = this.g.sup;
    if (kind === 'goods') { if (s.goods < units) return false; s.goods -= units; }
    else if (kind === 'food') { if (s.food < 50 * units) return false; s.food -= 50 * units; }
    else if (kind === 'ammo') { if (s.ammo < units) return false; s.ammo -= units; }
    else if (kind === 'medicine') { if (s.medicine < units) return false; s.medicine -= units; }
    return true;
  }
  tick() {
    this.patience--;
    if (this.patience <= 0 && !this.ended) {
      this.ended = true;
      if (this.kind === 'tense' && this.ts.attitude < 5) { this.result = 'hostil'; this.history.push('Se les agota la paciencia. La partida de guerra da media vuelta y carga.'); }
      else this.history.push('Se hace tarde; la delegación se despide.');
    }
  }
  do(key, arg) {
    const g = this.g, ts = this.ts, rng = g.rng;
    let msg = '';
    if (this.ended) return 'La reunión ha terminado.';
    if (key === 'saludo') {
      if (rng.random() < this.chance(.45)) { ts.attitude += rng.uniform(3, 6); msg = 'Saludas con respeto, mostrando las manos vacías. Asienten con gravedad: les ha gustado el gesto.'; }
      else { ts.attitude -= 2; msg = 'Tu saludo se malinterpreta. Intercambian miradas frías.'; }
      this.tick();
    } else if (key === 'regalo') {
      const [kind, units] = arg;
      const VAL = {goods: 4, food: 3, ammo: 5, medicine: 6};
      if (!this.spend(kind, units)) return 'No tienes eso para regalar.';
      let val = VAL[kind] * units * (this.info.wants === kind ? 1.5 : 1);
      if (kind === 'ammo') { val = VAL[kind] * units / 20 * (this.info.wants === kind ? 1.5 : 1); ts.arms += units / 20 * .5; }
      const gain = val * Math.max(.25, 1 - Math.max(0, ts.attitude) / 120);
      ts.attitude = Math.min(100, ts.attitude + gain); g.stats.gifts++;
      const nm = {goods: 'lote(s) de mercancías', food: '× 50 lb de comida', ammo: 'balas', medicine: 'dosis de medicina'}[kind];
      msg = `Entregas ${units} ${nm}; ${this.info.wants === kind ? 'les agrada muchísimo' : 'lo aceptan con cortesía'}. (+${Math.round(gain)})`;
      if (kind === 'ammo') msg += ' Ahora tienen más pólvora… para bien o para mal.';
      this.tick();
    } else if (key === 'comerciar') {
      if (ts.attitude < -20) return 'No están de humor para comerciar con quien no respetan.';
      this.shopRequested = true;
      if (!this.used.has('trade')) { ts.attitude += 2; this.used.add('trade'); }
      msg = 'Se extienden mantas en el suelo para el trueque.';
    } else if (key === 'paso') {
      if (ts.attitude < -25) return 'No quieren oír hablar de pactos mientras haya tanta desconfianza.';
      const lots = 3 + Math.floor(this.info.pride / 2);
      if (g.sup.goods < lots) return `El tributo ronda los ${lots} lotes de mercancías y no los tienes.`;
      g.sup.goods -= lots;
      if (rng.random() < this.chance(.38, .045)) {
        const days = 12 + Math.floor(Math.max(0, ts.attitude) / 8);
        ts.treatyUntil = g.day + days; ts.attitude += 4; g.stats.treaties++; this.result = 'paz';
        msg = `Paso seguro acordado: ${days} días de tregua. Pagas ${lots} lotes y el jefe sella el pacto con humo de pipa.`;
      } else { ts.attitude -= 3; msg = `Aceptan el tributo (${lots} lotes) pero no prometen nada: «veremos qué dicen los espíritus».`; }
      this.tick();
    } else if (key === 'info') {
      if (g.sup.goods < 1) return 'Necesitas al menos 1 lote de mercancías para pagar la información.';
      g.sup.goods--; ts.attitude += 2;
      const nxt = g.nextTribe(), parts = [];
      if (nxt && nxt !== this.tribe) { const a = g.tribes[nxt].attitude; parts.push(`Cuentan que más adelante los ${g.tribeName(nxt)} están ${a < -30 ? 'muy hostiles.' : a < 0 ? 'inquietos.' : a < 30 ? 'tranquilos.' : 'bien dispuestos.'}`); }
      parts.push(`Calculan que la partida de guerra más cercana tardará ${rng.int(3, 12)} días.`);
      if (rng.random() < .5) { g.sup.food += 25; parts.push('Te indican un manantial con caza abundante (+25 lb de comida).'); }
      msg = parts.join(' '); this.tick();
    } else if (key === 'guia') {
      if (ts.attitude < 10) return 'Necesitas ganarte más su confianza antes de que alguien guíe a forasteros.';
      if (g.sup.goods < 8) return 'El guía pide 8 lotes de mercancías.';
      g.sup.goods -= 8; g.guideUntil = g.mile + 450; g.guideTribe = this.tribe; ts.attitude += 3;
      msg = 'Un joven intérprete se une a la caravana por unas 450 millas. Facilita los tratos y reduce peligros.'; this.tick();
    } else if (key === 'alianza') {
      if (ts.attitude < 55 || ts.treatyUntil < 0) return 'Una alianza exige confianza (trato 55+) y un pacto previo.';
      if (g.sup.goods < 10) return 'El banquete de alianza cuesta 10 lotes de mercancías.';
      g.sup.goods -= 10;
      if (rng.random() < this.chance(.4, .05)) { ts.allied = true; ts.attitude += 6; msg = '¡Alianza sellada! Sus jinetes cabalgarán con vosotros si os atacan otros.'; }
      else { ts.attitude -= 2; msg = 'Piden más tiempo para consultar con el consejo.'; }
      this.tick();
    } else if (key === 'fuerza') {
      let p = .28 + .04 * g.best('shoot') + .015 * g.wagons.length + .01 * g.shooters().length - .04 * this.info.pride + (g.sup.ammo >= 60 ? .1 : -.1);
      p = clamp(p, .05, .85);
      if (rng.random() < p) { ts.treatyUntil = Math.max(ts.treatyUntil, g.day + 6); ts.attitude -= 8; msg = 'Los tiradores se alinean sobre las carretas con un estruendo de cerrojos. La partida se aparta… con rencor.'; }
      else {
        ts.attitude -= 16; msg = 'Tu exhibición los ofende. Hay gritos y flechas en los arcos.';
        if ((this.kind === 'tense' || this.kind === 'patrol') && rng.random() < .5) { this.result = 'hostil'; this.ended = true; msg += ' Ya no hay vuelta atrás.'; }
      }
      this.tick();
    } else if (key === 'eli') {
      const e = g.member('abuelo');
      if (!e || !g.flags.eli_friend) return 'Eli no está en condiciones de hablar por vosotros.';
      const p = .5 + (this.tribe === 'lakota' ? .3 : 0) + .002 * e.loyalty;
      if (rng.random() < p) {
        ts.attitude += 25; e.loyalty = Math.min(100, e.loyalty + 6);
        msg = 'Eli avanza solo, con las manos abiertas, y dice un nombre: «Sombra del Roble». Hay un silencio largo. Al rato, un hombre mayor responde. Las lanzas bajan.';
        this.result = 'paz'; ts.treatyUntil = Math.max(ts.treatyUntil, g.day + 10); this.ended = true;
      } else { ts.attitude -= 5; e.loyalty = Math.max(0, e.loyalty - 2); msg = 'Eli habla con firmeza, pero no es su gente: no conocen el nombre. Vuelve al círculo con la cabeza gacha.'; }
      this.tick();
    } else if (key === 'adios') {
      this.ended = true;
      if (this.kind === 'tense' && ts.attitude < 5) { this.result = 'hostil'; msg = 'Te retiras. Sin acuerdo, la partida de guerra continúa su avance.'; }
      else if (this.kind === 'patrol' && ts.attitude < -20 && !this.used.size) { ts.attitude -= 8; msg = 'Te marchas sin decir palabra; lo toman como un desaire.'; }
      else msg = 'Os despedís con cortesía.';
    }
    ts.attitude = clamp(ts.attitude, -100, 100);
    if (key !== 'adios' && this.kind === 'tense' && ts.attitude >= 25 && !this.ended) {
      this.ended = true; this.result = 'paz'; ts.treatyUntil = Math.max(ts.treatyUntil, g.day + 6); msg += ' La partida de guerra baja los arcos: no habrá batalla hoy.';
    }
    if (this.ended && this.kind === 'tense' && this.result === 'hostil') {
      this.specAfter = g.makeRaid(this.tribe); this.specAfter.tense = false; this.specAfter.prepTime = 12; this.specAfter.reason = 'El parlamento ha fracasado.';
    }
    this.history.push(msg);
    return msg;
  }
  finish() {
    if (this.result === 'hostil') {
      if (!this.specAfter) { this.specAfter = this.g.makeRaid(this.tribe); this.specAfter.prepTime = 12; }
      return this.specAfter;
    }
    return null;
  }
}
CV.Contact = Contact;

CV.tribeOffers = function (g, tid) {
  const r = new RNG((g.seed || 0) * 1000 + g.day * 7 + tid.length);
  const att = g.tribes[tid].attitude, rate = 1 + Math.max(0, att) / 120;
  const offers = [
    {give: ['food', Math.floor(50 * rate) + 25], take: ['goods', 1], text: 'Carne de bisonte seca (a cambio de 1 lote de mercancías)'},
    {give: ['oxen', 2], take: ['goods', 5], text: 'Un par de bueyes bien alimentados (por 5 mercancías)'},
    {give: ['goods', 2], take: ['food', 50], text: 'Pieles y mantas (por 50 lb de comida)'},
    {give: ['food', 120], take: ['ammo', 15], text: 'Pemmican de bisonte (por 15 balas)'},
    {give: ['medicine', 1], take: ['goods', 3], text: 'Hierbas curativas (por 3 mercancías)'},
    {give: ['ammo', 10], take: ['goods', 2], text: 'Munición recuperada (por 2 mercancías)'},
    {give: ['parts', 1], take: ['goods', 3], text: 'Un eje de buena madera (por 3 mercancías)'},
  ];
  r.shuffle(offers);
  return offers.slice(0, 5);
};
CV.applyOffer = function (g, o) {
  const [gk, gn] = o.give, [tk, tn] = o.take;
  if (g.sup[tk] < tn) return [false, 'No tienes lo que piden.'];
  g.sup[tk] -= tn; g.sup[gk] += gn;
  return [true, 'Trato cerrado.'];
};
})(globalThis.CV = globalThis.CV || {});
