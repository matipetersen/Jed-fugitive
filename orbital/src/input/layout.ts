export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ButtonDef extends Rect {
  id: 'prograde' | 'retrograde';
  label: string;
}

export interface Layout {
  width: number;
  height: number;
  /** Left strip that sets the throttle by dragging. */
  throttleZone: Rect;
  throttleTrack: { x: number; top: number; bottom: number };
  /** Right strip where a drag turns the ship. */
  rotateZone: Rect;
  rotateHome: { x: number; y: number };
  buttons: ButtonDef[];
}

export const ROTATE_REACH = 64;

export function computeLayout(width: number, height: number): Layout {
  const zoneW = Math.min(110, width * 0.2);
  const rotW = Math.min(190, width * 0.3);
  const bw = 62;
  const bh = 38;
  return {
    width,
    height,
    throttleZone: { x: 0, y: 0, w: zoneW, h: height },
    throttleTrack: { x: zoneW * 0.5, top: height * 0.16, bottom: height * 0.86 },
    rotateZone: { x: width - rotW, y: height * 0.3, w: rotW, h: height * 0.7 },
    rotateHome: { x: width - rotW * 0.5, y: height - Math.min(96, height * 0.25) },
    buttons: [
      { id: 'prograde', label: 'PRO', x: width - 2 * bw - 20, y: 12, w: bw, h: bh },
      { id: 'retrograde', label: 'RET', x: width - bw - 12, y: 12, w: bw, h: bh },
    ],
  };
}

export const inRect = (r: Rect, x: number, y: number): boolean =>
  x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h;
