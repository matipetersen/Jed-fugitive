import { type AutopilotMode } from '../sim/autopilot';
import { type Layout, ROTATE_REACH, computeLayout, inRect } from './layout';

type Zone = 'throttle' | 'rotate' | 'camera';

interface Pointer {
  zone: Zone;
  x: number;
  y: number;
  originX: number;
  originY: number;
}

const ZOOM_MIN = 0.02;
const ZOOM_MAX = 6;

/** Touch, mouse and keyboard input. Owns throttle, turn, autopilot mode and zoom. */
export class Input {
  throttle = 0;
  /** Manual turn command, -1..1, positive is counter-clockwise. */
  turn = 0;
  autopilot: AutopilotMode = 'off';
  zoom = 1.5;
  layout: Layout = computeLayout(800, 400);
  /** Active rotate-stick drag, for drawing. */
  stick: { ox: number; oy: number; x: number; y: number } | null = null;

  private pointers = new Map<number, Pointer>();
  private keys = new Set<string>();
  private restartRequested = false;

  constructor(private target: HTMLElement) {
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
    this.layout = computeLayout(width, height);
  }

  consumeRestart(): boolean {
    const r = this.restartRequested;
    this.restartRequested = false;
    return r;
  }

  reset(): void {
    this.throttle = 0;
    this.turn = 0;
    this.autopilot = 'off';
    this.stick = null;
    this.pointers.clear();
  }

  /** Applies held keys. Call once per frame. */
  update(dt: number): void {
    const k = this.keys;
    let turn = this.stick ? this.turn : 0;
    if (k.has('a') || k.has('arrowleft')) turn = 1;
    if (k.has('d') || k.has('arrowright')) turn = -1;
    if (!this.stick) this.turn = turn;
    if (k.has('w') || k.has('shift')) this.throttle = Math.min(1, this.throttle + 0.8 * dt);
    if (k.has('s') || k.has('control')) this.throttle = Math.max(0, this.throttle - 0.8 * dt);
    if (k.has('=') || k.has('+')) this.zoomBy(1 + 1.5 * dt);
    if (k.has('-')) this.zoomBy(1 / (1 + 1.5 * dt));
  }

  private zoomBy(f: number): void {
    this.zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, this.zoom * f));
  }

  private toggleAutopilot(mode: AutopilotMode): void {
    this.autopilot = this.autopilot === mode ? 'off' : mode;
  }

  private onKeyDown = (e: KeyboardEvent): void => {
    const key = e.key.toLowerCase();
    if (e.repeat) return;
    this.keys.add(key);
    if (key === 'z') this.throttle = 1;
    else if (key === 'x') this.throttle = 0;
    else if (key === 'p') this.toggleAutopilot('prograde');
    else if (key === 'r') this.toggleAutopilot('retrograde');
    else if (key === 'enter') this.restartRequested = true;
    if (['arrowleft', 'arrowright', ' '].includes(key)) e.preventDefault();
  };

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault();
    this.zoomBy(Math.exp(-e.deltaY * 0.0015));
  };

  private localPoint(e: PointerEvent): { x: number; y: number } {
    const rect = this.target.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  private onDown = (e: PointerEvent): void => {
    e.preventDefault();
    const { x, y } = this.localPoint(e);
    const L = this.layout;

    for (const b of L.buttons) {
      if (inRect(b, x, y)) {
        this.toggleAutopilot(b.id);
        return;
      }
    }

    let zone: Zone = 'camera';
    if (inRect(L.throttleZone, x, y)) zone = 'throttle';
    else if (inRect(L.rotateZone, x, y)) zone = 'rotate';
    else this.restartRequested = this.pointers.size === 0;

    this.target.setPointerCapture(e.pointerId);
    this.pointers.set(e.pointerId, { zone, x, y, originX: x, originY: y });
    if (zone === 'throttle') this.setThrottleFromY(y);
    if (zone === 'rotate') {
      this.autopilot = 'off';
      this.stick = { ox: x, oy: y, x, y };
    }
  };

  private onMove = (e: PointerEvent): void => {
    const p = this.pointers.get(e.pointerId);
    if (!p) return;
    const { x, y } = this.localPoint(e);

    if (p.zone === 'throttle') this.setThrottleFromY(y);
    else if (p.zone === 'rotate' && this.stick) {
      this.stick.x = x;
      this.stick.y = y;
      // Dragging right turns clockwise on screen, which is negative in world angle.
      this.turn = -Math.max(-1, Math.min(1, (x - this.stick.ox) / ROTATE_REACH));
    } else if (p.zone === 'camera') {
      const others = [...this.pointers.entries()].filter(([id, q]) => id !== e.pointerId && q.zone === 'camera');
      const other = others[0]?.[1];
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
    if (p.zone === 'rotate') {
      this.stick = null;
      this.turn = 0;
    }
  };

  private setThrottleFromY(y: number): void {
    const t = this.layout.throttleTrack;
    this.throttle = Math.max(0, Math.min(1, (t.bottom - y) / (t.bottom - t.top)));
    if (this.throttle < 0.04) this.throttle = 0;
    if (this.throttle > 0.96) this.throttle = 1;
  }
}
