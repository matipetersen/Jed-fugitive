import { type Vec2 } from '../sim/vec';

export interface Camera {
  center: Vec2;
  /** Pixels per world unit. */
  zoom: number;
  /** World angle that points to the top of the screen. */
  up: number;
}

/** Sets ctx so world coordinates (y up) map to the screen, rotated by the camera. */
export function applyCamera(ctx: CanvasRenderingContext2D, cam: Camera, w: number, h: number, dpr: number): void {
  const theta = Math.PI / 2 - cam.up;
  const c = Math.cos(theta) * cam.zoom;
  const s = Math.sin(theta) * cam.zoom;
  const a = c;
  const b = -s;
  const cc = -s;
  const d = -c;
  const e = w / 2 - a * cam.center.x - cc * cam.center.y;
  const f = h / 2 - b * cam.center.x - d * cam.center.y;
  ctx.setTransform(a * dpr, b * dpr, cc * dpr, d * dpr, e * dpr, f * dpr);
}
