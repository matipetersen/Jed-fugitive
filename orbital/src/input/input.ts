import { type Ui } from '../ui/ui';
import { type AutopilotMode } from '../sim/autopilot';

type Zone = 'throttle' | 'rotate' | 'camera' | 'ui';

interface Pointer {
  zone: Zone;
  x: number;
  y: number;
  startX: number;
  startY: number;
  startTime: number;
  moved: number;
}

export const ZOOM_MIN = 1e-9;
export const ZOOM_MAX = 8;
export const ROTATE_REACH = 64;

export interface InputLayout {
  width: number;
  height: number;
  throttleW: number;
  throttleTop: number;
  throttleBottom: number;
  rotateX: number;
  rotateY: number;
  rotateHomeX: number;
  rotateHomeY: number;
}

export function computeInputLayout(width: number, height: number): InputLayout {
  const tw = Math.min(100, width * 0.18);
  const rw = Math.min(190, width * 0.3);
  return {
    width,
    height,
    throttleW: tw,
    throttleTop: height * 0.16,
    throttleBottom: height * 0.86,
    rotateX: width - rw,
    rotateY: height * 0.5,
    rotateHomeX: width - rw * 0.5,
    rotateHomeY: height - Math.min(80, height * 0.22),
  };
}

/** Touch, mouse and keyboard input. Owns throttle, turn, zoom and the autopilot mode. */
export class Input {
  throttle = 0;
  /** Manual turn command, -1..1, positive is counter-clockwise. */
  turn = 0;
  autopilot: AutopilotMode = 'off';
  /** Pixels per world unit. */
  zoom = 0.8;
  /** True once the player zoomed by hand; the flight then stops auto-zooming. */
  zoomManual = false;
  layout: InputLayout = computeInputLayout(800, 400);
  stick: { ox: number; oy: number; x: number; y: number } | null = null;
  /** Short taps on the map area, consumed by the game. */
  taps: { x: number; y: number }[] = [];
  /** Keyboard commands consumed by the game (single presses). */
  keyCommands: string[] = [];
  enabled = true;

  private pointers = new Map<number, Pointer>();
  private keys = new Set<string>();

  constructor(
    private target: HTMLElement,
    private ui: Ui,
  ) {
    target.style.touchAction = 'none';
    target.addEventListener('pointerdown', this.onDown);
    target.addEventListener('pointermove', this.onMove);
    target.addEventListener('pointerup', this.onUp);
    target.addEventListener('pointercancel', this.onUp);
    target.addEventListener('wheel', this.onWheel, { passive: false });
    target.addEventListener('contextmenu', (e) => e.preventDefault());
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', (e) => this.keys.delete(e.key.toLowerCase()));
  }

  resize(width: number, height: number): void {
    this.layout = computeInputLayout(width, height);
  }

  reset(): void {
    this.throttle = 0;
    this.turn = 0;
    this.autopilot = 'off';
    this.stick = null;
    this.pointers.clear();
    this.ui.clear();
  }

  zoomBy(f: number): void {
    this.zoomManual = true;
    this.zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, this.zoom * f));
  }

  update(dt: number): void {
    const k = this.keys;
    if (!this.stick) {
      let turn = 0;
      if (k.has('a') || k.has('arrowleft')) turn = 1;
      if (k.has('d') || k.has('arrowright')) turn = -1;
      this.turn = turn;
    }
    if (k.has('w') || k.has('shift')) this.throttle = Math.min(1, this.throttle + 0.8 * dt);
    if (k.has('s') || k.has('control')) this.throttle = Math.max(0, this.throttle - 0.8 * dt);
    if (k.has('=') || k.has('+')) this.zoomBy(1 + 2 * dt);
    if (k.has('-')) this.zoomBy(1 / (1 + 2 * dt));
    this.ui.update(dt);
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    if (!this.enabled) return;
    const key = e.key.toLowerCase();
    if (e.repeat) return;
    this.keys.add(key);
    if (key === 'z') this.throttle = 1;
    else if (key === 'x') this.throttle = 0;
    else if (['p', 'r', 'n', 'f', 't', 'm', 'b', 'u', '.', ',', 'g', 'h', 'enter', 'v', 'o', 'e'].includes(key)) {
      this.keyCommands.push(key);
    }
    if (['arrowleft', 'arrowright', ' ', 'tab'].includes(key)) e.preventDefault();
  };

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault();
    this.zoomBy(Math.exp(-e.deltaY * 0.0015));
  };

  private local(e: PointerEvent): { x: number; y: number } {
    const r = this.target.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  private onDown = (e: PointerEvent): void => {
    if (!this.enabled) return;
    e.preventDefault();
    const { x, y } = this.local(e);
    const L = this.layout;
    const id = this.ui.hit(x, y);
    if (id) {
      this.target.setPointerCapture(e.pointerId);
      this.pointers.set(e.pointerId, { zone: 'ui', x, y, startX: x, startY: y, startTime: performance.now(), moved: 0 });
      this.ui.press(e.pointerId, id);
      return;
    }
    let zone: Zone = 'camera';
    if (x < L.throttleW) zone = 'throttle';
    else if (x > L.rotateX && y > L.rotateY) zone = 'rotate';
    this.target.setPointerCapture(e.pointerId);
    this.pointers.set(e.pointerId, { zone, x, y, startX: x, startY: y, startTime: performance.now(), moved: 0 });
    if (zone === 'throttle') this.setThrottleFromY(y);
    if (zone === 'rotate') {
      this.autopilot = 'off';
      this.stick = { ox: x, oy: y, x, y };
    }
  };

  private onMove = (e: PointerEvent): void => {
    const p = this.pointers.get(e.pointerId);
    if (!p) return;
    const { x, y } = this.local(e);
    p.moved += Math.hypot(x - p.x, y - p.y);
    if (p.zone === 'throttle') this.setThrottleFromY(y);
    else if (p.zone === 'rotate' && this.stick) {
      this.stick.x = x;
      this.stick.y = y;
      // Dragging right turns clockwise on screen, which is negative in world angle.
      this.turn = -Math.max(-1, Math.min(1, (x - this.stick.ox) / ROTATE_REACH));
    } else if (p.zone === 'camera') {
      const other = [...this.pointers.entries()].find(([id, q]) => id !== e.pointerId && q.zone === 'camera')?.[1];
      if (other) {
        const before = Math.hypot(p.x - other.x, p.y - other.y);
        const after = Math.hypot(x - other.x, y - other.y);
        if (before > 8) this.zoomBy(after / before);
      }
    }
    p.x = x;
    p.y = y;
  };

  private onUp = (e: PointerEvent): void => {
    const p = this.pointers.get(e.pointerId);
    if (!p) return;
    this.pointers.delete(e.pointerId);
    this.ui.release(e.pointerId);
    if (p.zone === 'rotate') {
      this.stick = null;
      this.turn = 0;
    }
    if (p.zone === 'camera' && p.moved < 10 && performance.now() - p.startTime < 400 && this.pointers.size === 0) {
      this.taps.push({ x: p.x, y: p.y });
    }
  };

  private setThrottleFromY(y: number): void {
    const L = this.layout;
    const t = Math.max(0, Math.min(1, (L.throttleBottom - y) / (L.throttleBottom - L.throttleTop)));
    this.throttle = t < 0.04 ? 0 : t > 0.96 ? 1 : t;
  }
}
