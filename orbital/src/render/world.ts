import { BODIES, BODY_COUNT, bodyPositions } from '../sim/bodies';
import { atmosphereTop } from '../sim/atmosphere';
import { LEG_LENGTH } from '../sim/physics';
import { terrainRadius } from '../sim/terrain';
import { AU, TAU, fmtNum } from '../sim/units';
import { COLORS, neonStroke } from './neon';
import { type Scene } from './scene';
import { P, type View, arcSegments, proj, screenAngle, visibleArc } from './view';

const BX = new Float64Array(BODY_COUNT);
const BY = new Float64Array(BODY_COUNT);
const FONT = '11px ui-monospace, Menlo, monospace';

/** Draws a world-space circle (centre and radius in world units) as a polyline of its visible part. */
function circlePath(ctx: CanvasRenderingContext2D, v: View, bx: number, by: number, r: number): boolean {
  const arc = visibleArc(v, bx, by, r);
  if (!arc) return false;
  const n = arcSegments(2 * arc.half * r * v.zoom);
  const a0 = arc.mid - arc.half;
  for (let i = 0; i <= n; i++) {
    const a = a0 + (2 * arc.half * i) / n;
    proj(v, bx + r * Math.cos(a), by + r * Math.sin(a));
    if (i === 0) ctx.moveTo(P.x, P.y);
    else ctx.lineTo(P.x, P.y);
  }
  return true;
}

interface LabelReq {
  text: string;
  x: number;
  y: number;
  color: string;
  alpha: number;
  priority: number;
}

let labelQueue: LabelReq[] = [];

/** Queues a label; overlapping ones are dropped when the queue is flushed. */
function label(_ctx: CanvasRenderingContext2D, text: string, x: number, y: number, color: string, alpha = 0.9, priority = 1): void {
  labelQueue.push({ text, x, y, color, alpha, priority });
}

function flushLabels(ctx: CanvasRenderingContext2D): void {
  ctx.font = FONT;
  const placed: { x0: number; y0: number; x1: number; y1: number }[] = [];
  labelQueue.sort((a, b) => b.priority - a.priority);
  for (const l of labelQueue) {
    const w = ctx.measureText(l.text).width;
    const r = { x0: l.x - 2, y0: l.y - 11, x1: l.x + w + 2, y1: l.y + 3 };
    if (placed.some((q) => r.x0 < q.x1 && r.x1 > q.x0 && r.y0 < q.y1 && r.y1 > q.y0)) continue;
    placed.push(r);
    ctx.globalAlpha = l.alpha;
    ctx.fillStyle = l.color;
    ctx.fillText(l.text, l.x, l.y);
  }
  ctx.globalAlpha = 1;
  labelQueue = [];
}

export function drawStars(ctx: CanvasRenderingContext2D, v: View): void {
  ctx.strokeStyle = '#6a8cff';
  ctx.lineWidth = 1;
  let seed = 1234567;
  const rnd = (): number => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const ox = v.cx * 1e-4;
  const oy = v.cy * 1e-4;
  for (let i = 0; i < 90; i++) {
    const x = (((rnd() * v.w - ox) % v.w) + v.w) % v.w;
    const y = (((rnd() * v.h + oy) % v.h) + v.h) % v.h;
    ctx.globalAlpha = 0.15 + rnd() * 0.45;
    ctx.beginPath();
    ctx.moveTo(x - 1.5, y);
    ctx.lineTo(x + 1.5, y);
    ctx.moveTo(x, y - 1.5);
    ctx.lineTo(x, y + 1.5);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

export function drawWorld(ctx: CanvasRenderingContext2D, v: View, scene: Scene): void {
  const w = scene.world;
  bodyPositions(w.time, BX, BY);
  labelQueue = [];

  drawBelt(ctx, v);
  for (let i = 1; i < BODY_COUNT; i++) drawOrbitRing(ctx, v, i);
  for (let i = 0; i < BODY_COUNT; i++) drawBody(ctx, v, scene, i);
  drawPath(ctx, v, scene);
  flushLabels(ctx);
}

function drawBelt(ctx: CanvasRenderingContext2D, v: View): void {
  const r = 2.8 * AU;
  if (r * v.zoom < 14 || r * v.zoom > 3e5) return;
  ctx.setLineDash([1.5, 9]);
  ctx.lineCap = 'round';
  neonStroke(ctx, '#8a7a6a', 1.6, () => circlePath(ctx, v, 0, 0, r), 0.8);
  ctx.setLineDash([]);
  proj(v, r, 0);
  if (P.x > 0 && P.x < v.w && P.y > 0 && P.y < v.h) label(ctx, 'CINTURÓN', P.x + 6, P.y - 6, '#8a7a6a', 0.7);
}

function drawOrbitRing(ctx: CanvasRenderingContext2D, v: View, i: number): void {
  const b = BODIES[i];
  const rpx = b.orbitRadius * v.zoom;
  if (rpx < 14 || rpx > 4000) return;
  neonStroke(ctx, b.color, 1, () => circlePath(ctx, v, BX[b.parentIndex], BY[b.parentIndex], b.orbitRadius), 0.28);
}

function drawBody(ctx: CanvasRenderingContext2D, v: View, scene: Scene, i: number): void {
  const b = BODIES[i];
  proj(v, BX[i], BY[i]);
  const sx = P.x;
  const sy = P.y;
  const rpx = b.radius * v.zoom;
  const margin = rpx + 80;
  const onScreen = sx > -margin && sx < v.w + margin && sy > -margin && sy < v.h + margin;
  const isTarget = scene.target === i;

  if (rpx < 5) {
    if (!onScreen) return;
    // Too small to see: draw an icon that stays readable at any zoom.
    neonStroke(ctx, b.color, 1.4, () => {
      ctx.moveTo(sx + 5, sy);
      ctx.arc(sx, sy, 5, 0, TAU);
    });
    if (isTarget) {
      ctx.setLineDash([3, 4]);
      neonStroke(ctx, COLORS.marker, 1.2, () => {
        ctx.moveTo(sx + 12, sy);
        ctx.arc(sx, sy, 12, 0, TAU);
      });
      ctx.setLineDash([]);
    }
    // The moon's label would clutter its parent's, so only label it once separated.
    const parentGap = b.parentIndex >= 0 ? Math.hypot(BX[i] - BX[b.parentIndex], BY[i] - BY[b.parentIndex]) * v.zoom : 99;
    if (parentGap > 26 || b.parentIndex <= 0) label(ctx, b.name, sx + 9, sy - 8, b.color, 0.9, isTarget ? 5 : i === scene.refIndex ? 4 : 2);
    return;
  }

  neonStroke(ctx, b.color, 1.6, () => circlePath(ctx, v, BX[i], BY[i], b.radius));
  if (b.star && rpx > 12 && rpx < 1500) {
    ctx.globalAlpha = 0.5;
    neonStroke(ctx, b.color, 1, () => {
      for (let k = 0; k < 28; k++) {
        const a = (k / 28) * TAU;
        proj(v, BX[i] + b.radius * Math.cos(a) * 1.12, BY[i] + b.radius * Math.sin(a) * 1.12);
        const x1 = P.x;
        const y1 = P.y;
        proj(v, BX[i] + b.radius * Math.cos(a) * 1.3, BY[i] + b.radius * Math.sin(a) * 1.3);
        ctx.moveTo(x1, y1);
        ctx.lineTo(P.x, P.y);
      }
    }, 0.5);
    ctx.globalAlpha = 1;
  }

  if (b.atmosphere && rpx > 30) drawAtmosphere(ctx, v, i);
  if (b.terrainAmp > 0 && rpx > 50) drawTerrain(ctx, v, scene, i);
  if (rpx > 12 && rpx < 140) label(ctx, b.name, sx + rpx * 0.75 + 6, sy - rpx * 0.75 - 4, b.color);
  if (isTarget) {
    ctx.setLineDash([4, 6]);
    neonStroke(ctx, COLORS.marker, 1.2, () => circlePath(ctx, v, BX[i], BY[i], b.radius + 18 / v.zoom));
    ctx.setLineDash([]);
  }
}

function drawAtmosphere(ctx: CanvasRenderingContext2D, v: View, i: number): void {
  const b = BODIES[i];
  const a = b.atmosphere!;
  const rings = [1, 2.2, 3.8, 5.8, 8];
  for (const k of rings) {
    const alt = a.scaleHeight * k;
    if (alt * v.zoom < 3) continue;
    const alpha = Math.min(0.55, 0.9 * Math.exp(-k * 0.45) * Math.min(1, a.density * 3 + 0.25));
    ctx.setLineDash([2, 7]);
    neonStroke(ctx, b.color, 1, () => circlePath(ctx, v, BX[i], BY[i], b.radius + alt), alpha);
    ctx.setLineDash([]);
  }
}

function drawTerrain(ctx: CanvasRenderingContext2D, v: View, scene: Scene, i: number): void {
  const b = BODIES[i];
  const arc = visibleArc(v, BX[i], BY[i], b.radius);
  if (!arc) return;
  const px = b.radius * v.zoom;
  const n = Math.min(1200, Math.max(30, Math.ceil((2 * arc.half * px) / 3)));
  const a0 = arc.mid - arc.half;
  const pts: number[] = [];
  const inner: number[] = [];
  const depth = Math.min(26, 40 / v.zoom);
  for (let k = 0; k <= n; k++) {
    const a = a0 + (2 * arc.half * k) / n;
    const r = terrainRadius(b, a);
    proj(v, BX[i] + r * Math.cos(a), BY[i] + r * Math.sin(a));
    pts.push(P.x, P.y);
    if (k % 3 === 0) {
      proj(v, BX[i] + (r - depth) * Math.cos(a), BY[i] + (r - depth) * Math.sin(a));
      inner.push(pts[pts.length - 2], pts[pts.length - 1], P.x, P.y);
    }
  }
  neonStroke(ctx, b.color, 1.6, () => {
    ctx.moveTo(pts[0], pts[1]);
    for (let k = 2; k < pts.length; k += 2) ctx.lineTo(pts[k], pts[k + 1]);
  });
  if (px > 120) {
    neonStroke(ctx, b.color, 1, () => {
      for (let k = 0; k < inner.length; k += 4) {
        ctx.moveTo(inner[k], inner[k + 1]);
        ctx.lineTo(inner[k + 2], inner[k + 3]);
      }
    }, 0.3);
  }

  // Landing sites, flags and bases.
  for (const s of b.sites) {
    const half = s.halfWidth / b.radius;
    const sa = [s.angle - half, s.angle + half];
    if (Math.abs(((s.angle - arc.mid + Math.PI * 3) % TAU) - Math.PI) > arc.half + 0.3 && arc.half < Math.PI) continue;
    neonStroke(ctx, COLORS.marker, 2, () => {
      for (let k = 0; k <= 6; k++) {
        const a = sa[0] + ((sa[1] - sa[0]) * k) / 6;
        proj(v, BX[i] + (b.radius + 0.5) * Math.cos(a), BY[i] + (b.radius + 0.5) * Math.sin(a));
        if (k === 0) ctx.moveTo(P.x, P.y);
        else ctx.lineTo(P.x, P.y);
      }
    });
    if (px > 200) {
      proj(v, BX[i] + (b.radius - 14) * Math.cos(s.angle), BY[i] + (b.radius - 14) * Math.sin(s.angle));
      label(ctx, s.name, P.x - 40, P.y + 12, COLORS.marker, 0.8);
    }
  }
  for (const f of scene.flags) if (f.body === i) drawFlag(ctx, v, i, f.theta);
  for (const m of scene.bases) if (m.body === i) drawBase(ctx, v, i, m.theta);
}

function localToScreen(v: View, i: number, theta: number, along: number, up: number): void {
  const b = BODIES[i];
  const r = terrainRadius(b, theta) + up;
  const tx = -Math.sin(theta);
  const ty = Math.cos(theta);
  proj(v, BX[i] + r * Math.cos(theta) + tx * along, BY[i] + r * Math.sin(theta) + ty * along);
}

function drawFlag(ctx: CanvasRenderingContext2D, v: View, i: number, theta: number): void {
  const u = Math.max(1, 14 / (v.zoom * 30));
  neonStroke(ctx, '#ffffff', 1.4, () => {
    localToScreen(v, i, theta, 18 * u, 0);
    ctx.moveTo(P.x, P.y);
    localToScreen(v, i, theta, 18 * u, 30 * u);
    ctx.lineTo(P.x, P.y);
    localToScreen(v, i, theta, 18 * u + 16 * u, 24 * u);
    ctx.lineTo(P.x, P.y);
    localToScreen(v, i, theta, 18 * u, 18 * u);
    ctx.lineTo(P.x, P.y);
  });
}

function drawBase(ctx: CanvasRenderingContext2D, v: View, i: number, theta: number): void {
  const u = Math.max(1, 14 / (v.zoom * 30));
  neonStroke(ctx, COLORS.good, 1.6, () => {
    const pts: [number, number][] = [
      [-16, 0], [-16, 7], [-10, 14], [10, 14], [16, 7], [16, 0],
    ];
    pts.forEach(([a, h], k) => {
      localToScreen(v, i, theta, -22 * u + a * u, h * u);
      if (k === 0) ctx.moveTo(P.x, P.y);
      else ctx.lineTo(P.x, P.y);
    });
    ctx.closePath();
    localToScreen(v, i, theta, -22 * u, 14 * u);
    ctx.moveTo(P.x, P.y);
    localToScreen(v, i, theta, -22 * u, 24 * u);
    ctx.lineTo(P.x, P.y);
  });
}

const FX = new Float64Array(BODY_COUNT);
const FY = new Float64Array(BODY_COUNT);
const NX = new Float64Array(BODY_COUNT);
const NY = new Float64Array(BODY_COUNT);

function drawPath(ctx: CanvasRenderingContext2D, v: View, scene: Scene): void {
  const p = scene.prediction;
  const w = scene.world;
  if (!p || p.count < 2 || w.ship.status !== 'flying') return;
  const frame = scene.frameBody;
  bodyPositions(w.time, NX, NY);
  const fx0 = frame >= 0 ? NX[frame] : 0;
  const fy0 = frame >= 0 ? NY[frame] : 0;
  const xs = new Float64Array(p.count);
  const ys = new Float64Array(p.count);
  for (let k = 0; k < p.count; k++) {
    if (frame >= 0) {
      bodyPositions(p.t[k], FX, FY);
      xs[k] = p.x[k] - FX[frame] + fx0;
      ys[k] = p.y[k] - FY[frame] + fy0;
    } else {
      xs[k] = p.x[k];
      ys[k] = p.y[k];
    }
  }
  const pre = p.nodeIndex < 0 ? p.count : p.nodeIndex + 1;
  const impact = p.end === 'impact' || p.end === 'atmosphere';

  const stroke = (from: number, to: number, color: string, intensity: number): void => {
    neonStroke(ctx, color, 1.2, () => {
      let started = false;
      for (let k = from; k < to; k++) {
        proj(v, xs[k], ys[k]);
        if (!started) {
          ctx.moveTo(P.x, P.y);
          started = true;
        } else ctx.lineTo(P.x, P.y);
      }
    }, intensity);
  };
  ctx.setLineDash([9, 6]);
  stroke(0, pre, p.nodeIndex < 0 && impact ? COLORS.danger : COLORS.path, 0.6);
  if (p.nodeIndex >= 0) stroke(p.nodeIndex, p.count, impact ? COLORS.danger : COLORS.postNode, 0.7);
  ctx.setLineDash([]);

  // Node marker.
  if (p.nodeIndex >= 0 && p.nodePos) {
    proj(v, xs[p.nodeIndex], ys[p.nodeIndex]);
    const nx = P.x;
    const ny = P.y;
    neonStroke(ctx, COLORS.marker, 1.6, () => {
      ctx.moveTo(nx, ny - 8);
      ctx.lineTo(nx + 8, ny);
      ctx.lineTo(nx, ny + 8);
      ctx.lineTo(nx - 8, ny);
      ctx.closePath();
    });
    label(ctx, 'NODO', nx + 11, ny - 9, COLORS.marker, 0.9, 7);
  }

  // Encounters: mark the closest point of each pass.
  for (const e of p.encounters) {
    if (e.body === scene.refIndex && !e.impact) continue;
    let best = 0;
    let bd = Infinity;
    for (let k = 0; k < p.count; k++) {
      const d = Math.abs(p.t[k] - e.tClosest);
      if (d < bd) {
        bd = d;
        best = k;
      }
    }
    proj(v, xs[best], ys[best]);
    const ex = P.x;
    const ey = P.y;
    const b = BODIES[e.body];
    neonStroke(ctx, e.impact ? COLORS.danger : b.color, 1.4, () => {
      ctx.moveTo(ex + 6, ey);
      ctx.arc(ex, ey, 6, 0, TAU);
    });
    const alt = e.closest - b.radius;
    label(ctx, `${b.name} ${e.impact ? 'IMPACTO' : 'PE ' + fmtNum(alt)}`, ex + 10, ey + 4, e.impact ? COLORS.danger : b.color, 0.9, 6);
  }
  void atmosphereTop;
}

export function drawAsteroids(ctx: CanvasRenderingContext2D, v: View, scene: Scene): void {
  for (const a of scene.world.asteroids) {
    proj(v, a.x, a.y);
    const r = Math.max(7, a.r * v.zoom);
    const sx = P.x;
    const sy = P.y;
    if (sx < -50 || sx > v.w + 50 || sy < -50 || sy > v.h + 50) {
      // Off screen: point an arrow at it from the edge.
      const cx = v.w / 2;
      const cy = v.h / 2;
      const ang = Math.atan2(sy - cy, sx - cx);
      const k = Math.min((v.w / 2 - 24) / Math.abs(Math.cos(ang) || 1e-9), (v.h / 2 - 24) / Math.abs(Math.sin(ang) || 1e-9));
      const ex = cx + Math.cos(ang) * k;
      const ey = cy + Math.sin(ang) * k;
      neonStroke(ctx, COLORS.danger, 1.6, () => {
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - Math.cos(ang - 0.5) * 14, ey - Math.sin(ang - 0.5) * 14);
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - Math.cos(ang + 0.5) * 14, ey - Math.sin(ang + 0.5) * 14);
      });
      continue;
    }
    const t = scene.clock + a.id;
    neonStroke(ctx, COLORS.danger, 1.6, () => {
      for (let k = 0; k < 9; k++) {
        const ang = (k / 9) * TAU + t * 0.6;
        const rr = r * (0.75 + 0.35 * Math.sin(k * 2.7 + a.id));
        const x = sx + Math.cos(ang) * rr;
        const y = sy + Math.sin(ang) * rr;
        if (k === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
    });
  }
}

export function drawShip(ctx: CanvasRenderingContext2D, v: View, scene: Scene): void {
  const s = scene.world.ship;
  proj(v, s.x, s.y);
  const sx = P.x;
  const sy = P.y;
  if (sx < -60 || sx > v.w + 60 || sy < -60 || sy > v.h + 60) return;
  // The ship is drawn in pixels: at least 20 px long, and true size (14 u) once zoomed in.
  const size = Math.max(20, 14 * v.zoom) / 14;
  const px = 1 / size;

  if (s.status === 'crashed') {
    neonStroke(ctx, COLORS.danger, 1.6, () => {
      for (let i = 0; i < 9; i++) {
        const a = (i / 9) * TAU + 0.3;
        const r1 = 5 + Math.sin(scene.clock * 5 + i) * 2;
        const r2 = 16 + 7 * ((i * 7) % 3);
        ctx.moveTo(sx + Math.cos(a) * r1, sy + Math.sin(a) * r1);
        ctx.lineTo(sx + Math.cos(a) * r2, sy + Math.sin(a) * r2);
      }
    });
    return;
  }

  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(screenAngle(v, s.angle));
  ctx.scale(size, size);
  if (scene.atmoGlow > 0.02) {
    ctx.globalAlpha = Math.min(1, scene.atmoGlow);
    neonStroke(ctx, '#ff7a1a', 1.6 * px, () => {
      ctx.moveTo(14, 0);
      ctx.arc(2, 0, 14, -1.2, 1.2);
    }, 1);
    ctx.globalAlpha = 1;
  }
  neonStroke(ctx, COLORS.ship, 1.6 * px, () => {
    ctx.moveTo(10, 0);
    ctx.lineTo(-4, 5);
    ctx.lineTo(-4, -5);
    ctx.closePath();
    ctx.moveTo(-2, 4);
    ctx.lineTo(-8, 8);
    ctx.moveTo(-2, -4);
    ctx.lineTo(-8, -8);
    ctx.moveTo(-10, 8);
    ctx.lineTo(-6, 8);
    ctx.moveTo(-10, -8);
    ctx.lineTo(-6, -8);
  });
  if (s.throttle > 0) {
    const flicker = 0.75 + 0.25 * Math.sin(scene.clock * 70) * Math.cos(scene.clock * 41);
    const l = 6 + 16 * s.throttle * flicker;
    neonStroke(ctx, '#ffb000', 1.4 * px, () => {
      ctx.moveTo(-4, 3);
      ctx.lineTo(-4 - l, 0);
      ctx.lineTo(-4, -3);
    });
  }
  ctx.restore();
  void LEG_LENGTH;
}
