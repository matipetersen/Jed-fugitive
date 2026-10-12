/* Blade Duels - flujo del torneo e interfaz. */
(function () {
  const BD = globalThis.BD;
  const $ = (s) => document.querySelector(s);
  const ZN = BD.ZONES;
  const TN = (t) => BD.TYPES[t].name;
  const store = {
    get(k, d) { try { const v = localStorage.getItem('bd_' + k); return v == null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('bd_' + k, v); } catch (e) { /* sin storage */ } },
  };

  const ME = { name: 'Vos', title: 'Aspirante', color: '#19e6ff' };
  const ROSTER = [
    { name: 'Taro', title: 'El Aprendiz', weapon: 'katana', level: 1, persona: 'balanced', color: '#7cff6b', taunt: 'Es mi primer torneo... ¡no me subestimes!' },
    { name: 'Hana', title: 'La Garza', weapon: 'dagas', level: 2, persona: 'trickster', color: '#ff9f1c', taunt: '¿Seguro que viste dónde iba mi hoja?' },
    { name: 'Gorm', title: 'El Yunque', weapon: 'hacha', level: 3, persona: 'brute', color: '#ff3b30', taunt: 'Voy a partir tu guardia en dos.' },
    { name: 'Sora', title: 'Viento Cortante', weapon: 'lanza', level: 3, persona: 'duelist', color: '#ffd60a', taunt: 'Nadie me alcanza a distancia.' },
    { name: 'Madame Kuro', title: 'La Viuda', weapon: 'dagas', level: 4, persona: 'turtle', color: '#bf5af2', perks: ['guard'], taunt: 'Paciencia... siempre gano esperando.' },
    { name: 'Ren', title: 'Muro Silente', weapon: 'katana', level: 4, persona: 'balanced', color: '#30d158', perks: ['armor'], taunt: '...' },
    { name: 'Ryuga', title: 'El Campeón', weapon: 'katana', level: 5, persona: 'aggressive', color: '#ff2d95', perks: ['edge', 'lungs'], taunt: 'Tres años invicto. Mostrame algo nuevo.' },
  ];
  const ROUND_NAMES = ['Cuartos de final', 'Semifinal', 'Gran final'];

  const G = {
    theme: store.get('theme', 'neon'), weapon: 'katana', perks: [],
    scene: null, round: 0, bracket: null,
  };

  // ---------- helpers de pantalla ----------
  const overlay = $('#overlay');
  function ask(html) {
    return new Promise((resolve) => {
      overlay.innerHTML = '<div class="screen">' + html + '</div>';
      overlay.classList.add('on'); overlay.scrollTop = 0;
      overlay.onclick = (e) => {
        const el = e.target.closest('[data-val]');
        if (!el) return;
        BD.Audio.sfx('ok');
        resolve(el.dataset.val);
        if (!el.dataset.keep) overlay.classList.remove('on');
      };
    });
  }
  function hideOverlay() { overlay.classList.remove('on'); }
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const stars = (n) => '★'.repeat(n) + '☆'.repeat(5 - n);

  function applyTheme(t) {
    G.theme = t; document.body.classList.toggle('theme-neon', t === 'neon'); document.body.classList.toggle('theme-primal', t === 'primal');
    G.scene.setTheme(t); store.set('theme', t);
    const b = $('#btn-theme'); if (b) b.textContent = t === 'neon' ? 'Estilo: Neón' : 'Estilo: Primal';
  }

  // ---------- panel de elección ----------
  const panel = {
    sel: { type: null, zone: null, block: null }, me: null, foe: null, habit: null, resolve: null,
    build() {
      const types = $('#types'), az = $('#azones'), bz = $('#bzones');
      const keysT = ['Q', 'W', 'E', 'R', 'T'], keysA = ['1', '2', '3'], keysB = ['Z', 'X', 'C'];
      types.innerHTML = BD.TYPE_ORDER.map((t, i) => `<button class="btn" data-t="${t}"><kbd>${keysT[i]}</kbd><span>${TN(t)}</span><small></small></button>`).join('');
      const zl = ['▲ Alta', '▬ Media', '▼ Baja'];
      az.innerHTML = zl.map((z, i) => `<button class="btn" data-z="${i}"><kbd>${keysA[i]}</kbd><span>${z}</span></button>`).join('');
      bz.innerHTML = zl.map((z, i) => `<button class="btn blk" data-b="${i}"><kbd>${keysB[i]}</kbd><span>${z}</span></button>`).join('');
      types.onclick = (e) => { const b = e.target.closest('[data-t]'); if (b && !b.disabled) this.pickType(b.dataset.t); };
      az.onclick = (e) => { const b = e.target.closest('[data-z]'); if (b && !b.disabled) this.pickZone(+b.dataset.z); };
      bz.onclick = (e) => { const b = e.target.closest('[data-b]'); if (b) this.pickBlock(+b.dataset.b); };
      $('#go').onclick = () => this.confirm();
      document.addEventListener('keydown', (e) => {
        if (!this.resolve || e.repeat || e.ctrlKey || e.metaKey || e.altKey) return;
        const k = e.key.toUpperCase();
        const iT = keysT.indexOf(k), iA = keysA.indexOf(k), iB = keysB.indexOf(k);
        if (iT >= 0) { const t = BD.TYPE_ORDER[iT]; if (this.legalTypes().has(t)) this.pickType(t); }
        else if (iA >= 0) { if (!$('#azones [data-z="' + iA + '"]').disabled) this.pickZone(iA); }
        else if (iB >= 0) this.pickBlock(iB);
        else if (k === 'ENTER' || k === ' ') { e.preventDefault(); this.confirm(); }
      });
    },
    legalTypes() { return new Set(BD.legalAttacks(this.me).map((m) => m.type)); },
    pickType(t) {
      BD.Audio.sfx('ui');
      this.sel.type = t;
      if (t === 'rest') this.sel.zone = -1;
      else if (this.sel.zone === -1 || (this.sel.zone != null && !BD.isLegal(this.me, { type: t, zone: this.sel.zone }))) this.sel.zone = null;
      this.refresh();
    },
    pickZone(z) {
      BD.Audio.sfx('ui');
      this.sel.zone = z;
      if (this.sel.type && this.sel.type !== 'rest' && !BD.isLegal(this.me, { type: this.sel.type, zone: z })) this.sel.type = null;
      this.refresh();
    },
    pickBlock(b) { BD.Audio.sfx('ui'); this.sel.block = b; this.refresh(); },
    ready() { const s = this.sel; return s.type && (s.type === 'rest' || s.zone >= 0 && s.zone != null) && s.block != null; },
    confirm() {
      if (!this.resolve || !this.ready()) return;
      const mv = { type: this.sel.type, zone: this.sel.type === 'rest' ? -1 : this.sel.zone, block: this.sel.block };
      const r = this.resolve; this.resolve = null; $('#panel').classList.add('locked'); $('#go').disabled = true;
      BD.Audio.unlock(); r(mv);
    },
    refresh() {
      const me = this.me, s = this.sel, legal = BD.legalAttacks(me), n = me.chain.length;
      document.querySelectorAll('#types .btn').forEach((b) => {
        const t = b.dataset.t, ok = legal.some((m) => m.type === t && (s.zone == null || s.zone === -1 || m.zone === s.zone || t === 'rest'));
        b.disabled = !ok; b.classList.toggle('sel', s.type === t);
        b.querySelector('small').textContent = t === 'rest' ? '+aguante' : BD.attackCost(me, t, n) + ' aguante';
      });
      document.querySelectorAll('#azones .btn').forEach((b) => {
        const z = +b.dataset.z;
        const ok = s.type === 'rest' ? false : legal.some((m) => m.type !== 'rest' && m.zone === z && (!s.type || m.type === s.type));
        b.disabled = !ok; b.classList.toggle('sel', s.zone === z);
      });
      document.querySelectorAll('#bzones .btn').forEach((b) => b.classList.toggle('sel', s.block === +b.dataset.b));
      $('#go').disabled = !this.ready();
      this.hint();
    },
    hint() {
      const me = this.me, foe = this.foe, n = me.chain.length, s = this.sel;
      const chainTxt = me.chain.map((c) => TN(c.type) + ' ' + ZN[c.zone]).join(' → ');
      let h = '';
      if (n === 0) h = 'Sin racha: todo el árbol está abierto.';
      else {
        h = `Racha <b>${n}/3</b>: ${chainTxt}. `;
        if (n === 1) h += 'Ahora no podés repetir dirección (salvo Finta) y se cierran opciones.';
        else if (n === 2) h += 'Solo direcciones contiguas y 1-2 tipos. <span class="warn">Un Rápido o Estocada bloqueado ahora = PARRY.</span>';
        else h += '<b>¡Cierre obligatorio!</b> Solo Pesado o Estocada.';
      }
      if (me.open) h += ' <span class="warn">Estás ABIERTO: tu bloqueo no cuenta este turno.</span>';
      if (foe.open) h += ' <span class="combo">¡El rival está ABIERTO! Su bloqueo no cuenta: cualquier golpe entra.</span>';
      if (s.type && s.type !== 'rest') {
        const c = BD.findCombo(me.chain.map((x) => x.type).concat(s.type));
        if (c) h += ` <span class="combo">Combo: ${c.name} ×${c.mult} si conecta.</span>`;
      }
      $('#hint').innerHTML = h;
      const r = me.mods.reader && this.habit && BD.readout(this.habit);
      $('#reader').textContent = r ? `Ojo de halcón: ${foe.name} suele atacar ${ZN[r.zone]} (${Math.round(r.zoneP * 100)}%), bloquear ${ZN[r.block]} (${Math.round(r.blockP * 100)}%) y usar ${TN(r.type)} (${Math.round(r.typeP * 100)}%).` : '';
    },
    choose(me, foe, habit) {
      this.me = me; this.foe = foe; this.habit = habit; this.sel = { type: null, zone: null, block: null };
      $('#panel').classList.remove('locked');
      this.refresh();
      return new Promise((res) => { this.resolve = res; });
    },
  };

  // ---------- simulación headless de combates del cuadro ----------
  function simulate(specA, specB) {
    const A = BD.makeFighter(specA), B = BD.makeFighter(specB);
    const brA = BD.makeBrain(A.level, A.persona), brB = BD.makeBrain(B.level, B.persona);
    const w = { a: 0, b: 0 };
    while (w.a < 2 && w.b < 2) {
      const s = BD.newDuel(A, B);
      for (;;) {
        const ma = BD.decide(brA, s, 'a'), mb = BD.decide(brB, s, 'b');
        BD.observe(brA, mb); BD.observe(brB, ma);
        BD.step(s, { a: ma, b: mb });
        const r = BD.roundOver(s);
        if (r.over) { w[r.winner]++; break; }
      }
    }
    return w.a > w.b ? specA : specB;
  }

  // ---------- pantallas ----------
  const WEAPON_STATS = (w) => `${w.hp} vida · Rápido ×${w.dmg.quick} · Pesado ×${w.dmg.heavy} · Estocada ×${w.dmg.thrust}`;

  async function titleScreen() {
    const rules = `<div class="legend">
      <b>Cada turno elegís 3 cosas en secreto</b> (el rival también): <b>tipo de ataque</b>, <b>dirección</b> (alta/media/baja) y <b>bloqueo</b> (alta/media/baja).<br>
      <b>Rápido</b> interrumpe a Pesado · <b>Pesado</b> rompe la guardia · <b>Finta</b> abre al que bloquea · <b>Estocada</b> castiga la Finta.<br>
      Encadenar ataques arma <b>combos</b> con más daño, pero el árbol se estrecha: en la 3ª jugada solo queda el cierre, y un Rápido/Estocada bloqueado en racha larga es <b>parry</b>.<br>
      Todo gasta <b>aguante</b>. Ganás una ronda con KO o con más vida al turno 14. Mejor de 3 rondas por combate.</div>`;
    await ask(`<h2>Blade Duels</h2><p>Torneo del Filo Supremo · 8 luchadores · 3 combates para la gloria</p>${rules}
      <div><button class="cta" data-val="go">Inscribirme</button></div>`);
  }

  async function weaponScreen() {
    const cards = Object.values(BD.WEAPONS).map((w) => `<button class="card" data-val="${w.id}"><h3>${w.name}</h3><p>${w.desc}</p><div class="stats">${WEAPON_STATS(w)}</div></button>`).join('');
    return ask(`<h2>Elegí tu arma</h2><p>Cada arma cambia daños, costos y vida. El árbol de combos es el mismo.</p><div class="cards">${cards}</div>`);
  }

  function bracketHtml(br, current) {
    const slot = (sp, m) => {
      if (!sp) return '<div class="slot"><span class="nm">—</span></div>';
      const cls = ['slot', sp.isMe ? 'me' : '', m.winner ? (m.winner === sp ? 'win' : 'lose') : ''].join(' ');
      return `<div class="${cls}"><span class="nm"><span class="dot" style="background:${sp.color}"></span>${esc(sp.name)}</span><span>${sp.isMe ? '' : stars(sp.level).slice(0, sp.level)}</span></div>`;
    };
    const col = (r) => `<div class="col"><h5>${ROUND_NAMES[r].toUpperCase()}</h5>${br[r].map((m, i) => `<div class="match ${current && current.r === r && current.i === i ? 'now' : ''}">${slot(m.a, m)}${slot(m.b, m)}</div>`).join('')}</div>`;
    return `<div class="bracket">${col(0)}${col(1)}${col(2)}</div>`;
  }

  async function bracketScreen(r) {
    const m = G.bracket[r][0], foe = m.b;
    const weapon = BD.WEAPONS[foe.weapon];
    const perks = (G.perks.length ? '<ul class="perks">' + G.perks.map((id) => { const p = BD.PERKS.find((x) => x.id === id); return `<li>✔ ${p.name}: ${p.desc}</li>`; }).join('') + '</ul>' : '');
    await ask(`<h2>${ROUND_NAMES[r]}</h2>${bracketHtml(G.bracket, { r, i: 0 })}
      <div class="vs"><b>${esc(ME.name)} vs ${esc(foe.name)}</b> — ${esc(foe.title)}<br>${weapon.name} · nivel ${stars(foe.level)}<br><span class="taunt">“${esc(foe.taunt)}”</span></div>${perks}
      <button class="cta" data-val="fight">¡A pelear!</button>`);
  }

  async function perkScreen() {
    const pool = BD.PERKS.filter((p) => !G.perks.includes(p.id)).sort(() => Math.random() - 0.5).slice(0, 3);
    if (!pool.length) return;
    const cards = pool.map((p) => `<button class="card" data-val="${p.id}"><h3>${p.name}</h3><p>${p.desc}</p></button>`).join('');
    const id = await ask(`<h2>¡Victoria!</h2><p>Elegí una mejora para el próximo combate.</p><div class="cards">${cards}</div>`);
    G.perks.push(id);
  }

  async function endScreen(champion, r) {
    BD.Audio.sfx(champion ? 'win' : 'lose');
    const html = champion
      ? `<h2>¡Campeón del Filo Supremo!</h2><p>Venciste a los 7 rivales del torneo.</p>${bracketHtml(G.bracket)}`
      : `<h2>Eliminado</h2><p>Caíste en ${ROUND_NAMES[r].toLowerCase()}. El árbol de combos premia al que lee, no al que insiste.</p>${bracketHtml(G.bracket)}`;
    return ask(html + `<div><button class="cta" data-val="same">Reintentar con ${BD.WEAPONS[G.weapon].name}</button><button class="cta alt" data-val="new">Cambiar de arma</button></div>`);
  }

  // ---------- combate ----------
  function snapF(f) { return { hp: f.hp, st: f.st, chain: f.chain.slice(), open: f.open }; }

  async function playMatch(oppSpec) {
    const sc = G.scene;
    const me = BD.makeFighter(Object.assign({}, ME, { weapon: G.weapon, perks: G.perks, level: 3 }));
    const foe = BD.makeFighter(oppSpec);
    const brain = BD.makeBrain(foe.level, foe.persona), habit = BD.makeBrain(1, 'balanced');
    sc.setFighters(me, foe);
    const wins = { a: 0, b: 0 };
    let round = 1;
    while (wins.a < 2 && wins.b < 2) {
      const duel = BD.newDuel(me, foe);
      sc.hud.round = round; sc.hud.turn = 0; sc.hud.limit = BD.TURN_LIMIT;
      sc.setHud('a', me, wins.a); sc.setHud('b', foe, wins.b); sc.syncHudInstant(); sc.idleAll();
      await sc.banner('RONDA ' + round, '', 1.0);
      await sc.banner('¡LUCHA!', '', 0.8);
      for (;;) {
        const mvA = await panel.choose(duel.a, duel.b, habit);
        const mvB = BD.decide(brain, duel, 'b');
        BD.observe(brain, mvA); BD.observe(habit, mvB);
        const res = BD.step(duel, { a: mvA, b: mvB });
        const after = { a: snapF(duel.a), b: snapF(duel.b) };
        await sc.playTurn({ a: mvA, b: mvB }, res, after);
        sc.setHud('a', duel.a, wins.a); sc.setHud('b', duel.b, wins.b);
        const ro = BD.roundOver(duel);
        if (ro.over) { wins[ro.winner]++; sc.hud.a.wins = wins.a; sc.hud.b.wins = wins.b; await sc.ko(ro.winner, ro.ko); break; }
      }
      round++;
    }
    return wins.a > wins.b;
  }

  // ---------- torneo ----------
  async function tournament() {
    const meSpec = Object.assign({ isMe: true, level: 3 }, ME);
    const R = ROSTER.map((r) => Object.assign({}, r));
    G.perks = [];
    G.bracket = [
      [{ a: meSpec, b: R[0] }, { a: R[1], b: R[2] }, { a: R[3], b: R[4] }, { a: R[5], b: R[6] }],
      [{}, {}],
      [{}],
    ];
    for (let r = 0; r < 3; r++) {
      if (r > 0) G.bracket[r].forEach((m, i) => { m.a = G.bracket[r - 1][i * 2].winner; m.b = G.bracket[r - 1][i * 2 + 1].winner; });
      // los demás combates se resuelven solos
      G.bracket[r].forEach((m, i) => { if (i > 0) m.winner = simulate(m.a, m.b); });
      await bracketScreen(r);
      const won = await playMatch(G.bracket[r][0].b);
      G.bracket[r][0].winner = won ? meSpec : G.bracket[r][0].b;
      if (!won) { G.scene.hud.round = 1; return { champion: false, r }; }
      if (r < 2) { BD.Audio.sfx('win'); await perkScreen(); }
    }
    return { champion: true };
  }

  async function main() {
    G.scene = new BD.Scene($('#cv'));
    G.scene.start();
    BD.Audio.muted = store.get('mute', '0') === '1';
    G.scene.speed = +store.get('speed', '1') || 1;
    panel.build();
    $('#panel').classList.add('locked');
    applyTheme(G.theme);
    // demo de fondo mientras se muestra el título
    const fa = BD.makeFighter({ name: 'Vos', weapon: 'katana', color: ME.color }), fb = BD.makeFighter({ name: 'Ryuga', weapon: 'katana', color: '#ff2d95' });
    G.scene.setFighters(fa, fb); G.scene.setHud('a', fa, 0); G.scene.setHud('b', fb, 0); G.scene.syncHudInstant();

    const bT = $('#btn-theme'), bS = $('#btn-sound'), bV = $('#btn-speed');
    bT.onclick = () => applyTheme(G.theme === 'neon' ? 'primal' : 'neon');
    const syncSound = () => { bS.textContent = BD.Audio.muted ? 'Sonido: no' : 'Sonido: sí'; bS.setAttribute('aria-pressed', String(!BD.Audio.muted)); };
    bS.onclick = () => { BD.Audio.muted = !BD.Audio.muted; store.set('mute', BD.Audio.muted ? '1' : '0'); syncSound(); BD.Audio.unlock(); };
    const syncSpeed = () => { bV.textContent = 'Velocidad ×' + G.scene.speed; };
    bV.onclick = () => { G.scene.speed = G.scene.speed === 1 ? 1.6 : 1; store.set('speed', G.scene.speed); syncSpeed(); };
    syncSound(); syncSpeed();

    await titleScreen(); BD.Audio.unlock();
    for (;;) {
      G.weapon = await weaponScreen();
      for (;;) {
        const r = await tournament();
        const next = await endScreen(r.champion, r.r);
        if (next === 'new') break;
      }
    }
  }

  window.BDGame = { G, panel, scene: () => G.scene };
  window.addEventListener('DOMContentLoaded', main);
})();
