/* Blade Duels - reglas del duelo (sin gráficos, sin DOM).
 *
 * Cada turno ambos luchadores eligen EN SECRETO: tipo de ataque, dirección
 * del ataque y dirección del bloqueo. Luego se revelan y se resuelven a la vez.
 * step() devuelve una lista de eventos que la capa visual reproduce.
 */
(function () {
  const BD = (globalThis.BD = globalThis.BD || {});

  const ZONES = ['Alta', 'Media', 'Baja'];
  const ZONE_MULT = [1.2, 1.0, 0.85];
  const TYPES = {
    quick: { name: 'Rápido', dmg: 8, cost: 6 },
    heavy: { name: 'Pesado', dmg: 22, cost: 18 },
    thrust: { name: 'Estocada', dmg: 14, cost: 12 },
    feint: { name: 'Finta', dmg: 0, cost: 8 },
    rest: { name: 'Descansar', dmg: 0, cost: 0 },
  };
  const TYPE_ORDER = ['quick', 'heavy', 'thrust', 'feint', 'rest'];
  const BLOCK_COST = 3;
  const MAX_CHAIN = 3; // la 4ª jugada de una racha es el cierre obligatorio
  const TURN_LIMIT = 14;

  // Qué puede seguir a cada movimiento (el árbol de combos).
  const FOLLOW1 = {
    quick: ['quick', 'heavy', 'thrust', 'feint'],
    heavy: ['quick', 'feint'],
    thrust: ['quick', 'heavy'],
    feint: ['quick', 'heavy', 'thrust'],
  };
  const FOLLOW2 = {
    quick: ['heavy', 'thrust'],
    heavy: ['quick'],
    thrust: ['heavy'],
    feint: ['heavy', 'thrust'],
  };
  const FINISH = ['heavy', 'thrust'];

  const COMBOS = [
    { seq: ['feint', 'thrust', 'heavy'], name: 'Eclipse', mult: 2.0 },
    { seq: ['quick', 'quick', 'heavy'], name: 'Guillotina', mult: 1.8 },
    { seq: ['quick', 'heavy', 'thrust'], name: 'Marea', mult: 1.7 },
    { seq: ['feint', 'heavy'], name: 'Engaño', mult: 1.4 },
    { seq: ['quick', 'thrust'], name: 'Aguijón', mult: 1.3 },
    { seq: ['thrust', 'heavy'], name: 'Embestida', mult: 1.3 },
    { seq: ['quick', 'quick'], name: 'Tijera', mult: 1.25 },
  ];

  const WEAPONS = {
    katana: {
      id: 'katana', name: 'Katana', desc: 'Equilibrada. Sin debilidades.',
      dmg: { quick: 1, heavy: 1, thrust: 1 }, cost: { quick: 1, heavy: 1, thrust: 1, feint: 1 },
      hp: 106, st: 100, regen: 8, len: 84, shape: 'blade',
    },
    dagas: {
      id: 'dagas', name: 'Daga', desc: 'Rápidos baratos y letales. Pesado débil. Poca vida.',
      dmg: { quick: 1.6, heavy: 0.75, thrust: 1.05 }, cost: { quick: 0.65, heavy: 1, thrust: 1, feint: 0.8 },
      hp: 94, st: 100, regen: 9, len: 46, shape: 'dagger',
    },
    lanza: {
      id: 'lanza', name: 'Lanza', desc: 'Estocadas devastadoras y baratas. Rápidos flojos.',
      dmg: { quick: 0.85, heavy: 0.9, thrust: 1.3 }, cost: { quick: 1, heavy: 1, thrust: 0.9, feint: 1 },
      hp: 100, st: 100, regen: 8, len: 138, shape: 'spear',
    },
    hacha: {
      id: 'hacha', name: 'Hacha', desc: 'Pesados brutales y mucha vida. Se cansa rápido.',
      dmg: { quick: 0.8, heavy: 1.28, thrust: 0.9 }, cost: { quick: 1.1, heavy: 1, thrust: 1.1, feint: 1.1 },
      hp: 108, st: 100, regen: 7, len: 76, shape: 'axe',
    },
  };

  const PERKS = [
    { id: 'hp', name: 'Corazón de piedra', desc: '+15 vida máxima', apply: (m) => { m.hp += 15; } },
    { id: 'lungs', name: 'Pulmones de acero', desc: '+3 recuperación y +10 aguante', apply: (m) => { m.regen += 3; m.st += 10; } },
    { id: 'edge', name: 'Filo afilado', desc: '+12% de daño', apply: (m) => { m.dmgMult *= 1.12; } },
    { id: 'armor', name: 'Armadura ligera', desc: '-10% de daño recibido', apply: (m) => { m.armor *= 0.9; } },
    { id: 'guard', name: 'Guardia firme', desc: 'Bloquear no gasta aguante', apply: (m) => { m.blockFree = true; } },
    { id: 'combo', name: 'Maestro de combos', desc: 'Los combos pegan mucho más', apply: (m) => { m.comboBoost += 0.5; } },
    { id: 'reader', name: 'Ojo de halcón', desc: 'Ves las costumbres del rival', apply: (m) => { m.reader = true; } },
  ];

  function makeFighter(spec) {
    const w = WEAPONS[spec.weapon] || WEAPONS.katana;
    const m = { hp: 0, st: 0, regen: 0, dmgMult: 1, armor: 1, blockFree: false, comboBoost: 1, reader: false };
    (spec.perks || []).forEach((id) => {
      const p = PERKS.find((x) => x.id === id);
      if (p) p.apply(m);
    });
    const f = {
      name: spec.name, title: spec.title || '', weapon: w.id, color: spec.color, level: spec.level || 3,
      persona: spec.persona || 'balanced', taunt: spec.taunt || '', perks: (spec.perks || []).slice(),
      maxHp: w.hp + m.hp, maxSt: w.st + m.st, regen: w.regen + m.regen, mods: m,
    };
    return resetFighter(f);
  }

  function resetFighter(f) {
    f.hp = f.maxHp;
    f.st = f.maxSt;
    f.chain = [];
    f.open = false;
    return f;
  }

  function cloneFighter(f) {
    return Object.assign({}, f, { chain: f.chain.slice() });
  }
  function cloneState(s) {
    return { a: cloneFighter(s.a), b: cloneFighter(s.b), turn: s.turn };
  }
  function newDuel(a, b) {
    return { a: resetFighter(a), b: resetFighter(b), turn: 0 };
  }

  function attackCost(f, type, chainLen) {
    if (type === 'rest') return 0;
    const w = WEAPONS[f.weapon];
    return Math.max(2, Math.round(TYPES[type].cost * (w.cost[type] || 1) * (1 + 0.2 * chainLen)));
  }
  function blockCost(f) {
    return f.mods.blockFree ? 0 : BLOCK_COST;
  }

  // Ataques que el luchador puede elegir ahora. El árbol se estrecha con la racha.
  function legalAttacks(f) {
    const out = [];
    const n = f.chain.length;
    const last = f.chain[n - 1];
    let types;
    if (n === 0) types = ['quick', 'heavy', 'thrust', 'feint'];
    else if (n === 1) types = FOLLOW1[last.type];
    else if (n === 2) types = FOLLOW2[last.type];
    else types = FINISH;
    types.forEach((t) => {
      if (attackCost(f, t, n) > f.st) return;
      for (let z = 0; z < 3; z++) {
        if (n === 1 && last.type !== 'feint' && z === last.zone) continue;
        if (n === 2 && Math.abs(z - last.zone) !== 1) continue;
        out.push({ type: t, zone: z });
      }
    });
    out.push({ type: 'rest', zone: -1 });
    return out;
  }
  function isLegal(f, mv) {
    return legalAttacks(f).some((a) => a.type === mv.type && a.zone === mv.zone);
  }

  function findCombo(types) {
    for (const c of COMBOS) {
      if (types.length >= c.seq.length && c.seq.every((t, i) => types[types.length - c.seq.length + i] === t)) return c;
    }
    return null;
  }

  // Resuelve un turno. mv = { a:{type,zone,block}, b:{type,zone,block} }. Muta el estado.
  function step(s, mv) {
    const F = { a: s.a, b: s.b };
    const other = { a: 'b', b: 'a' };
    const events = [];
    const out = {};
    const info = {};
    const flags = { a: { broken: false, open: false }, b: { broken: false, open: false } };
    const dmgTaken = { a: 0, b: 0 };
    const stLoss = { a: 0, b: 0 };

    ['a', 'b'].forEach((k) => {
      const f = F[k], m = mv[k];
      const types = f.chain.map((c) => c.type).concat(m.type);
      info[k] = { cost: attackCost(f, m.type, f.chain.length), combo: m.type === 'rest' ? null : findCombo(types), streak: f.chain.length };
    });

    ['a', 'b'].forEach((att) => {
      const def = other[att];
      const A = F[att], D = F[def], ma = mv[att], md = mv[def];
      if (ma.type === 'rest') { out[att] = { kind: 'rest' }; return; }
      const dBlock = D.open ? -1 : md.block;
      const blocked = dBlock === ma.zone;
      const wm = WEAPONS[A.weapon].dmg[ma.type] || 1;
      const base = TYPES[ma.type].dmg * wm * A.mods.dmgMult;
      const zm = ZONE_MULT[ma.zone];
      const openMult = D.open ? 1.2 : 1;
      const combo = info[att].combo;
      const comboMult = combo ? 1 + (combo.mult - 1) * A.mods.comboBoost : 1;
      let kind, dmg = 0, counter = false;

      if (ma.type === 'heavy' && md.type === 'quick') {
        kind = 'interrupt'; flags[att].broken = true;
      } else if (ma.type === 'thrust' && md.type === 'feint') {
        kind = 'punish'; dmg = base * zm * 1.5 * openMult;
        flags[def].broken = true;
      } else if (blocked) {
        if (ma.type === 'feint') {
          kind = 'feintOpen'; flags[def].open = true;
        } else if (ma.type === 'heavy') {
          kind = 'guardbreak'; dmg = base * zm * 0.4; stLoss[def] += 12; flags[def].broken = true;
        } else if (ma.type === 'thrust') {
          if (info[att].streak >= 2) { kind = 'parry'; flags[att].broken = true; flags[att].open = true; }
          else { kind = 'block'; dmg = base * zm * 0.35; flags[att].broken = true; }
        } else { // quick
          if (info[att].streak >= 2) { kind = 'parry'; flags[att].broken = true; flags[att].open = true; }
          else kind = 'block';
        }
      } else if (ma.type === 'feint') {
        kind = 'whiff';
      } else {
        kind = 'hit';
        if (ma.type === 'quick' && md.type === 'heavy') counter = true;
        dmg = base * zm * comboMult * openMult * (counter ? 1.25 : 1);
      }
      dmg = Math.round(dmg * D.mods.armor);
      out[att] = { kind, dmg, counter, combo: kind === 'hit' || kind === 'punish' ? combo : null };
      dmgTaken[def] += dmg;
    });

    // aplicar
    ['a', 'b'].forEach((k) => {
      const f = F[k], m = mv[k], o = out[k];
      const foeOut = out[other[k]];
      f.hp -= dmgTaken[k];
      f.rawHp = f.hp;
      f.hp = Math.max(0, f.hp);
      f.st -= info[k].cost + blockCost(f) + stLoss[k];
      f.st = Math.max(0, f.st);
      f.st = Math.min(f.maxSt, f.st + f.regen + (m.type === 'rest' ? 14 : 0));
      // cadena
      if (m.type === 'rest' || flags[k].broken || info[k].streak >= MAX_CHAIN) f.chain = [];
      else f.chain.push({ type: m.type, zone: m.zone });
      f.open = flags[k].open;
      if (foeOut && foeOut.kind === 'guardbreak') f.chain = [];
      const ev = Object.assign({ src: k, dst: other[k], type: m.type, zone: m.zone, streak: info[k].streak }, o);
      events.push(ev);
    });
    s.turn += 1;
    return { events, out };
  }

  function roundOver(s) {
    const a = s.a, b = s.b;
    if (a.hp <= 0 || b.hp <= 0) {
      if (a.hp <= 0 && b.hp <= 0) {
        const ra = a.rawHp, rb = b.rawHp;
        return { over: true, winner: ra > rb ? 'a' : rb > ra ? 'b' : (a.st >= b.st ? 'a' : 'b'), ko: true };
      }
      return { over: true, winner: a.hp > 0 ? 'a' : 'b', ko: true };
    }
    if (s.turn >= TURN_LIMIT) {
      const w = a.hp !== b.hp ? (a.hp > b.hp ? 'a' : 'b') : (a.st >= b.st ? 'a' : 'b');
      return { over: true, winner: w, ko: false };
    }
    return { over: false };
  }

  Object.assign(BD, {
    ZONES, ZONE_MULT, TYPES, TYPE_ORDER, BLOCK_COST, MAX_CHAIN, TURN_LIMIT, COMBOS, WEAPONS, PERKS,
    makeFighter, resetFighter, cloneState, newDuel, attackCost, blockCost, legalAttacks, isLegal, findCombo, step, roundOver,
  });
  if (typeof module !== 'undefined' && module.exports) module.exports = BD;
})();
