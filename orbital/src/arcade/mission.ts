import { mulberry32 } from '../sim/rng';
import { RIVAL_AI, RivalDriver } from './ai';
import { Arena, STEP } from './arena';
import { type Meta, MISSION_LIVES, addRecord, kitCount, shipStats } from './meta';
import { STAGES } from './stages';
import { type ArenaEvent, type Controls, type Ship, type StageDef } from './types';

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
  reward: number;
  reason: string;
}

const DATA_GATE = 10;
const DATA_SLING = 15;
const DATA_LAND = 25;
const DATA_OVERTAKE = 20;

/** A run through the stages: lives, carried data, beacon, kits and the rival. */
export class Mission {
  arena!: Arena;
  player!: Ship;
  rival!: Ship;
  driver!: RivalDriver;
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
  /** Set when the mission is over for good (won or failed). */
  over: 'won' | 'failed' | null = null;
  /** Called for every arena event, for effects and sound. */
  onEvent: ((e: ArenaEvent) => void) | null = null;
  private acc = 0;
  private deadFor = 0;
  private overtook = false;
  private slung = new Set<number>();
  private close = new Map<number, boolean>();
  private rivalRnd: () => number;
  private recorded = false;

  constructor(
    readonly meta: Meta,
    opts: { stage?: number; practice?: boolean } = {},
  ) {
    this.practice = !!opts.practice;
    this.stageIdx = opts.stage ?? 0;
    this.kits = kitCount(meta.upgrades);
    this.rivalRnd = mulberry32(1000 + this.stageIdx);
    if (!this.practice) meta.attempts++;
    this.loadStage(this.stageIdx);
  }

  readonly practice: boolean;

  get def(): StageDef {
    return STAGES[this.stageIdx];
  }

  private loadStage(idx: number): void {
    this.stageIdx = idx;
    const def = STAGES[idx];
    this.arena = new Arena(def);
    const stats = shipStats(this.meta.upgrades);
    this.player = this.arena.addShip({ isPlayer: true, name: 'Tú', color: '#00f0ff', stats, start: def.start });
    this.rival = this.arena.addShip({
      isPlayer: false,
      name: def.rival.name,
      color: '#ff2bd6',
      stats: { thrust: 150 * def.rival.skill, turnRate: 3.6, fuelMax: 100, hullMax: 100 },
      start: def.rivalStart,
      infiniteFuel: true,
    });
    this.rivalRnd = mulberry32(1000 + idx);
    this.driver = new RivalDriver(this.rivalRnd, def.rival.ai ?? RIVAL_AI, def.rival.delay);
    this.phase = 'countdown';
    this.result = null;
    this.beacon = null;
    this.overtook = false;
    this.slung.clear();
    this.close.clear();
    this.deadFor = 0;
    this.kitCooldown = 0;
    this.acc = 0;
  }

  private note(text: string, kind: MissionEvent['kind'] = 'info'): void {
    this.log.push({ text, kind });
    if (this.log.length > 30) this.log.shift();
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
    const rc = this.driver.control(a, this.rival);
    a.step([this.player.status === 'dead' ? { throttle: 0, turn: 0 } : controls, rc], STEP);
    if (this.phase === 'countdown' && a.go) {
      this.phase = 'race';
      this.note('¡YA!', 'good');
    }
    this.watchSlingshot();
    for (const e of a.events) this.handle(e);
    a.events.length = 0;

    // Overtaking the rival.
    if (!this.overtook && this.player.nextGate > this.rival.nextGate && this.rival.nextGate > 0 && this.phase === 'race') {
      this.overtook = true;
      this.gain(DATA_OVERTAKE, 'Rebasaste al rival');
    }

    if (this.player.status === 'dead') {
      this.deadFor += STEP;
      if (this.phase !== 'dead') this.phase = 'dead';
      if (this.player.deadTimer <= 0) this.afterDeath();
    }

    if (this.player.finished && a.winner === this.player.id) this.finishStage(true);
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
      if (b.def.star) continue;
      const alt = Math.hypot(p.x - a.bx[i], p.y - a.by[i]) - b.def.r;
      const rel = Math.hypot(p.vx - a.bvx[i], p.vy - a.bvy[i]);
      if (alt < 70 && rel > 110) this.close.set(i, true);
      if (alt > 130 && this.close.get(i) && !this.slung.has(i)) {
        this.slung.add(i);
        this.close.set(i, false);
        this.gain(DATA_SLING, `Honda gravitatoria en ${b.def.name}`);
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
    } else if (e.type === 'die' && e.ship === this.rival.id) {
      this.note(`${this.rival.name} se estrelló (${e.reason})`, 'good');
    }
  }

  /** Landing on a bonfire: bank the data, refill the kits, and set the respawn point. */
  private rest(body: number): void {
    const banked = this.carried;
    this.earned += banked;
    if (!this.practice) this.meta.data += banked;
    this.carried = 0;
    this.kits = kitCount(this.meta.upgrades);
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
  }

  private afterDeath(): void {
    if (!this.practice && this.lives <= 0) {
      this.endMission('failed', 'Sin vidas');
      return;
    }
    const p = this.player;
    const a = this.arena;
    const bf = p.bonfire;
    const spot = bf ? { body: bf.body, angle: a.bodies[bf.body].def.pads![bf.pad].angle } : { body: a.bodyIndex(this.def.start.body), angle: this.def.start.angle };
    a.respawn(p, spot, { fuel: p.stats.fuelMax, hull: p.stats.hullMax * 0.7 });
    this.kits = Math.max(this.kits, kitCount(this.meta.upgrades) - (bf ? 0 : 1));
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

  private finishStage(won: boolean): void {
    const a = this.arena;
    const time = this.player.finished ? this.player.finishTime : a.clock;
    const rivalTime = this.rival.finished ? this.rival.finishTime : a.clock;
    if (!won) {
      if (this.practice) {
        this.phase = 'cleared';
        this.result = { won: false, time, rivalTime, reward: 0, reason: `${this.rival.name} llegó primero` };
        return;
      }
      this.endMission('failed', `${this.rival.name} llegó primero`);
      return;
    }
    const margin = Math.max(0, rivalTime - time);
    const reward = this.practice ? 0 : Math.round(100 * (this.stageIdx + 1) + margin * 4 + (this.player.hull / this.player.stats.hullMax) * 30);
    this.earned += this.carried + reward;
    if (!this.practice) this.meta.data += this.carried + reward;
    this.carried = 0;
    this.clearedTime += time;
    this.stagesCleared++;
    if (!this.practice) {
      this.meta.cleared = Math.max(this.meta.cleared, this.stageIdx + 1);
      const best = this.meta.best[this.stageIdx];
      if (best === null || time < best) this.meta.best[this.stageIdx] = time;
    }
    this.phase = 'cleared';
    this.result = { won: true, time, rivalTime, reward, reason: '' };
    this.note(`Etapa ${this.stageIdx + 1} superada en ${time.toFixed(1)} s`, 'good');
    if (this.stageIdx === STAGES.length - 1) this.endMission('won', '');
  }

  private endMission(kind: 'won' | 'failed', reason: string): void {
    this.over = kind;
    this.phase = kind === 'won' ? 'cleared' : 'failed';
    if (kind === 'failed') this.result = { won: false, time: this.arena.clock, rivalTime: this.rival.finished ? this.rival.finishTime : 0, reward: 0, reason };
    if (this.practice || this.recorded) return;
    this.recorded = true;
    if (kind === 'won') this.meta.won = true;
    addRecord(this.meta, { stages: this.stagesCleared, time: this.clearedTime, data: this.earned, won: kind === 'won', deaths: this.deaths });
  }

  /** Moves on after a cleared stage: refills the ship partly and loads the next stage. */
  nextStage(): boolean {
    if (this.phase !== 'cleared' || this.over || this.stageIdx >= STAGES.length - 1) return false;
    this.loadStage(this.stageIdx + 1);
    this.kits = kitCount(this.meta.upgrades);
    return true;
  }

  /** Practice mode: try the same stage again. */
  retry(): void {
    this.loadStage(this.stageIdx);
  }
}
