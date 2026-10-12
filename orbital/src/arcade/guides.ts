import { COLORS, lineStroke, neonStroke, quality } from '../render/neon';
import { P, type View, proj } from '../render/view';
import { text } from '../render/hud';
import { type ArcadeGame } from './game';
import { type Arena } from './arena';

const TAU = Math.PI * 2;
const AMBER = '#ffb000';
const GOOD = '#7dff6b';
const BAD = '#ff3b3b';

const wrap = (a: number): number => {
  let r = (a + Math.PI) % TAU;
  if (r < 0) r += TAU;
  return r - Math.PI;
};

interface Pt {
  x: number;
  y: number;
}

/** Racing-line guides, like the ideal line in a motor-racing game: the route, the corner apexes and the speeds to carry. */
export function drawGuides(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const m = g.mission;
  const a = m.arena;
  const p = m.player;
  if (!g.guides || p.status === 'dead' || m.phase === 'cleared') return;
  const route = p.route;
  const n = route.length;
  const k0 = p.nextGate;

  // 1. The line: ship, then the next few targets, smoothed.
  const pts: Pt[] = [{ x: p.x, y: p.y }];
  const tmp = { x: 0, y: 0 };
  for (let i = k0; i < Math.min(n, k0 + 4); i++) {
    a.gatePos(i, tmp, a.cur, route);
    pts.push({ x: tmp.x, y: tmp.y });
  }
  if (k0 >= n) {
    a.padPoint(p.finishPad.body, p.finishPad.pad, tmp);
    pts.push({ x: tmp.x, y: tmp.y });
  }
  if (pts.length >= 2) drawLine(ctx, v, g, pts);

  // 2. Fly-bys: the ideal arc round each planet whose gates come up.
  const done = new Set<number>();
  for (let i = k0; i < Math.min(n, k0 + 9); i++) {
    const gate = route[i];
    if (gate.land || gate.body < 0 || done.has(gate.body)) continue;
    // Gates in a row on the same body make a fly-by.
    let j = i;
    while (j + 1 < n && route[j + 1].body === gate.body && !route[j + 1].land) j++;
    if (j - i < 1) continue;
    done.add(gate.body);
    drawFlyby(ctx, v, g, a, gate.body, i, j);
  }

  // 3. The last metres of a landing: speed limits by height.
  const wp = route[k0]?.land;
  if (wp || k0 >= n) {
    const body = wp ? wp.body : p.finishPad.body;
    const pad = wp ? wp.pad : p.finishPad.pad;
    drawLadder(ctx, v, g, a, body, pad);
  }
}

function drawLine(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame, pts: Pt[]): void {
  // Catmull-Rom through the points (the ship's own position is the first).
  const out: Pt[] = [];
  const at = (i: number): Pt => pts[Math.max(0, Math.min(pts.length - 1, i))];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = at(i - 1);
    const p1 = at(i);
    const p2 = at(i + 1);
    const p3 = at(i + 2);
    const steps = 14;
    for (let s = 0; s < steps; s++) {
      const t = s / steps;
      const t2 = t * t;
      const t3 = t2 * t;
      out.push({
        x: 0.5 * (2 * p1.x + (-p0.x + p2.x) * t + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
        y: 0.5 * (2 * p1.y + (-p0.y + p2.y) * t + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3),
      });
    }
  }
  out.push(pts[pts.length - 1]);
  // Sharp turns ahead are painted amber: that is where speed has to come off.
  ctx.setLineDash([10, 8]);
  ctx.lineDashOffset = -g.clock * 40;
  const chunk = 14;
  for (let c = 0; c * chunk < out.length - 1; c++) {
    const from = c * chunk;
    const to = Math.min(out.length - 1, from + chunk);
    const a0 = Math.atan2(out[from + 1].y - out[from].y, out[from + 1].x - out[from].x);
    const a1 = Math.atan2(out[to].y - out[Math.max(from, to - 1)].y, out[to].x - out[Math.max(from, to - 1)].x);
    const bend = Math.abs(wrap(a1 - a0));
    const color = bend > 0.55 ? AMBER : bend > 0.25 ? '#c8ff6b' : GOOD;
    lineStroke(ctx, color, 1.6, () => {
      for (let i = from; i <= to; i++) {
        proj(v, out[i].x, out[i].y);
        if (i === from) ctx.moveTo(P.x, P.y);
        else ctx.lineTo(P.x, P.y);
      }
    }, Math.max(0.12, 0.5 - c * 0.07));
  }
  ctx.setLineDash([]);
  ctx.lineDashOffset = 0;
}

function drawFlyby(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame, a: Arena, bi: number, i0: number, i1: number): void {
  const route = g.mission.player.route;
  const b = a.bodies[bi];
  const cx = a.bx[bi];
  const cy = a.by[bi];
  const g0 = { x: 0, y: 0 };
  const g1 = { x: 0, y: 0 };
  const gm = { x: 0, y: 0 };
  a.gatePos(i0, g0, a.cur, route);
  a.gatePos(i1, g1, a.cur, route);
  a.gatePos(Math.floor((i0 + i1) / 2), gm, a.cur, route);
  const aE = Math.atan2(g0.y - cy, g0.x - cx);
  const aX = Math.atan2(g1.y - cy, g1.x - cx);
  const aM = Math.atan2(gm.y - cy, gm.x - cx);
  const rE = Math.hypot(g0.x - cx, g0.y - cy);
  const rX = Math.hypot(g1.x - cx, g1.y - cy);
  const rM = Math.hypot(gm.x - cx, gm.y - cy);
  // Go from entry to exit round the side that passes through the middle gate.
  let d1 = wrap(aM - aE);
  let d2 = wrap(aX - aM);
  if (Math.sign(d1) !== Math.sign(d2)) d2 = d1 > 0 ? d2 + (d2 < 0 ? TAU : 0) : d2 - (d2 > 0 ? TAU : 0);
  const total = d1 + d2;
  const steps = 36;
  const arc: Pt[] = [];
  for (let s = 0; s <= steps; s++) {
    const t = s / steps;
    const ang = aE + total * t;
    const rr = t < 0.5 ? rE + (rM - rE) * (t / 0.5) : rM + (rX - rM) * ((t - 0.5) / 0.5);
    arc.push({ x: cx + Math.cos(ang) * rr, y: cy + Math.sin(ang) * rr });
  }
  proj(v, cx, cy);
  const sx = P.x;
  const sy = P.y;
  const rp = b.def.r * v.zoom;
  if (sx < -rp * 4 - 200 || sx > v.w + rp * 4 + 200 || sy < -rp * 4 - 200 || sy > v.h + rp * 4 + 200) return;

  // The arc in three colours: set up (cyan), the apex (green), the exit (amber).
  const cols = ['#00f0ff', GOOD, AMBER];
  for (let part = 0; part < 3; part++) {
    const from = Math.floor((steps * part) / 3);
    const to = Math.floor((steps * (part + 1)) / 3);
    neonStroke(ctx, cols[part], 2, () => {
      for (let s = from; s <= to; s++) {
        proj(v, arc[s].x, arc[s].y);
        if (s === from) ctx.moveTo(P.x, P.y);
        else ctx.lineTo(P.x, P.y);
      }
    }, 0.75);
  }
  // Direction chevrons.
  lineStroke(ctx, '#ffffff', 1.4, () => {
    for (let s = 4; s < steps; s += 8) {
      proj(v, arc[s].x, arc[s].y);
      const x0 = P.x;
      const y0 = P.y;
      proj(v, arc[s + 1].x, arc[s + 1].y);
      const ang = Math.atan2(P.y - y0, P.x - x0);
      ctx.moveTo(x0 - Math.cos(ang - 0.6) * 8, y0 - Math.sin(ang - 0.6) * 8);
      ctx.lineTo(x0, y0);
      ctx.lineTo(x0 - Math.cos(ang + 0.6) * 8, y0 - Math.sin(ang + 0.6) * 8);
    }
  }, 0.8);

  // The apex: where the line passes closest.
  proj(v, gm.x, gm.y);
  const ax = P.x;
  const ay = P.y;
  neonStroke(ctx, GOOD, 1.6, () => {
    ctx.moveTo(ax, ay - 7);
    ctx.lineTo(ax + 7, ay);
    ctx.lineTo(ax, ay + 7);
    ctx.lineTo(ax - 7, ay);
    ctx.closePath();
  }, 0.9);

  // Where the planet is heading and whether the apex is behind it (speed gain) or ahead (speed loss).
  const vpx = a.bvx[bi];
  const vpy = a.bvy[bi];
  const vp = Math.hypot(vpx, vpy);
  let hint = '';
  let hintColor = COLORS.hud;
  if (vp > 25) {
    const dot = (gm.x - cx) * vpx + (gm.y - cy) * vpy;
    const behind = dot < 0;
    hint = behind ? 'POR DETRÁS: GANÁS VELOCIDAD' : 'POR DELANTE: PERDÉS VELOCIDAD';
    hintColor = behind ? GOOD : AMBER;
    // Planet motion arrow.
    proj(v, cx + (vpx / vp) * (b.def.r + 40), cy + (vpy / vp) * (b.def.r + 40));
    const hx = P.x;
    const hy = P.y;
    proj(v, cx + (vpx / vp) * (b.def.r + 40 + vp * 1.4), cy + (vpy / vp) * (b.def.r + 40 + vp * 1.4));
    const tx = P.x;
    const ty = P.y;
    const ang = Math.atan2(ty - hy, tx - hx);
    neonStroke(ctx, '#ff2bd6', 1.4, () => {
      ctx.moveTo(hx, hy);
      ctx.lineTo(tx, ty);
      ctx.moveTo(tx - Math.cos(ang - 0.5) * 9, ty - Math.sin(ang - 0.5) * 9);
      ctx.lineTo(tx, ty);
      ctx.lineTo(tx - Math.cos(ang + 0.5) * 9, ty - Math.sin(ang + 0.5) * 9);
    }, 0.8);
    if (!quality.low) text(ctx, `${b.def.name} ${Math.round(vp)} u/s`, tx + 6, ty - 4, '#ff2bd6', 10);
  }

  // Speed to carry at the apex: between circular and escape speed the planet bends the path the most.
  const vc = Math.sqrt(b.gm / Math.max(1, rM));
  const esc = vc * Math.SQRT2;
  const p = g.mission.player;
  const rel = Math.hypot(p.vx - vpx, p.vy - vpy);
  const ok = rel >= vc * 0.85 && rel <= esc * 1.2;
  const verdict = rel < vc * 0.85 ? 'MUY LENTO: TE CAPTURA' : rel > esc * 1.2 ? 'MUY RÁPIDO: CASI NO DOBLA' : 'BUENA VELOCIDAD';
  if (ax > -60 && ax < v.w + 60 && ay > 20 && ay < v.h + 40) {
    const ty0 = ay < 120 ? ay + 40 : ay - 12;
    text(ctx, `ÁPICE · ideal ${Math.round(vc)}-${Math.round(esc)} · ahora ${Math.round(rel)}`, ax + 12, ty0, ok ? GOOD : BAD, 10);
    text(ctx, verdict, ax + 12, ty0 + 14, ok ? GOOD : BAD, 10);
    if (hint) text(ctx, hint, ax + 12, ty0 + 28, hintColor, 10);
  }
}

/** A ladder above a pad: the most speed you can carry at each height and still touch down softly. */
function drawLadder(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame, a: Arena, bi: number, pad: number): void {
  const p = g.mission.player;
  const pt = { x: 0, y: 0 };
  const ang = a.padPoint(bi, pad, pt);
  if (Math.hypot(p.x - pt.x, p.y - pt.y) > 900) return;
  const nx = Math.cos(ang);
  const ny = Math.sin(ang);
  const rungs = [260, 160, 90, 45, 15];
  proj(v, pt.x, pt.y);
  const bx = P.x;
  const by = P.y;
  proj(v, pt.x + nx * 300, pt.y + ny * 300);
  const tx = P.x;
  const ty = P.y;
  ctx.setLineDash([3, 7]);
  lineStroke(ctx, GOOD, 1, () => {
    ctx.moveTo(bx, by);
    ctx.lineTo(tx, ty);
  }, 0.5);
  ctx.setLineDash([]);
  const rel = Math.hypot(p.vx - a.bvx[bi], p.vy - a.bvy[bi]);
  for (const h of rungs) {
    const limit = Math.round(Math.min(60, 8 + 0.4 * h));
    proj(v, pt.x + nx * h, pt.y + ny * h);
    const px = P.x;
    const py = P.y;
    const px2 = -(ty - by) / (Math.hypot(tx - bx, ty - by) || 1);
    const py2 = (tx - bx) / (Math.hypot(tx - bx, ty - by) || 1);
    lineStroke(ctx, GOOD, 1.4, () => {
      ctx.moveTo(px - px2 * 9, py - py2 * 9);
      ctx.lineTo(px + px2 * 9, py + py2 * 9);
    }, 0.7);
    const alt = Math.hypot(p.x - pt.x, p.y - pt.y);
    const over = Math.abs(alt - h) < h * 0.5 + 12 && rel > limit * 1.15;
    if (px > 0 && px < v.w && py > 60 && py < v.h) text(ctx, `${h} · ≤${limit}`, px + 12 * (px2 >= 0 ? 1 : -1) + 4, py + 4, over ? BAD : GOOD, 10);
  }
}
