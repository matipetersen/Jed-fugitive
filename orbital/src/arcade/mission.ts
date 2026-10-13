import { mulberry32 } from '../sim/rng';
import { RIVAL_AI, RivalDriver } from './ai';
import { Arena, type RGate, STEP } from './arena';
import { type Meta, MISSION_LIVES, type Upgrades, addRecord, kitCount, raceProgress, shipStats, zeroUpgrades } from './meta';
import { RACES } from './races';
import { type ArenaEvent, type Controls, type RaceDef, type Ship, type StageDef } from './types';

export type Phase = 'countdown' | 'race' | 'dead' | 'cleared' | 'failed';

export interface Beacon {
  /** Body it is attached to and the offset from its centre. */
  body: number;
  dx: number;
  dy: number;
  data: number;
}

export interface MissionEvent {
  text: string;
  kind: 'info' | 'good' | 'bad';
}

export interface StageResult {
  won: boolean;
  time: number;
  rivalTime: number;
  /** Final place in a mass start, and how many started. */
  place?: number;
  field?: number;
  reward: number;
  reason: string;
}

const DATA_GATE = 10;
const DATA_SLING = 15;
const DATA_LAND = 25;
const DATA_OVERTAKE = 20;
const DATA_WRECK = 14;
/**
 * Everyone leaves at the same moment; what used to be the rival's head-start delay is now a slightly
 * lower cruise pace, so a stage is about as hard as before without anybody waiting at the start.
 */
export function rivalPace(def: StageDef, level = 1): number {
  return Math.max(0.45, Math.min(1.05, Math.min(1, 1 - def.rival.delay / (def.par * 0.9 + 5)) * 0.9 * [0.88, 1, 1.1][level]!));
}

const FIELD_COLORS = ['#ff2bd6', '#ffb000', '#7dff6b', '#b46bff', '#ff6a3c', '#2f9bff', '#ffe14a', '#ff4d8d', '#4dffd2', '#c8d4ff', '#ff9a5a'];

/** A run through the stages: lives, carried data, beacon, kits and the rival. */
export class Mission {
  arena!: Arena;
  player!: Ship;
  rival!: Ship;
  driver!: RivalDriver;
  /** Every AI ship (just the rival, or the whole field in a mass start) and their pilots. */
  rivals: Ship[] = [];
  drivers: RivalDriver[] = [];
  stageIdx = 0;
  lives = MISSION_LIVES;
  carried = 0;
  earned = 0;
  beacon: Beacon | null = null;
  kits = 0;
  kitCooldown = 0;
  phase: Phase = 'countdown';
  result: StageResult | null = null;
  log: MissionEvent[] = [];
  deaths = 0;
  clearedTime = 0;
  stagesCleared = 0;
  /** Endless runs: lost stages left to spend and the current streak of wins. */
  continues = 0;
  streak = 0;
  /** Set when the mission is over for good (won or failed). */
  over: 'won' | 'failed' | null = null;
  /** Called for every arena event, for effects and sound. */
  onEvent: ((e: ArenaEvent) => void) | null = null;
  private acc = 0;
  private deadFor = 0;
  private overtook = false;
  private slung = new Set<number>();
  private close = new Map<number, boolean>();
  private entry = new Map<number, { vx: number; vy: number }>();
  /** Bodies the ship has already been well clear of, so leaving its own planet is not a fly-by. */
  private seenFar = new Set<number>();
  /** Speed won from gravity assists in this stage. */
  slingGain = 0;
  private rivalRnd: () => number;
  private recorded = false;

  constructor(
    readonly meta: Meta,
    opts: { stage?: number; practice?: boolean; race?: RaceDef } = {},
  ) {
    this.race = opts.race ?? RACES[0];
    this.practice = !!opts.practice;
    this.stageIdx = opts.stage ?? 0;
    if (!this.practice) {
      // Every run starts from scratch: no technology and no data carried over.
      meta.upgrades = zeroUpgrades();
      meta.data = 0;
      meta.attempts++;
    }
    this.continues = this.race.endless?.continues ?? 0;
    this.kits = kitCount(this.upgrades);
    this.rivalRnd = mulberry32(1000 + this.stageIdx);
    this.loadStage(this.stageIdx);
  }

  /** Technology of this run (practice always flies the base ship). */
  get upgrades(): Upgrades {
    return this.practice ? zeroUpgrades() : this.meta.upgrades;
  }

  readonly practice: boolean;
  readonly race: RaceDef;

  get stageCount(): number {
    return this.race.stages.length;
  }

  get def(): StageDef {
    return this.race.stages[this.stageIdx];
  }

  private loadStage(idx: number): void {
    this.stageIdx = idx;
    const def = this.race.stages[idx];
    this.arena = new Arena(def);
    const stats = shipStats(this.upgrades);
    stats.fuelMax = Math.round(stats.fuelMax * (def.tank ?? 1));
    this.player = this.arena.addShip({ isPlayer: true, name: 'Tú', color: '#00f0ff', stats, start: def.start, orbit: def.startAt });
    this.rivals = [];
    this.drivers = [];
    if (def.field) {
      const f = def.field;
      const rnd = mulberry32(5000 + idx);
      f.slots.forEach((ang, k) => {
        const skill = def.rival.skill * (0.9 + 0.2 * rnd());
        const ship = this.arena.addShip({
          isPlayer: false,
          name: `${def.rival.name} ${k + 1}`,
          color: FIELD_COLORS[k % FIELD_COLORS.length],
          stats: { thrust: 150 * skill, turnRate: 3.6, fuelMax: 100, hullMax: 100, shield: 0, boost: 0 },
          start: { body: f.body, angle: (ang * Math.PI) / 180 },
          infiniteFuel: true,
        });
        const ai = { ...(def.rival.ai ?? RIVAL_AI), noise: (def.rival.ai?.noise ?? 0.2) * (0.6 + 0.9 * rnd()), interval: 0.25, pace: 0.86 + 0.14 * rnd() };
        const drv = new RivalDriver(mulberry32(7000 + idx * 31 + k), ai, 0);
        drv.ai.nextAt = rnd() * ai.interval;
        this.rivals.push(ship);
        this.drivers.push(drv);
      });
      this.rival = this.rivals[0];
      this.driver = this.drivers[0];
      this.applyFieldRoute(this.player, def.start.angle);
      this.rivals.forEach((sh, k) => this.applyFieldRoute(sh, (f.slots[k] * Math.PI) / 180));
    } else {
      this.rival = this.arena.addShip({
        isPlayer: false,
        name: def.rival.name,
        color: '#ff2bd6',
        stats: { thrust: 150 * def.rival.skill * (0.55 + 0.45 * rivalPace(def, this.meta.rivalLevel ?? 1)), turnRate: 3.6, fuelMax: 100, hullMax: 100, shield: 0, boost: 0 },
        start: def.rivalStart,
        orbit: def.startAt ? { ...def.startAt, angle: def.startAt.angle + 9 * (def.startAt.dir ?? 1) } : undefined,
        infiniteFuel: true,
      });
      this.rivalRnd = mulberry32(1000 + idx);
      this.driver = new RivalDriver(this.rivalRnd, { ...(def.rival.ai ?? RIVAL_AI), pace: rivalPace(def, this.meta.rivalLevel ?? 1) }, 0);
      this.rivals = [this.rival];
      this.drivers = [this.driver];
    }
    this.lives = MISSION_LIVES;
    if (!this.practice) {
      const pr = raceProgress(this.meta, this.race.id, this.stageCount);
      pr.reached = Math.max(pr.reached, idx + 1);
    }
    this.phase = 'countdown';
    this.result = null;
    this.beacon = null;
    this.overtook = false;
    this.slung.clear();
    this.close.clear();
    this.entry.clear();
    this.seenFar.clear();
    this.slingGain = 0;
    this.deadFor = 0;
    this.kitCooldown = 0;
    this.acc = 0;
  }

  private note(text: string, kind: MissionEvent['kind'] = 'info'): void {
    this.log.push({ text, kind });
    if (this.log.length > 30) this.log.shift();
  }

  /**
   * A mass start gives every ship its own route: the first ring gate ahead of its pad, the same number of
   * laps, and a landing on its own pad. All run the same distance wherever on the planet they start.
   */
  private applyFieldRoute(ship: Ship, angle: number): void {
    const f = this.def.field;
    if (!f) return;
    const a = this.arena;
    const bi = a.bodyIndex(f.body);
    const body = a.bodies[bi];
    const pads = body.def.pads ?? [];
    let padIdx = 0;
    let bestPad = Infinity;
    pads.forEach((pd, i) => {
      const d = Math.abs(Math.atan2(Math.sin(pd.angle - angle), Math.cos(pd.angle - angle)));
      if (d < bestPad) {
        bestPad = d;
        padIdx = i;
      }
    });
    const ring = a.gates;
    const TAU = Math.PI * 2;
    let first = 0;
    let bestAhead = Infinity;
    ring.forEach((gt, i) => {
      let ahead = (((Math.atan2(gt.def.y, gt.def.x) - angle) * f.dir) % TAU + TAU) % TAU;
      if (ahead < 0.3) ahead += TAU;
      if (ahead < bestAhead) {
        bestAhead = ahead;
        first = i;
      }
    });
    const route: RGate[] = [];
    for (let k = 0; k < f.laps * ring.length; k++) route.push(ring[(first + k) % ring.length]);
    const pa = pads[padIdx]?.angle ?? angle;
    const R = body.def.r + 110;
    route.push(a.makeGate({ x: Math.round(Math.cos(pa) * R), y: Math.round(Math.sin(pa) * R), final: true }));
    ship.route = route;
    ship.finishPad = { body: bi, pad: padIdx };
  }

  /** Position of the player among all ships, by gates passed and distance to the next target. */
  rank(): { pos: number; total: number } {
    const a = this.arena;
    const tmp = { x: 0, y: 0 };
    const score = (s: Ship): number => {
      if (s.finished) return 1e9 - s.finishTime;
      a.objective(s, tmp);
      return s.nextGate * 1e5 - Math.hypot(s.x - tmp.x, s.y - tmp.y);
    };
    const mine = score(this.player);
    let ahead = 0;
    for (const r of this.rivals) if (score(r) > mine) ahead++;
    return { pos: ahead + 1, total: this.rivals.length + 1 };
  }

  /** Positive when the player is ahead, in gates. */
  gateLead(): number {
    return this.player.nextGate - this.rival.nextGate;
  }

  useKit(): boolean {
    const p = this.player;
    if (this.kits <= 0 || this.kitCooldown > 0 || p.status === 'dead' || this.phase === 'cleared' || this.phase === 'failed') return false;
    this.kits--;
    this.kitCooldown = 2.5;
    p.fuel = Math.min(p.stats.fuelMax, p.fuel + 50);
    p.hull = Math.min(p.stats.hullMax, p.hull + 40);
    this.note('Cápsula usada: +50 combustible, +40 casco', 'good');
    return true;
  }

  /** Beacon position at the current time, or null. */
  beaconPos(): { x: number; y: number } | null {
    if (!this.beacon) return null;
    return { x: this.arena.bx[this.beacon.body] + this.beacon.dx, y: this.arena.by[this.beacon.body] + this.beacon.dy };
  }

  /** Advances the mission by a real time step, stepping the arena in fixed slices. */
  update(dt: number, controls: Controls): void {
    if (this.ended()) return;
    this.acc += Math.min(dt, 0.1);
    while (this.acc >= STEP) {
      this.acc -= STEP;
      this.tick(controls);
      if (this.ended()) break;
    }
  }

  /** True once the stage or the mission is decided. */
  ended(): boolean {
    return this.over !== null || this.phase === 'cleared' || this.phase === 'failed';
  }

  private tick(controls: Controls): void {
    const a = this.arena;
    if (this.kitCooldown > 0) this.kitCooldown = Math.max(0, this.kitCooldown - STEP);
    const ctl: Controls[] = [this.player.status === 'dead' ? { throttle: 0, turn: 0 } : controls];
    for (let i = 0; i < this.rivals.length; i++) ctl[this.rivals[i].id] = this.drivers[i].control(a, this.rivals[i]);
    a.step(ctl, STEP);
    if (this.phase === 'countdown' && a.go) {
      this.phase = 'race';
      this.note('¡YA!', 'good');
    }
    this.watchSlingshot();
    for (const e of a.events) this.handle(e);
    a.events.length = 0;

    // Overtaking the rival.
    if (!this.overtook && !this.def.field && this.player.nextGate > this.rival.nextGate && this.rival.nextGate > 0 && this.phase === 'race') {
      this.overtook = true;
      this.gain(DATA_OVERTAKE, 'Rebasaste al rival');
    }

    if (this.player.status === 'dead') {
      this.deadFor += STEP;
      if (this.phase !== 'dead') this.phase = 'dead';
      if (this.player.deadTimer <= 0) this.afterDeath();
    }

    const field = this.def.field;
    if (field) {
      if (this.player.finished) this.finishStage(a.finishOrder.indexOf(this.player.id) < field.podium);
      else if (a.finishOrder.length >= field.podium && this.phase === 'race') this.finishStage(false);
    } else if (this.player.finished && a.winner === this.player.id) this.finishStage(true);
    else if (this.rival.finished && !this.player.finished && this.phase === 'race') this.finishStage(false);
  }

  private gain(n: number, why: string): void {
    this.carried += n;
    this.note(`+${n} datos · ${why}`, 'good');
  }

  private watchSlingshot(): void {
    const p = this.player;
    if (p.status !== 'flying') return;
    const a = this.arena;
    for (let i = 0; i < a.bodies.length; i++) {
      const b = a.bodies[i];
      if (b.def.star || b.def.hole) continue;
      const alt = Math.hypot(p.x - a.bx[i], p.y - a.by[i]) - b.def.r;
      const rel = Math.hypot(p.vx - a.bvx[i], p.vy - a.bvy[i]);
      // Big planets count from farther out: a fly-by is "close" in proportion to the body.
      const near = 50 + 0.8 * b.def.r;
      if (alt > near + 90) this.seenFar.add(i);
      if (alt < near && rel > 90 && this.seenFar.has(i)) {
        if (!this.close.get(i)) this.entry.set(i, { vx: p.vx, vy: p.vy });
        this.close.set(i, true);
      }
      if (alt > near + 90 && this.close.get(i) && !this.slung.has(i)) {
        this.slung.add(i);
        this.close.set(i, false);
        const e = this.entry.get(i);
        const sIn = e ? Math.hypot(e.vx, e.vy) : 0;
        const sOut = Math.hypot(p.vx, p.vy);
        const gainSpeed = sOut - sIn;
        let turn = 0;
        if (e && sIn > 1 && sOut > 1) turn = Math.abs(Math.atan2(p.vx * e.vy - p.vy * e.vx, p.vx * e.vx + p.vy * e.vy)) * (180 / Math.PI);
        const bonus = Math.max(0, Math.round(gainSpeed * 0.25)) + Math.round(turn * 0.15);
        this.slingGain += Math.max(0, gainSpeed);
        this.gain(DATA_SLING + bonus, `Honda gravitatoria en ${b.def.name}: ${gainSpeed >= 0 ? '+' : ''}${Math.round(gainSpeed)} u/s, giro ${Math.round(turn)}°`);
      }
    }
  }

  private handle(e: ArenaEvent): void {
    this.onEvent?.(e);
    if (e.type === 'gate' && e.ship === this.player.id) {
      this.gain(DATA_GATE, `Aro ${e.index + 1}`);
    } else if (e.type === 'land' && e.ship === this.player.id) {
      if (e.bonfire) this.rest(e.body);
    } else if (e.type === 'die' && e.ship === this.player.id) {
      this.onPlayerDeath(e.reason, e.x, e.y);
    } else if (e.type === 'hit' && e.ship === this.player.id && e.damage >= 20) {
      this.note(`Golpe: -${Math.round(e.damage)} casco (${e.by})`, 'bad');
    } else if (e.type === 'cell' && e.ship === this.player.id) {
      this.note('Celda de combustible', 'good');
    } else if (e.type === 'die' && e.ship === this.rival.id && !this.def.field) {
      this.note(`${this.rival.name} se estrelló (${e.reason})`, 'good');
    }
  }

  /** Landing on a bonfire: bank the data, refill the kits, and set the respawn point. */
  private rest(body: number): void {
    const banked = this.carried;
    this.earned += banked;
    if (!this.practice) this.meta.data += banked;
    this.carried = 0;
    this.kits = kitCount(this.upgrades);
    this.beacon = null;
    this.gain(DATA_LAND, 'Estación alcanzada');
    // Landing gain is banked immediately too.
    this.earned += this.carried;
    if (!this.practice) this.meta.data += this.carried;
    this.carried = 0;
    this.note(banked > 0 ? `Datos guardados: ${banked}` : 'Punto de control', 'good');
    void body;
  }

  private onPlayerDeath(reason: string, x: number, y: number): void {
    this.deaths++;
    this.meta.deaths += this.practice ? 0 : 1;
    const a = this.arena;
    // The lost data waits where you died, attached to the nearest body.
    let near = 0;
    let nd = Infinity;
    for (let i = 0; i < a.bodies.length; i++) {
      const d = Math.hypot(x - a.bx[i], y - a.by[i]);
      if (d < nd) {
        nd = d;
        near = i;
      }
    }
    if (this.carried > 0 && !this.practice) {
      this.beacon = { body: near, dx: x - a.bx[near], dy: y - a.by[near], data: this.carried };
    }
    const lost = this.carried;
    this.carried = 0;
    if (!this.practice) this.lives--;
    this.note(`Muerte: ${reason}${lost > 0 && !this.practice ? ` · ${lost} datos quedaron en la baliza` : ''}`, 'bad');
    if (!this.practice) {
      // The wreck is not wasted: the telemetry of a lost ship pays for improvements.
      const wreck = DATA_WRECK + 6 * Math.min(this.stageIdx, 12);
      this.earned += wreck;
      this.meta.data += wreck;
      this.note(`+${wreck} datos · telemetría de la nave perdida`, 'info');
    }
  }

  private afterDeath(): void {
    if (!this.practice && this.lives <= 0) {
      this.finishStage(false, 'Te quedaste sin vidas en esta etapa.');
      return;
    }
    const p = this.player;
    const a = this.arena;
    const bf = p.bonfire;
    const spot = bf ? { body: bf.body, angle: a.bodies[bf.body].def.pads![bf.pad].angle } : { body: a.bodyIndex(this.def.start.body), angle: this.def.start.angle };
    if (!bf && this.def.startAt) {
      // A stage that starts in flight restarts in flight.
      a.putInOrbit(p, this.def.startAt);
      p.fuel = p.stats.fuelMax;
      p.hull = p.stats.hullMax * 0.7;
      p.deadTimer = 0;
      p.deathReason = '';
      p.invuln = 1.5;
    } else a.respawn(p, spot, { fuel: p.stats.fuelMax, hull: p.stats.hullMax * 0.7 });
    this.kits = Math.max(this.kits, kitCount(this.upgrades) - (bf ? 0 : 1));
    this.phase = 'race';
    this.deadFor = 0;
    this.note(bf ? 'Reapareciste en la estación' : 'Reapareciste en la plataforma', 'info');
  }

  /** Touching the beacon returns the lost data. Called every frame by the game. */
  checkBeacon(): void {
    const bp = this.beaconPos();
    const p = this.player;
    if (!bp || !this.beacon || p.status === 'dead') return;
    if (Math.hypot(p.x - bp.x, p.y - bp.y) < 26) {
      this.carried += this.beacon.data;
      this.note(`Recuperaste ${this.beacon.data} datos`, 'good');
      this.beacon = null;
    }
  }

  private finishStage(won: boolean, lost = ''): void {
    const a = this.arena;
    const last = this.stageIdx === this.stageCount - 1;
    const time = this.player.finished ? this.player.finishTime : a.clock;
    const rivalTime = this.rival.finished ? this.rival.finishTime : a.clock;
    const field = this.def.field;
    const place = field ? (a.finishOrder.includes(this.player.id) ? a.finishOrder.indexOf(this.player.id) + 1 : this.rank().pos) : undefined;
    let reward = 0;
    let reason = '';
    if (field && place) {
      reward = this.practice ? 0 : won ? Math.round(500 - 125 * (place - 1) + (this.player.hull / this.player.stats.hullMax) * 30) : 60;
      if (won) {
        this.stagesCleared++;
        this.clearedTime += time;
        this.note(`¡Podio! Llegaste ${place}º de ${field.slots.length + 1}`, 'good');
      } else reason = a.finishOrder.includes(this.player.id) ? `Llegaste ${place}º de ${field.slots.length + 1}: fuera del podio.` : `El podio se llenó sin vos. Ibas ${place}º de ${field.slots.length + 1}.`;
      if (won && !this.practice) {
        const pr = raceProgress(this.meta, this.race.id, this.stageCount);
        pr.cleared = Math.max(pr.cleared, this.stageIdx + 1);
        const best = pr.best[this.stageIdx];
        if (best === null || time < best) pr.best[this.stageIdx] = time;
      }
    } else if (won) {
      const margin = Math.max(0, rivalTime - time);
      reward = this.practice ? 0 : Math.round(100 * Math.min(this.stageIdx + 1, 12) + margin * 4 + (this.player.hull / this.player.stats.hullMax) * 30);
      this.stagesCleared++;
      this.clearedTime += time;
      if (!this.practice) {
        const pr = raceProgress(this.meta, this.race.id, this.stageCount);
        pr.cleared = Math.max(pr.cleared, this.stageIdx + 1);
        const best = pr.best[this.stageIdx];
        if (best === null || time < best) pr.best[this.stageIdx] = time;
      }
      this.note(`Etapa ${this.stageIdx + 1} superada en ${time.toFixed(1)} s`, 'good');
    } else {
      // A lost stage still pays a little: the run goes on.
      reward = this.practice ? 0 : 25 * Math.min(this.stageIdx + 1, 12);
      if (lost) reason = lost;
      else {
        const total = this.player.route.length;
        reason = `${this.rival.name} llegó primero: pasó los ${total} aros y aterrizó a los ${rivalTime.toFixed(0)} s; vos ${a.gatesDone(this.player) ? 'ya habías pasado los aros pero no llegaste a aterrizar' : `ibas por ${this.player.nextGate}/${total} aros`}.`;
      }
    }
    this.earned += this.carried + reward;
    if (!this.practice) this.meta.data += this.carried + reward;
    this.carried = 0;
    this.phase = 'cleared';
    this.result = { won, time, rivalTime, place, field: field ? field.slots.length + 1 : undefined, reward, reason };
    const endless = this.race.endless;
    if (endless && !this.practice) {
      if (won) {
        this.streak++;
        if (this.streak % 5 === 0) this.continues = Math.min(endless.maxContinues, this.continues + 1);
      } else {
        this.streak = 0;
        this.continues--;
        if (this.continues <= 0) this.endMission('failed');
      }
    }
    if (last && !this.practice && !this.over) this.endMission(won ? 'won' : 'failed');
  }

  private endMission(kind: 'won' | 'failed'): void {
    this.over = kind;
    if (this.phase !== 'cleared') this.phase = 'failed';
    if (this.practice || this.recorded) return;
    this.recorded = true;
    if (kind === 'won') raceProgress(this.meta, this.race.id, this.stageCount).won = true;
    addRecord(this.meta, { race: this.race.id, stages: this.stagesCleared, time: this.clearedTime, data: this.earned, won: kind === 'won', deaths: this.deaths });
  }

  /** Leaving a run early: it ends and is recorded as it stands. */
  abandon(): void {
    if (this.practice || this.over) return;
    this.endMission('failed');
  }

  /** Moves on after a cleared stage: refills the ship partly and loads the next stage. */
  nextStage(): boolean {
    if (this.phase !== 'cleared' || this.over || this.stageIdx >= this.stageCount - 1) return false;
    this.loadStage(this.stageIdx + 1);
    this.kits = kitCount(this.upgrades);
    return true;
  }

  /** Practice mode: try the same stage again. */
  retry(): void {
    this.loadStage(this.stageIdx);
  }
}
