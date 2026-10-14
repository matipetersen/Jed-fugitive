/* Motor de combate en tiempo real: defensa 360° del círculo de carretas. Espejo de caravana/battle.py */
(function (CV) {
'use strict';
const D = CV.data, clamp = CV.clamp;
const WAGON_L = 92, WAGON_GAP = 14, FIELD_RADIUS = 640, GIVE_UP = 260, RIFLE_RANGE = 380, PLATFORM_RANGE = 55, WALK = 95;
const angDiff = (a, b) => ((a - b + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
const hyp = Math.hypot;
let FOE_ID = 0;

class Battle {
  constructor(game, spec, seed) {
    this.game = game; this.spec = spec;
    this.rng = new CV.RNG(seed !== undefined ? seed : Math.floor(game.rng.random() * 4294967295));
    this.time = 0; this.fightTime = 0; this.prep = spec.prepTime;
    this.phase = spec.prepTime > 0 ? 'prep' : 'fight'; this.done = false; this.result = null;
    this.policy = 'libre'; this.focus = null; this.foes = []; this.allies = []; this.arrows = [];
    this.msgs = []; this.fx = []; this.night = spec.night; this.parleyCd = 0; this.parleyAvailable = !!game.tribes[spec.foe];
    this.ammoStart = game.sup.ammo;
    this.totalFoes = spec.waves.reduce((a, w) => a + Object.values(w[2]).reduce((x, y) => x + y, 0), 0);
    this.killed = 0; this.fledCount = 0; this.deadNames = []; this.chiefDead = false; this.retreating = false; this.peace = false; this.meltUsed = 0; this.checkCd = 0;
    this.lastSpawn = 0; this.waveShift = 0; this.delaysUsed = 0; this.spawnedTotal = 0; this.warnedAmmo = false;
    this.pending = spec.waves.map(w => [w[0], w[1], Object.assign({}, w[2])]).sort((a, b) => a[0] - b[0]);
    this.allyPending = spec.allies > 0;
    game.normalizePosts();
    const n = Math.max(1, game.wagons.length);
    this.n = n; this.R = Math.max(118, n * (WAGON_L + WAGON_GAP) / (2 * Math.PI)); this.Rout = this.R + 30;
    this.wagons = game.wagons.map((w, i) => {
      const a = -Math.PI / 2 + 2 * Math.PI * i / n;
      return {ref: w, idx: i, angle: a, x: Math.cos(a) * this.R, y: Math.sin(a) * this.R, burning: 0, burnTime: 0, barricade: 0, buildProgress: 0, stakes: 0, destroyed: false, flash: 0};
    });
    this.colonists = game.living().map(c => {
      const a = this.rng.uniform(0, 2 * Math.PI), r = this.rng.uniform(25, Math.max(30, this.R - 55));
      return {ref: c, x: Math.cos(a) * r, y: Math.sin(a) * r, tx: 0, ty: 0, task: 'idle', cool: 0, wander: 0, flash: 0, workTarget: null, aim: null, panicked: false};
    });
    for (const bc of this.colonists) this.assignIdleTarget(bc);
    this.say(spec.prepTime > 0 ? `¡Cerrad el círculo! ${this.colonists.length} colonos, ${n} carretas.` : '¡Al combate!');
    if (spec.reason) this.say(spec.reason, '#ffbe78');
    if (this.night) this.say('Es de noche: sólo se ve lo que ilumina el fuego y los faroles.', '#a0beff');
  }
  say(text, color) { this.msgs.push([this.time, text, color || '#ebe1c3']); if (this.msgs.length > 8) this.msgs.shift(); }
  emit(...ev) { this.fx.push(ev); if (this.fx.length > 400) this.fx.splice(0, 100); }
  sector(ang) { const step = 2 * Math.PI / this.n; const k = Math.round((ang + Math.PI / 2) / step); return ((k % this.n) + this.n) % this.n; }
  postPos(w, slot) {
    const wg = this.wagons[w], r = this.R - 30, off = (slot === 'tirador' ? -.17 : .17), a = wg.angle + off * 90 / Math.max(60, this.R) * 1.15;
    return [Math.cos(a) * r, Math.sin(a) * r];
  }
  isLit(x, y) {
    if (!this.night) return true;
    if (hyp(x, y) < this.R + 190) return true;
    for (const w of this.wagons) if (w.ref.lantern && !w.destroyed && hyp(x - w.x, y - w.y) < 300) return true;
    for (const w of this.wagons) if (w.burning > 0 && hyp(x - w.x, y - w.y) < 150) return true;
    return false;
  }
  isVisible(f) { return !this.night || f.revealed > 0 || this.isLit(f.x, f.y); }
  aliveFoes() { return this.foes.filter(f => f.alive && !f.fled); }
  // ---------------------------------------------------------- órdenes
  startFight() { if (this.phase === 'prep') { this.phase = 'fight'; this.prep = 0; this.say('¡Aquí vienen!', '#ff9678'); } }
  assign(bc, w, slot) { if (w >= this.wagons.length || this.wagons[w].destroyed) return false; return this.game.assign(bc.ref, w, slot); }
  unassign(bc) { bc.ref.post = null; }
  threatMap() {
    const out = {}, foes = this.aliveFoes();
    for (const w of this.wagons) {
      if (w.destroyed) continue;
      let s = 0;
      for (const f of foes) { const d = hyp(f.x - w.x, f.y - w.y); if (d < RIFLE_RANGE + 80) s += 1 / Math.pow(1 + d / 140, 2) * ((f.state === 'attack' || f.state === 'inside') ? 1.6 : 1); }
      out[w.idx] = s;
    }
    return out;
  }
  autoAssign() { this.game.autoAssign(this.threatMap()); }
  setFocus(f) { this.focus = f && f.alive ? f : null; }
  orderBarricade(w) {
    const wg = this.wagons[w];
    if (!wg.destroyed || wg.barricade > 0 || wg.buildProgress > .0001) return false;
    if (this.game.sup.parts < 1) { this.say('No quedan repuestos para una barricada.', '#ff8c78'); return false; }
    this.game.sup.parts--; wg.buildProgress = .001; this.say(`Se levanta una barricada en el hueco ${w + 1}.`); return true;
  }
  orderStakes(w) {
    const wg = this.wagons[w];
    if (!wg || wg.destroyed) return false;
    if (wg.stakes > 55) { this.say(`La carreta ${w + 1} ya tiene estacas.`, '#c8c8a0'); return false; }
    if (this.game.sup.parts < 1) { this.say('No quedan repuestos para clavar estacas.', '#ff8c78'); return false; }
    this.game.sup.parts--; wg.stakes = 80; this.say(`Estacas afiladas frente a la carreta ${w + 1}: frenarán a los atacantes a pie.`, '#d2e6a0'); return true;
  }
  melt() {
    const s = this.game.sup;
    if (s.goods < 5) { this.say('Necesitas 5 mercancías para fundir en balas.', '#ff8c78'); return false; }
    s.goods -= 5; s.ammo += 12; this.meltUsed++; this.say('Se funden peltre y cucharas: +12 balas.', '#ffdc8c'); return true;
  }
  parleyChance(gift) {
    const g = this.game, ts = g.tribes[this.spec.foe];
    const loss = this.killed / Math.max(1, this.totalFoes), ourLoss = this.deadNames.length / Math.max(1, g.colonists.length);
    let p = .12 + .004 * ts.attitude + .03 * g.best('talk') + .12 * gift + .25 * loss + .1 * ourLoss;
    if (g.hasGuide()) p += .1;
    return clamp(p, .05, .85);
  }
  parley(gift) {
    gift = gift || 0;
    if (!this.parleyAvailable) return [false, 'Estos hombres no quieren hablar.'];
    if (this.phase === 'prep') return [false, 'Aún no ha empezado el combate.'];
    if (this.parleyCd > 0) return [false, 'Aún no pueden oírte; espera unos segundos.'];
    if (this.fightTime < 10) return [false, 'Hay que dejar que se oiga primero el estruendo.'];
    const g = this.game, cost = [0, 3, 8][gift];
    if (g.sup.goods < cost) return [false, 'No tienes mercancías para el regalo.'];
    g.sup.goods -= cost;
    const p = this.parleyChance(gift); this.parleyCd = 28;
    if (this.rng.random() < p) { this.peace = true; this.say('¡Un jefe alza la lanza! Los atacantes aceptan hablar.', '#aaffaa'); for (const f of this.aliveFoes()) f.state = 'flee'; return [true, 'El parlamento tiene éxito.']; }
    this.say('Rechazan el parlamento con gritos de guerra.', '#ff826e');
    for (const f of this.aliveFoes()) f.speed *= 1.05;
    return [false, 'Rechazan hablar.'];
  }
  // ---------------------------------------------------------- bucle
  update(dt) {
    if (this.done) return;
    this.time += dt; this.parleyCd = Math.max(0, this.parleyCd - dt);
    if (this.phase === 'prep') { this.prep -= dt; if (this.prep <= 0) this.startFight(); }
    else { this.fightTime += dt; this.spawnWaves(); }
    this.updateColonists(dt); this.updateWagons(dt);
    if (this.phase === 'fight') { this.updateFoes(dt); this.updateAllies(dt); this.updateArrows(dt); this.shoot(dt); this.moraleCheck(dt); this.checkEnd(); }
    for (const bc of this.colonists) bc.flash = Math.max(0, bc.flash - dt);
    for (const f of this.foes) { f.flash = Math.max(0, f.flash - dt); f.revealed = Math.max(0, f.revealed - dt); }
  }
  warnings() {
    if (this.phase === 'prep') return this.pending.slice(0, 3).map(([t, a, c]) => [a, t + Math.max(0, this.prep), c]);
    return this.pending.filter(([t]) => t + this.waveShift - this.fightTime < 9).map(([t, a, c]) => [a, t + this.waveShift - this.fightTime, c]);
  }
  dirText(ang) { const deg = ((ang * 180 / Math.PI) % 360 + 360) % 360; return ['este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste', 'norte', 'noreste'][Math.floor(((deg + 22.5) % 360) / 45)]; }
  spawnWaves() {
    while (this.pending.length) {
      const due = this.pending[0][0] + this.waveShift;
      const dec = this.game.director.waveDecision(this, due);
      if (dec === 'wait') break;
      if (dec !== 'now' && due > this.fightTime) break;
      const [, ang, comp] = this.pending.shift();
      this.lastSpawn = this.fightTime;
      const names = [];
      for (const kind in comp) {
        const cnt = comp[kind];
        names.push(`${cnt} ${D.FOES[kind].name.toLowerCase()}${cnt > 1 ? 's' : ''}`);
        for (let i = 0; i < cnt; i++) {
          const a = ang + this.rng.uniform(-.35, .35), r = FIELD_RADIUS + this.rng.uniform(0, 90);
          const f = this.newFoe(kind, Math.cos(a) * r, Math.sin(a) * r);
          if (kind === 'jinete' || kind === 'jefe') f.orbitR = this.Rout + this.rng.uniform(120, 200) + (kind === 'jefe' ? 90 : 0);
          if (kind === 'fuego') f.standR = this.Rout + this.rng.uniform(95, 150);
          if (kind === 'bandido') f.standR = this.Rout + this.rng.uniform(150, 230);
          this.foes.push(f); this.spawnedTotal++;
        }
      }
      this.say(`¡Oleada por el ${this.dirText(ang)}!: ` + names.join(', '), '#ffaa78');
      this.emit('wave', ang);
    }
    if (this.allyPending && this.fightTime > 6) {
      this.allyPending = false;
      for (let i = 0; i < this.spec.allies; i++) { const a = this.rng.uniform(0, 2 * Math.PI); this.allies.push({x: Math.cos(a) * (this.R + 260), y: Math.sin(a) * (this.R + 260), hp: 55, alive: true, cool: 0, life: 75, face: 0}); }
      this.say('¡Jinetes aliados cabalgan en vuestra ayuda!', '#aaffaa');
    }
  }
  newFoe(kind, x, y) {
    const d = D.FOES[kind], r = this.rng;
    const hs = 1 + .25 * this.game.mile / 2000;
    return {id: FOE_ID++, kind, x, y, hp: d.hp * hs, maxHp: d.hp * hs, speed: d.speed * r.uniform(.9, 1.1), state: 'approach', cool: r.uniform(1, 4), shots: r.int(3, 6), orbitR: 0, orbitDir: r.choice([-1, 1]),
      standR: 0, timer: 0, attackCool: r.uniform(0, 1), targetWagon: null, alive: true, fled: false, flash: 0, face: 0, revealed: 0, mounted: kind === 'jinete' || kind === 'jefe'};
  }
  // ---------------------------------------------------------- colonos
  assignIdleTarget(bc) { const a = this.rng.uniform(0, 2 * Math.PI), r = this.rng.uniform(32, Math.max(36, this.R - 62)); bc.tx = Math.cos(a) * r; bc.ty = Math.sin(a) * r; bc.wander = this.rng.uniform(3, 7); }
  move(o, tx, ty, speed, dt) {
    const dx = tx - o.x, dy = ty - o.y, d = hyp(dx, dy);
    if (d < 2) return true;
    const step = Math.min(d, speed * dt);
    o.x += dx / d * step; o.y += dy / d * step; o.face = Math.atan2(dy, dx);
    return d - step < 2;
  }
  updateColonists(dt) {
    const g = this.game, wounded = this.colonists.filter(bc => bc.ref.alive && bc.ref.health < 60);
    for (const bc of this.colonists) {
      if (!bc.ref.alive) continue;
      const c = bc.ref;
      const panic = c.loyalty < 25 && c.health < 55 && !c.isLeader;
      if (panic && c.post && !bc.panicked) { bc.panicked = true; this.say(`${c.name} pierde los nervios y abandona su puesto.`, '#ffbe82'); c.post = null; }
      if (c.health < 30 || (panic && c.health < 55)) { bc.task = 'wounded'; bc.tx = -14 + (c.cid % 5) * 8; bc.ty = 42 + (c.cid % 3) * 9; this.move(bc, bc.tx, bc.ty, WALK * .4, dt); continue; }
      const post = c.post;
      if (post && post[0] < this.wagons.length && !this.wagons[post[0]].destroyed) { bc.task = 'post'; const [px, py] = this.postPos(post[0], post[1]); this.move(bc, px, py, WALK, dt); continue; }
      if (post && (post[0] >= this.wagons.length || this.wagons[post[0]].destroyed)) c.post = null;
      const job = this.pickJob(bc, wounded);
      if (job) {
        const [kind, tgt] = job; bc.task = kind; bc.workTarget = tgt;
        if (kind === 'extinguish') { const w = this.wagons[tgt]; this.move(bc, w.x * .78, w.y * .78, WALK, dt); if (hyp(bc.x - w.x * .78, bc.y - w.y * .78) < 14) { w.burning -= dt * .35; if (w.burning <= 0) { w.burning = 0; w.burnTime = 0; } } }
        else if (kind === 'build') { const w = this.wagons[tgt]; this.move(bc, w.x * .8, w.y * .8, WALK, dt); if (hyp(bc.x - w.x * .8, bc.y - w.y * .8) < 18) { w.buildProgress += (.6 + c.build / 10) / (g.profession === 'carpintero' ? 4 : 7) * dt; if (w.buildProgress >= 1) { w.buildProgress = 0; w.barricade = 90; this.say(`Barricada terminada en el hueco ${tgt + 1}.`, '#c8e6a0'); } } }
        else if (kind === 'heal') { const t = tgt; this.move(bc, t.x + 8, t.y + 6, WALK, dt); if (hyp(bc.x - t.x, bc.y - t.y) < 18) t.ref.health = Math.min(100, t.ref.health + 2.2 * (.5 + c.medic / 5) * dt); }
        else if (kind === 'repair') { const w = this.wagons[tgt]; this.move(bc, w.x * .8, w.y * .8, WALK, dt); if (hyp(bc.x - w.x * .8, bc.y - w.y * .8) < 18) { const cap = w.ref.maxHp * .85; if (w.ref.hp < cap) w.ref.hp = Math.min(cap, w.ref.hp + 3.5 * (.5 + c.build / 8) * dt); } }
        continue;
      }
      let near = null;
      if ((c.group === 'adulto' || c.group === 'joven') && c.health > 30) near = this.foes.find(f => f.alive && !f.fled && f.state === 'inside' && hyp(f.x - bc.x, f.y - bc.y) < 60) || null;
      if (near) { bc.task = 'melee'; this.move(bc, near.x, near.y, WALK, dt); if (hyp(near.x - bc.x, near.y - bc.y) < 18) this.damageFoe(near, (6 + c.shoot) * dt * 1.6, c); continue; }
      bc.task = 'idle'; bc.wander -= dt; if (bc.wander <= 0) this.assignIdleTarget(bc);
      this.move(bc, bc.tx, bc.ty, WALK * .45, dt);
    }
    for (const bc of this.colonists) if (bc.ref.alive && bc.task === 'post' && bc.ref.post && bc.ref.post[1] === 'ayuda') {
      const w = this.wagons[bc.ref.post[0]];
      if (w.burning > 0) { w.burning -= dt * .28; if (w.burning <= 0) { w.burning = 0; w.burnTime = 0; } }
    }
  }
  pickJob(bc, wounded) {
    const c = bc.ref;
    const burning = this.wagons.filter(w => w.burning > 0 && !w.destroyed);
    if (burning.length) return ['extinguish', burning.reduce((a, b) => hyp(a.x - bc.x, a.y - bc.y) < hyp(b.x - bc.x, b.y - bc.y) ? a : b).idx];
    for (const w of this.wagons) if (w.destroyed && w.barricade <= 0 && w.buildProgress > 0 && c.group !== 'niño') return ['build', w.idx];
    if (wounded.length && c.medic >= 3 && c.group !== 'niño') {
      const cand = wounded.filter(x => x !== bc && x.ref.alive && x.ref.health < 70);
      if (cand.length) return ['heal', cand.reduce((a, b) => a.ref.health < b.ref.health ? a : b)];
    }
    if (c.group !== 'niño') {
      const hurt = this.wagons.filter(w => !w.destroyed && w.ref.hp < w.ref.maxHp * .8);
      if (hurt.length) return ['repair', hurt.reduce((a, b) => a.ref.hp / a.ref.maxHp < b.ref.hp / b.ref.maxHp ? a : b).idx];
    }
    return null;
  }
  // ---------------------------------------------------------- carretas
  updateWagons(dt) {
    for (const w of this.wagons) {
      w.flash = Math.max(0, w.flash - dt);
      if (w.destroyed) continue;
      if (w.burning > 0) {
        w.burnTime += dt; w.ref.hp -= 6 * w.burning * dt;
        if (w.burnTime > 18) { w.burning = 0; w.burnTime = 0; }
        else if (this.rng.random() < .03 * dt * 10 * .2) {
          const nb = this.wagons[((w.idx + this.rng.choice([-1, 1])) % this.n + this.n) % this.n];
          if (!nb.destroyed && nb.burning <= 0 && this.rng.random() < .5) { nb.burning = .7; nb.burnTime = 0; this.say(`¡El fuego se extiende a la carreta ${nb.idx + 1}!`, '#ff965a'); }
        }
      }
      if (w.ref.hp <= 0) this.destroyWagon(w);
    }
  }
  destroyWagon(w) {
    w.destroyed = true; w.ref.hp = 0; w.burning = 0;
    this.say(`¡La carreta ${w.idx + 1} ha caído! Hay un hueco en el círculo.`, '#ff786e');
    this.emit('boom', w.x, w.y);
    for (const c of this.game.colonists) if (c.post && c.post[0] === w.idx) c.post = null;
  }
  // ---------------------------------------------------------- disparo
  hitChance(bc, w, f) {
    const c = bc.ref, d = hyp(f.x - w.x, f.y - w.y), rng_ = RIFLE_RANGE + (w.ref.platform ? PLATFORM_RANGE : 0);
    const base = .24 + .04 * c.shoot;
    const distf = d <= 120 ? 1 : Math.max(.35, 1 - (d - 120) / (rng_ - 120) * .65);
    const hf = c.health < 50 ? .7 : 1, mf = .8 + .4 * (this.game.morale / 100);
    const nf = (this.night && !w.ref.lantern) ? .75 : 1, pf = w.ref.platform ? 1.15 : 1;
    const mv = (f.mounted && ['orbit', 'approach', 'retreat'].includes(f.state)) ? .8 : 1;
    const lf = 1 + .08 * (c.loyalty - 50) / 50;
    return clamp(base * distf * hf * mf * nf * pf * mv * lf, .05, .95);
  }
  targetsFor(w) {
    const rng_ = RIFLE_RANGE + (w.ref.platform ? PLATFORM_RANGE : 0);
    return this.foes.filter(f => f.alive && !f.fled && f.state !== 'flee' && hyp(f.x - w.x, f.y - w.y) <= rng_ && this.isVisible(f));
  }
  shoot(dt) {
    const g = this.game;
    for (const w of this.wagons) {
      if (w.destroyed) continue;
      const bc = this.colonists.find(b => b.ref.alive && b.ref.post && b.ref.post[0] === w.idx && b.ref.post[1] === 'tirador' && b.task === 'post');
      if (!bc) continue;
      bc.cool = Math.max(0, bc.cool - dt);
      if (bc.cool > 0 || this.policy === 'alto' || bc.ref.health < 15 || g.sup.ammo <= 0) continue;
      const [px, py] = this.postPos(w.idx, 'tirador');
      if (hyp(bc.x - px, bc.y - py) > 6) continue;
      if (w.ref.cannon) { this.fireCannon(bc, w); continue; }
      let targets = this.targetsFor(w);
      if (this.policy === 'contenido') targets = targets.filter(f => hyp(f.x - w.x, f.y - w.y) < 210);
      if (!targets.length) continue;
      let tgt;
      if (this.focus && targets.includes(this.focus)) tgt = this.focus;
      else tgt = targets.reduce((a, b) => this.prio(a, w) <= this.prio(b, w) ? a : b);
      const c = bc.ref; let cd = 5.2 * (1.3 - .06 * c.shoot);
      const helper = g.postOf(w.idx, 'ayuda'); if (helper && helper.health > 25) cd *= .68;
      if (c.health < 50) cd *= 1.25;
      bc.cool = cd * this.rng.uniform(.9, 1.15);
      g.sup.ammo--;
      const hit = this.rng.random() < this.hitChance(bc, w, tgt);
      this.emit('shot', px, py, tgt.x, tgt.y, hit); bc.flash = .15; bc.aim = [tgt.x, tgt.y];
      if (hit) this.damageFoe(tgt, this.rng.uniform(30, 55) + 2 * (c.shoot - 5), c);
    }
    if (g.sup.ammo <= 0 && !this.warnedAmmo && this.fightTime > 0) { this.warnedAmmo = true; this.say('¡SIN MUNICIÓN! Funde utensilios o intenta parlamentar.', '#ff786e'); }
  }
  prio(f, w) { return hyp(f.x - w.x, f.y - w.y) - ((f.kind === 'fuego' || f.kind === 'bandido') ? 30 : 0) - ((f.state === 'inside' || f.state === 'attack') ? 90 : 0); }
  fireCannon(bc, w) {
    const g = this.game; let best = null, bestn = 0;
    for (const f of this.targetsFor(w)) {
      const d = hyp(f.x - w.x, f.y - w.y); if (d > 440 || d < 70) continue;
      const n = this.foes.filter(o => o.alive && !o.fled && hyp(o.x - f.x, o.y - f.y) < 58).length;
      if (n > bestn) { best = f; bestn = n; }
    }
    if (!best || g.sup.ammo < 3) return;
    const helper = g.postOf(w.idx, 'ayuda');
    bc.cool = (helper ? 6.4 : 9) * this.rng.uniform(.95, 1.1); g.sup.ammo -= 3;
    const [px, py] = this.postPos(w.idx, 'tirador');
    this.emit('cannon', px, py, best.x, best.y);
    for (const o of this.foes) { if (!o.alive || o.fled) continue; const d = hyp(o.x - best.x, o.y - best.y); if (d < 62) this.damageFoe(o, 85 * (1 - d / 140), bc.ref); }
  }
  damageFoe(f, dmg, by) {
    f.hp -= dmg; f.flash = .2; this.emit('hit', f.x, f.y);
    if (f.hp <= 0 && f.alive) {
      f.alive = false; this.killed++; if (by) by.kills++;
      this.emit('death', f.x, f.y, f.kind);
      if (f.kind === 'jefe') { this.chiefDead = true; this.say('¡El jefe de guerra ha caído! Sus hombres titubean.', '#beffa0'); for (const o of this.aliveFoes()) if (this.rng.random() < .6) o.state = 'flee'; }
    }
  }
  // ---------------------------------------------------------- enemigos
  nearestOpenSector(ang) {
    let best = null, bd = 9;
    for (const w of this.wagons) if (w.destroyed && w.barricade <= 0) { const d = Math.abs(angDiff(w.angle, ang)); if (d < bd) { best = w; bd = d; } }
    return bd < 1.6 ? best : null;
  }
  updateFoes(dt) {
    const boss = this.foes.filter(f => f.alive && f.kind === 'jefe');
    for (const f of this.foes) {
      if (!f.alive || f.fled) continue;
      let speed = f.speed;
      for (const b of boss) if (b !== f && hyp(b.x - f.x, b.y - f.y) < 200) { speed *= 1.15; break; }
      const r = hyp(f.x, f.y), ang = Math.atan2(f.y, f.x);
      if (f.state === 'flee') { f.x += f.x / Math.max(r, 1) * speed * 1.2 * dt; f.y += f.y / Math.max(r, 1) * speed * 1.2 * dt; f.face = ang; if (r > FIELD_RADIUS + 40) { f.fled = true; this.fledCount++; } continue; }
      if (f.kind === 'jinete' || f.kind === 'jefe') this.aiRider(f, r, ang, speed, dt);
      else if (f.kind === 'fuego') this.aiStander(f, r, ang, speed, dt, true);
      else if (f.kind === 'bandido') this.aiStander(f, r, ang, speed, dt, false);
      else this.aiMelee(f, r, ang, speed, dt);
    }
  }
  aiRider(f, r, ang, speed, dt) {
    if (f.state === 'approach') { if (r > f.orbitR + 8) this.move(f, f.x - f.x / r * 200, f.y - f.y / r * 200, speed, dt); else f.state = 'orbit'; }
    else if (f.state === 'orbit') {
      const w = (speed * .55) / Math.max(f.orbitR, 1) * f.orbitDir, na = ang + w * dt, rr = r + (f.orbitR - r) * Math.min(1, dt * 2);
      f.x = Math.cos(na) * rr; f.y = Math.sin(na) * rr; f.face = na + (Math.PI / 2) * f.orbitDir;
      f.cool -= dt;
      if (f.cool <= 0 && f.shots > 0) {
        f.cool = f.kind === 'jinete' ? this.rng.uniform(1.8, 3) : this.rng.uniform(3, 4.2); f.shots--; this.enemyArrow(f, false);
        if (f.shots <= 0) { f.state = 'retreat'; f.timer = this.rng.uniform(5, 9); }
      }
    } else if (f.state === 'retreat') {
      f.timer -= dt; this.move(f, f.x * 2, f.y * 2, speed, dt);
      if (f.timer <= 0) { f.state = 'approach'; f.shots = this.rng.int(3, 6); f.orbitDir = this.rng.choice([-1, 1]); f.orbitR = Math.max(this.Rout + 100, f.orbitR + this.rng.uniform(-30, 30)); }
    }
  }
  aiStander(f, r, ang, speed, dt, fire) {
    if (f.state === 'approach') { if (r > f.standR + 5) this.move(f, 0, 0, speed, dt); else { f.state = 'stand'; f.cool = this.rng.uniform(.5, 2.5); } }
    else {
      f.face = ang + Math.PI; f.cool -= dt;
      if (f.cool <= 0) { if (fire) { f.cool = this.rng.uniform(3.8, 5.5); this.enemyArrow(f, true); } else { f.cool = this.rng.uniform(3.4, 5); this.enemyRifle(f); } }
    }
  }
  aiMelee(f, r, ang, speed, dt) {
    const gap = this.nearestOpenSector(ang);
    if (r > this.Rout + 4) {
      if (gap) { const gx = Math.cos(gap.angle) * (this.Rout + 8), gy = Math.sin(gap.angle) * (this.Rout + 8); if (r > this.Rout + 60 || Math.abs(angDiff(gap.angle, ang)) > .08) { this.move(f, gx, gy, speed, dt); return; } }
      const sec = this.wagons[this.sector(ang)];
      if (!sec.destroyed && sec.stakes > 0) {
        if (r > this.Rout + 28) { this.move(f, Math.cos(ang) * (this.Rout + 24), Math.sin(ang) * (this.Rout + 24), speed, dt); return; }
        f.attackCool -= dt;
        if (f.attackCool <= 0) { f.attackCool = 1; sec.stakes -= 7 * (f.kind === 'jefe' ? 1.5 : 1); this.emit('chop', f.x, f.y); if (sec.stakes <= 0) { sec.stakes = 0; this.say(`Las estacas de la carreta ${sec.idx + 1} ceden.`, '#ff8c64'); } }
        return;
      }
      if (sec.destroyed && sec.barricade <= 0) { this.move(f, 0, 0, speed, dt); }
      else { this.move(f, Math.cos(ang) * (this.Rout + 2), Math.sin(ang) * (this.Rout + 2), speed, dt); if (hyp(f.x, f.y) <= this.Rout + 6) { f.state = 'attack'; f.targetWagon = sec.idx; } }
      return;
    }
    if (f.state === 'attack' || r <= this.Rout + 6) {
      const sec = this.wagons[this.sector(ang)];
      if (!sec.destroyed || sec.barricade > 0) { f.state = 'attack'; f.targetWagon = sec.idx; f.attackCool -= dt; if (f.attackCool <= 0) { f.attackCool = 1; this.meleeWagon(f, sec); } return; }
      f.state = 'inside';
    }
    const live = this.colonists.filter(b => b.ref.alive);
    if (!live.length) return;
    const tgt = live.reduce((a, b) => hyp(a.x - f.x, a.y - f.y) < hyp(b.x - f.x, b.y - f.y) ? a : b);
    const d = hyp(tgt.x - f.x, tgt.y - f.y);
    if (d > 14) this.move(f, tgt.x, tgt.y, speed, dt);
    else { f.attackCool -= dt; if (f.attackCool <= 0) { f.attackCool = .9; this.hurtColonist(tgt, this.rng.uniform(9, 16)); } }
    if (hyp(f.x, f.y) < 40) { f.timer += dt; if (f.timer > 3) { f.timer = 0; const s = this.game.sup; s.food = Math.max(0, s.food - 12); s.goods = Math.max(0, s.goods - (this.rng.random() < .4 ? 1 : 0)); } }
  }
  meleeWagon(f, sec) {
    const dmg = 9 * (f.kind === 'jefe' ? 1.5 : 1), reinforce = 1 - .08 * sec.ref.reinforced;
    if (sec.destroyed && sec.barricade > 0) { sec.barricade -= dmg; if (sec.barricade <= 0) { sec.barricade = 0; this.say(`¡La barricada del hueco ${sec.idx + 1} cede!`, '#ff8c64'); } this.emit('chop', f.x, f.y); return; }
    sec.ref.hp -= dmg * reinforce; sec.flash = .2; this.emit('chop', f.x, f.y);
    if (this.rng.random() < .3) { const tir = this.game.postOf(sec.idx, 'tirador'); if (tir) { const bc = this.colonists.find(b => b.ref === tir && b.ref.alive); if (bc) this.hurtColonist(bc, this.rng.uniform(7, 13)); } }
    if (sec.ref.hp <= 0 && !sec.destroyed) this.destroyWagon(sec);
  }
  enemyArrow(f, fire) {
    const ang = Math.atan2(f.y, f.x);
    let cands = this.wagons.filter(w => !w.destroyed && Math.abs(angDiff(w.angle, ang)) < 1);
    if (!cands.length) cands = this.wagons.filter(w => !w.destroyed);
    if (!cands.length) return;
    const w = this.rng.choice(cands); let tc = null;
    const hitCol = this.rng.random() < (.30 + (w.ref.platform ? .08 : 0) - .04 * w.ref.reinforced) && !fire;
    if (hitCol) tc = this.colonists.findIndex(bc => bc.ref.alive && bc.ref.post && bc.ref.post[0] === w.idx);
    if (tc === -1) tc = null;
    let tx = tc !== null ? this.colonists[tc].x : w.x * .98, ty = tc !== null ? this.colonists[tc].y : w.y * .98;
    tx += this.rng.uniform(-9, 9); ty += this.rng.uniform(-9, 9);
    this.arrows.push({x: f.x, y: f.y, tx, ty, fire, dmg: this.rng.uniform(12, 20), tw: w.idx, tc, speed: 460});
    f.flash = .1; f.revealed = 3; this.emit('bow', f.x, f.y, fire);
  }
  enemyRifle(f) {
    const ang = Math.atan2(f.y, f.x), cands = this.wagons.filter(w => !w.destroyed && Math.abs(angDiff(w.angle, ang)) < .9);
    if (!cands.length) return;
    const w = this.rng.choice(cands); this.emit('rifle', f.x, f.y, w.x, w.y); f.revealed = 3;
    const tir = this.colonists.filter(bc => bc.ref.alive && bc.ref.post && bc.ref.post[0] === w.idx);
    if (tir.length && this.rng.random() < .28 - .03 * w.ref.reinforced + (w.ref.platform ? .06 : 0)) this.hurtColonist(this.rng.choice(tir), this.rng.uniform(20, 32));
    else { w.ref.hp -= 9; w.flash = .15; if (w.ref.hp <= 0 && !w.destroyed) this.destroyWagon(w); }
  }
  hurtColonist(bc, dmg) {
    const c = bc.ref; if (!c.alive) return;
    c.health -= dmg * (c.group === 'adulto' ? .8 : 1) * ((c.group === 'niño' || c.group === 'anciano') ? 1.25 : 1);
    bc.flash = .35; this.emit('hurt', bc.x, bc.y);
    if (c.health <= 0) {
      const surv = .4 + .04 * this.game.best('medic') - ((c.group === 'niño' || c.group === 'anciano') ? .15 : 0);
      if (this.rng.random() < surv) { c.health = this.rng.uniform(3, 9); c.post = null; this.say(`¡${c.name} cae gravemente herido/a, pero sigue con vida!`, '#ffaa78'); return; }
      c.alive = false; c.cause = 'muerto en combate'; c.post = null; this.deadNames.push(c.name); this.game.stats.lost++;
      this.game.morale = Math.max(0, this.game.morale - 6); this.say(`¡${c.name} ha muerto!`, '#ff6e64'); this.emit('death_col', bc.x, bc.y);
    }
  }
  updateArrows(dt) {
    for (let i = this.arrows.length - 1; i >= 0; i--) {
      const a = this.arrows[i], dx = a.tx - a.x, dy = a.ty - a.y, d = hyp(dx, dy), step = a.speed * dt;
      if (d <= step) { this.arrows.splice(i, 1); this.arrowHit(a); } else { a.x += dx / d * step; a.y += dy / d * step; }
    }
  }
  arrowHit(a) {
    const w = this.wagons[a.tw];
    if (a.tc !== null) { const bc = this.colonists[a.tc]; if (bc.ref.alive && hyp(bc.x - a.tx, bc.y - a.ty) < 26) { this.hurtColonist(bc, a.dmg); return; } }
    if (w.destroyed) return;
    w.ref.hp -= 6 * (1 - .08 * w.ref.reinforced); w.flash = .15; this.emit('thunk', a.tx, a.ty);
    if (a.fire && this.rng.random() < .75 && w.burning <= 0) { w.burning = 1; w.burnTime = 0; this.say(`¡Flecha incendiaria! La carreta ${w.idx + 1} arde.`, '#ff9650'); }
    if (w.ref.hp <= 0 && !w.destroyed) this.destroyWagon(w);
  }
  updateAllies(dt) {
    for (const al of this.allies) {
      if (!al.alive) continue;
      al.life -= dt; al.cool -= dt;
      if (al.life <= 0) { al.alive = false; continue; }
      const foes = this.aliveFoes();
      if (!foes.length) { this.move(al, Math.cos(al.life) * (this.R + 220), Math.sin(al.life) * (this.R + 220), 160, dt); continue; }
      const tgt = foes.reduce((a, b) => hyp(a.x - al.x, a.y - al.y) < hyp(b.x - al.x, b.y - al.y) ? a : b);
      if (hyp(tgt.x - al.x, tgt.y - al.y) > 22) this.move(al, tgt.x, tgt.y, 190, dt);
      else if (al.cool <= 0) { al.cool = 1.1; this.damageFoe(tgt, this.rng.uniform(28, 45), null); if (this.rng.random() < .12) { al.hp -= 25; if (al.hp <= 0) al.alive = false; } }
    }
  }
  moraleCheck(dt) {
    this.checkCd -= dt;
    if (this.checkCd > 0 || this.retreating || this.peace) return;
    this.checkCd = .5;
    const cas = (this.killed + this.fledCount) / Math.max(1, this.totalFoes);
    let th = this.spec.foe !== 'bandidos' ? .55 : .45;
    if (this.foes.some(f => f.alive && f.kind === 'jefe')) th += .15;
    if (this.game.tribes[this.spec.foe] && this.game.tribes[this.spec.foe].arms > 6) th += .05;
    if (cas >= th && !this.pending.length) { this.retreating = true; this.say('¡El enemigo rompe filas y se retira!', '#beffa0'); for (const f of this.aliveFoes()) f.state = 'flee'; }
    if (this.fightTime > GIVE_UP && !this.retreating) { this.retreating = true; this.say('Cae la tarde; el enemigo se cansa y se retira.', '#beffa0'); for (const f of this.aliveFoes()) f.state = 'flee'; }
  }
  checkEnd() {
    const living = this.colonists.filter(b => b.ref.alive), can = living.filter(b => this.game.canShoot(b.ref));
    if (!living.length) { this.finish('derrota'); return; }
    if (this.wagons.every(w => w.destroyed) || (!can.length && this.aliveFoes().length && this.aliveFoes().some(f => hyp(f.x, f.y) < this.R))) { this.finish('derrota'); return; }
    if (!this.pending.length && !this.aliveFoes().length) {
      if (this.peace) this.finish('paz');
      else if (this.retreating || this.fledCount) this.finish(this.killed >= this.totalFoes * .6 ? 'victoria' : 'huida');
      else this.finish('victoria');
    }
  }
  finish(outcome) {
    if (this.done) return;
    this.done = true;
    const g = this.game;
    const res = {outcome, killed: this.killed, total: this.totalFoes, dead: this.deadNames.slice(), ammoUsed: Math.max(0, this.ammoStart - g.sup.ammo + this.meltUsed * 12), time: this.fightTime, wagonsLost: 0};
    const lost = this.wagons.filter(w => w.destroyed); res.wagonsLost = lost.length;
    if (lost.length) {
      const frac = lost.length / Math.max(1, this.wagons.length);
      g.sup.food = Math.max(0, g.sup.food * (1 - frac * .8)); g.sup.goods = Math.floor(g.sup.goods * (1 - frac * .7)); g.sup.ammo = Math.floor(g.sup.ammo * (1 - frac * .5));
      g.wagons = this.wagons.filter(w => !w.destroyed).map(w => w.ref);
      if (!g.wagons.length) g.wagons = [{hp: 40, maxHp: 240, reinforced: 0, platform: false, lantern: false, cannon: false}];
    }
    for (const c of g.colonists) if (c.alive && c.health < 8) c.health = 8;
    g.normalizePosts();
    this.result = res;
    this.say({victoria: '¡Victoria!', huida: 'El enemigo se ha retirado.', paz: 'Se ha acordado la paz.', derrota: 'Todo está perdido…'}[outcome]);
  }
}
CV.Battle = Battle;
CV.runHeadless = function (game, spec, seed, smart) {
  const b = new Battle(game, spec, seed); b.startFight();
  let t = 0, nxt = 0;
  while (!b.done && t < 600) {
    if (smart !== false && t >= nxt) { b.autoAssign(); nxt = t + 6; if (game.sup.parts > 0) for (const w of b.wagons) if (w.destroyed && w.barricade <= 0 && w.buildProgress <= 0) b.orderBarricade(w.idx); if (game.sup.parts > 6) { const th = b.threatMap(); b.wagons.filter(w => !w.destroyed && w.stakes <= 0).sort((a, c) => (th[c.idx] || 0) - (th[a.idx] || 0)).slice(0, 2).forEach(w => b.orderStakes(w.idx)); } }
    b.update(.1); t += .1;
  }
  if (!b.done) b.finish('huida');
  return b.result;
};
})(globalThis.CV = globalThis.CV || {});
