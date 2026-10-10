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
import { refineNode, suggestTransfer } from '../sim/planner';
import { ENGINES, type EngineId, statsFor } from '../sim/tech';
import { siteAt } from '../sim/terrain';
import { AU, DAY, fmtDate, fmtDuration, fmtNum } from '../sim/units';
import { type Campaign } from './campaign';
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

  get warp(): number {
    return WARP_LEVELS[this.warpIdx];
  }

  controls(): Controls {
    const w = this.world;
    const rs = refState(w);
    let nodeDir: number | null = null;
    const dv = this.node?.dvVec ?? this.pred?.nodeDv ?? null;
    if (dv) nodeDir = Math.atan2(dv.y, dv.x);
    const turn =
      this.input.turn !== 0
        ? this.input.turn
        : autopilotTurn(this.input.autopilot, w.ship, rs.rvx, rs.rvy, nodeDir, Math.atan2(rs.ry, rs.rx));
    return { throttle: this.input.throttle, turn };
  }

  // ---------------------------------------------------------------- update

  update(dtReal: number, clock: number): void {
    this.clock = clock;
    this.toasts = this.toasts.filter((t) => t.until > clock);
    this.input.update(dtReal);
    this.processInput();

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
      n.total = Math.hypot(n.dvVec.x, n.dvVec.y);
    }
    if (n.dvVec && n.v0) {
      const rem = this.nodeRemaining();
      if (rem !== null && rem < Math.max(0.4, n.total * 0.01)) {
        this.toast('NODO COMPLETADO', 'good');
        this.node = null;
        if (this.input.autopilot === 'node') this.input.autopilot = 'off';
        this.predDirty = true;
      }
    }
    if (this.node && w.time > this.node.t + 900 && !this.node.v0) {
      this.node = null;
      this.toast('NODO VENCIDO', 'info');
    }
  }

  /** Delta-v still to be applied for the current node, or null. */
  nodeRemaining(): number | null {
    const n = this.node;
    const s = this.world.ship;
    if (!n || !n.dvVec) return null;
    if (!n.v0) return Math.hypot(n.dvVec.x, n.dvVec.y);
    return Math.hypot(n.dvVec.x - (s.vx - n.v0.x), n.dvVec.y - (s.vy - n.v0.y));
  }

  private updatePrediction(dtReal: number): void {
    this.predTimer -= dtReal;
    if (this.world.ship.status !== 'flying') {
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

  private computeAlerts(): void {
    const a: { text: string; kind: 'info' | 'bad' }[] = [];
    const s = this.world.ship;
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
        this.nodePanel = false;
        if (input.autopilot === 'node') input.autopilot = 'off';
        this.predDirty = true;
      }
      if (ui.pressed('nwarp')) this.autoWarpNode = true;
      if (ui.pressed('nauto')) this.suggest();
      if (ui.pressed('nref')) this.refine();
    }

    // Taps on a body select it as the target.
    for (const tap of input.taps.splice(0)) this.tapSelect(tap.x, tap.y);

    // Landed actions.
    if (hit('flag', 'b')) this.plantFlag();
    if (hit('base', 'u')) this.buildBase();
    if (hit('refuel', 'g')) this.refuel();
    if (ui.pressed('engine')) this.swapEngine();
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
    if (s.status !== 'landed') return out;
    const flagged = c.flags.some((f) => f.body === s.landedBody);
    if (site && !flagged) out.push({ id: 'flag', label: 'BANDERA' });
    const hasBase = c.bases.some((b) => b.body === s.landedBody);
    if (site && !hasBase && s.landedBody !== indexOf('earth') && !BODIES[s.landedBody].gas) out.push({ id: 'base', label: `BASE ${c.sandbox ? '' : BASE_COST}`.trim() });
    const bi = this.baseHere();
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
            aiming: this.input.autopilot === 'node',
          }
        : null,
      closest:
        this.pred?.targetClosest && this.target >= 0
          ? `${BODIES[this.target].name} PE ${fmtNum(this.pred.targetClosest.dist - BODIES[this.target].radius)} EN ${fmtDuration(this.pred.targetClosest.t - w.time)}`
          : null,
      status: s.status,
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
  crashReason: string;
  impactSpeed: number;
  hasFlown: boolean;
  autopilot: AutopilotMode;
  blackout: boolean;
}
