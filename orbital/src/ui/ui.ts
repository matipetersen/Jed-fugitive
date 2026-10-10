export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface Registered {
  id: string;
  rect: Rect;
  repeat: boolean;
}

interface Held {
  id: string;
  time: number;
  nextAt: number;
}

export const inRect = (r: Rect, x: number, y: number): boolean =>
  x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h;

/**
 * Immediate-mode buttons for the canvas HUD. The renderer registers each button
 * every frame; pointer events are matched against the rectangles of the frame
 * before, and game logic reads presses with `pressed(id)`.
 */
export class Ui {
  private live: Registered[] = [];
  private next: Registered[] = [];
  private queue: string[] = [];
  private held = new Map<number, Held>();

  register(id: string, rect: Rect, repeat = false): void {
    this.next.push({ id, rect, repeat });
  }

  /** Call once per frame after drawing, so the next frame's hit tests see this one's buttons. */
  commit(): void {
    this.live = this.next;
    this.next = [];
  }

  hit(x: number, y: number): string | null {
    for (let i = this.live.length - 1; i >= 0; i--) {
      const b = this.live[i];
      if (inRect(b.rect, x, y)) return b.id;
    }
    return null;
  }

  press(pointerId: number, id: string): void {
    this.queue.push(id);
    const reg = this.live.find((b) => b.id === id);
    if (reg?.repeat) this.held.set(pointerId, { id, time: 0, nextAt: 0.4 });
  }

  release(pointerId: number): void {
    this.held.delete(pointerId);
  }

  clear(): void {
    this.queue = [];
    this.held.clear();
  }

  update(dt: number): void {
    for (const h of this.held.values()) {
      h.time += dt;
      while (h.time >= h.nextAt) {
        this.queue.push(h.id);
        h.nextAt += 0.07;
      }
    }
  }

  /** True once per press (or repeat tick) of the button. */
  pressed(id: string): boolean {
    const i = this.queue.indexOf(id);
    if (i < 0) return false;
    this.queue.splice(i, 1);
    return true;
  }

  isHeld(id: string): boolean {
    for (const h of this.held.values()) if (h.id === id) return true;
    return false;
  }

  /** Drops queued presses that no logic consumed this frame. */
  flush(): void {
    this.queue.length = 0;
  }
}
