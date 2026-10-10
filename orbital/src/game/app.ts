import { BODIES, indexOf } from '../sim/bodies';
import { type Controls, type World, advance, createWorld } from '../sim/physics';
import { statsFor, techById } from '../sim/tech';
import { DAY, YEAR, fmtDate } from '../sim/units';
import { type Input } from '../input/input';
import { type Ui } from '../ui/ui';
import { Overlay } from '../ui/dom';
import { drawHud } from '../render/hud';
import { drawAsteroids, drawShip, drawStars, drawWorld } from '../render/world';
import { quality } from '../render/neon';
import { screens } from '../ui/screens';
import { type Audio } from './audio';
import { type Bloc, type Campaign, clearSave, loadGame, newCampaign, saveGame } from './campaign';
import { armFailure, checkEngine, processEvents } from './events';
import { Flight, tickBases } from './flight';
import { type RecordEntry, addRecord, recordFor } from './records';
import {
  LAUNCH_COST,
  MILESTONES,
  addNews,
  checkMilestones,
  makeRivalYears,
  registerVictory,
  tickCalendar,
} from './rules';

export type Mode = 'title' | 'hq' | 'flight' | 'end';

export interface LaunchPlan {
  /** -1 = the bloc's pad on Earth, otherwise an index into campaign.bases. */
  site: number;
  engine: Campaign['engine'];
  fuelLoad: number;
}

const NONE: Controls = { throttle: 0, turn: 0 };

/** Owns the campaign, the active flight and the screens, and moves between them. */
export class App {
  mode: Mode = 'title';
  campaign: Campaign | null = null;
  world: World | null = null;
  flight: Flight | null = null;
  hqTab = 'mision';
  plan: LaunchPlan = { site: -1, engine: 'chem', fuelLoad: 1 };
  lastRecord: RecordEntry | null = null;
  confirming = false;
  /** Called once if the device is too slow, so the host can lower the canvas resolution. */
  onLowQuality: (() => void) | null = null;
  private frameEma = 16;
  private frameCount = 0;
  private saveClock = 0;
  private endShown = false;
  private width = 800;
  private height = 400;
  private dpr = 1;

  constructor(
    readonly canvas: HTMLCanvasElement,
    readonly ctx: CanvasRenderingContext2D,
    readonly ui: Ui,
    readonly input: Input,
    readonly overlay: Overlay,
    readonly audio: Audio,
  ) {}

  resize(w: number, h: number, dpr: number): void {
    this.width = w;
    this.height = h;
    this.dpr = dpr;
  }

  // ------------------------------------------------------------ navigation

  showTitle(): void {
    this.mode = 'title';
    this.input.enabled = false;
    this.overlay.show(screens.title(this));
  }

  hasSave(): boolean {
    return loadGame() !== null;
  }

  newCampaign(bloc: Bloc, difficulty: 0 | 1 | 2): void {
    const c = newCampaign({ bloc, difficulty });
    c.rivalYears = makeRivalYears(c.seed, difficulty);
    addNews(c, 0, `1957: comienza la carrera. ${bloc === 'usa' ? 'EE.UU.' : 'La URSS'} apuesta por Plutón.`, 'info');
    this.campaign = c;
    this.world = null;
    this.flight = null;
    this.endShown = false;
    this.plan = { site: -1, engine: 'chem', fuelLoad: 1 };
    this.save();
    this.enterHQ();
  }

  startSandbox(): void {
    const c = newCampaign({ sandbox: true });
    c.rivalYears = makeRivalYears(c.seed, 1);
    this.campaign = c;
    this.endShown = true;
    this.world = this.padWorld(c, 1);
    this.startFlight();
  }

  continueGame(): void {
    const blob = loadGame();
    if (!blob) return this.showTitle();
    this.campaign = blob.campaign;
    this.world = blob.world;
    this.endShown = this.campaign.status !== 'playing';
    if (this.world) {
      this.startFlight();
      this.openPause();
    } else this.enterHQ();
  }

  enterHQ(): void {
    if (!this.campaign) return this.showTitle();
    if (this.mode === 'flight') this.hqTab = 'mision';
    this.mode = 'hq';
    this.input.enabled = false;
    this.ui.clear();
    this.save();
    this.overlay.show(screens.hq(this));
  }

  /** Re-renders the current overlay screen after state changed. */
  refresh(): void {
    const keep = this.overlay.el.scrollTop;
    if (this.mode === 'hq') this.overlay.show(screens.hq(this));
    this.overlay.el.scrollTop = keep;
  }

  openPause(): void {
    this.input.enabled = false;
    this.overlay.show(screens.pause(this));
  }

  closeOverlay(): void {
    this.overlay.hide();
    if (this.flight) {
      this.mode = 'flight';
      this.input.enabled = true;
      this.ui.clear();
    }
  }

  openRecords(): void {
    this.overlay.show(screens.records(this));
  }

  openHelp(back: () => void): void {
    this.overlay.show(screens.help(back));
  }

  // ----------------------------------------------------------------- flight

  private padWorld(c: Campaign, fuelFraction: number): World {
    const earth = indexOf('earth');
    const idx = c.bloc === 'usa' ? 0 : 1;
    const site = BODIES[earth].sites[idx];
    const stats = statsFor(c.techs, c.engine);
    // A sandbox ship has every upgrade, so a full tank would be too heavy to lift: cap the load.
    const fuel = c.sandbox ? Math.min(stats.fuelCap, 1000) : stats.fuelCap * fuelFraction;
    return createWorld(stats, earth, site.angle, c.time, fuel);
  }

  /** Cost and fuel of a launch plan, or null if it cannot be flown. */
  planInfo(): { stats: ReturnType<typeof statsFor>; fuel: number; body: number; theta: number; cost: number; label: string } | null {
    const c = this.campaign;
    if (!c) return null;
    const stats = statsFor(c.techs, this.plan.engine);
    const want = stats.fuelCap * this.plan.fuelLoad;
    if (this.plan.site < 0) {
      const earth = indexOf('earth');
      const site = BODIES[earth].sites[c.bloc === 'usa' ? 0 : 1];
      return { stats, fuel: want, body: earth, theta: site.angle, cost: c.sandbox ? 0 : LAUNCH_COST, label: site.name };
    }
    const base = c.bases[this.plan.site];
    if (!base) return null;
    return { stats, fuel: Math.min(want, base.stock), body: base.body, theta: base.theta, cost: c.sandbox ? 0 : LAUNCH_COST, label: base.name };
  }

  launch(): boolean {
    const c = this.campaign;
    const info = this.planInfo();
    if (!c || !info) return false;
    if (c.funds < info.cost) return false;
    c.funds -= info.cost;
    c.engine = this.plan.engine;
    c.launches++;
    if (this.plan.site >= 0) c.bases[this.plan.site].stock -= info.fuel;
    const w = createWorld(info.stats, info.body, info.theta, c.time, info.fuel);
    armFailure(c, w, c.launches);
    this.world = w;
    this.confirming = false;
    addNews(c, c.time, `Lanzamiento desde ${info.label}`, 'info');
    this.startFlight();
    return true;
  }

  private startFlight(): void {
    const c = this.campaign!;
    const w = this.world!;
    const f = new Flight(w, c, this.input, this.ui);
    this.flight = f;
    this.input.reset();
    f.hooks = {
      onMenu: () => this.openPause(),
      afterUpdate: (fl, sim) => this.tick(fl, sim),
      onCrash: () => this.onCrash(),
      onRestart: () => this.onRestart(),
      onRecover: () => this.recover(),
    };
    this.mode = 'flight';
    this.input.enabled = true;
    this.overlay.hide();
  }

  private onCrash(): void {
    const c = this.campaign;
    if (!c || c.sandbox) return;
    c.shipsLost++;
    addNews(c, c.time, 'Nave perdida', 'bad');
    this.audio.alarm();
    this.save();
  }

  private onRestart(): void {
    const c = this.campaign;
    if (!c) return;
    if (c.sandbox) {
      this.world = this.padWorld(c, 1);
      this.startFlight();
      return;
    }
    this.world = null;
    this.flight = null;
    this.enterHQ();
  }

  private recover(): void {
    const c = this.campaign;
    if (!c || !this.world) return;
    c.funds += 10;
    addNews(c, c.time, 'Nave recuperada en la plataforma (+10 fondos)', 'good');
    this.world = null;
    this.flight = null;
    this.enterHQ();
  }

  abandonShip(): void {
    const c = this.campaign;
    const w = this.world;
    if (!c || !w) return;
    if (w.ship.status === 'flying') {
      w.ship.status = 'crashed';
      w.ship.crashReason = 'abandoned';
      if (!c.sandbox) {
        c.shipsLost++;
        addNews(c, c.time, 'Nave abandonada en el espacio', 'bad');
      }
    }
    this.world = null;
    this.flight = null;
    this.enterHQ();
  }

  // ------------------------------------------------------------------- tick

  /** Per-frame campaign upkeep tied to simulated time. */
  private tick(f: Flight, simulated: number): void {
    const c = this.campaign;
    const w = this.world;
    if (!c || !w) return;
    c.time = w.time;
    tickBases(c, w.stats.isru, simulated);
    if (c.sandbox) return;
    this.runCalendar(f);
    for (const ev of checkMilestones(c, w)) {
      const def = MILESTONES[ev.id - 1];
      f.toast(`HITO: ${def.name.toUpperCase()} (+${c.milestones[ev.id - 1].points})`, 'good', 7);
      this.audio.chime();
    }
    processEvents(c, w, w.time, (r) => {
      f.pushEvent(r);
      if (r.interrupt) this.audio.alarm();
    });
    checkEngine(c, w, (r) => f.pushEvent(r));
    registerVictory(c);
    this.afterStateChange();
    this.saveClock += simulated > 0 ? 1 : 0;
  }

  private runCalendar(f: Flight): void {
    const c = this.campaign!;
    const w = this.world!;
    const res = tickCalendar(c, w.time);
    for (const n of res.news) f.toast(n.text.toUpperCase(), n.kind === 'rival' ? 'bad' : 'info', 6);
    if (res.news.some((n) => n.kind === 'rival')) this.audio.alarm();
  }

  private afterStateChange(): void {
    const c = this.campaign;
    if (!c || this.endShown || c.status === 'playing') return;
    this.endShown = true;
    this.lastRecord = addRecord(recordFor(c, c.time)).find((r) => r.seed === c.seed) ?? recordFor(c, c.time);
    this.mode = 'end';
    this.input.enabled = false;
    this.save();
    this.overlay.show(screens.end(this));
  }

  /** Lets calendar time pass at the control centre, with the ship parked or absent. */
  waitDays(days: number): void {
    const c = this.campaign;
    if (!c || (this.world && this.world.ship.status === 'flying')) return;
    let left = days * DAY;
    const chunk = 15 * DAY;
    while (left > 0 && c.status === 'playing') {
      const dt = Math.min(chunk, left);
      left -= dt;
      const t = c.time + dt;
      if (this.world) advance(this.world, NONE, dt, 4);
      else c.time = t;
      const time = this.world ? this.world.time : t;
      c.time = time;
      const isru = this.world ? this.world.stats.isru : statsFor(c.techs, c.engine).isru;
      tickBases(c, isru, dt);
      tickCalendar(c, time);
      processEvents(c, this.world, time, () => undefined);
      checkMilestones(c, this.world ?? createWorld());
      registerVictory(c);
    }
    this.afterStateChange();
    this.save();
    if (this.mode === 'hq') this.refresh();
  }

  buyTech(id: string): boolean {
    const c = this.campaign;
    const t = techById(id);
    if (!c || !t || c.techs.includes(id)) return false;
    if (c.funds < t.cost) return false;
    if (t.milestone > 0 && !c.milestones[t.milestone - 1].done) return false;
    if (t.prereq && !c.techs.includes(t.prereq)) return false;
    c.funds -= t.cost;
    c.techs.push(id);
    addNews(c, c.time, `Tecnología: ${t.name}`, 'good');
    this.save();
    return true;
  }

  // ------------------------------------------------------------------- save

  save(): void {
    if (!this.campaign || this.campaign.sandbox) return;
    saveGame(this.campaign, this.world);
  }

  deleteSave(): void {
    clearSave();
  }

  // ------------------------------------------------------------------ frame

  frame(now: number, dt: number): void {
    const { ctx, width, height, dpr } = { ctx: this.ctx, width: this.width, height: this.height, dpr: this.dpr };
    this.frameCount++;
    this.frameEma = this.frameEma * 0.95 + dt * 1000 * 0.05;
    if (!quality.low && this.frameCount > 150 && this.frameEma > 32) {
      quality.low = true;
      this.onLowQuality?.();
    }
    const f = this.flight;
    if (f && this.mode === 'flight') {
      f.update(dt, now / 1000);
      this.saveClock += dt;
      if (this.saveClock > 4) {
        this.saveClock = 0;
        this.save();
      }
      this.audio.update(f);
    } else this.audio.silence();

    ctx.globalCompositeOperation = 'source-over';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#02020a';
    ctx.fillRect(0, 0, width, height);
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    if (!f) {
      // A slow orbiting backdrop behind the menus.
      return;
    }
    const v = f.view;
    v.w = width;
    v.h = height;
    const scene = f.scene();
    drawStars(ctx, v);
    drawWorld(ctx, v, scene);
    drawAsteroids(ctx, v, scene);
    drawShip(ctx, v, scene);
    if (this.mode === 'flight') drawHud(ctx, f, width, height);
  }
}

export { YEAR, fmtDate };
