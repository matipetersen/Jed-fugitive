import { mulberry32 } from '../sim/rng';
import {
  type Asteroid,
  type ArenaEvent,
  type Controls,
  type GateDef,
  type Ship,
  type ShipStats,
  type StageDef,
} from './types';

export const SHIP_R = 7;
export const GATE_R = 36;
export const LAND_SPEED = 40;
export const LAND_TILT = 0.55;
export const BURN_RATE = 6;
export const BASE_STATS: ShipStats = { thrust: 150, turnRate: 3.4, fuelMax: 100, hullMax: 100 };
export const STEP = 1 / 120;

const TAU = Math.PI * 2;
const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));
const wrap = (a: number): number => {
  let r = (a + Math.PI) % TAU;
  if (r < 0) r += TAU;
  return r - Math.PI;
};

export interface RBody {
  def: StageDef['bodies'][number];
  index: number;
  parent: number;
  gm: number;
}

export interface RGate {
  def: GateDef;
  body: number;
  r: number;
}

export interface RCell {
  x: number;
  y: number;
  body: number;
  fuel: number;
  taken: boolean;
}

export interface Frame {
  x: Float64Array;
  y: Float64Array;
  vx: Float64Array;
  vy: Float64Array;
}

const makeFrame = (n: number): Frame => ({ x: new Float64Array(n), y: new Float64Array(n), vx: new Float64Array(n), vy: new Float64Array(n) });

/** One stage's world: bodies on rails, ships and asteroids under their gravity. */
export class Arena {
  t = 0;
  /** Seconds since GO; negative during the countdown. */
  clock = -3;
  go = false;
  winner = -1;
  readonly bodies: RBody[] = [];
  readonly gates: RGate[] = [];
  readonly cells: RCell[] = [];
  ships: Ship[] = [];
  asteroids: Asteroid[] = [];
  events: ArenaEvent[] = [];
  /** Body states at the current time `t`. */
  cur: Frame;
  private nxt: Frame;
  private readonly index = new Map<string, number>();
  private readonly g0 = { x: 0, y: 0 };
  private readonly g1 = { x: 0, y: 0 };
  private readonly gp = { x: 0, y: 0 };

  constructor(readonly def: StageDef) {
    def.bodies.forEach((b, i) => {
      this.index.set(b.id, i);
      this.bodies.push({ def: b, index: i, parent: -1, gm: b.g * b.r * b.r });
    });
    for (const b of this.bodies) {
      if (b.def.orbit) b.parent = this.index.get(b.def.orbit.parent) ?? -1;
    }
    this.cur = makeFrame(this.bodies.length);
    this.nxt = makeFrame(this.bodies.length);
    for (const g of def.gates) {
      this.gates.push({ def: g, body: g.body ? (this.index.get(g.body) ?? -1) : -1, r: g.r ?? GATE_R });
    }
    for (const c of def.cells) {
      this.cells.push({ x: c.x, y: c.y, body: c.body ? (this.index.get(c.body) ?? -1) : -1, fuel: c.fuel, taken: false });
    }
    this.framesAt(0, this.cur);
    this.spawnAsteroids();
  }

  bodyIndex(id: string): number {
    return this.index.get(id) ?? -1;
  }

  /** Fills a frame with body positions and velocities at time t. Parents come first. */
  framesAt(t: number, f: Frame): void {
    for (let i = 0; i < this.bodies.length; i++) {
      const b = this.bodies[i];
      const o = b.def.orbit;
      if (!o || b.parent < 0) {
        f.x[i] = b.def.x ?? 0;
        f.y[i] = b.def.y ?? 0;
        f.vx[i] = 0;
        f.vy[i] = 0;
      } else {
        const phi = o.phase + o.omega * t;
        const sp = o.a * o.omega;
        f.x[i] = f.x[b.parent] + o.a * Math.cos(phi);
        f.y[i] = f.y[b.parent] + o.a * Math.sin(phi);
        f.vx[i] = f.vx[b.parent] - sp * Math.sin(phi);
        f.vy[i] = f.vy[b.parent] + sp * Math.cos(phi);
      }
    }
  }

  get bx(): Float64Array {
    return this.cur.x;
  }
  get by(): Float64Array {
    return this.cur.y;
  }
  get bvx(): Float64Array {
    return this.cur.vx;
  }
  get bvy(): Float64Array {
    return this.cur.vy;
  }

  /** Gate centre at the arena's current time. */
  gatePos(i: number, out: { x: number; y: number }, f: Frame = this.cur): void {
    const g = this.gates[i];
    out.x = g.def.x + (g.body >= 0 ? f.x[g.body] : 0);
    out.y = g.def.y + (g.body >= 0 ? f.y[g.body] : 0);
  }

  private spawnAsteroids(): void {
    let id = 1;
    for (const spec of this.def.asteroids) {
      const rnd = mulberry32(spec.seed);
      const c = this.index.get(spec.around) ?? 0;
      const gm = this.bodies[c].gm;
      for (let k = 0; k < spec.count; k++) {
        const r = spec.rIn + rnd() * (spec.rOut - spec.rIn);
        const a = rnd() * TAU;
        const vc = Math.sqrt(gm / r) * spec.speed * (0.9 + rnd() * 0.2);
        this.asteroids.push({
          id: id++,
          x: this.cur.x[c] + r * Math.cos(a),
          y: this.cur.y[c] + r * Math.sin(a),
          vx: this.cur.vx[c] - vc * Math.sin(a),
          vy: this.cur.vy[c] + vc * Math.cos(a),
          r: spec.size[0] + rnd() * (spec.size[1] - spec.size[0]),
          alive: true,
        });
      }
    }
  }

  addShip(opts: { isPlayer: boolean; name: string; color: string; stats: ShipStats; start: { body: string; angle: number }; infiniteFuel?: boolean }): Ship {
    const body = this.index.get(opts.start.body) ?? 0;
    const ship: Ship = {
      id: this.ships.length,
      isPlayer: opts.isPlayer,
      name: opts.name,
      color: opts.color,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      angle: opts.start.angle,
      throttle: 0,
      fuel: opts.stats.fuelMax,
      hull: opts.stats.hullMax,
      stats: opts.stats,
      status: 'landed',
      landedBody: body,
      landedAngle: opts.start.angle,
      deadTimer: 0,
      deathReason: '',
      invuln: 0,
      nextGate: 0,
      finished: false,
      finishTime: 0,
      infiniteFuel: !!opts.infiniteFuel,
      bonfire: null,
    };
    this.ships.push(ship);
    this.place(ship);
    return ship;
  }

  /** Puts a landed or dead ship on its body, which keeps orbiting. */
  place(s: Ship, f: Frame = this.cur): void {
    const b = this.bodies[s.landedBody];
    const r = b.def.r + SHIP_R;
    s.x = f.x[s.landedBody] + r * Math.cos(s.landedAngle);
    s.y = f.y[s.landedBody] + r * Math.sin(s.landedAngle);
    s.vx = f.vx[s.landedBody];
    s.vy = f.vy[s.landedBody];
  }

  /** Brings a dead ship back, landed on a pad or at the start. */
  respawn(s: Ship, spot: { body: number; angle: number }, restore: { fuel: number; hull: number }): void {
    s.status = 'landed';
    s.landedBody = spot.body;
    s.landedAngle = spot.angle;
    s.angle = spot.angle;
    s.throttle = 0;
    s.fuel = Math.min(s.stats.fuelMax, restore.fuel);
    s.hull = Math.min(s.stats.hullMax, restore.hull);
    s.deadTimer = 0;
    s.deathReason = '';
    s.invuln = 1.5;
    this.place(s);
  }

  /** Pad whose window contains `angle` on a body, or -1. */
  padAt(body: number, angle: number): number {
    const b = this.bodies[body];
    const pads = b.def.pads;
    if (!pads) return -1;
    for (let i = 0; i < pads.length; i++) {
      if (Math.abs(wrap(angle - pads[i].angle)) * b.def.r <= pads[i].half) return i;
    }
    return -1;
  }

  /** Gravity from all bodies at a point for a given set of body positions. */
  gravity(x: number, y: number, f: Frame, out: { x: number; y: number }): void {
    let ax = 0;
    let ay = 0;
    for (let i = 0; i < this.bodies.length; i++) {
      const b = this.bodies[i];
      const dx = f.x[i] - x;
      const dy = f.y[i] - y;
      let d2 = dx * dx + dy * dy;
      const min = b.def.r * 0.6;
      if (d2 < min * min) d2 = min * min;
      const d = Math.sqrt(d2);
      const k = b.gm / (d2 * d);
      ax += dx * k;
      ay += dy * k;
    }
    out.x = ax;
    out.y = ay;
  }

  private die(s: Ship, reason: string): void {
    if (s.status === 'dead') return;
    s.status = 'dead';
    s.deathReason = reason;
    s.deadTimer = s.isPlayer ? 2.2 : 3;
    s.throttle = 0;
    this.events.push({ type: 'die', ship: s.id, reason, x: s.x, y: s.y });
  }

  damage(s: Ship, amount: number, by: string): void {
    if (s.status === 'dead' || s.invuln > 0) return;
    s.hull -= amount;
    this.events.push({ type: 'hit', ship: s.id, damage: amount, by });
    if (s.hull <= 0) this.die(s, by);
  }

  /** Starts the race: ships may fly and the clock begins at zero. */
  start(): void {
    this.go = true;
    this.clock = 0;
  }

  step(controls: (Controls | undefined)[], h: number = STEP): void {
    this.framesAt(this.t + h, this.nxt);
    for (const s of this.ships) this.stepShip(s, controls[s.id] ?? { throttle: 0, turn: 0 }, h);
    this.stepAsteroids(h);
    this.t += h;
    this.clock += h;
    const swap = this.cur;
    this.cur = this.nxt;
    this.nxt = swap;
    if (!this.go && this.clock >= 0) this.start();
    this.shipCollisions();
    this.passGates();
    this.pickCells();
    for (const s of this.ships) {
      if (s.status === 'landed') this.place(s);
    }
  }

  /** Puts a ship back in flight at a point, moving with the closest body (used for the rival). */
  respawnFlying(s: Ship, x: number, y: number): void {
    let best = 0;
    let bd = Infinity;
    for (let i = 0; i < this.bodies.length; i++) {
      const d = Math.hypot(x - this.cur.x[i], y - this.cur.y[i]) - this.bodies[i].def.r;
      if (d < bd) {
        bd = d;
        best = i;
      }
    }
    s.status = 'flying';
    s.x = x;
    s.y = y;
    s.vx = this.cur.vx[best];
    s.vy = this.cur.vy[best];
    s.hull = s.stats.hullMax;
    s.fuel = s.stats.fuelMax;
    s.deadTimer = 0;
    s.deathReason = '';
    s.invuln = 1.5;
  }

  private stepShip(s: Ship, c: Controls, h: number): void {
    if (s.invuln > 0) s.invuln = Math.max(0, s.invuln - h);
    if (s.status === 'dead') {
      s.deadTimer -= h;
      return;
    }
    const thr = this.go && (s.fuel > 0 || s.infiniteFuel) ? clamp(c.throttle, 0, 1) : 0;
    s.throttle = thr;
    const aT = thr * s.stats.thrust;
    if (!s.infiniteFuel) s.fuel = Math.max(0, s.fuel - thr * BURN_RATE * h);

    if (s.status === 'landed') {
      const b = this.bodies[s.landedBody];
      const lift = aT * Math.cos(s.angle - s.landedAngle) - b.def.g;
      if (lift <= 0) return;
      // Lift off and go straight on into this step's flight, so the ship keeps pace with its moving body.
      s.status = 'flying';
      s.vx = this.cur.vx[s.landedBody];
      s.vy = this.cur.vy[s.landedBody];
    }

    s.angle = wrap(s.angle + clamp(c.turn, -1, 1) * s.stats.turnRate * h);
    const nx = Math.cos(s.angle);
    const ny = Math.sin(s.angle);

    // Extra forces held constant over the step: atmosphere drag, wind, radiation, stellar heat.
    let fx = 0;
    let fy = 0;
    for (let i = 0; i < this.bodies.length; i++) {
      const b = this.bodies[i];
      const d = Math.hypot(s.x - this.cur.x[i], s.y - this.cur.y[i]);
      const atm = b.def.atm;
      if (atm && d - b.def.r < atm.h * 3) {
        const rho = Math.exp(-Math.max(d - b.def.r, 0) / atm.h);
        const rvx = s.vx - this.cur.vx[i];
        const rvy = s.vy - this.cur.vy[i];
        const sp = Math.hypot(rvx, rvy);
        fx -= atm.drag * rho * sp * rvx;
        fy -= atm.drag * rho * sp * rvy;
      }
      if (b.def.star && d < b.def.r * 1.9) this.damage(s, 16 * h, 'calor');
    }
    for (const f of this.def.fields) {
      if (Math.hypot(s.x - f.x, s.y - f.y) > f.r) continue;
      if (f.kind === 'wind') {
        fx += f.ax ?? 0;
        fy += f.ay ?? 0;
      } else this.damage(s, (f.dps ?? 10) * h, 'radiación');
    }
    if (s.status !== 'flying') return;

    this.gravity(s.x, s.y, this.cur, this.g0);
    s.vx += (this.g0.x + nx * aT + fx) * h * 0.5;
    s.vy += (this.g0.y + ny * aT + fy) * h * 0.5;
    s.x += s.vx * h;
    s.y += s.vy * h;
    this.gravity(s.x, s.y, this.nxt, this.g1);
    s.vx += (this.g1.x + nx * aT + fx) * h * 0.5;
    s.vy += (this.g1.y + ny * aT + fy) * h * 0.5;

    this.shipVsBodies(s);
  }

  /** Collision with the bodies at their end-of-step positions. */
  private shipVsBodies(s: Ship): void {
    const f = this.nxt;
    for (let i = 0; i < this.bodies.length; i++) {
      const b = this.bodies[i];
      const dx = s.x - f.x[i];
      const dy = s.y - f.y[i];
      const d = Math.hypot(dx, dy);
      if (d >= b.def.r + SHIP_R) continue;
      const speed = Math.hypot(s.vx - f.vx[i], s.vy - f.vy[i]);
      const normal = Math.atan2(dy, dx);
      const tilt = Math.abs(wrap(s.angle - normal));
      if (b.def.star) {
        this.die(s, 'sol');
        return;
      }
      if (speed <= LAND_SPEED && tilt <= LAND_TILT) {
        s.status = 'landed';
        s.landedBody = i;
        s.landedAngle = normal;
        s.throttle = 0;
        const pad = this.padAt(i, normal);
        const bonfire = pad >= 0 && !!b.def.pads?.[pad].bonfire;
        if (bonfire) {
          s.bonfire = { body: i, pad };
          s.fuel = s.stats.fuelMax;
          s.hull = s.stats.hullMax;
        }
        this.events.push({ type: 'land', ship: s.id, body: i, pad, bonfire });
      } else this.die(s, speed > LAND_SPEED ? 'impacto' : 'mal aterrizaje');
      return;
    }
  }

  private stepAsteroids(h: number): void {
    for (const a of this.asteroids) {
      if (!a.alive) continue;
      this.gravity(a.x, a.y, this.cur, this.g0);
      a.vx += this.g0.x * h;
      a.vy += this.g0.y * h;
      a.x += a.vx * h;
      a.y += a.vy * h;
      // Rocks that touch a body or drift far away disappear. They never depend on the player.
      if (Math.abs(a.x) > 40000 || Math.abs(a.y) > 40000) a.alive = false;
      for (let i = 0; i < this.bodies.length; i++) {
        if (Math.hypot(a.x - this.nxt.x[i], a.y - this.nxt.y[i]) < this.bodies[i].def.r + a.r) {
          a.alive = false;
          break;
        }
      }
    }
    for (const s of this.ships) {
      if (s.status === 'dead') continue;
      for (const a of this.asteroids) {
        if (!a.alive) continue;
        if (Math.hypot(a.x - s.x, a.y - s.y) < a.r + SHIP_R) {
          const rel = Math.hypot(a.vx - s.vx, a.vy - s.vy);
          a.alive = false;
          this.damage(s, clamp(0.3 * rel, 8, 55), 'asteroide');
        }
      }
    }
  }

  private shipCollisions(): void {
    for (let i = 0; i < this.ships.length; i++) {
      for (let j = i + 1; j < this.ships.length; j++) {
        const a = this.ships[i];
        const b = this.ships[j];
        if (a.status !== 'flying' || b.status !== 'flying') continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const d = Math.hypot(dx, dy);
        if (d >= SHIP_R * 2 || d < 1e-6) continue;
        const nx = dx / d;
        const ny = dy / d;
        const rel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny;
        const push = (SHIP_R * 2 - d) / 2;
        a.x -= nx * push;
        a.y -= ny * push;
        b.x += nx * push;
        b.y += ny * push;
        if (rel < 0) {
          const j2 = -(1 + 0.6) * rel * 0.5;
          a.vx -= j2 * nx;
          a.vy -= j2 * ny;
          b.vx += j2 * nx;
          b.vy += j2 * ny;
          this.events.push({ type: 'bump', a: a.id, b: b.id });
          const speed = -rel;
          if (speed > 50) {
            const dmg = 4 + 0.16 * (speed - 50);
            this.damage(a, dmg, 'choque');
            this.damage(b, dmg, 'choque');
          }
        }
      }
    }
  }

  private passGates(): void {
    if (!this.go) return;
    for (const s of this.ships) {
      if (s.status !== 'flying' || s.finished) continue;
      if (s.nextGate >= this.gates.length) continue;
      this.gatePos(s.nextGate, this.gp);
      if (Math.hypot(s.x - this.gp.x, s.y - this.gp.y) <= this.gates[s.nextGate].r) {
        const idx = s.nextGate;
        const final = !!this.gates[idx].def.final || idx === this.gates.length - 1;
        s.nextGate++;
        this.events.push({ type: 'gate', ship: s.id, index: idx, final });
        if (final) {
          s.finished = true;
          s.finishTime = this.clock;
          if (this.winner < 0) this.winner = s.id;
        }
      }
    }
  }

  private pickCells(): void {
    for (const c of this.cells) {
      if (c.taken) continue;
      const cx = c.x + (c.body >= 0 ? this.cur.x[c.body] : 0);
      const cy = c.y + (c.body >= 0 ? this.cur.y[c.body] : 0);
      for (const s of this.ships) {
        if (s.status !== 'flying' || !s.isPlayer) continue;
        if (Math.hypot(s.x - cx, s.y - cy) < 22) {
          c.taken = true;
          s.fuel = Math.min(s.stats.fuelMax, s.fuel + c.fuel);
          this.events.push({ type: 'cell', ship: s.id });
        }
      }
    }
  }

  /** Cell centre at the current time. */
  cellPos(c: RCell, out: { x: number; y: number }): void {
    out.x = c.x + (c.body >= 0 ? this.cur.x[c.body] : 0);
    out.y = c.y + (c.body >= 0 ? this.cur.y[c.body] : 0);
  }
}
