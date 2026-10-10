import { BODIES, BODY_COUNT, bodyPos, indexOf } from '../sim/bodies';
import { type Input } from '../input/input';
import { type View } from '../render/view';
import { type Scene } from '../render/scene';
import { type Ui } from '../ui/ui';
import { type AutopilotMode, autopilotTurn } from '../sim/autopilot';
import { orbitElements } from '../sim/orbit';
import {
  type Controls,
  type World,
  advance,
  deltaVLeft,
  realTimeOnly,
  refState,
} from '../sim/physics';
import { type BurnNode, HORIZON_LEVELS, type Prediction, autoHorizon, predict } from '../sim/predict';
import { planCircularizeOrReason, refineNode, suggestTransfer } from '../sim/planner';
import { ENGINES, type EngineId, statsFor } from '../sim/tech';
import { siteAt } from '../sim/terrain';
import { AU, DAY, fmtDate, fmtDuration, fmtNum } from '../sim/units';
import { type Campaign } from './campaign';
import { type EventResult, stepAsteroids } from './events';
import { atmosphereTop } from '../sim/atmosphere';

export const WARP_LEVELS = [1, 5, 10, 50, 100, 500, 1e3, 5e3, 1e4, 5e4, 1e5, 5e5, 1e6];
export const BASE_COST = 40;
export const BASE_CAPACITY = 1500;
export const REFUEL_RANGE = 420;
const ENGINE_CODE: Record<EngineId, string> = { chem: 'QUÍM', hyper: 'HIPER', nerva: 'NUCL', ion: 'IÓN' };
const T_STEPS = [1, 10, 100, 1e3, 1e4, 1e5];
const DV_STEPS = [0.1, 1, 10];

export interface NodeState extends BurnNode {
  /** Expected transfer time, used to size the prediction horizon. */
  eta: number;
  /** Burn vector frozen once the node time has passed. */
  dvVec: { x: number; y: number } | null;
  /** Velocity at the start of the burn, to measure delta-v spent. */
  v0: { x: number; y: number } | null;
  /** Ship mass when the burn began, to measure delta-v spent by the rocket equation. */
  m0?: number;
  /** 'circ': hold altitude while burning at apoapsis. */
  kind?: 'circ';
  /** For circularisation: periapsis radius that counts as done. */
  goalPe?: number;
  total: number;
}

export interface Toast {
  text: string;
  kind: 'info' | 'good' | 'bad';
  until: number;
}

export interface FlightHooks {
  afterUpdate?(f: Flight, simulated: number): void;
  onMenu?(): void;
  onRestart?(): void;
  onCrash?(f: Flight): void;
  onFlag?(f: Flight, body: number): void;
  onBase?(f: Flight, body: number): void;
  onRecover?(f: Flight): void;
}

export interface ContextAction {
  id: string;
  label: string;
}

export function baseRate(campaign: Campaign, body: number, isru: number): number {
  void campaign;
  return 1.2 * BODIES[body].ice * isru;
}

/** Production of all bases over dt game seconds. */
export function tickBases(campaign: Campaign, isru: number, dt: number): void {
  for (const b of campaign.bases) {
    b.stock = Math.min(BASE_CAPACITY, b.stock + baseRate(campaign, b.body, isru) * dt);
  }
}

export class Flight {
  world: World;
  warpIdx = 0;
  warpEff = 1;
  autoWarpNode = false;
  node: NodeState | null = null;
  nodePanel = false;
  tStepIdx = 2;
  dvStepIdx = 1;
  target = -1;
  /** 0 = automatic (reference body), 1.. = body index + 1. */
  frameIdx = 0;
  horizonIdx = 0;
  focusTarget = false;
  coachOn = true;
  /** Aim, wait for the node time and burn by itself. */
  autoBurn = false;
  pred: Prediction | null = null;
  toasts: Toast[] = [];
  clock = 0;
  hasFlown = false;
  hooks: FlightHooks = {};
  view: View = { cx: 0, cy: 0, zoom: 1.5, up: Math.PI / 2, w: 800, h: 400 };
  ref = 2;
  /** Alerts shown in the HUD this frame. */
  alerts: { text: string; kind: 'info' | 'bad' }[] = [];

  private predTimer = 0;
  private predDirty = true;
  private lastRef = -1;
  private lastStatus: string;
  private noTarget = false;
  private lastAsteroids = 0;

  constructor(
    world: World,
    public campaign: Campaign,
    public input: Input,
    public ui: Ui,
  ) {
    this.world = world;
    this.lastStatus = world.ship.status;
    const s = world.ship;
    this.hasFlown = s.status === 'flying';
    const rs = refState(world);
    this.ref = rs.index;
    this.lastRef = rs.index;
    this.view.cx = s.x;
    this.view.cy = s.y;
    this.view.up = Math.atan2(rs.ry, rs.rx);
  }

  toast(text: string, kind: Toast['kind'] = 'info', seconds = 4): void {
    this.toasts.push({ text, kind, until: this.clock + seconds });
    if (this.toasts.length > 4) this.toasts.shift();
  }

  /** Shows an event to the player and drops time warp if it needs attention. */
  pushEvent(r: EventResult): void {
    this.toast(r.text, r.kind === 'bad' ? 'bad' : r.kind === 'good' ? 'good' : 'info', r.interrupt ? 7 : 5);
    if (r.interrupt) {
      this.warpIdx = 0;
      this.autoWarpNode = false;
    }
  }

  private zoomToAsteroid(): void {
    const a = this.world.asteroids[this.world.asteroids.length - 1];
    const s = this.world.ship;
    if (!a) return;
    const d = Math.hypot(a.x - s.x, a.y - s.y);
    const fit = (0.8 * Math.min(this.view.w, this.view.h)) / (2 * Math.max(d, 200));
    this.input.zoomManual = true;
    this.input.zoom = Math.min(this.input.zoom, Math.max(fit, 1e-4));
    this.focusTarget = false;
  }

  get warp(): number {
    return WARP_LEVELS[this.warpIdx];
  }

  controls(): Controls {
    const w = this.world;
    const rs = refState(w);
    let nodeDir: number | null = null;
    const dv = this.node?.dvVec ?? this.pred?.nodeDv ?? null;
    if (dv) {
      nodeDir = Math.atan2(dv.y, dv.x);
      if (this.node?.kind === 'circ' && w.ship.throttle > 0) {
        // Burning from a low arc: tilt towards the sky while falling, so the burn builds an orbit instead of a dive.
        const vr = (rs.rx * rs.rvx + rs.ry * rs.rvy) / Math.max(rs.r, 1);
        const radial = Math.atan2(rs.ry, rs.rx);
        const diff = Math.atan2(Math.sin(radial - nodeDir), Math.cos(radial - nodeDir));
        nodeDir += Math.sign(diff) * Math.max(-0.4, Math.min(0.9, -vr * 0.05));
      }
    }
    const blackout = w.ship.blackoutUntil > w.time;
    const turn =
      this.input.turn !== 0 || blackout
        ? this.input.turn
        : autopilotTurn(this.input.autopilot, w.ship, rs.rvx, rs.rvy, nodeDir, Math.atan2(rs.ry, rs.rx));
    return { throttle: this.input.throttle, turn };
  }

  /** Drives the throttle for an automatic node burn. */
  private driveAutoBurn(): void {
    const n = this.node;
    const w = this.world;
    const s = w.ship;
    if (!this.autoBurn) return;
    if (!n || s.status !== 'flying' || s.fuel <= 0) {
      this.autoBurn = false;
      return;
    }
    if (this.input.turn !== 0) {
      this.autoBurn = false;
      this.toast('QUEMA AUTOMÁTICA CANCELADA', 'info');
      return;
    }
    this.input.autopilot = 'node';
    const dv = n.dvVec ?? this.pred?.nodeDv ?? null;
    if (!dv) return;
    const mass = w.stats.dryMass + s.fuel;
    const accel = Math.max(0.5, (w.stats.thrust * Math.max(s.thrustMult, 0.05)) / mass);
    const total = n.v0 ? n.total : Math.hypot(dv.x, dv.y);
    const startAt = n.t - total / accel / 2;
    const heading = Math.atan2(dv.y, dv.x);
    const err = Math.abs(Math.atan2(Math.sin(heading - s.angle), Math.cos(heading - s.angle)));
    const rem = this.nodeRemaining();
    if (n.kind === 'circ' && n.v0 && n.goalPe !== undefined) {
      // The goal is a safe orbit, not an exact delta-v: finite burns lose some to gravity.
      const rs = refState(w);
      const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, BODIES[rs.index].gm);
      if (el.bound && el.periapsis >= n.goalPe) {
        this.toast('ÓRBITA LOGRADA', 'good');
        this.node = null;
        this.autoBurn = false;
        this.input.throttle = 0;
        if (this.input.autopilot === 'node') this.input.autopilot = 'off';
        this.predDirty = true;
        return;
      }
      this.input.throttle = 1;
      return;
    }
    if (w.time >= startAt && (err < 0.12 || n.v0) && rem !== null) {
      this.input.throttle = Math.min(1, Math.max(0.06, rem / (accel * 0.7)));
    } else if (this.input.throttle > 0 && !n.v0) this.input.throttle = 0;
  }

  // ---------------------------------------------------------------- update

  update(dtReal: number, clock: number): void {
    this.clock = clock;
    this.toasts = this.toasts.filter((t) => t.until > clock);
    this.input.update(dtReal);
    this.processInput();
    this.driveAutoBurn();

    const w = this.world;
    const c = this.controls();
    let warp = this.warp;
    if (this.autoWarpNode && this.node) {
      const lead = this.burnLead();
      const remain = this.node.t - lead - w.time;
      if (remain <= 0) {
        this.autoWarpNode = false;
        this.warpIdx = 0;
        this.toast('NODO CERCA: prepará el encendido', 'info');
        warp = 1;
      } else warp = Math.max(1, Math.min(WARP_LEVELS[WARP_LEVELS.length - 1], remain / (dtReal * 1.5)));
    }
    if (realTimeOnly(w, c)) warp = 1;
    if (w.asteroids.length > 0) warp = 1;
    if (w.ship.status === 'crashed') warp = Math.min(warp, 1);

    const dt = dtReal * warp;
    const simulated = advance(w, c, dt, warp > 1 ? 1500 : 400);
    if (w.asteroids.length > 0) stepAsteroids(w, this.campaign, simulated, (r) => this.pushEvent(r));
    if (w.asteroids.length > this.lastAsteroids) this.zoomToAsteroid();
    this.lastAsteroids = w.asteroids.length;
    const eff = simulated / Math.max(dtReal, 1e-6);
    this.warpEff += (eff - this.warpEff) * 0.2;

    if (w.ship.status === 'flying') this.hasFlown = true;
    const rs = refState(w);
    this.ref = rs.index;
    if (w.ship.status === 'flying' && rs.index !== this.lastRef && this.lastRef >= 0 && !this.autoWarpNode) {
      if (this.warpIdx > 0) this.warpIdx = 0;
      this.toast(`ENTRASTE EN LA ESFERA DE ${BODIES[rs.index].name.toUpperCase()}`, 'info');
      this.predDirty = true;
    }
    this.lastRef = rs.index;

    if (w.ship.status !== this.lastStatus) {
      if (w.ship.status === 'crashed') this.hooks.onCrash?.(this);
      this.lastStatus = w.ship.status;
      this.predDirty = true;
    }

    this.trackNode();
    this.hooks.afterUpdate?.(this, simulated);
    this.updatePrediction(dtReal);
    this.updateView(dtReal);
    this.computeAlerts();
    this.ui.flush();
  }

  private burnLead(): number {
    const n = this.node;
    if (!n) return 30;
    const w = this.world;
    const mass = w.stats.dryMass + w.ship.fuel;
    const accel = (w.stats.thrust * w.ship.thrustMult) / mass;
    const dv = Math.hypot(n.prograde, n.radial);
    return 25 + dv / Math.max(accel, 0.5) / 2;
  }

  private trackNode(): void {
    const n = this.node;
    const w = this.world;
    if (!n) return;
    if (this.pred?.nodeDv && w.time < n.t) n.dvVec = this.pred.nodeDv;
    if (n.dvVec && !n.v0 && this.input.throttle > 0 && w.time >= n.t - this.burnLead() * 2 && w.ship.status === 'flying') {
      n.v0 = { x: w.ship.vx, y: w.ship.vy };
      n.m0 = w.stats.dryMass + w.ship.fuel;
      n.total = Math.hypot(n.dvVec.x, n.dvVec.y);
    }
    if (n.dvVec && n.v0) {
      const rem = this.nodeRemaining();
      if (n.kind === 'circ') {
        // Circularisation ends when the orbit is safe (see driveAutoBurn); give up after a generous overshoot.
        const spent = n.m0 !== undefined ? w.stats.ve * Math.log(n.m0 / (w.stats.dryMass + w.ship.fuel)) : 0;
        if (spent > Math.max(60, n.total * 2.4)) {
          this.toast('NO SE LOGRÓ LA ÓRBITA: REVISÁ LA ALTURA Y PROBÁ CIRC DE NUEVO', 'bad', 6);
          this.node = null;
          this.autoBurn = false;
          this.input.throttle = 0;
          if (this.input.autopilot === 'node') this.input.autopilot = 'off';
          this.predDirty = true;
        }
      } else if (rem !== null && rem < Math.max(0.4, n.total * 0.01)) {
        this.toast('NODO COMPLETADO', 'good');
        this.node = null;
        if (this.autoBurn) {
          this.autoBurn = false;
          this.input.throttle = 0;
        }
        if (this.input.autopilot === 'node') this.input.autopilot = 'off';
        this.predDirty = true;
      }
    }
    if (this.node && w.time > this.node.t + 900 && !this.node.v0) {
      this.node = null;
      this.toast('NODO VENCIDO', 'info');
    }
  }

  /**
   * Delta-v still to be applied for the current node, or null. Spent delta-v is
   * counted from the fuel burned (rocket equation), because in orbit gravity
   * keeps changing the velocity and the difference of velocities is meaningless.
   */
  nodeRemaining(): number | null {
    const n = this.node;
    const w = this.world;
    if (!n || !n.dvVec) return null;
    if (!n.v0 || n.m0 === undefined) return Math.hypot(n.dvVec.x, n.dvVec.y);
    const spent = w.stats.ve * Math.log(n.m0 / (w.stats.dryMass + w.ship.fuel));
    return Math.max(0, n.total - spent);
  }

  private updatePrediction(dtReal: number): void {
    this.predTimer -= dtReal;
    if (this.world.ship.status !== 'flying' || this.world.ship.blackoutUntil > this.world.time) {
      this.pred = null;
      return;
    }
    const moving = this.input.throttle > 0 || this.input.turn !== 0;
    if (!this.predDirty && !(moving && this.predTimer <= 0) && this.predTimer > -1.5) return;
    if (this.predTimer > 0 && !this.predDirty) return;
    this.predDirty = false;
    this.predTimer = moving ? 0.1 : 0.5;
    this.pred = this.runPrediction();
  }

  private runPrediction(): Prediction {
    const w = this.world;
    const lv = HORIZON_LEVELS[this.horizonIdx];
    let hz = lv.seconds > 0 ? lv.seconds : autoHorizon(w);
    const n = this.node && this.node.t > w.time ? this.node : null;
    if (n && lv.seconds === 0) hz = Math.max(hz, n.t - w.time + (n.eta > 0 ? n.eta * 1.3 : 0));
    return predict(w, { horizon: hz, node: n, target: this.target });
  }

  private updateView(dtReal: number): void {
    const s = this.world.ship;
    const v = this.view;
    if (!this.input.zoomManual) this.autoZoom(dtReal);
    v.zoom = this.input.zoom;
    if (this.focusTarget && this.target >= 0) {
      const p = bodyPos(this.target, this.world.time);
      v.cx = p.x;
      v.cy = p.y;
    } else {
      v.cx = s.x;
      v.cy = s.y;
    }
    const rs = refState(this.world);
    const rpx = BODIES[rs.index].radius * v.zoom;
    const want = rpx > 120 && !(this.focusTarget && this.target >= 0) ? Math.atan2(rs.ry, rs.rx) : Math.PI / 2;
    let d = want - v.up;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    v.up += d * (1 - Math.exp(-6 * dtReal));
  }

  /** Keeps the ship and the nearby ground or orbit in view as altitude changes. */
  private autoZoom(dtReal: number): void {
    const w = this.world;
    const rs = refState(w);
    const b = BODIES[rs.index];
    let half = rs.alt * 1.5 + 260;
    if (w.ship.status === 'flying') {
      const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, b.gm);
      if (el.bound && el.apoapsis !== null && el.apoapsis < b.soi * 0.5) half = Math.max(half, el.apoapsis * 1.25);
      if (rs.index === 0) half = Math.max(half, rs.r * 1.2);
    }
    const target = Math.min(this.view.w, this.view.h) / 2 / half;
    const k = 1 - Math.exp(-2.5 * dtReal);
    this.input.zoom = Math.exp(Math.log(this.input.zoom) + (Math.log(target) - Math.log(this.input.zoom)) * k);
  }

  /** Throttle needed to leave the ground (above 1 means the engine cannot lift the ship). */
  liftoffThrottle(): number | null {
    const w = this.world;
    const s = w.ship;
    if (s.status !== 'landed') return null;
    const b = BODIES[s.landedBody];
    const mass = w.stats.dryMass + s.fuel;
    const full = (w.stats.thrust * Math.max(s.thrustMult, 0.01)) / mass;
    return b.surfaceGravity / full;
  }

  /** One line of contextual advice for the player, or null. */
  coach(): string | null {
    if (!this.coachOn) return null;
    const w = this.world;
    const s = w.ship;
    if (s.status === 'crashed') return null;
    const lt = this.liftoffThrottle();
    if (lt !== null && !this.hasFlown) {
      if (lt > 1) return 'La nave pesa demasiado para despegar: en el centro de control cargá menos combustible.';
      return `Subí el empuje (franja izquierda) por encima de la marca amarilla, ${Math.ceil(lt * 100)}%, para despegar.`;
    }
    if (s.status === 'landed') return this.landedSite() ? 'Aterrizaste en terreno plano: abajo podés plantar la bandera o instalar una base.' : null;
    const rs = refState(w);
    const b = BODIES[rs.index];
    const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, b.gm);
    const vr = (rs.rx * rs.rvx + rs.ry * rs.rvy) / rs.r;
    const thr = this.input.throttle > 0;
    if (this.node) {
      if (this.node.v0) return 'Mantené el encendido hasta que ΔV REST llegue a 0.';
      if (this.autoBurn) return 'Quema automática en curso: la nave acelera el tiempo, apunta y enciende sola.';
      return 'NODO listo: REFINA ajusta el paso y después tocá QUEMA: acelera el tiempo, apunta y enciende sola. (O hacelo a mano: IR NODO, girá y empujá hasta ΔV REST 0.)';
    }
    if (this.target >= 0 && this.pred?.targetClosest && rs.index !== this.target && (!el.bound || (el.apoapsis ?? 0) - b.radius > 8000 || rs.index === 0)) {
      const goal = Math.max(BODIES[this.target].radius * 5, 1500);
      const d = this.pred.targetClosest.dist;
      if (d > goal * 3) return `La trayectoria pasa lejos de ${BODIES[this.target].name} (${fmtNum(d)} u). NODO y REFINA proponen una corrección chica; después QUEMA.`;
      return `Vas a pasar cerca de ${BODIES[this.target].name}. Acelerá el tiempo con W+ hasta entrar en su esfera de influencia.`;
    }
    if (rs.index !== 0 && rs.index !== indexOf('earth') && !b.gas) {
      if (!el.bound) return `Pasás de largo. Apuntá RET y frená cerca del punto más cercano (PE) para que ${b.name} te capture.`;
      if (el.periapsis - b.radius < 0) return 'Vas a bajar a la superficie. Para aterrizar: RET y frená casi hasta parar, y bajá despacio (menos de 12 u/s) con la nave derecha.';
      return `Estás en órbita de ${b.name}. Para aterrizar: bajá el PE con un encendido hacia atrás (RET) y descendé con cuidado.`;
    }
    if (rs.index === indexOf('earth')) {
      const pe = el.periapsis - b.radius;
      const ap = el.apoapsis === null ? Infinity : el.apoapsis - b.radius;
      if (pe < 180) {
        if (thr) {
          if (rs.alt < 100) return 'Subí recto hasta unos 100 de altura. Después inclinate hacia un costado.';
          if (ap < 320) return 'Inclinate hacia un costado (arrastrá en la zona de giro) para ganar velocidad lateral. Seguí con el motor.';
          return 'El apogeo ya es suficiente (AP sobre 320): cortá el motor (empuje a 0) y esperá arriba.';
        }
        if (ap >= 200 && vr > 6) return 'Subiendo sin motor. Cuando RAD llegue cerca de 0 (el punto más alto), apuntá al costado y encendé.';
        if (ap >= 200) return 'Estás arriba: apuntá al costado (girá o usá PRO) y encendé hasta que PE supere 180. Eso es una órbita.';
        return 'Todavía no alcanza: necesitás más altura y más velocidad lateral para no caer.';
      }
      if (!el.bound) return 'Vas demasiado rápido y salís de la órbita. Girá hacia atrás (RET) y frená un poco hasta que aparezca AP.';
      if (el.e > 0.08 && this.target < 0) return 'Tu órbita es elíptica. Si querés una circular: NODO y tocá CIRC, que propone el encendido en el apogeo.';
      if (this.target < 0) return 'En órbita. Siguiente: tocá OBJ y elegí la Luna (o tocá la Luna en el mapa), después NODO.';
      return 'Abrí NODO y tocá AUTO: propone cuándo y cuánto encender para llegar al objetivo.';
    }
    if (this.target < 0) return 'Elegí un destino con OBJ y abrí NODO para planificar la salida.';
    return null;
  }

  private computeAlerts(): void {
    const a: { text: string; kind: 'info' | 'bad' }[] = [];
    const s = this.world.ship;
    if (s.blackoutUntil > this.world.time) a.push({ text: 'SIN SEÑAL: AUTOPILOTO Y PREDICCIÓN CAÍDOS', kind: 'bad' });
    if (s.leak > 0) a.push({ text: 'FUGA DE COMBUSTIBLE', kind: 'bad' });
    if (s.thrustMult < 1) a.push({ text: 'MOTOR DAÑADO', kind: 'bad' });
    for (const ast of this.world.asteroids) {
      const rx = ast.x - s.x;
      const ry = ast.y - s.y;
      const rvx = ast.vx - s.vx;
      const rvy = ast.vy - s.vy;
      const v2 = rvx * rvx + rvy * rvy || 1;
      const ttc = -(rx * rvx + ry * rvy) / v2;
      const miss = Math.hypot(rx + rvx * ttc, ry + rvy * ttc);
      if (ttc > 0) a.push({ text: `ASTEROIDE ${ttc.toFixed(0)}s · ${miss < ast.r + 6 ? 'IMPACTO' : 'PASA A ' + miss.toFixed(0)}`, kind: miss < ast.r + 6 ? 'bad' : 'info' });
    }
    if (s.heat > this.world.stats.heatLimit * 0.6) a.push({ text: `CALOR ${Math.round((s.heat / this.world.stats.heatLimit) * 100)}%`, kind: 'bad' });
    if (s.fuel <= 0 && s.status === 'flying') a.push({ text: 'SIN COMBUSTIBLE', kind: 'bad' });
    if (s.hull < 40 && s.status === 'flying') a.push({ text: `CASCO ${Math.round(s.hull)}%`, kind: 'bad' });
    if (this.pred && (this.pred.end === 'impact' || this.pred.end === 'atmosphere') && s.status === 'flying') {
      const e = this.pred.endBody >= 0 ? BODIES[this.pred.endBody].name : '';
      const t = this.pred.t[this.pred.count - 1] - this.world.time;
      if (t < 3600 * 6) a.push({ text: `${this.pred.end === 'impact' ? 'IMPACTO' : 'REENTRADA'} ${e.toUpperCase()} EN ${fmtDuration(t)}`, kind: 'bad' });
    }
    this.alerts = a;
  }

  // ----------------------------------------------------------------- input

  private cycleFrame(): void {
    this.frameIdx = (this.frameIdx + 1) % (BODY_COUNT + 1);
  }

  private cycleTarget(): void {
    this.target = this.target + 1 >= BODY_COUNT ? -1 : this.target + 1;
    if (this.target === 0) this.target = 1;
    this.noTarget = this.target < 0;
    this.predDirty = true;
  }

  private ensureNode(): void {
    if (this.node) return;
    const w = this.world;
    const rs = refState(w);
    const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, BODIES[rs.index].gm);
    const lead = el.bound && el.period ? Math.min(el.period / 4, DAY) : DAY * 0.5;
    this.node = { t: w.time + Math.max(60, lead), prograde: 0, radial: 0, eta: 0, dvVec: null, v0: null, total: 0 };
    this.predDirty = true;
  }

  private processInput(): void {
    const ui = this.ui;
    const input = this.input;
    const key = new Set(input.keyCommands.splice(0));
    const hit = (id: string, k?: string): boolean => ui.pressed(id) || (k !== undefined && key.has(k));
    const w = this.world;

    if (hit('pro', 'p')) input.autopilot = input.autopilot === 'prograde' ? 'off' : 'prograde';
    if (hit('ret', 'r')) input.autopilot = input.autopilot === 'retrograde' ? 'off' : 'retrograde';
    if (hit('node', 'n')) {
      if (!this.nodePanel) {
        this.nodePanel = true;
        this.ensureNode();
      } else this.nodePanel = false;
    }
    if (hit('menu', 'm')) this.hooks.onMenu?.();
    if (hit('wdn', ',')) {
      this.warpIdx = Math.max(0, this.warpIdx - 1);
      this.autoWarpNode = false;
    }
    if (hit('wup', '.')) {
      this.warpIdx = Math.min(WARP_LEVELS.length - 1, this.warpIdx + 1);
      this.autoWarpNode = false;
    }
    if (hit('frame', 'f')) {
      this.cycleFrame();
      this.predDirty = true;
    }
    if (hit('tgt', 't')) this.cycleTarget();
    if (hit('zauto', 'o')) input.zoomManual = !input.zoomManual;
    if (hit('zout')) input.zoomBy(1 / 1.18);
    if (hit('zin')) input.zoomBy(1.18);
    if (hit('hor', 'h')) {
      this.horizonIdx = (this.horizonIdx + 1) % HORIZON_LEVELS.length;
      this.predDirty = true;
    }
    if (hit('foc', 'v')) this.focusTarget = !this.focusTarget;

    // Node panel.
    if (this.node) {
      const n = this.node;
      const ts = T_STEPS[this.tStepIdx];
      const ds = DV_STEPS[this.dvStepIdx];
      if (ui.pressed('nt-')) { n.t = Math.max(w.time + 1, n.t - ts); this.predDirty = true; }
      if (ui.pressed('nt+')) { n.t += ts; this.predDirty = true; }
      if (ui.pressed('np-')) { n.prograde -= ds; this.predDirty = true; }
      if (ui.pressed('np+')) { n.prograde += ds; this.predDirty = true; }
      if (ui.pressed('nr-')) { n.radial -= ds; this.predDirty = true; }
      if (ui.pressed('nr+')) { n.radial += ds; this.predDirty = true; }
      if (ui.pressed('nts')) this.tStepIdx = (this.tStepIdx + 1) % T_STEPS.length;
      if (ui.pressed('nds')) this.dvStepIdx = (this.dvStepIdx + 1) % DV_STEPS.length;
      if (ui.pressed('naim')) input.autopilot = input.autopilot === 'node' ? 'off' : 'node';
      if (ui.pressed('ndel')) {
        this.node = null;
        this.autoBurn = false;
        this.nodePanel = false;
        if (input.autopilot === 'node') input.autopilot = 'off';
        this.predDirty = true;
      }
      if (ui.pressed('nwarp')) this.autoWarpNode = true;
      if (ui.pressed('nburn')) {
        this.autoBurn = !this.autoBurn;
        if (this.autoBurn) {
          this.autoWarpNode = true;
          input.autopilot = 'node';
          this.toast('QUEMA AUTOMÁTICA: VA AL NODO, APUNTA Y ENCIENDE SOLA', 'good', 5);
        } else {
          input.throttle = 0;
          this.autoWarpNode = false;
        }
      }
      if (ui.pressed('nauto')) this.suggest();
      if (ui.pressed('ncirc')) this.circularize();
      if (ui.pressed('nref')) this.refine();
    }

    // Taps on a body select it as the target.
    for (const tap of input.taps.splice(0)) this.tapSelect(tap.x, tap.y);

    // Landed actions.
    if (hit('flag', 'b')) this.plantFlag();
    if (hit('base', 'u')) this.buildBase();
    if (hit('refuel', 'g')) this.refuel();
    if (ui.pressed('engine')) this.swapEngine();
    if (hit('seal', 'e') && w.ship.leak > 0) {
      w.ship.leak = 0;
      this.campaign.eventsHandled++;
      this.toast('VÁLVULA SELLADA (+10)', 'good');
    }
    if (ui.pressed('recover')) this.hooks.onRecover?.(this);
    void this.noTarget;
  }

  private tapSelect(x: number, y: number): void {
    if (this.world.ship.status === 'crashed') {
      this.hooks.onRestart?.();
      return;
    }
    const v = this.view;
    const theta = Math.PI / 2 - v.up;
    const c = Math.cos(theta);
    const s = Math.sin(theta);
    let best = -1;
    let bd = 34;
    for (let i = 1; i < BODY_COUNT; i++) {
      const p = bodyPos(i, this.world.time);
      const dx = p.x - v.cx;
      const dy = p.y - v.cy;
      const sx = v.w / 2 + v.zoom * (c * dx - s * dy);
      const sy = v.h / 2 - v.zoom * (s * dx + c * dy);
      const d = Math.hypot(sx - x, sy - y) - BODIES[i].radius * v.zoom;
      if (d < bd) {
        bd = d;
        best = i;
      }
    }
    if (best >= 0) {
      this.target = this.target === best ? -1 : best;
      this.predDirty = true;
      this.toast(this.target >= 0 ? `OBJETIVO: ${BODIES[best].name.toUpperCase()}` : 'OBJETIVO LIBRE', 'info', 2);
    }
  }

  private suggest(): void {
    if (this.target < 0) {
      this.toast('ELEGÍ UN OBJETIVO (OBJ O TOCÁ UN CUERPO)', 'bad');
      return;
    }
    const sug = suggestTransfer(this.world, this.target);
    if (!sug) {
      this.toast('SIN PLAN: ORBITÁ UN CUERPO DE FORMA ESTABLE', 'bad');
      return;
    }
    this.node = { ...sug.node, eta: sug.eta, dvVec: null, v0: null, total: 0 };
    this.nodePanel = true;
    this.predDirty = true;
    this.toast(`VENTANA EN ${fmtDuration(sug.tWindow - this.world.time)} · ΔV ${sug.dv.toFixed(0)} · VUELO ${fmtDuration(sug.eta)}`, 'good', 6);
  }

  private circularize(): void {
    const plan = planCircularizeOrReason(this.world);
    if (!('node' in plan)) {
      this.toast(plan.reason.toUpperCase(), 'bad', 5);
      return;
    }
    const body = BODIES[this.ref];
    const goalPe = Math.max(plan.radius * 0.93, body.radius + (body.atmosphere ? atmosphereTop(body) : 0) + 25);
    this.node = { ...plan.node, eta: 0, dvVec: null, v0: null, total: 0, kind: 'circ', goalPe };
    this.nodePanel = true;
    this.predDirty = true;
    this.toast(`CIRCULARIZAR: ΔV ${Math.hypot(plan.node.prograde, plan.node.radial).toFixed(1)} · ${fmtDuration(plan.node.t - this.world.time)}`, 'good', 6);
  }

  private refine(): void {
    const n = this.node;
    if (!n || this.target < 0) {
      this.toast('NECESITO UN NODO Y UN OBJETIVO', 'bad');
      return;
    }
    const horizon = n.t - this.world.time + (n.eta > 0 ? n.eta * 1.3 : DAY * 20);
    const r = refineNode(this.world, this.target, n, horizon, 450);
    this.node = { ...n, ...r.node };
    this.predDirty = true;
    this.toast(`REFINADO: APROXIMACIÓN ${fmtNum(r.closest)} u`, 'good', 5);
  }

  // --------------------------------------------------------- landed actions

  /** Site the ship is resting on, if landed on a flat site. */
  landedSite(): { body: number; theta: number; name: string } | null {
    const s = this.world.ship;
    if (s.status !== 'landed') return null;
    const site = siteAt(BODIES[s.landedBody], s.landedTheta);
    return site ? { body: s.landedBody, theta: s.landedTheta, name: site.name } : null;
  }

  baseHere(): number {
    const s = this.world.ship;
    if (s.status !== 'landed') return -1;
    const b = BODIES[s.landedBody];
    return this.campaign.bases.findIndex(
      (m) => m.body === s.landedBody && Math.abs(Math.atan2(Math.sin(m.theta - s.landedTheta), Math.cos(m.theta - s.landedTheta))) * b.radius < REFUEL_RANGE,
    );
  }

  contextActions(): ContextAction[] {
    const out: ContextAction[] = [];
    const site = this.landedSite();
    const c = this.campaign;
    const s = this.world.ship;
    if (s.leak > 0 && s.status !== 'crashed') out.push({ id: 'seal', label: 'SELLAR' });
    if (s.status !== 'landed') return out;
    const flagged = c.flags.some((f) => f.body === s.landedBody);
    if (site && !flagged) out.push({ id: 'flag', label: 'BANDERA' });
    const hasBase = c.bases.some((b) => b.body === s.landedBody);
    if (site && !hasBase && s.landedBody !== indexOf('earth') && !BODIES[s.landedBody].gas) out.push({ id: 'base', label: `BASE ${c.sandbox ? '' : BASE_COST}`.trim() });
    const bi = this.baseHere();
    if (s.landedBody === indexOf('earth') && !c.sandbox) out.push({ id: 'recover', label: 'RECUPERAR' });
    if (bi >= 0 || s.landedBody === indexOf('earth')) {
      if (bi >= 0) out.push({ id: 'refuel', label: `RECARGA ${Math.round(c.bases[bi].stock)}` });
      out.push({ id: 'engine', label: `MOT ${ENGINE_CODE[c.engine]}` });
    }
    return out;
  }

  plantFlag(): void {
    const site = this.landedSite();
    const c = this.campaign;
    if (!site) return;
    if (c.flags.some((f) => f.body === site.body)) return;
    c.flags.push({ body: site.body, theta: site.theta, time: this.world.time });
    this.toast(`BANDERA PLANTADA EN ${BODIES[site.body].name.toUpperCase()} · ${site.name.toUpperCase()}`, 'good', 6);
    this.hooks.onFlag?.(this, site.body);
  }

  buildBase(): void {
    const site = this.landedSite();
    const c = this.campaign;
    if (!site || c.bases.some((b) => b.body === site.body)) return;
    if (!c.sandbox && c.funds < BASE_COST) {
      this.toast(`FONDOS INSUFICIENTES (${BASE_COST})`, 'bad');
      return;
    }
    if (!c.sandbox) c.funds -= BASE_COST;
    c.bases.push({ body: site.body, theta: site.theta, name: `Base ${BODIES[site.body].name}`, stock: 0, built: this.world.time });
    this.toast(`BASE INSTALADA EN ${BODIES[site.body].name.toUpperCase()}`, 'good', 6);
    this.hooks.onBase?.(this, site.body);
  }

  refuel(): void {
    const bi = this.baseHere();
    if (bi < 0) return;
    const base = this.campaign.bases[bi];
    const s = this.world.ship;
    const room = this.world.stats.fuelCap - s.fuel;
    const moved = Math.min(room, base.stock);
    if (moved <= 0.5) {
      this.toast(base.stock <= 0.5 ? 'DEPÓSITO VACÍO: ESPERÁ LA PRODUCCIÓN' : 'TANQUES LLENOS', 'info');
      return;
    }
    s.fuel += moved;
    base.stock -= moved;
    s.hull = Math.min(100, s.hull + 30);
    this.toast(`+${moved.toFixed(0)} DE COMBUSTIBLE`, 'good');
  }

  swapEngine(): void {
    const c = this.campaign;
    const avail = ENGINES.filter((e) => e.tech === null || c.techs.includes(e.tech));
    const idx = avail.findIndex((e) => e.id === c.engine);
    const next: EngineId = avail[(idx + 1) % avail.length].id;
    c.engine = next;
    const fuel = this.world.ship.fuel;
    this.world.stats = statsFor(c.techs, next);
    this.world.ship.fuel = Math.min(fuel, this.world.stats.fuelCap);
    this.toast(`MOTOR: ${ENGINES.find((e) => e.id === next)!.name.toUpperCase()}`, 'info');
  }

  // ------------------------------------------------------------------ scene

  frameBody(): number {
    return this.frameIdx === 0 ? this.ref : this.frameIdx - 1;
  }

  scene(): Scene {
    const s = this.world.ship;
    let glow = 0;
    const rs = refState(this.world);
    const b = BODIES[rs.index];
    if (b.atmosphere && rs.alt < atmosphereTop(b)) glow = Math.min(1, (s.heat / this.world.stats.heatLimit) * 1.6);
    return {
      world: this.world,
      prediction: this.pred,
      frameBody: this.frameBody(),
      node: this.node,
      target: this.target,
      refIndex: this.ref,
      bases: this.campaign.bases.map((m) => ({ body: m.body, theta: m.theta })),
      flags: this.campaign.flags.map((m) => ({ body: m.body, theta: m.theta })),
      clock: this.clock,
      atmoGlow: glow,
    };
  }

  // -------------------------------------------------------------------- HUD

  hud(): HudData {
    const w = this.world;
    const s = w.ship;
    const rs = refState(w);
    const b = BODIES[rs.index];
    const el = orbitElements(rs.rx, rs.ry, rs.rvx, rs.rvy, b.gm);
    const speed = Math.hypot(rs.rvx, rs.rvy);
    const radial = (rs.rx * rs.rvx + rs.ry * rs.rvy) / rs.r;
    const tangential = Math.sqrt(Math.max(0, speed * speed - radial * radial));
    const sun = rs.index === 0;
    const dist = sun ? `${(rs.r / AU).toFixed(2)} UA` : fmtNum(rs.alt);
    const fmtAlt = (r: number | null): string => (r === null ? '--' : sun ? `${(r / AU).toFixed(2)} UA` : r - b.radius < 0 ? 'SUELO' : fmtNum(r - b.radius));
    const frame = this.frameIdx === 0 ? `AUTO (${BODIES[this.frameBody()].name})` : BODIES[this.frameIdx - 1].name;
    const n = this.node;
    const lv = HORIZON_LEVELS[this.horizonIdx].label;
    const dvRem = this.nodeRemaining();
    return {
      ref: b.name,
      altLabel: sun ? 'DIST' : 'ALT',
      alt: dist,
      speed: speed.toFixed(speed >= 100 ? 0 : 1),
      radial: radial.toFixed(1),
      tangential: tangential.toFixed(1),
      ap: fmtAlt(el.apoapsis),
      pe: fmtAlt(el.periapsis),
      peDanger: !sun && el.periapsis - b.radius < 0 && s.status === 'flying',
      fuelPct: Math.round((s.fuel / w.stats.fuelCap) * 100),
      dv: deltaVLeft(w).toFixed(0),
      heat: Math.min(1.2, s.heat / w.stats.heatLimit),
      hull: s.hull,
      date: fmtDate(w.time),
      warp: this.warp,
      warpEff: this.warpEff,
      frame,
      target: this.target >= 0 ? BODIES[this.target].name : '--',
      horizon: lv,
      node: n
        ? {
            tMinus: fmtDuration(n.t - w.time),
            tPast: n.t < w.time,
            pro: n.prograde.toFixed(1),
            rad: n.radial.toFixed(1),
            remaining: dvRem === null ? null : dvRem.toFixed(1),
            tStep: fmtDuration(T_STEPS[this.tStepIdx]),
            dvStep: String(DV_STEPS[this.dvStepIdx]),
            aiming: this.autoBurn,
          }
        : null,
      closest:
        this.pred?.targetClosest && this.target >= 0
          ? `${BODIES[this.target].name} PE ${fmtNum(this.pred.targetClosest.dist - BODIES[this.target].radius)} EN ${fmtDuration(this.pred.targetClosest.t - w.time)}`
          : null,
      status: s.status,
      liftoff: this.liftoffThrottle(),
      coach: this.coach(),
      crashReason: s.crashReason,
      impactSpeed: s.impactSpeed,
      hasFlown: this.hasFlown,
      autopilot: this.input.autopilot,
      blackout: s.blackoutUntil > w.time,
    };
  }
}

export interface HudData {
  ref: string;
  altLabel: string;
  alt: string;
  speed: string;
  radial: string;
  tangential: string;
  ap: string;
  pe: string;
  peDanger: boolean;
  fuelPct: number;
  dv: string;
  heat: number;
  hull: number;
  date: string;
  warp: number;
  warpEff: number;
  frame: string;
  target: string;
  horizon: string;
  node: {
    tMinus: string;
    tPast: boolean;
    pro: string;
    rad: string;
    remaining: string | null;
    tStep: string;
    dvStep: string;
    aiming: boolean;
  } | null;
  closest: string | null;
  status: string;
  liftoff: number | null;
  coach: string | null;
  crashReason: string;
  impactSpeed: number;
  hasFlown: boolean;
  autopilot: AutopilotMode;
  blackout: boolean;
}
