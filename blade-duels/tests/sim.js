// node blade-duels/tests/sim.js [duelos]   -> tests de reglas + simulación de balance
const assert = require('assert');
const BD = require('../core.js');
require('../ai.js');

const mk = (weapon, level, persona, perks) => BD.makeFighter({ name: weapon, weapon, level, persona, color: '#fff', perks });
const dm = (type, zone, block) => ({ type, zone, block });
const fresh = (wa = 'katana', wb = 'katana') => BD.newDuel(mk(wa), mk(wb));

// --- reglas ---
(function rules() {
  let s = fresh();
  // golpe limpio: Rápido Alto vs bloqueo Bajo
  let r = BD.step(s, { a: dm('quick', 0, 2), b: dm('rest', -1, 2) });
  assert.strictEqual(r.out.a.kind, 'hit');
  assert.strictEqual(s.b.hp, s.b.maxHp - Math.round(8 * 1.2));

  // bloqueo correcto
  s = fresh();
  r = BD.step(s, { a: dm('quick', 1, 0), b: dm('rest', -1, 1) });
  assert.strictEqual(r.out.a.kind, 'block'); assert.strictEqual(s.b.hp, s.b.maxHp);

  // Rápido interrumpe Pesado
  s = fresh();
  r = BD.step(s, { a: dm('heavy', 1, 1), b: dm('quick', 1, 0) });
  assert.strictEqual(r.out.a.kind, 'interrupt'); assert.strictEqual(r.out.b.kind, 'block');
  assert.strictEqual(s.b.hp, s.b.maxHp);

  // Pesado rompe guardia
  s = fresh();
  r = BD.step(s, { a: dm('heavy', 1, 0), b: dm('rest', -1, 1) });
  assert.strictEqual(r.out.a.kind, 'guardbreak'); assert.ok(s.b.hp < s.b.maxHp && s.b.hp > s.b.maxHp - 12);

  // Finta contra bloqueo => abierto; el siguiente golpe ignora el bloqueo
  s = fresh();
  r = BD.step(s, { a: dm('feint', 1, 0), b: dm('rest', -1, 1) });
  assert.strictEqual(r.out.a.kind, 'feintOpen'); assert.strictEqual(s.b.open, true);
  const hp = s.b.hp;
  r = BD.step(s, { a: dm('quick', 1, 0), b: dm('rest', -1, 1) });
  assert.strictEqual(r.out.a.kind, 'hit'); assert.ok(s.b.hp < hp);

  // Estocada castiga Finta
  s = fresh();
  r = BD.step(s, { a: dm('thrust', 1, 0), b: dm('feint', 1, 1) });
  assert.strictEqual(r.out.a.kind, 'punish'); assert.ok(s.b.hp < s.b.maxHp);

  // el árbol se estrecha con la racha
  s = fresh();
  const n0 = BD.legalAttacks(s.a).length;
  BD.step(s, { a: dm('quick', 1, 0), b: dm('rest', -1, 1) }); // bloqueado pero cadena sigue
  assert.strictEqual(s.a.chain.length, 1);
  const n1 = BD.legalAttacks(s.a).length;
  BD.step(s, { a: dm('quick', 0, 0), b: dm('rest', -1, 0) });
  const n2 = BD.legalAttacks(s.a).length;
  assert.ok(n0 > n1 && n1 > n2, `opciones deben decrecer: ${n0} ${n1} ${n2}`);

  // parry: racha>=2 bloqueada con Rápido
  s = fresh();
  s.a.chain = [{ type: 'quick', zone: 0 }, { type: 'quick', zone: 1 }];
  r = BD.step(s, { a: dm('heavy', 2, 0), b: dm('rest', -1, 2) });
  assert.strictEqual(r.out.a.kind, 'guardbreak');
  s = fresh();
  s.a.chain = [{ type: 'heavy', zone: 0 }, { type: 'quick', zone: 1 }];
  s.a.st = 100;
  r = BD.step(s, { a: dm('thrust', 2, 0), b: dm('rest', -1, 2) });
  assert.strictEqual(r.out.a.kind, 'parry'); assert.strictEqual(s.a.open, true);

  // combo
  s = fresh();
  BD.step(s, { a: dm('quick', 0, 0), b: dm('rest', -1, 0) });
  r = BD.step(s, { a: dm('quick', 1, 0), b: dm('rest', -1, 2) });
  assert.strictEqual(r.out.a.kind, 'hit'); assert.strictEqual(r.out.a.combo.name, 'Tijera');

  // el cierre obligatorio reinicia la cadena
  s = fresh();
  s.a.chain = [{ type: 'quick', zone: 0 }, { type: 'quick', zone: 1 }, { type: 'quick', zone: 0 }];
  assert.deepStrictEqual([...new Set(BD.legalAttacks(s.a).map((m) => m.type))].sort(), ['heavy', 'rest', 'thrust']);
  BD.step(s, { a: dm('heavy', 0, 0), b: dm('rest', -1, 2) });
  assert.strictEqual(s.a.chain.length, 0);

  // sin aguante => solo descansar
  s = fresh(); s.a.st = 0;
  assert.deepStrictEqual(BD.legalAttacks(s.a).map((m) => m.type), ['rest']);
  console.log('reglas OK');
})();

// --- simulación ---
function duel(wa, la, pa, wb, lb, pb, seed) {
  const rng = BD.mulberry32(seed);
  const A = mk(wa, la, pa), B = mk(wb, lb, pb);
  const brA = BD.makeBrain(la, pa, rng), brB = BD.makeBrain(lb, pb, rng);
  const wins = { a: 0, b: 0 };
  let turns = 0, rounds = 0, rests = 0, moves = 0;
  while (wins.a < 2 && wins.b < 2) {
    const s = BD.newDuel(A, B);
    for (;;) {
      const ma = BD.decide(brA, s, 'a'), mb = BD.decide(brB, s, 'b');
      if (!BD.isLegal(s.a, ma) || !BD.isLegal(s.b, mb)) throw new Error('movimiento ilegal');
      moves += 2; if (ma.type === 'rest') rests++; if (mb.type === 'rest') rests++;
      BD.observe(brA, mb); BD.observe(brB, ma);
      BD.step(s, { a: ma, b: mb });
      turns++;
      const ro = BD.roundOver(s);
      if (ro.over) { wins[ro.winner]++; rounds++; break; }
    }
  }
  return { winner: wins.a > wins.b ? 'a' : 'b', turns, rounds, rests, moves };
}

function batch(label, wa, la, pa, wb, lb, pb, n) {
  let w = 0, turns = 0, rounds = 0, rests = 0, moves = 0;
  for (let i = 0; i < n; i++) {
    const r = duel(wa, la, pa, wb, lb, pb, 1000 + i);
    if (r.winner === 'a') w++;
    turns += r.turns; rounds += r.rounds; rests += r.rests; moves += r.moves;
  }
  console.log(`${label.padEnd(34)} A gana ${(100 * w / n).toFixed(0).padStart(3)}%  turnos/ronda ${(turns / rounds).toFixed(1)}  descansos ${(100 * rests / moves).toFixed(0)}%`);
}

const N = +process.argv[2] || 40;
const t0 = Date.now();
batch('nivel 5 vs nivel 1', 'katana', 5, 'balanced', 'katana', 1, 'balanced', N);
batch('nivel 3 vs nivel 1', 'katana', 3, 'balanced', 'katana', 1, 'balanced', N);
batch('nivel 3 vs nivel 3 (espejo)', 'katana', 3, 'balanced', 'katana', 3, 'balanced', N);
['dagas', 'lanza', 'hacha'].forEach((w) => batch(`katana vs ${w} (nivel 3)`, 'katana', 3, 'balanced', w, 3, 'balanced', N));
batch('lanza vs hacha (nivel 3)', 'lanza', 3, 'balanced', 'hacha', 3, 'balanced', N);
batch('dagas vs hacha (nivel 3)', 'dagas', 3, 'balanced', 'hacha', 3, 'balanced', N);
['aggressive', 'turtle', 'trickster', 'brute', 'duelist'].forEach((p) => batch(`${p} vs balanced (nivel 4)`, 'katana', 4, p, 'katana', 4, 'balanced', N));
console.log(`(${((Date.now() - t0) / 1000).toFixed(1)}s)`);
