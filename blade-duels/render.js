/* Blade Duels - render. Rig vectorial procedural + dos skins (neón / primal).
 * La lógica de reglas devuelve eventos; Scene.playTurn() los traduce en animación.
 */
(function () {
  const BD = (globalThis.BD = globalThis.BD || {});
  const W = 960, H = 540, GROUND = 430, D2R = Math.PI / 180;
  const ZONE_Y = [-150, -102, -52];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const E = {
    lin: (t) => t,
    out: (t) => 1 - Math.pow(1 - t, 3),
    inout: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    back: (t) => { const c = 2.70158; return 1 + c * Math.pow(t - 1, 3) + (c - 1) * Math.pow(t - 1, 2); },
    in: (t) => t * t * t,
  };

  // ---------- poses (grados; 0 = adelante, 90 = abajo, -90 = arriba) ----------
  const P0 = { x: 0, lift: 0, lean: 6, tilt: 0, rot: 0, u: 35, f: -25, w: -62, bu: 70, bf: 120, fa: 25, fk: -30, ba: -25, bk: 25 };
  const PK = Object.keys(P0);
  const pose = (o) => Object.assign({}, P0, o);
  const mixPose = (a, b, t) => { const r = {}; PK.forEach((k) => { r[k] = lerp(a[k], b[k], t); }); return r; };

  const ZA = [-26, 0, 28];
  const POSES = {
    idle: pose({}),
    guard: [
      pose({ u: -50, f: -35, w: -18, lean: 3, bu: 20, bf: 60 }),
      pose({ u: 5, f: -50, w: -88, lean: 4, bu: 60, bf: 110 }),
      pose({ u: 62, f: 42, w: 60, lean: 10, fa: 34, fk: -55, ba: -30, bk: 34, bu: 80, bf: 140 }),
    ],
    slashWind: [
      pose({ x: -10, lean: -8, u: -130, f: -160, w: -165, bu: -70, bf: -100, fa: 18, fk: -28 }),
      pose({ x: -12, lean: -8, u: 178, f: 180, w: -125, bu: 150, bf: 170, fa: 20, fk: -30 }),
      pose({ x: -12, lean: 0, u: 128, f: 150, w: 125, bu: 110, bf: 150, fa: 36, fk: -58, ba: -34, bk: 30 }),
    ],
    slashStrike: [
      pose({ x: 22, lean: 26, u: 35, f: 45, w: 68, bu: 90, bf: 120, fa: 34, fk: -40, ba: -34, bk: 20 }),
      pose({ x: 24, lean: 18, u: 5, f: 0, w: 8, bu: 100, bf: 130, fa: 36, fk: -42, ba: -34, bk: 18 }),
      pose({ x: 22, lean: 12, u: 48, f: 22, w: -42, bu: 110, bf: 140, fa: 38, fk: -58, ba: -34, bk: 22 }),
    ],
    thrustWind: [0, 1, 2].map((z) => pose({ x: -14, lean: -10, u: 96, f: -6 + ZA[z] * 0.5, w: ZA[z], bu: 60, bf: 100, fa: 22, fk: -34, ba: -30, bk: 30 })),
    thrustStrike: [0, 1, 2].map((z) => pose({ x: 54, lean: 10 + z * 9, u: ZA[z] * 0.9 - 4, f: ZA[z] * 0.9, w: ZA[z], bu: 150, bf: 165, fa: 48, fk: -58, ba: -44, bk: 22 })),
    hit: pose({ x: -26, lean: -16, tilt: -14, u: 70, f: 100, w: 100, bu: 110, bf: 150, fa: 10, fk: -20, ba: -10, bk: 10 }),
    stagger: pose({ x: -40, lean: -28, tilt: -25, rot: -0.18, u: -30, f: -120, w: -150, bu: -40, bf: -100, fa: -5, fk: -10, ba: -40, bk: 15 }),
    dizzy: pose({ lean: 14, tilt: 18, u: 70, f: 110, w: 100, bu: 100, bf: 140, fa: 15, fk: -10, ba: -15, bk: 10 }),
    ko: pose({ x: -80, rot: -1.5, lean: -10, tilt: -20, u: 100, f: 130, w: 140, bu: 120, bf: 140, fa: 5, fk: -5, ba: -5, bk: 5 }),
    victory: pose({ lean: -4, u: -70, f: -95, w: -92, bu: -30, bf: -60, fa: 15, fk: -20 }),
  };

  function attackPose(type, zone, phase) {
    if (type === 'rest') return POSES.guard[1];
    const thrust = type === 'thrust';
    let p;
    if (phase === 'wind') {
      p = thrust ? POSES.thrustWind[zone] : POSES.slashWind[zone];
      if (type === 'quick' || type === 'feint') p = mixPose(POSES.idle, p, 0.68);
      if (type === 'heavy') p = Object.assign({}, p, { fa: p.fa + 12, fk: p.fk - 18, lean: p.lean - 6, x: p.x - 8 });
    } else {
      p = thrust ? POSES.thrustStrike[zone] : POSES.slashStrike[zone];
      if (type === 'quick') p = Object.assign({}, p, { x: p.x * 0.6 });
      if (type === 'heavy') p = Object.assign({}, p, { x: p.x + 14, lean: p.lean + 8 });
      if (type === 'feint') p = mixPose(attackPose('feint', zone, 'wind'), p, 0.4);
    }
    return p;
  }

  // ---------- rig (cinemática directa) ----------
  const T = 44, S = 44, TORSO = 62, UA = 34, FA = 32, NECK = 22;
  function rig(p, wlen) {
    const r = (a) => a * D2R;
    const foot = (a, k) => ({ x: T * Math.sin(r(a)) + S * Math.sin(r(a + k)), y: T * Math.cos(r(a)) + S * Math.cos(r(a + k)) });
    const ff = foot(p.fa, p.fk), bf = foot(p.ba, p.bk);
    const py = -Math.max(ff.y, bf.y) - p.lift;
    const pel = { x: 0, y: py };
    const sh = { x: Math.sin(r(p.lean)) * TORSO, y: py - Math.cos(r(p.lean)) * TORSO };
    const head = { x: sh.x + Math.sin(r(p.lean + p.tilt)) * NECK, y: sh.y - Math.cos(r(p.lean + p.tilt)) * NECK };
    const arm = (u, f) => {
      const el = { x: sh.x + UA * Math.cos(r(u)), y: sh.y + UA * Math.sin(r(u)) };
      return { el, hd: { x: el.x + FA * Math.cos(r(f)), y: el.y + FA * Math.sin(r(f)) } };
    };
    const fa = arm(p.u, p.f), ba = arm(p.bu, p.bf);
    const tip = { x: fa.hd.x + wlen * Math.cos(r(p.w)), y: fa.hd.y + wlen * Math.sin(r(p.w)) };
    return {
      pel, sh, head, fa, ba, tip,
      fk: { x: pel.x + T * Math.sin(r(p.fa)), y: pel.y + T * Math.cos(r(p.fa)) },
      ff: { x: pel.x + ff.x, y: pel.y + ff.y },
      bk: { x: pel.x + T * Math.sin(r(p.ba)), y: pel.y + T * Math.cos(r(p.ba)) },
      bf: { x: pel.x + bf.x, y: pel.y + bf.y },
    };
  }

  // ---------- helpers de trazo ----------
  function path(ctx, pts) {
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.stroke();
  }
  function neonLine(ctx, pts, w, col, a) {
    a = a == null ? 1 : a;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = col;
    ctx.globalAlpha = 0.1 * a; ctx.lineWidth = w * 3.6; path(ctx, pts);
    ctx.globalAlpha = 0.24 * a; ctx.lineWidth = w * 2.0; path(ctx, pts);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = a; ctx.lineWidth = w; path(ctx, pts);
    ctx.strokeStyle = '#fff'; ctx.globalAlpha = 0.75 * a; ctx.lineWidth = Math.max(1, w * 0.34); path(ctx, pts);
    ctx.globalAlpha = 1;
  }
  function inkLine(ctx, pts, w, col, outline) {
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = w + (outline == null ? 8 : outline); path(ctx, pts);
    ctx.strokeStyle = col; ctx.lineWidth = w; path(ctx, pts);
  }
  function arcPts(cx, cy, rad, a0, a1, n) {
    const out = [];
    for (let i = 0; i <= n; i++) { const a = lerp(a0, a1, i / n); out.push({ x: cx + Math.cos(a) * rad, y: cy + Math.sin(a) * rad }); }
    return out;
  }

  function weaponPts(shape, hand, ang, len) {
    const c = Math.cos(ang * D2R), s = Math.sin(ang * D2R);
    const at = (d, o) => ({ x: hand.x + c * d - s * (o || 0), y: hand.y + s * d + c * (o || 0) });
    switch (shape) {
      case 'spear': return { shaft: [at(-34), at(len - 22)], head: [at(len - 24, -6), at(len + 8), at(len - 24, 6)], guard: null };
      case 'axe': return { shaft: [at(-14), at(len)], head: [at(len - 4, -2), at(len - 2, -26), at(len + 14, -20), at(len + 12, 6)], guard: null };
      case 'dagger': return { shaft: [at(-4), at(len)], head: null, guard: [at(4, -7), at(4, 7)] };
      default: return { shaft: [at(-8), at(len)], head: null, guard: [at(8, -9), at(8, 9)] };
    }
  }

  function hash(str) { let h = 0; for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0; return Math.abs(h); }
  const SKINS = ['#f1c27d', '#e0a06a', '#c68642', '#8d5524', '#f5d0a9'];

  // ---------- luchador visual ----------
  class Actor {
    constructor(side, bx, face) {
      this.side = side; this.bx = bx; this.face = face;
      this.cur = Object.assign({}, P0); this.from = this.cur; this.to = this.cur; this.t = 1; this.dur = 0.001; this.ease = E.out;
      this.color = '#19e6ff'; this.weapon = BD.WEAPONS.katana; this.name = '';
      this.trail = []; this.swinging = false; this.ward = null; this.dizzy = false; this.flash = 0; this.phase = Math.random() * 6;
      this.skin = SKINS[0];
    }
    setFighter(f) {
      this.color = f.color; this.weapon = BD.WEAPONS[f.weapon]; this.name = f.name; this.skin = SKINS[hash(f.name) % SKINS.length];
    }
    go(p, dur, ease) { this.from = Object.assign({}, this.cur); this.to = p; this.t = 0; this.dur = Math.max(0.001, dur); this.ease = ease || E.out; }
    snap(p) { this.cur = Object.assign({}, p); this.from = this.cur; this.to = p; this.t = 1; }
    update(dt) {
      if (this.t < 1) {
        this.t = Math.min(1, this.t + dt / this.dur);
        const k = this.ease(this.t);
        PK.forEach((key) => { this.cur[key] = lerp(this.from[key], this.to[key], k); });
      }
      this.phase += dt;
      if (this.flash > 0) this.flash -= dt;
    }
    drawPose(time) {
      const p = Object.assign({}, this.cur);
      const idle = this.t >= 1;
      const br = Math.sin(time * 3 + this.phase) * (idle ? 1 : 0.4);
      p.lean += br * 1.2; p.u += br * 2; p.bu += br * 2; p.lift += Math.abs(br) * 0.6;
      if (this.dizzy) { p.tilt += Math.sin(time * 5) * 8; p.lean += Math.sin(time * 4) * 5; }
      return p;
    }
    toWorld(pt, p) {
      const c = Math.cos(p.rot), s = Math.sin(p.rot);
      const x = pt.x * c - pt.y * s + p.x, y = pt.x * s + pt.y * c;
      return { x: this.bx + this.face * x, y: GROUND + y };
    }
  }

  // ---------- Scene ----------
  class Scene {
    constructor(canvas) {
      this.cv = canvas; this.ctx = canvas.getContext('2d');
      canvas.width = W; canvas.height = H;
      this.theme = 'neon'; this.speed = 1; this.time = 0; this.clock = 0; this.sched = [];
      this.actors = { a: new Actor('a', 300, 1), b: new Actor('b', 660, -1) };
      this.parts = []; this.texts = []; this.banners = []; this.callouts = [];
      this.shake = 0; this.freeze = 0; this.impact = 0; this.flashWhite = 0; this.zoom = 0; this.slowmo = 0;
      this.hud = { a: this.blankHud(), b: this.blankHud(), round: 1, turn: 0, limit: 14 };
      this.hudShow = { a: { hp: 1, ghost: 1, st: 1 }, b: { hp: 1, ghost: 1, st: 1 } };
      this.bg = {};
      this.last = 0; this.running = false;
      this.reset();
    }
    blankHud() { return { name: '', title: '', hp: 1, maxHp: 1, st: 1, maxSt: 1, chain: 0, open: false, wins: 0 }; }
    reset() { ['a', 'b'].forEach((k) => { this.actors[k].snap(POSES.idle); this.actors[k].ward = null; this.actors[k].dizzy = false; this.actors[k].trail = []; }); }
    setTheme(t) { this.theme = t; }
    setFighters(fa, fb) {
      this.actors.a.setFighter(fa); this.actors.b.setFighter(fb); this.reset();
    }
    setHud(side, f, wins) {
      const h = this.hud[side];
      Object.assign(h, { name: f.name, title: f.title, hp: f.hp, maxHp: f.maxHp, st: f.st, maxSt: f.maxSt, chain: f.chain.length, open: f.open, wins: wins == null ? h.wins : wins });
      this.actors[side].dizzy = f.open;
    }
    syncHudInstant() { ['a', 'b'].forEach((k) => { const h = this.hud[k]; this.hudShow[k] = { hp: h.hp / h.maxHp, ghost: h.hp / h.maxHp, st: h.st / h.maxSt }; }); }

    at(t, fn) { this.sched.push({ at: this.clock + t, fn }); this.sched.sort((x, y) => x.at - y.at); }
    wait(t) { return new Promise((res) => this.at(t, res)); }

    // ----- ciclo -----
    start() {
      if (this.running) return;
      this.running = true;
      const loop = (ts) => {
        if (!this.running) return;
        const real = Math.min(0.05, (ts - (this.last || ts)) / 1000);
        this.last = ts;
        this.tick(real);
        this.draw();
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
    tick(real) {
      this.time += real;
      this.shake = Math.max(0, this.shake - real * 30);
      this.zoom = Math.max(0, this.zoom - real * 0.25);
      this.flashWhite = Math.max(0, this.flashWhite - real * 4);
      this.impact = Math.max(0, this.impact - real);
      if (this.freeze > 0) { this.freeze -= real; return; }
      const dt = real * this.speed * (this.slowmo > 0 ? 0.3 : 1);
      if (this.slowmo > 0) this.slowmo -= real;
      this.clock += dt;
      while (this.sched.length && this.sched[0].at <= this.clock) this.sched.shift().fn();
      ['a', 'b'].forEach((k) => {
        const a = this.actors[k];
        a.update(dt);
        if (a.swinging) {
          const p = a.cur, rg = rig(p, a.weapon.len);
          const base = a.toWorld({ x: lerp(rg.fa.hd.x, rg.tip.x, 0.25), y: lerp(rg.fa.hd.y, rg.tip.y, 0.25) }, p);
          const tip = a.toWorld(rg.tip, p);
          a.trail.push({ bx: base.x, by: base.y, tx: tip.x, ty: tip.y, age: 0 });
        }
        a.trail.forEach((t) => { t.age += dt; });
        a.trail = a.trail.filter((t) => t.age < 0.22).slice(-16);
        if (a.ward) a.ward.t += dt;
        const hs = this.hudShow[k], h = this.hud[k];
        const tgt = h.hp / h.maxHp;
        hs.hp += (tgt - hs.hp) * Math.min(1, dt * 14);
        hs.ghost += (hs.ghost > tgt ? -Math.min(hs.ghost - tgt, dt * 0.35) : tgt - hs.ghost);
        hs.st += (h.st / h.maxSt - hs.st) * Math.min(1, dt * 8);
      });
      this.parts.forEach((p) => {
        p.life -= dt;
        if (p.type === 'spark' || p.type === 'shard' || p.type === 'blob') { p.x += p.vx * dt; p.y += p.vy * dt; p.vy += (p.g || 0) * dt; p.vx *= 1 - dt * 2; }
        if (p.type === 'ring') p.r += p.vr * dt;
      });
      this.parts = this.parts.filter((p) => p.life > 0);
      this.texts.forEach((t) => { t.life -= dt; t.y -= t.vy * dt; });
      this.texts = this.texts.filter((t) => t.life > 0);
      this.banners.forEach((b) => { b.t += dt; });
      this.banners.filter((b) => b.t >= b.dur).forEach((b) => b.done());
      this.banners = this.banners.filter((b) => b.t < b.dur);
      this.callouts.forEach((c) => { c.t += dt; });
      this.callouts = this.callouts.filter((c) => c.t < c.dur);
    }

    // ----- efectos -----
    sparks(x, y, n, col, speed, dir, spread) {
      for (let i = 0; i < n; i++) {
        const a = (dir == null ? Math.random() * 6.283 : dir + (Math.random() - 0.5) * (spread || 1.6));
        const sp = speed * (0.4 + Math.random());
        this.parts.push({ type: 'spark', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 500, life: 0.25 + Math.random() * 0.3, max: 0.5, col, size: 2 + Math.random() * 2 });
      }
    }
    ring(x, y, col, r1, w) { this.parts.push({ type: 'ring', x, y, r: 6, vr: r1 * 5, life: 0.28, max: 0.28, col, size: w || 4 }); }
    shards(x, y, n, col) {
      for (let i = 0; i < n; i++) {
        const a = Math.random() * 6.283, sp = 120 + Math.random() * 280;
        this.parts.push({ type: 'shard', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 120, g: 900, life: 0.5 + Math.random() * 0.3, max: 0.8, col, size: 5 + Math.random() * 7, rot: Math.random() * 6 });
      }
    }
    floatText(x, y, text, col, size) { this.texts.push({ x, y, text, col, size: size || 28, life: 1.0, max: 1.0, vy: 46 }); }
    callout(text, col) { this.callouts.push({ text, col, t: 0, dur: 1.2 }); }
    banner(text, sub, dur) {
      return new Promise((res) => { this.banners.push({ text, sub: sub || '', t: 0, dur: dur || 1.1, done: res }); });
    }
    doFreeze(s) { this.freeze = Math.max(this.freeze, s); }
    doShake(m) { this.shake = Math.max(this.shake, m); }

    contact(D, zone) {
      return { x: D.bx + D.face * 34, y: GROUND + ZONE_Y[Math.max(0, zone)] };
    }

    // ----- reproducir un turno -----
    // mv: movimientos revelados; res: resultado de BD.step; after: estado posterior {a,b}
    playTurn(mv, res, after, winsNow) {
      return new Promise((resolve) => {
        const A = this.actors;
        const ev = {};
        res.events.forEach((e) => { ev[e.src] = e; });
        // fase 0: ward + windup
        ['a', 'b'].forEach((k) => {
          const a = A[k], m = mv[k];
          a.ward = { zone: m.block, t: 0, state: 'up', flash: 0 };
          a.swinging = false;
          a.go(attackPose(m.type, Math.max(0, m.zone), 'wind'), m.type === 'rest' ? 0.3 : (m.type === 'heavy' ? 0.42 : 0.34), E.out);
          if (m.type === 'heavy') this.sparksCharge(a);
        });
        this.hud.turn += 1;
        // stamina inmediato
        ['a', 'b'].forEach((k) => { this.hud[k].st = after[k].st; this.hud[k].chain = after[k].chain.length; });
        BD.Audio && BD.Audio.sfx('whoosh');
        // fase 1: golpe
        this.at(0.38, () => {
          ['a', 'b'].forEach((k) => {
            const a = A[k], m = mv[k];
            if (m.type === 'rest') return;
            a.swinging = true;
            a.go(attackPose(m.type, m.zone, 'strike'), m.type === 'quick' ? 0.09 : 0.12, E.back);
          });
          BD.Audio && BD.Audio.sfx('swing');
        });
        // fase 2: impacto
        this.at(0.5, () => {
          ['a', 'b'].forEach((k) => { this.hud[k].hp = after[k].hp; this.hud[k].open = after[k].open; });
          ['a', 'b'].forEach((k) => { if (ev[k]) this.applyEvent(ev[k], mv, k); });
        });
        // fase 3: recuperar
        this.at(1.0, () => {
          ['a', 'b'].forEach((k) => {
            const a = A[k]; a.swinging = false;
            a.dizzy = after[k].open;
            if (after[k].hp > 0) a.go(a.dizzy ? POSES.dizzy : POSES.idle, 0.35, E.inout);
            if (a.ward) a.ward.state = 'fade';
          });
        });
        this.at(1.3, () => { ['a', 'b'].forEach((k) => { A[k].ward = null; }); });
        this.at(1.5, resolve);
      });
    }

    sparksCharge(a) {
      for (let i = 0; i < 6; i++) this.parts.push({ type: 'ring', x: a.bx + a.face * 10, y: GROUND - 70, r: 60 + i * 6, vr: -150, life: 0.3 + i * 0.03, max: 0.45, col: a.color, size: 2 });
    }

    applyEvent(e, mv, k) {
      const A = this.actors, att = A[e.src], def = A[e.dst];
      const col = att.color, zone = e.zone;
      const pt = this.contact(def, zone);
      const wd = def.ward;
      const ap = BD.Audio ? (n) => BD.Audio.sfx(n) : () => {};
      switch (e.kind) {
        case 'hit': case 'punish': {
          def.go(POSES.hit, 0.09, E.out); def.flash = 0.18;
          this.sparks(pt.x, pt.y, 14 + e.dmg, col, 380, att.face > 0 ? -0.2 : Math.PI + 0.2, 1.8);
          this.ring(pt.x, pt.y, col, 40 + e.dmg);
          this.floatText(pt.x, pt.y - 20, '-' + e.dmg, '#fff', 26 + Math.min(18, e.dmg));
          this.doFreeze(0.05 + e.dmg * 0.003); this.doShake(4 + e.dmg * 0.5); this.zoom = Math.min(0.08, 0.02 + e.dmg * 0.002);
          if (e.dmg >= 18 || e.combo) this.impact = 0.12;
          if (e.kind === 'punish') this.callout('¡CASTIGO!', '#ffd60a');
          if (e.counter) this.callout('¡CONTRAGOLPE!', '#ffd60a');
          if (e.combo) { this.callout('¡' + e.combo.name.toUpperCase() + '!', col); this.doShake(14); this.impact = 0.14; }
          ap(e.dmg >= 18 ? 'heavy' : 'hit');
          break;
        }
        case 'block': {
          if (wd) { wd.flash = 0.25; }
          this.sparks(pt.x, pt.y, 10, '#ffe08a', 300, att.face > 0 ? Math.PI : 0, 1.4);
          att.go(mixPose(POSES.slashStrike[Math.max(0, zone)], POSES.hit, 0.35), 0.1, E.out);
          if (e.dmg > 0) this.floatText(pt.x, pt.y - 20, '-' + e.dmg, '#ffe08a', 20);
          this.doFreeze(0.04); this.doShake(3);
          ap('block');
          break;
        }
        case 'guardbreak': {
          if (wd) wd.state = 'broken';
          this.shards(pt.x, pt.y, 16, def.color);
          def.go(POSES.hit, 0.1, E.out); def.flash = 0.2;
          this.floatText(pt.x, pt.y - 20, '-' + e.dmg, '#fff', 26);
          this.callout('¡GUARDIA ROTA!', '#ff8c00');
          this.ring(pt.x, pt.y, '#ff8c00', 80); this.doFreeze(0.1); this.doShake(12); this.impact = 0.1;
          ap('break');
          break;
        }
        case 'parry': {
          if (wd) wd.flash = 0.35;
          att.go(POSES.stagger, 0.12, E.out); att.swinging = false;
          this.ring(pt.x, pt.y, '#fff', 90, 6); this.sparks(pt.x, pt.y, 22, '#fff', 480);
          this.callout('¡PARRY!', '#ffffff');
          this.doFreeze(0.12); this.doShake(10); this.flashWhite = 0.5; this.impact = 0.1;
          ap('parry');
          break;
        }
        case 'interrupt': {
          att.go(POSES.stagger, 0.1, E.out); att.swinging = false;
          this.sparks(att.bx + att.face * 20, GROUND - 90, 12, '#ffd60a', 260);
          this.callout('¡INTERRUMPIDO!', '#ffd60a');
          this.doFreeze(0.06); this.doShake(5);
          ap('block');
          break;
        }
        case 'feintOpen': {
          if (wd) wd.state = 'broken';
          def.go(POSES.dizzy, 0.15, E.out); def.dizzy = true;
          this.ring(pt.x, pt.y, '#ffd60a', 60);
          this.callout('¡ABIERTO!', '#ffd60a');
          this.doShake(4);
          ap('feint');
          break;
        }
        case 'whiff': {
          this.floatText(att.bx + att.face * 40, GROUND - 130, 'finta', '#bbb', 18);
          break;
        }
        case 'rest': {
          this.ring(att.bx, GROUND - 60, '#7dffb0', 44, 3);
          this.floatText(att.bx, GROUND - 160, 'respira', '#7dffb0', 18);
          break;
        }
        default: break;
      }
    }

    // fin de ronda
    async ko(winner, isKo) {
      const A = this.actors, L = A[winner === 'a' ? 'b' : 'a'], Wn = A[winner];
      if (isKo) {
        this.slowmo = 0.9; this.impact = 0.2; this.doShake(18);
        L.swinging = false; L.go(POSES.ko, 0.7, E.out); L.dizzy = false; L.ward = null;
        BD.Audio && BD.Audio.sfx('ko');
        await this.wait(0.6);
        Wn.go(POSES.victory, 0.4, E.back);
        await this.banner('¡K.O.!', '', 1.3);
      } else {
        Wn.go(POSES.victory, 0.4, E.back); L.go(POSES.dizzy, 0.4, E.out);
        await this.banner('¡TIEMPO!', '', 1.2);
      }
    }
    idleAll() { ['a', 'b'].forEach((k) => { const a = this.actors[k]; a.swinging = false; a.ward = null; a.dizzy = false; a.go(POSES.idle, 0.3, E.inout); }); }

    // ----- dibujo -----
    draw() {
      const ctx = this.ctx, neon = this.theme === 'neon';
      ctx.save();
      ctx.clearRect(0, 0, W, H);
      const sx = (Math.random() - 0.5) * this.shake, sy = (Math.random() - 0.5) * this.shake;
      const cz = (this.cv.clientWidth < 600 ? 1.3 : 1) * (1 + this.zoom);
      ctx.translate(W / 2 + sx, 330 + sy); ctx.scale(cz, cz); ctx.translate(-W / 2, -330);
      const silhouette = !neon && this.impact > 0;
      if (silhouette) this.drawImpactBg(ctx); else this.drawBg(ctx);
      ['a', 'b'].forEach((k) => this.drawShadow(ctx, this.actors[k]));
      ['a', 'b'].forEach((k) => this.drawTrail(ctx, this.actors[k], neon));
      ['a', 'b'].forEach((k) => this.drawActor(ctx, this.actors[k], neon, silhouette));
      this.drawParts(ctx, neon);
      ctx.restore();
      if (neon && this.impact > 0) this.drawGlitch(ctx);
      if (this.flashWhite > 0) { ctx.globalAlpha = Math.min(1, this.flashWhite) * 0.6; ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
      this.drawHud(ctx, neon);
      this.drawTexts(ctx, neon);
    }

    font(size, neon) { return (neon ? '800 ' : '900 ') + size + 'px ' + (neon ? 'Orbitron, "Trebuchet MS", "Segoe UI", sans-serif' : 'Bangers, Impact, "Arial Black", sans-serif'); }

    // fondos
    drawBg(ctx) {
      if (this.theme === 'neon') this.drawNeonBg(ctx); else this.drawPrimalBg(ctx);
    }
    drawNeonBg(ctx) {
      if (!this.bg.neon) {
        const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
        const sky = g.createLinearGradient(0, 0, 0, 340); sky.addColorStop(0, '#04030d'); sky.addColorStop(0.6, '#150636'); sky.addColorStop(1, '#4a0f63');
        g.fillStyle = sky; g.fillRect(0, 0, W, H);
        g.fillStyle = '#000'; for (let i = 0; i < 70; i++) { g.globalAlpha = Math.random() * 0.8; g.fillRect(Math.random() * W, Math.random() * 230, 2, 2); }
        g.globalAlpha = 1;
        // sol sintético
        const sg = g.createLinearGradient(0, 150, 0, 330); sg.addColorStop(0, '#ffe14d'); sg.addColorStop(0.5, '#ff4fa3'); sg.addColorStop(1, '#a22bff');
        g.save(); g.beginPath(); g.arc(W / 2, 250, 110, 0, 6.283); g.clip(); g.fillStyle = sg; g.fillRect(0, 130, W, 250);
        g.fillStyle = '#12052b'; for (let i = 0; i < 8; i++) { const y = 250 + i * 14; g.fillRect(0, y, W, 2 + i * 1.6); }
        g.restore();
        // skyline
        let x = 0; g.strokeStyle = '#3c7bff'; g.fillStyle = '#080419'; g.lineWidth = 2; g.shadowColor = '#3c7bff'; g.shadowBlur = 8;
        let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
        while (x < W) { const w = 40 + rnd() * 60, h = 50 + rnd() * 130; g.beginPath(); g.rect(x, 336 - h, w, h); g.fill(); g.stroke(); x += w + 4; }
        g.shadowBlur = 0;
        // piso
        const fl = g.createLinearGradient(0, 336, 0, H); fl.addColorStop(0, '#220845'); fl.addColorStop(1, '#05030d');
        g.fillStyle = fl; g.fillRect(0, 336, W, H - 336);
        this.bg.neon = c;
      }
      ctx.drawImage(this.bg.neon, 0, 0);
      // rejilla en perspectiva animada
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 336, W, H - 336); ctx.clip();
      ctx.strokeStyle = '#ff2d95'; ctx.lineWidth = 1.5; ctx.shadowColor = '#ff2d95'; ctx.shadowBlur = 6;
      const vp = { x: W / 2, y: 336 };
      for (let i = -14; i <= 14; i++) { ctx.beginPath(); ctx.moveTo(vp.x + i * 14, vp.y); ctx.lineTo(vp.x + i * 150, H); ctx.stroke(); }
      for (let i = 0; i < 9; i++) {
        const t = ((i + (this.time * 0.35) % 1) / 9); const y = vp.y + Math.pow(t, 2.1) * (H - vp.y);
        ctx.globalAlpha = 0.25 + t * 0.75; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }
      ctx.restore();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = '#ff2d95'; ctx.lineWidth = 2; ctx.shadowColor = '#ff2d95'; ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.moveTo(0, 336); ctx.lineTo(W, 336); ctx.stroke(); ctx.shadowBlur = 0;
    }
    drawPrimalBg(ctx) {
      if (!this.bg.primal) {
        const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
        g.fillStyle = '#f4a259'; g.fillRect(0, 0, W, 140);
        g.fillStyle = '#ee7b4f'; g.fillRect(0, 140, W, 110);
        g.fillStyle = '#c8452f'; g.fillRect(0, 250, W, 120);
        g.fillStyle = '#fbe3a1'; g.beginPath(); g.arc(700, 210, 92, 0, 6.283); g.fill();
        g.lineWidth = 6; g.strokeStyle = '#0b0b0b'; g.stroke();
        let seed = 11; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
        g.fillStyle = '#0b0b0b'; g.beginPath(); g.moveTo(0, 360);
        let x = 0; while (x < W) { x += 40 + rnd() * 70; g.lineTo(x - 20, 230 + rnd() * 90); g.lineTo(x, 360 - rnd() * 40); }
        g.lineTo(W, 370); g.lineTo(0, 370); g.fill();
        // árboles secos
        g.strokeStyle = '#0b0b0b'; g.lineCap = 'round';
        [[120, 360, 120], [840, 360, 96]].forEach(([tx, ty, th]) => {
          g.lineWidth = 9; g.beginPath(); g.moveTo(tx, ty); g.lineTo(tx - 6, ty - th); g.stroke();
          g.lineWidth = 5; g.beginPath(); g.moveTo(tx - 4, ty - th * 0.6); g.lineTo(tx - 40, ty - th * 0.9); g.moveTo(tx - 5, ty - th * 0.75); g.lineTo(tx + 34, ty - th * 1.05); g.stroke();
        });
        g.fillStyle = '#3a2418'; g.fillRect(0, 360, W, H - 360);
        g.fillStyle = '#5a3a26'; g.fillRect(0, 360, W, 14);
        g.strokeStyle = '#0b0b0b'; g.lineWidth = 6; g.beginPath(); g.moveTo(0, 361); g.lineTo(W, 361); g.stroke();
        g.strokeStyle = '#241309'; g.lineWidth = 3;
        for (let i = 0; i < 40; i++) { const gx = rnd() * W, gy = 380 + rnd() * 150; g.beginPath(); g.moveTo(gx, gy); g.lineTo(gx + 14 + rnd() * 30, gy + (rnd() - 0.5) * 4); g.stroke(); }
        g.fillStyle = '#000'; for (let i = 0; i < 1400; i++) { g.globalAlpha = 0.05 + rnd() * 0.08; g.fillRect(rnd() * W, rnd() * H, 2, 2); }
        this.bg.primal = c;
      }
      ctx.drawImage(this.bg.primal, 0, 0);
    }
    drawImpactBg(ctx) {
      ctx.fillStyle = '#d62828'; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 3;
      for (let i = 0; i < 46; i++) {
        const a = (i / 46) * 6.283 + this.time * 0.3, r0 = 150 + Math.random() * 120, r1 = 700;
        ctx.beginPath(); ctx.moveTo(W / 2 + Math.cos(a) * r0, 250 + Math.sin(a) * r0); ctx.lineTo(W / 2 + Math.cos(a) * r1, 250 + Math.sin(a) * r1); ctx.stroke();
      }
    }
    drawGlitch(ctx) {
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 6; i++) {
        const y = Math.random() * H, h = 4 + Math.random() * 18;
        ctx.globalAlpha = 0.35; ctx.drawImage(this.cv, 0, y, W, h, (Math.random() - 0.5) * 40, y, W, h);
      }
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }

    drawShadow(ctx, a) {
      const p = a.cur;
      ctx.save(); ctx.globalAlpha = this.theme === 'neon' ? 0.35 : 0.5;
      ctx.fillStyle = this.theme === 'neon' ? a.color : '#000';
      ctx.beginPath(); ctx.ellipse(a.bx + a.face * p.x * 0.8, GROUND + 4, 56, 9, 0, 0, 6.283); ctx.fill(); ctx.restore();
    }

    drawTrail(ctx, a, neon) {
      if (a.trail.length < 2) return;
      ctx.save();
      for (let i = 1; i < a.trail.length; i++) {
        const p0 = a.trail[i - 1], p1 = a.trail[i], k = 1 - p1.age / 0.22;
        if (k <= 0) continue;
        ctx.beginPath(); ctx.moveTo(p0.bx, p0.by); ctx.lineTo(p0.tx, p0.ty); ctx.lineTo(p1.tx, p1.ty); ctx.lineTo(p1.bx, p1.by); ctx.closePath();
        if (neon) { ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.55 * k; ctx.fillStyle = a.color; ctx.fill(); }
        else { ctx.globalAlpha = 0.9 * k; ctx.fillStyle = '#fff6df'; ctx.fill(); ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = 2; ctx.stroke(); }
      }
      ctx.restore();
    }

    drawActor(ctx, a, neon, sil) {
      const p = a.drawPose(this.time), rg = rig(p, a.weapon.len);
      ctx.save();
      ctx.translate(a.bx, GROUND); ctx.scale(a.face, 1); ctx.translate(p.x, 0); ctx.rotate(p.rot);
      const col = a.flash > 0 ? '#ffffff' : a.color;
      if (a.ward) this.drawWard(ctx, a, neon);
      if (neon) this.drawNeonBody(ctx, a, p, rg, col);
      else this.drawPrimalBody(ctx, a, p, rg, col, sil);
      if (a.dizzy) this.drawStars(ctx, rg.head, neon);
      ctx.restore();
    }

    drawNeonBody(ctx, a, p, rg, col) {
      const wp = weaponPts(a.weapon.shape, rg.fa.hd, p.w, a.weapon.len);
      neonLine(ctx, [rg.sh, rg.ba.el, rg.ba.hd], 4, col, 0.7);
      neonLine(ctx, [rg.pel, rg.bk, rg.bf], 5, col, 0.75);
      neonLine(ctx, [rg.pel, rg.sh], 6, col);
      neonLine(ctx, [rg.pel, rg.fk, rg.ff], 5, col);
      // pie
      neonLine(ctx, [rg.ff, { x: rg.ff.x + 12, y: rg.ff.y }], 4, col, 0.9);
      neonLine(ctx, [rg.bf, { x: rg.bf.x + 12, y: rg.bf.y }], 4, col, 0.7);
      // bufanda animada
      const sc = []; for (let i = 0; i < 6; i++) sc.push({ x: rg.sh.x - i * 9 - 4, y: rg.sh.y - 4 + Math.sin(this.time * 7 + i * 0.9 + a.phase) * (2 + i) + i * 2 });
      neonLine(ctx, sc, 3, '#ff2d95', 0.9);
      neonLine(ctx, arcPts(rg.head.x, rg.head.y, 12, 0, 6.283, 18), 4, col);
      neonLine(ctx, [rg.sh, rg.fa.el, rg.fa.hd], 5, col);
      neonLine(ctx, wp.shaft, 4, '#9ffcff');
      if (wp.head) neonLine(ctx, wp.head, 3.5, '#9ffcff');
      if (wp.guard) neonLine(ctx, wp.guard, 3, '#9ffcff');
    }

    drawPrimalBody(ctx, a, p, rg, col, sil) {
      const k = (c) => (sil ? '#0b0b0b' : c);
      const skin = k(a.skin), skin2 = k(shade(a.skin, -30)), cloth = k(col), pants = k(shade(col, -70)), steel = sil ? '#fff' : '#e8eef5';
      const wp = weaponPts(a.weapon.shape, rg.fa.hd, p.w, a.weapon.len);
      inkLine(ctx, [rg.sh, rg.ba.el, rg.ba.hd], 11, skin2);
      inkLine(ctx, [rg.pel, rg.bk, rg.bf], 14, shade(pants, 0));
      inkLine(ctx, [rg.bf, { x: rg.bf.x + 13, y: rg.bf.y }], 9, k('#2b2118'));
      inkLine(ctx, [rg.pel, rg.sh], 26, cloth, 9);
      inkLine(ctx, [rg.pel, rg.fk, rg.ff], 15, pants);
      inkLine(ctx, [rg.ff, { x: rg.ff.x + 14, y: rg.ff.y }], 10, k('#2b2118'));
      // cinturón
      inkLine(ctx, [{ x: rg.pel.x - 11, y: rg.pel.y - 6 }, { x: rg.pel.x + 11, y: rg.pel.y - 6 }], 6, k('#111'), 3);
      // cabeza
      ctx.fillStyle = '#0b0b0b'; ctx.beginPath(); ctx.arc(rg.head.x, rg.head.y, 18, 0, 6.283); ctx.fill();
      ctx.fillStyle = skin; ctx.beginPath(); ctx.arc(rg.head.x, rg.head.y, 14, 0, 6.283); ctx.fill();
      if (!sil) {
        // pelo y cinta
        ctx.fillStyle = '#0b0b0b'; ctx.beginPath(); ctx.arc(rg.head.x - 2, rg.head.y - 3, 15, Math.PI * 0.95, Math.PI * 2.05); ctx.lineTo(rg.head.x - 14, rg.head.y - 2); ctx.fill();
        inkLine(ctx, [{ x: rg.head.x - 14, y: rg.head.y - 6 }, { x: rg.head.x + 12, y: rg.head.y - 7 }], 5, col, 3);
        const tail = []; for (let i = 0; i < 5; i++) tail.push({ x: rg.head.x - 14 - i * 8, y: rg.head.y - 6 + Math.sin(this.time * 8 + i + a.phase) * (2 + i * 1.2) + i * 2 });
        inkLine(ctx, tail, 4, col, 3);
        // ojo furioso
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(rg.head.x + 6, rg.head.y + 1, 4.5, 3.2, 0, 0, 6.283); ctx.fill();
        ctx.fillStyle = '#0b0b0b'; ctx.beginPath(); ctx.arc(rg.head.x + 7.5, rg.head.y + 1.2, 1.8, 0, 6.283); ctx.fill();
        ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(rg.head.x, rg.head.y - 5); ctx.lineTo(rg.head.x + 11, rg.head.y - 1); ctx.stroke();
      }
      // arma
      const wcol = steel;
      inkLine(ctx, wp.shaft, a.weapon.shape === 'spear' || a.weapon.shape === 'axe' ? 6 : 7, a.weapon.shape === 'spear' || a.weapon.shape === 'axe' ? k('#7a4a25') : wcol, 6);
      if (wp.head) { ctx.beginPath(); ctx.moveTo(wp.head[0].x, wp.head[0].y); for (let i = 1; i < wp.head.length; i++) ctx.lineTo(wp.head[i].x, wp.head[i].y); ctx.closePath(); ctx.fillStyle = wcol; ctx.fill(); ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = 4; ctx.lineJoin = 'round'; ctx.stroke(); }
      if (wp.guard) inkLine(ctx, wp.guard, 5, k('#d4a017'), 5);
      inkLine(ctx, [rg.sh, rg.fa.el, rg.fa.hd], 11, skin);
      ctx.fillStyle = '#0b0b0b'; ctx.beginPath(); ctx.arc(rg.fa.hd.x, rg.fa.hd.y, 8, 0, 6.283); ctx.fill();
      ctx.fillStyle = skin; ctx.beginPath(); ctx.arc(rg.fa.hd.x, rg.fa.hd.y, 5.5, 0, 6.283); ctx.fill();
    }

    drawStars(ctx, head, neon) {
      for (let i = 0; i < 3; i++) {
        const a = this.time * 4 + i * 2.1, x = head.x + Math.cos(a) * 22, y = head.y - 26 + Math.sin(a) * 6;
        ctx.fillStyle = neon ? '#ffe14d' : '#fbd34d'; ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = neon ? 0 : 2;
        ctx.beginPath();
        for (let j = 0; j < 10; j++) { const rr = j % 2 ? 3 : 7, aa = (j / 10) * 6.283 - 1.57; ctx.lineTo(x + Math.cos(aa) * rr, y + Math.sin(aa) * rr); }
        ctx.closePath(); ctx.fill(); if (!neon) ctx.stroke();
      }
    }

    drawWard(ctx, a, neon) {
      const w = a.ward; if (!w) return;
      const fade = w.state === 'fade' ? Math.max(0, 1 - (w.t - 0.9) * 4) : 1;
      const alpha = clamp(w.t * 5, 0, 1) * fade;
      if (alpha <= 0) return;
      const cy = ZONE_Y[w.zone] - 6, cx = 40;
      if (w.state === 'broken') {
        const pts = arcPts(cx - 70, cy, 76, -0.45, -0.05, 6).concat(arcPts(cx - 70, cy, 76, 0.1, 0.45, 6));
        if (neon) neonLine(ctx, pts, 3, '#888', 0.4 * alpha); else inkLine(ctx, pts, 4, '#999', 4);
        return;
      }
      const pts = arcPts(cx - 70, cy, 76, -0.5, 0.5, 14);
      const boost = w.flash > 0 ? (w.flash -= 0.016, 1.8) : 1;
      if (neon) neonLine(ctx, pts, 4 * boost, w.flash > 0 ? '#fff' : '#66fcff', 0.85 * alpha);
      else { ctx.globalAlpha = alpha; inkLine(ctx, pts, 7 * boost, '#fff6df', 5); ctx.globalAlpha = 1; }
    }

    drawParts(ctx, neon) {
      this.parts.forEach((p) => {
        const k = clamp(p.life / p.max, 0, 1);
        ctx.save();
        if (neon) ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = k;
        if (p.type === 'spark') {
          ctx.strokeStyle = neon ? p.col : (k > 0.5 ? '#fff6df' : p.col); ctx.lineWidth = p.size; ctx.lineCap = 'round';
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * 0.04, p.y - p.vy * 0.04); ctx.stroke();
        } else if (p.type === 'ring') {
          ctx.strokeStyle = p.col; ctx.lineWidth = p.size * k + 1;
          if (!neon) { ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = p.size * k + 5; ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(1, p.r), 0, 6.283); ctx.stroke(); ctx.strokeStyle = p.col; ctx.lineWidth = p.size * k + 1; }
          ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(1, p.r), 0, 6.283); ctx.stroke();
        } else if (p.type === 'shard') {
          ctx.translate(p.x, p.y); ctx.rotate(p.rot + (p.max - p.life) * 6);
          ctx.fillStyle = p.col; ctx.beginPath(); ctx.moveTo(-p.size, -p.size / 2); ctx.lineTo(p.size, 0); ctx.lineTo(-p.size / 3, p.size / 1.5); ctx.closePath(); ctx.fill();
          if (!neon) { ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = 2; ctx.stroke(); }
        }
        ctx.restore();
      });
    }

    drawTexts(ctx, neon) {
      this.texts.forEach((t) => {
        const k = clamp(t.life / t.max, 0, 1), pop = 1 + Math.max(0, (0.85 - k) * -0.6) + (k > 0.85 ? (k - 0.85) * 3 : 0);
        ctx.save(); ctx.globalAlpha = Math.min(1, k * 2.2); ctx.textAlign = 'center'; ctx.font = this.font(t.size * pop, neon);
        if (neon) { ctx.shadowColor = t.col; ctx.shadowBlur = 12; ctx.fillStyle = t.col; ctx.fillText(t.text, t.x, t.y); }
        else { ctx.lineWidth = 7; ctx.strokeStyle = '#0b0b0b'; ctx.lineJoin = 'round'; ctx.strokeText(t.text, t.x, t.y); ctx.fillStyle = t.col; ctx.fillText(t.text, t.x, t.y); }
        ctx.restore();
      });
      this.callouts.forEach((c) => {
        const k = c.t / c.dur, sc = k < 0.15 ? E.back(k / 0.15) : 1, al = k > 0.75 ? 1 - (k - 0.75) * 4 : 1;
        ctx.save(); ctx.translate(W / 2, 168); ctx.scale(sc, sc); ctx.rotate(neon ? 0 : -0.05); ctx.globalAlpha = al; ctx.textAlign = 'center'; ctx.font = this.font(46, neon);
        if (neon) { ctx.shadowColor = c.col; ctx.shadowBlur = 22; ctx.fillStyle = '#fff'; ctx.fillText(c.text, 0, 0); ctx.shadowBlur = 8; ctx.fillStyle = c.col; ctx.globalAlpha = al * 0.6; ctx.fillText(c.text, 0, 0); }
        else { ctx.lineWidth = 10; ctx.strokeStyle = '#0b0b0b'; ctx.lineJoin = 'round'; ctx.strokeText(c.text, 0, 0); ctx.fillStyle = c.col === '#ffffff' ? '#fff6df' : c.col; ctx.fillText(c.text, 0, 0); }
        ctx.restore();
      });
      this.banners.forEach((b) => {
        const k = b.t / b.dur, sc = k < 0.18 ? E.back(k / 0.18) : 1 + (k - 0.18) * 0.06, al = k > 0.82 ? 1 - (k - 0.82) / 0.18 : 1;
        ctx.save(); ctx.translate(W / 2, H / 2 - 30); ctx.scale(sc, sc); ctx.globalAlpha = al; ctx.textAlign = 'center';
        ctx.font = this.font(96, neon);
        if (neon) { ctx.shadowColor = '#ff2d95'; ctx.shadowBlur = 30; ctx.fillStyle = '#fff'; ctx.fillText(b.text, 0, 0); ctx.shadowColor = '#19e6ff'; ctx.shadowBlur = 50; ctx.globalAlpha = al * 0.5; ctx.fillText(b.text, 0, 0); }
        else { ctx.rotate(-0.06); ctx.lineWidth = 16; ctx.strokeStyle = '#0b0b0b'; ctx.lineJoin = 'round'; ctx.strokeText(b.text, 0, 0); ctx.fillStyle = '#ffd23f'; ctx.fillText(b.text, 0, 0); }
        if (b.sub) { ctx.font = this.font(30, neon); ctx.globalAlpha = al; ctx.shadowBlur = 0; if (!neon) { ctx.lineWidth = 7; ctx.strokeText(b.sub, 0, 46); } ctx.fillStyle = '#fff'; ctx.fillText(b.sub, 0, 46); }
        ctx.restore();
      });
    }

    drawHud(ctx, neon) {
      const bars = [
        { k: 'a', x: 28, w: 400, dir: 1 },
        { k: 'b', x: W - 28, w: 400, dir: -1 },
      ];
      bars.forEach(({ k, x, w, dir }) => {
        const h = this.hud[k], s = this.hudShow[k], c = this.cv.clientWidth < 600, bh = c ? 34 : 22, y = c ? 10 : 22, sh = c ? 15 : 9;
        const col = this.actors[k].color;
        const x0 = dir > 0 ? x : x - w;
        ctx.save();
        // fondo
        if (neon) { ctx.fillStyle = 'rgba(8,4,24,.8)'; ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.shadowColor = col; ctx.shadowBlur = 10; }
        else { ctx.fillStyle = '#1a1209'; ctx.strokeStyle = '#0b0b0b'; ctx.lineWidth = 5; }
        roundRect(ctx, x0, y, w, bh, 4); ctx.fill(); ctx.stroke(); ctx.shadowBlur = 0;
        const fx = (frac) => (dir > 0 ? x0 : x0 + w - w * frac);
        // ghost
        ctx.fillStyle = neon ? 'rgba(255,255,255,.5)' : '#f2e8cf';
        ctx.fillRect(fx(s.ghost) + (dir > 0 ? 2 : 0), y + 2, Math.max(0, w * s.ghost - 2), bh - 4);
        const hpc = h.hp / h.maxHp < 0.3 ? '#ff4d4d' : (neon ? col : '#f4c430');
        ctx.fillStyle = hpc; if (neon) { ctx.shadowColor = hpc; ctx.shadowBlur = 10; }
        ctx.fillRect(fx(s.hp) + (dir > 0 ? 2 : 0), y + 2, Math.max(0, w * s.hp - 2), bh - 4); ctx.shadowBlur = 0;
        // aguante
        const sy = y + bh + 5;
        const tw = w * 0.62, tx = dir > 0 ? x0 : x0 + w - tw;
        ctx.fillStyle = neon ? 'rgba(8,4,24,.8)' : '#1a1209'; ctx.fillRect(tx, sy, tw, sh);
        ctx.fillStyle = neon ? '#7dffb0' : '#4cc35f'; ctx.fillRect(dir > 0 ? tx : tx + tw - tw * s.st, sy, tw * s.st, sh);
        ctx.strokeStyle = neon ? '#7dffb0' : '#0b0b0b'; ctx.lineWidth = neon ? 1 : 3; ctx.strokeRect(tx, sy, tw, sh);
        // racha
        for (let i = 0; i < 3; i++) {
          const px = dir > 0 ? tx + tw + 14 + i * 16 : tx - 14 - i * 16, on = i < h.chain;
          ctx.beginPath(); ctx.arc(px, sy + sh / 2, c ? 7.5 : 5.5, 0, 6.283);
          ctx.fillStyle = on ? '#ffd60a' : 'rgba(255,255,255,.12)'; ctx.fill(); ctx.strokeStyle = neon ? '#ffd60a' : '#0b0b0b'; ctx.lineWidth = neon ? 1 : 2.5; ctx.stroke();
        }
        // nombre
        ctx.textAlign = dir > 0 ? 'left' : 'right'; ctx.font = this.font(c ? 28 : 17, neon);
        const nx = dir > 0 ? x0 : x0 + w;
        if (neon) { ctx.shadowColor = col; ctx.shadowBlur = 10; ctx.fillStyle = '#fff'; ctx.fillText(h.name.toUpperCase(), nx, y + bh + sh + (c ? 38 : 31)); }
        else { ctx.lineWidth = 5; ctx.strokeStyle = '#0b0b0b'; ctx.lineJoin = 'round'; ctx.strokeText(h.name.toUpperCase(), nx, y + bh + sh + (c ? 38 : 31)); ctx.fillStyle = '#fff'; ctx.fillText(h.name.toUpperCase(), nx, y + bh + sh + (c ? 38 : 31)); }
        ctx.shadowBlur = 0;
        // rondas ganadas
        for (let i = 0; i < 2; i++) {
          const px = dir > 0 ? x0 + w - 10 - i * (c ? 26 : 20) : x0 + 10 + i * (c ? 26 : 20), on = i < h.wins;
          ctx.beginPath(); ctx.arc(px, y + bh + sh + (c ? 30 : 25), c ? 10 : 7, 0, 6.283); ctx.fillStyle = on ? '#ffd60a' : 'rgba(255,255,255,.1)'; ctx.fill();
          ctx.strokeStyle = neon ? '#ffd60a' : '#0b0b0b'; ctx.lineWidth = neon ? 1.5 : 3; ctx.stroke();
        }
        if (h.open) {
          ctx.font = this.font(c ? 22 : 14, neon); ctx.fillStyle = '#ffd60a'; ctx.textAlign = 'center';
          ctx.fillText('¡ABIERTO!', x0 + w / 2, y + bh / 2 + (c ? 8 : 5));
        }
        ctx.restore();
      });
      // centro: ronda y turno
      ctx.save(); ctx.textAlign = 'center';
      const cmp = this.cv.clientWidth < 600;
      ctx.font = this.font(cmp ? 30 : 18, neon);
      const label = (cmp ? 'R' : 'RONDA ') + this.hud.round;
      if (neon) { ctx.shadowColor = '#ff2d95'; ctx.shadowBlur = 10; ctx.fillStyle = '#fff'; } else { ctx.lineWidth = 5; ctx.strokeStyle = '#0b0b0b'; ctx.strokeText(label, W / 2, cmp ? 44 : 38); ctx.fillStyle = '#fff'; }
      ctx.fillText(label, W / 2, cmp ? 44 : 38);
      ctx.font = this.font(cmp ? 22 : 13, neon); ctx.fillStyle = neon ? '#bbb' : '#f2e8cf';
      ctx.fillText((cmp ? '' : 'TURNO ') + Math.min(this.hud.turn + 1, this.hud.limit) + '/' + this.hud.limit, W / 2, cmp ? 72 : 58);
      ctx.restore();
    }
  }

  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16), r = clamp((n >> 16) + amt, 0, 255), g = clamp(((n >> 8) & 255) + amt, 0, 255), b = clamp((n & 255) + amt, 0, 255);
    return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  Object.assign(BD, { Scene, POSES, attackPose, rig, W, H });
})();
