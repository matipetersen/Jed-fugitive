export interface View {
  /** World point at the centre of the screen. */
  cx: number;
  cy: number;
  /** Pixels per world unit. */
  zoom: number;
  /** World angle that points to the top of the screen. */
  up: number;
  w: number;
  h: number;
}

export const P = { x: 0, y: 0 };

/** Projects a world point to screen pixels, written into the shared P. */
export function proj(v: View, x: number, y: number): void {
  const theta = Math.PI / 2 - v.up;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const dx = x - v.cx;
  const dy = y - v.cy;
  P.x = v.w / 2 + v.zoom * (c * dx - s * dy);
  P.y = v.h / 2 - v.zoom * (s * dx + c * dy);
}

/** Screen-space direction (canvas rotation) of a world angle. */
export function screenAngle(v: View, worldAngle: number): number {
  return -(worldAngle + (Math.PI / 2 - v.up));
}

export interface ArcRange {
  /** Centre angle of the visible part, in world angle around the circle's centre. */
  mid: number;
  /** Half width of the visible part. Math.PI means the whole circle. */
  half: number;
}

/**
 * Part of a circle (in world units) that can be on screen. `bx`,`by` is the
 * circle centre, `r` its radius. Returns null when no part is visible.
 */
export function visibleArc(v: View, bx: number, by: number, r: number): ArcRange | null {
  const dx = v.cx - bx;
  const dy = v.cy - by;
  const dC = Math.hypot(dx, dy);
  const rho = (Math.hypot(v.w, v.h) / 2 + 12) / v.zoom;
  if (r + rho < dC || r - rho > dC) return null;
  if (r + dC <= rho || dC < 1e-9) return { mid: 0, half: Math.PI };
  const cos = (r * r + dC * dC - rho * rho) / (2 * r * dC);
  const half = Math.acos(Math.max(-1, Math.min(1, cos)));
  return { mid: Math.atan2(dy, dx), half };
}

/** Number of polyline segments for an arc of the given pixel length. */
export const arcSegments = (pixels: number): number => Math.max(10, Math.min(700, Math.ceil(pixels / 7)));
