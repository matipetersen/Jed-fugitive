const OB = require('../dist/engine.js');
const assert = require('assert');
let bad = 0, n = 0;
const t0 = Date.now();
for (const era of Object.values(OB.CONTENT.eras)) {
  for (let seed = 0; seed < 25; seed++) {
    const w = OB.generate_overworld(new OB.RNG(seed), era, 120, 76);
    const kinds = new Set(Object.values(w.pois).map((p) => p.kind));
    for (const k of OB.POI_KINDS) assert(kinds.has(k), `${era.id} ${seed} missing ${k}`);
    // reachability from start
    const lv = w.level, seen = new Uint8Array(lv.w * lv.h), q = [w.start[0] + w.start[1] * lv.w];
    seen[q[0]] = 1;
    for (let i = 0; i < q.length; i++) {
      const x = q[i] % lv.w, y = Math.floor(q[i] / lv.w);
      for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
        const nx = x + dx, ny = y + dy;
        if (lv.walkable(nx, ny) && !seen[ny * lv.w + nx]) { seen[ny * lv.w + nx] = 1; q.push(ny * lv.w + nx); }
      }
    }
    for (const p of Object.values(w.pois)) {
      if (p.kind === 'breach') continue;
      n++;
      if (!seen[p.x + p.y * lv.w]) bad++;
    }
  }
}
console.log(`world: ${n} doors checked, ${bad} unreachable, ${(Date.now() - t0)} ms total`);
assert.strictEqual(bad, 0);
