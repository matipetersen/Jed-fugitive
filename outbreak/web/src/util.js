// ---------------------------------------------------------------- util: seeded RNG, geometry, helpers
// Field and function names deliberately mirror the Python engine (snake_case) so the two stay easy to compare.

function hash_string(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  h = Math.imul(h ^ (h >>> 16), 2246822507);
  h = Math.imul(h ^ (h >>> 13), 3266489909);
  return (h ^ (h >>> 16)) >>> 0;
}

class RNG {
  constructor(seed) {
    this.state = (typeof seed === 'string' ? hash_string(seed) : (seed >>> 0)) || 1;
  }
  random() {                                   // mulberry32
    this.state = (this.state + 0x6D2B79F5) >>> 0;
    let t = this.state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  randint(a, b) { return a + Math.floor(this.random() * (b - a + 1)); }   // inclusive
  uniform(a, b) { return a + this.random() * (b - a); }
  choice(arr) { return arr[Math.floor(this.random() * arr.length)]; }
  shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(this.random() * (i + 1));
      const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }
  sample(arr, k) { return this.shuffle(arr.slice()).slice(0, k); }
}

const DIRS4 = [[0, -1], [1, 0], [0, 1], [-1, 0]];
const DIRS8 = DIRS4.concat([[1, -1], [1, 1], [-1, 1], [-1, -1]]);

const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
const cheb = (a, b) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]));
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const sign = (v) => (v > 0) - (v < 0);

// Bresenham from a (excluded) to b (included)
function line(a, b) {
  let [x0, y0] = a;
  const [x1, y1] = b;
  const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  const out = [];
  while (x0 !== x1 || y0 !== y1) {
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x0 += sx; }
    if (e2 <= dx) { err += dx; y0 += sy; }
    out.push([x0, y0]);
  }
  return out;
}

function weighted_choice(rng, pairs) {          // pairs: [[value, weight], ...]
  let total = 0;
  for (const p of pairs) if (p[1] > 0) total += p[1];
  if (total <= 0) throw new Error('weighted_choice needs a positive weight');
  let roll = rng.random() * total;
  for (const p of pairs) {
    if (p[1] <= 0) continue;
    roll -= p[1];
    if (roll <= 0) return p[0];
  }
  return pairs[pairs.length - 1][0];
}

function compass(dx, dy) {
  if (dx === 0 && dy === 0) return 'here';
  const ang = (Math.atan2(dx, -dy) * 180 / Math.PI + 360) % 360;
  const names = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
  return names[Math.floor((ang + 22.5) / 45) % 8];
}

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
const article = (noun) => ('aeiou'.includes((noun[0] || '').toLowerCase()) ? 'an' : 'a');
