export interface OrbitElements {
  bound: boolean;
  /** Eccentricity. */
  e: number;
  /** Unit vector from the focus towards periapsis. */
  periX: number;
  periY: number;
  /** Periapsis radius from the focus. */
  periapsis: number;
  /** Apoapsis radius from the focus, null when unbound. */
  apoapsis: number | null;
  /** Orbital period in seconds, null when unbound. */
  period: number | null;
  /** Specific angular momentum (positive = counter-clockwise). */
  h: number;
}

/** Two-body orbital elements of a position/velocity pair around a mass at the origin. */
export function orbitElements(x: number, y: number, vx: number, vy: number, gm: number): OrbitElements {
  const r = Math.hypot(x, y);
  const v2 = vx * vx + vy * vy;
  const energy = v2 / 2 - gm / r;
  const h = x * vy - y * vx;
  const k = v2 - gm / r;
  const rv = x * vx + y * vy;
  const ex = (k * x - rv * vx) / gm;
  const ey = (k * y - rv * vy) / gm;
  const e = Math.hypot(ex, ey);
  const periX = e > 1e-9 ? ex / e : x / r;
  const periY = e > 1e-9 ? ey / e : y / r;

  if (energy < 0) {
    const a = -gm / (2 * energy);
    return {
      bound: true,
      e,
      periX,
      periY,
      periapsis: a * (1 - e),
      apoapsis: a * (1 + e),
      period: 2 * Math.PI * Math.sqrt((a * a * a) / gm),
      h,
    };
  }
  return { bound: false, e, periX, periY, periapsis: (h * h) / (gm * (1 + e)), apoapsis: null, period: null, h };
}

function stumpffC(z: number): number {
  if (z > 1e-6) return (1 - Math.cos(Math.sqrt(z))) / z;
  if (z < -1e-6) return (Math.cosh(Math.sqrt(-z)) - 1) / -z;
  return 0.5 - z / 24;
}

function stumpffS(z: number): number {
  if (z > 1e-6) {
    const s = Math.sqrt(z);
    return (s - Math.sin(s)) / (s * s * s);
  }
  if (z < -1e-6) {
    const s = Math.sqrt(-z);
    return (Math.sinh(s) - s) / (s * s * s);
  }
  return 1 / 6 - z / 120;
}

/**
 * Two-body propagation with universal variables. Takes a state relative to the
 * attracting body and returns the state dt seconds later as [x, y, vx, vy].
 */
export function keplerPropagate(
  x0: number,
  y0: number,
  vx0: number,
  vy0: number,
  mu: number,
  dt: number,
): [number, number, number, number] {
  const r0 = Math.hypot(x0, y0);
  const alpha = 2 / r0 - (vx0 * vx0 + vy0 * vy0) / mu;
  if (alpha > 1e-12) {
    const period = (2 * Math.PI) / (Math.sqrt(mu) * Math.pow(alpha, 1.5));
    dt %= period;
  }
  if (dt === 0) return [x0, y0, vx0, vy0];
  const sqrtMu = Math.sqrt(mu);
  const rv = x0 * vx0 + y0 * vy0;
  let chi: number;
  if (alpha > 1e-12) chi = sqrtMu * dt * alpha;
  else if (alpha < -1e-12) {
    const a = 1 / alpha;
    const sign = Math.sign(dt);
    chi =
      sign *
      Math.sqrt(-a) *
      Math.log((-2 * mu * alpha * dt) / (rv + sign * Math.sqrt(-mu * a) * (1 - r0 * alpha)));
  } else chi = (sqrtMu * dt) / r0;

  let c = 0;
  let s = 0;
  let r = r0;
  for (let i = 0; i < 80; i++) {
    const psi = chi * chi * alpha;
    c = stumpffC(psi);
    s = stumpffS(psi);
    r = chi * chi * c + (rv / sqrtMu) * chi * (1 - psi * s) + r0 * (1 - psi * c);
    const f = chi * chi * chi * s + (rv / sqrtMu) * chi * chi * c + r0 * chi * (1 - psi * s) - sqrtMu * dt;
    const next = chi - f / r;
    if (Math.abs(next - chi) <= 1e-10 * Math.max(1, Math.abs(chi))) {
      chi = next;
      break;
    }
    chi = next;
  }
  const psi = chi * chi * alpha;
  c = stumpffC(psi);
  s = stumpffS(psi);
  r = chi * chi * c + (rv / sqrtMu) * chi * (1 - psi * s) + r0 * (1 - psi * c);
  const f = 1 - (chi * chi * c) / r0;
  const g = dt - (chi * chi * chi * s) / sqrtMu;
  const fd = (sqrtMu / (r * r0)) * chi * (psi * s - 1);
  const gd = 1 - (chi * chi * c) / r;
  return [f * x0 + g * vx0, f * y0 + g * vy0, fd * x0 + gd * vx0, fd * y0 + gd * vy0];
}
