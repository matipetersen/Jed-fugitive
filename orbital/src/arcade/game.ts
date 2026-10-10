import { type Input } from '../input/input';
import { type View } from '../render/view';
import { type Audio } from '../game/audio';
import { type Ui } from '../ui/ui';
import { Mission } from './mission';
import { type Meta, predictorSeconds } from './meta';
import { type Controls } from './types';

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  max: number;
  color: string;
  size: number;
}

export interface Toast {
  text: string;
  kind: 'info' | 'good' | 'bad';
  until: number;
}

const TAU = Math.PI * 2;

/** Frame-by-frame play of a mission: input to controls, camera, effects and sound. */
export class ArcadeGame {
  mission: Mission;
  view: View = { cx: 0, cy: 0, zoom: 0.8, up: Math.PI / 2, w: 800, h: 400 };
  particles: Particle[] = [];
  toasts: Toast[] = [];
  autoAim = false;
  clock = 0;
  /** While false the mission is frozen (intro cards and menus are up). */
  playing = false;
  shake = 0;
  pauseRequested = false;
  private logSeen = 0;
  private flameAcc = 0;

  constructor(
    readonly meta: Meta,
    readonly input: Input,
    readonly ui: Ui,
    readonly audio: Audio,
    mission: Mission,
  ) {
    this.mission = mission;
    this.attach();
    this.snapCamera();
  }

  setMission(m: Mission): void {
    this.mission = m;
    this.logSeen = 0;
    this.particles.length = 0;
    this.attach();
    this.snapCamera();
  }

  private attach(): void {
    this.mission.onEvent = (e) => {
      const p = this.mission.player;
      if (e.type === 'die') {
        const s = this.mission.arena.ships[e.ship];
        this.burst(e.x, e.y, s.color, 46, 150);
        if (e.ship === p.id) {
          this.shake = 0.7;
          this.audio.alarm();
        }
      } else if (e.type === 'gate' && e.ship === p.id) {
        this.burst(p.x, p.y, e.final ? '#7dff6b' : '#00f0ff', 14, 90);
        this.audio.chime();
      } else if (e.type === 'hit' && e.ship === p.id) {
        this.shake = Math.max(this.shake, Math.min(0.5, e.damage / 60));
      } else if (e.type === 'bump') {
        this.burst((this.mission.arena.ships[e.a].x + this.mission.arena.ships[e.b].x) / 2, (this.mission.arena.ships[e.a].y + this.mission.arena.ships[e.b].y) / 2, '#ffffff', 8, 70);
      } else if (e.type === 'land' && e.ship === p.id && e.bonfire) this.burst(p.x, p.y, '#ffb000', 24, 70);
    };
  }

  private snapCamera(): void {
    const p = this.mission.player;
    this.view.cx = p.x;
    this.view.cy = p.y;
  }

  toast(text: string, kind: Toast['kind'] = 'info', seconds = 3.5): void {
    this.toasts.push({ text, kind, until: this.clock + seconds });
    if (this.toasts.length > 4) this.toasts.shift();
  }

  private burst(x: number, y: number, color: string, n: number, speed: number): void {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * TAU;
      const s = speed * (0.3 + Math.random() * 0.9);
      this.particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 0, max: 0.5 + Math.random() * 0.8, color, size: 1 + Math.random() * 1.5 });
    }
    if (this.particles.length > 400) this.particles.splice(0, this.particles.length - 400);
  }

  /** Throttle needed to leave the ground, when landed. */
  liftoffThrottle(): number | null {
    const p = this.mission.player;
    if (p.status !== 'landed') return null;
    return this.mission.arena.bodies[p.landedBody].def.g / p.stats.thrust;
  }

  controls(): Controls {
    const m = this.mission;
    const p = m.player;
    let turn = this.input.turn;
    if (turn === 0 && this.autoAim && p.status === 'flying' && p.nextGate < m.arena.gates.length) {
      const g = { x: 0, y: 0 };
      m.arena.gatePos(p.nextGate, g);
      const want = Math.atan2(g.y - p.y, g.x - p.x);
      let err = want - p.angle;
      err = Math.atan2(Math.sin(err), Math.cos(err));
      turn = Math.max(-1, Math.min(1, err * 4));
    }
    if (this.input.turn !== 0 && this.autoAim) this.autoAim = false;
    return { throttle: this.input.throttle, turn };
  }

  update(dtReal: number, clock: number): void {
    this.clock = clock;
    this.toasts = this.toasts.filter((t) => t.until > clock);
    this.input.update(dtReal);
    const m = this.mission;
    const ui = this.ui;
    if (this.playing) {
      if (ui.pressed('pause')) this.pauseRequested = true;
      if (ui.pressed('kit')) {
        if (!m.useKit()) this.toast('SIN CÁPSULAS O EN ESPERA', 'bad', 1.5);
      }
      if (ui.pressed('aim')) this.autoAim = !this.autoAim;
      if (ui.pressed('zoom')) this.input.zoomManual = !this.input.zoomManual;
      m.update(dtReal, this.controls());
      m.checkBeacon();
      if (m.player.status === 'dead') this.input.throttle = 0;
      this.pullLog();
      this.effects(dtReal);
    }
    this.camera(dtReal);
    this.shake = Math.max(0, this.shake - dtReal * 1.6);
    this.audio.engineLevel(this.playing && m.player.status !== 'dead' ? m.player.throttle : 0, 0);
    ui.flush();
  }

  private pullLog(): void {
    const log = this.mission.log;
    while (this.logSeen < log.length) {
      const e = log[this.logSeen++];
      this.toast(e.text, e.kind);
    }
    if (log.length >= 30) this.logSeen = Math.min(this.logSeen, log.length);
  }

  private effects(dt: number): void {
    const m = this.mission;
    for (const s of m.arena.ships) {
      if (s.status === 'flying' && s.throttle > 0.05) {
        this.flameAcc += dt * 60 * s.throttle;
        while (this.flameAcc >= 1) {
          this.flameAcc -= 1;
          const a = s.angle + Math.PI + (Math.random() - 0.5) * 0.4;
          const sp = 70 + Math.random() * 60;
          this.particles.push({ x: s.x - Math.cos(s.angle) * 7, y: s.y - Math.sin(s.angle) * 7, vx: s.vx + Math.cos(a) * sp, vy: s.vy + Math.sin(a) * sp, life: 0, max: 0.25 + Math.random() * 0.2, color: s.isPlayer ? '#ffb000' : '#ff6ad6', size: 1.2 });
        }
      }
    }
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.life += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.life >= p.max) this.particles.splice(i, 1);
    }
  }

  private camera(dtReal: number): void {
    const m = this.mission;
    const p = m.player;
    const v = this.view;
    const k = 1 - Math.exp(-8 * dtReal);
    v.cx += (p.x - v.cx) * k;
    v.cy += (p.y - v.cy) * k;
    if (!this.input.zoomManual) {
      const g = { x: 0, y: 0 };
      let dist = 0;
      if (p.nextGate < m.arena.gates.length) {
        m.arena.gatePos(p.nextGate, g);
        dist = Math.hypot(g.x - p.x, g.y - p.y);
      }
      const speed = Math.hypot(p.vx, p.vy);
      const half = Math.max(260, Math.min(1500, 240 + speed * 0.9 + dist * 0.12));
      const target = Math.min(v.w, v.h) / 2 / half;
      this.input.zoom = Math.exp(Math.log(this.input.zoom) + (Math.log(target) - Math.log(this.input.zoom)) * (1 - Math.exp(-2.2 * dtReal)));
    }
    v.zoom = this.input.zoom;
    v.up = Math.PI / 2;
  }

  predictorSeconds(): number {
    return predictorSeconds(this.meta.upgrades);
  }
}

export { Mission };
