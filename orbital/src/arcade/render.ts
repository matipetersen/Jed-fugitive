import { FLOAT_REACH, ROTATE_REACH } from '../input/input';
import { COLORS, lineStroke, neonStroke, quality } from '../render/neon';
import { P, type View, proj, screenAngle } from '../render/view';
import { btn, meter, text } from '../render/hud';
import { circlePath } from '../render/world';
import { type Ui } from '../ui/ui';
import { type ArcadeGame } from './game';
import { type Ship } from './types';
import { coastPath } from './predict';
import { LAND_SPEED, SHIP_R } from './arena';

const TAU = Math.PI * 2;

/** '#rrggbb' to an rgba() string. */
function hexA(hex: string, a: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
/** Height reserved at the top: the host app's browser bar can cover the first pixels of the page. */
const TOP = 56;
const AMBER = '#ffb000';
const GOOD = '#7dff6b';
const BAD = '#ff3b3b';

export function drawArcade(ctx: CanvasRenderingContext2D, g: ArcadeGame, width: number, height: number): void {
  const v = g.view;
  v.w = width;
  v.h = height;
  // Camera shake nudges the whole scene.
  const sh = g.shake * 7;
  const view: View = sh > 0.1 ? { ...v, cx: v.cx + (Math.random() - 0.5) * sh / v.zoom, cy: v.cy + (Math.random() - 0.5) * sh / v.zoom } : v;
  drawSky(ctx, view, g);
  drawBodies(ctx, view, g);
  drawFields(ctx, view, g);
  drawGates(ctx, view, g);
  drawCells(ctx, view, g);
  drawAsteroids(ctx, view, g);
  drawBeacon(ctx, view, g);
  drawPredictor(ctx, view, g);
  drawTrails(ctx, view, g);
  drawParticles(ctx, view, g);
  for (const s of g.mission.arena.ships) drawShip(ctx, view, s, g);
  drawRings(ctx, view, g);
}


// ---------------------------------------------------------------- sky

const STAR_COLORS = ['#6a8cff', '#00f0ff', '#ff2bd6', '#ffb000', '#c8d4ff', '#7dff6b'];

/** Deterministic pseudo-random in 0..1 for star `i` of a layer. */
function hash(i: number, k: number): number {
  const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

/** Coloured stars on three parallax layers, faint nebula rings, a glow at the horizon and speed streaks. */
function drawSky(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const w = v.w;
  const h = v.h;
  const low = quality.low;
  // Colour wash: violet above, teal below, so the black is never flat.
  const wash = ctx.createLinearGradient(0, 0, 0, h);
  wash.addColorStop(0, 'rgba(70,10,110,0.26)');
  wash.addColorStop(0.55, 'rgba(0,0,0,0)');
  wash.addColorStop(1, 'rgba(0,70,110,0.24)');
  ctx.fillStyle = wash;
  ctx.fillRect(0, 0, w, h);

  // Nebula rings: huge, dashed, almost still.
  if (!low) {
    const rings: [number, number, number, string][] = [[0.18, 0.3, 380, '#ff2bd6'], [0.8, 0.7, 520, '#00f0ff'], [0.55, 0.1, 300, '#7a5cff']];
    ctx.setLineDash([3, 14]);
    for (const [fx, fy, r, c] of rings) {
      const ox = -v.cx * 0.012;
      const oy = v.cy * 0.012;
      lineStroke(ctx, c, 2, () => {
        ctx.moveTo(w * fx + ox + r, h * fy + oy);
        ctx.arc(w * fx + ox, h * fy + oy, r, 0, TAU);
      }, 0.13);
    }
    ctx.setLineDash([]);
  }

  // Stars: per layer a few groups by colour, each one path.
  const layers: [number, number, number, number][] = low ? [[0.03, 28, 1.6, 0.5], [0.09, 18, 2.2, 0.8]] : [[0.02, 46, 1.4, 0.35], [0.05, 34, 1.9, 0.55], [0.11, 22, 2.8, 0.85]];
  const t = g.clock;
  layers.forEach(([par, n, size, alpha], li) => {
    const ox = -v.cx * par;
    const oy = v.cy * par;
    const groups: number[][] = STAR_COLORS.map(() => []);
    for (let i = 0; i < n; i++) {
      const x = (((hash(i, li) * w + ox) % w) + w) % w;
      const y = (((hash(i, li + 9) * h + oy) % h) + h) % h;
      groups[Math.floor(hash(i, li + 4) * STAR_COLORS.length)].push(x, y);
    }
    groups.forEach((pts, ci) => {
      if (!pts.length) return;
      const tw = 0.75 + 0.25 * Math.sin(t * (1.5 + ci * 0.7) + li * 2);
      lineStroke(ctx, STAR_COLORS[ci], 1, () => {
        for (let i = 0; i < pts.length; i += 2) {
          ctx.moveTo(pts[i] - size, pts[i + 1]);
          ctx.lineTo(pts[i] + size, pts[i + 1]);
          ctx.moveTo(pts[i], pts[i + 1] - size);
          ctx.lineTo(pts[i], pts[i + 1] + size);
        }
      }, alpha * tw);
    });
    // The near layer also gets a few bright flares.
    if (li === layers.length - 1 && !low) {
      for (let i = 0; i < 4; i++) {
        const x = (((hash(i, 77) * w + ox) % w) + w) % w;
        const y = (((hash(i, 78) * h + oy) % h) + h) % h;
        const c = STAR_COLORS[i % 4];
        const r = 5 + 2 * Math.sin(t * 2 + i);
        neonStroke(ctx, c, 1, () => {
          ctx.moveTo(x - r, y);
          ctx.lineTo(x + r, y);
          ctx.moveTo(x, y - r);
          ctx.lineTo(x, y + r);
        }, 0.7);
      }
    }
  });

  // Speed streaks: stars smeared against the velocity.
  const p = g.mission.player;
  const sp = Math.hypot(p.vx, p.vy);
  if (sp > 70 && p.status !== 'dead') {
    const ang = screenAngle(v, Math.atan2(p.vy, p.vx));
    const dx = Math.cos(ang);
    const dy = Math.sin(ang);
    const len = Math.min(70, sp * 0.18);
    const a = Math.min(0.5, (sp - 70) / 400);
    const n = low ? 8 : 18;
    lineStroke(ctx, '#9be8ff', 1, () => {
      for (let i = 0; i < n; i++) {
        const x = (((hash(i, 31) * w - v.cx * 0.2) % w) + w) % w;
        const y = (((hash(i, 32) * h + v.cy * 0.2) % h) + h) % h;
        ctx.moveTo(x, y);
        ctx.lineTo(x - dx * len, y - dy * len);
      }
    }, a);
  }
}

function drawBodies(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const a = g.mission.arena;
  for (let i = 0; i < a.bodies.length; i++) {
    const b = a.bodies[i];
    const x = a.bx[i];
    const y = a.by[i];
    const o = b.def.orbit;
    if (o && b.parent >= 0 && o.a * v.zoom > 20 && o.a * v.zoom < 3000) {
      lineStroke(ctx, b.def.color, 1, () => circlePath(ctx, v, a.bx[b.parent], a.by[b.parent], o.a), 0.22);
    }
    proj(v, x, y);
    const cxp = P.x;
    const cyp = P.y;
    const rp = b.def.r * v.zoom;
    if (rp > 8 && cxp > -rp * 2 && cxp < v.w + rp * 2 && cyp > -rp * 2 && cyp < v.h + rp * 2) {
      // Soft glow outside the rim.
      const reach = b.def.star ? 2.6 : b.def.atm ? 1.5 : 1.28;
      const gr = ctx.createRadialGradient(cxp, cyp, rp * 0.9, cxp, cyp, rp * reach);
      gr.addColorStop(0, hexA(b.def.color, b.def.star ? 0.45 : 0.28));
      gr.addColorStop(1, hexA(b.def.color, 0));
      ctx.fillStyle = gr;
      ctx.beginPath();
      ctx.arc(cxp, cyp, rp * reach, 0, TAU);
      ctx.fill();
    }
    if (b.def.hole) {
      drawHole(ctx, v, g, x, y, b.def.r, b.def.color);
      proj(v, x, y);
      const rp2 = b.def.r * v.zoom;
      if (rp2 > 6 && P.x > -50 && P.x < v.w + 50 && P.y > -50 && P.y < v.h + 50) {
        ctx.globalAlpha = 0.8;
        text(ctx, b.def.name, P.x - ctx.measureText(b.def.name).width / 2, P.y + rp2 * 2.6 + 12, b.def.color, 11);
        ctx.globalAlpha = 1;
      }
      continue;
    }
    neonStroke(ctx, b.def.color, 1.8, () => circlePath(ctx, v, x, y, b.def.r));
    // Wireframe: parallels and a hatch of inner rings, as if the sphere were a vector model.
    if (rp > 14) {
      lineStroke(ctx, b.def.color, 1, () => {
        for (const k of [0.78, 0.52, 0.26]) circlePath(ctx, v, x, y, b.def.r * k);
      }, 0.16);
    }
    if (b.def.star) {
      lineStroke(ctx, b.def.color, 1.2, () => circlePath(ctx, v, x, y, b.def.r * 1.45), 0.35);
      lineStroke(ctx, '#ff7a1a', 1, () => circlePath(ctx, v, x, y, b.def.r * 1.9), 0.25);
    }
    if (b.def.atm) {
      for (const k of [1, 2, 3]) {
        const alt = b.def.atm.h * k;
        if (alt * v.zoom < 3) continue;
        lineStroke(ctx, b.def.color, 1, () => circlePath(ctx, v, x, y, b.def.r + alt), 0.3 / k);
      }
    }
    // Pads: amber strip along the ground, with a flame on bonfires.
    for (const pad of b.def.pads ?? []) {
      const half = pad.half / b.def.r;
      neonStroke(ctx, AMBER, 2.2, () => {
        for (let k = 0; k <= 6; k++) {
          const ang = pad.angle - half + (2 * half * k) / 6;
          proj(v, x + (b.def.r + 0.5) * Math.cos(ang), y + (b.def.r + 0.5) * Math.sin(ang));
          if (k === 0) ctx.moveTo(P.x, P.y);
          else ctx.lineTo(P.x, P.y);
        }
      });
      if (pad.bonfire) drawFlame(ctx, v, x + (b.def.r + 12) * Math.cos(pad.angle), y + (b.def.r + 12) * Math.sin(pad.angle), g.clock);
    }
    proj(v, x, y);
    const rpx = b.def.r * v.zoom;
    if (rpx > 6 && P.x > -50 && P.x < v.w + 50 && P.y > -50 && P.y < v.h + 50) {
      ctx.globalAlpha = 0.8;
      text(ctx, b.def.name, P.x - ctx.measureText(b.def.name).width / 2, P.y + 4, b.def.color, 11);
      ctx.globalAlpha = 1;
    }
  }
}

/** Black hole: dark horizon, a tilted accretion disc and lensing arcs. */
function drawHole(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame, x: number, y: number, r: number, color: string): void {
  proj(v, x, y);
  const sx = P.x;
  const sy = P.y;
  const rp = r * v.zoom;
  if (sx < -rp * 4 || sx > v.w + rp * 4 || sy < -rp * 4 || sy > v.h + rp * 4) return;
  // Hot glow around the horizon.
  const gr = ctx.createRadialGradient(sx, sy, rp * 0.9, sx, sy, rp * 3.2);
  gr.addColorStop(0, hexA(color, 0.5));
  gr.addColorStop(0.35, hexA('#ff7a1a', 0.18));
  gr.addColorStop(1, hexA(color, 0));
  ctx.fillStyle = gr;
  ctx.beginPath();
  ctx.arc(sx, sy, rp * 3.2, 0, TAU);
  ctx.fill();
  // The horizon itself blocks the light behind it.
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000';
  ctx.beginPath();
  ctx.arc(sx, sy, rp * 0.98, 0, TAU);
  ctx.fill();
  ctx.globalCompositeOperation = 'lighter';
  neonStroke(ctx, '#ffffff', 1.8, () => {
    ctx.moveTo(sx + rp, sy);
    ctx.arc(sx, sy, rp, 0, TAU);
  }, 0.9);
  // Accretion disc: tilted ellipses spinning against each other.
  for (const [k, c, w] of [[1.7, '#ff7a1a', 0.55], [2.2, color, 0.4], [2.7, '#ff2bd6', 0.3]] as [number, string, number][]) {
    ctx.setLineDash([12, 9]);
    ctx.lineDashOffset = -g.clock * 30 * (3 - k);
    lineStroke(ctx, c, 1.6, () => {
      ctx.moveTo(sx + rp * k, sy);
      ctx.ellipse(sx, sy, rp * k, rp * k * 0.28, -0.35, 0, TAU);
    }, w);
  }
  ctx.setLineDash([]);
  ctx.lineDashOffset = 0;
  // Danger ring at the edge of the burning zone.
  lineStroke(ctx, '#ff3b3b', 1, () => {
    ctx.moveTo(sx + rp * 2.2, sy);
    ctx.arc(sx, sy, rp * 2.2, 0, TAU);
  }, 0.25);
}

function drawFlame(ctx: CanvasRenderingContext2D, v: View, x: number, y: number, clock: number): void {
  proj(v, x, y);
  const sx = P.x;
  const sy = P.y;
  const s = Math.max(5, 9 * Math.min(1, v.zoom * 2));
  const f = 0.8 + 0.2 * Math.sin(clock * 11);
  neonStroke(ctx, AMBER, 1.5, () => {
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx - s * 0.6, sy - s * 0.9);
    ctx.lineTo(sx - s * 0.2, sy - s * 1.2 * f);
    ctx.lineTo(sx, sy - s * 1.9 * f);
    ctx.lineTo(sx + s * 0.25, sy - s * 1.1);
    ctx.lineTo(sx + s * 0.6, sy - s * 0.9);
    ctx.closePath();
  });
}

function drawFields(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const a = g.mission.arena;
  for (const f of a.def.fields) {
    const fb = f.body ? a.bodyIndex(f.body) : -1;
    const fx = f.x + (fb >= 0 ? a.bx[fb] : 0);
    const fy = f.y + (fb >= 0 ? a.by[fb] : 0);
    ctx.setLineDash([10, 8]);
    ctx.lineDashOffset = -g.clock * 12;
    lineStroke(ctx, f.color, 1.4, () => circlePath(ctx, v, fx, fy, f.r), 0.5);
    ctx.setLineDash([]);
    ctx.lineDashOffset = 0;
    if (f.kind === 'wind') {
      const n = 14;
      lineStroke(ctx, f.color, 1.2, () => {
        for (let i = 0; i < n; i++) {
          const an = (i / n) * TAU;
          const rr = f.r * (0.25 + 0.6 * ((i * 7) % n) / n);
          const x0 = fx + Math.cos(an) * rr;
          const y0 = fy + Math.sin(an) * rr;
          const len = 55;
          const l = Math.hypot(f.ax ?? 1, f.ay ?? 0) || 1;
          proj(v, x0, y0);
          ctx.moveTo(P.x, P.y);
          proj(v, x0 + ((f.ax ?? 0) / l) * len, y0 + ((f.ay ?? 0) / l) * len);
          ctx.lineTo(P.x, P.y);
        }
      }, 0.35);
    } else if (!quality.low) {
      // Radiation and dust: flickering specks inside the area.
      lineStroke(ctx, f.color, 1.4, () => {
        for (let i = 0; i < 26; i++) {
          const an = hash(i, 5) * TAU;
          const rr = f.r * Math.sqrt(hash(i, 6)) * 0.95;
          const wob = Math.sin(g.clock * 3 + i) * 6;
          proj(v, fx + Math.cos(an) * rr + wob, fy + Math.sin(an) * rr);
          ctx.moveTo(P.x - 2, P.y);
          ctx.lineTo(P.x + 2, P.y);
        }
      }, 0.5);
    }
    proj(v, fx, fy - f.r - 14);
    if (f.label && P.x > 0 && P.x < v.w && P.y > 0 && P.y < v.h) text(ctx, f.label, P.x - 28, P.y, f.color, 10);
  }
}

function drawGates(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const a = g.mission.arena;
  const next = g.mission.player.nextGate;
  const gp = { x: 0, y: 0 };
  for (let i = next; i < a.gates.length; i++) {
    if (i > next + 3) break;
    a.gatePos(i, gp);
    const gate = a.gates[i];
    const final = !!gate.def.final || i === a.gates.length - 1;
    const isNext = i === next;
    const color = final ? GOOD : isNext ? AMBER : COLORS.hud;
    const pulse = isNext ? 0.75 + 0.25 * Math.sin(g.clock * 6) : 0.4;
    if (isNext) {
      ctx.setLineDash([9, 6]);
      ctx.lineDashOffset = -g.clock * 24;
    }
    neonStroke(ctx, color, isNext ? 2.2 : 1.4, () => circlePath(ctx, v, gp.x, gp.y, gate.r), pulse);
    ctx.setLineDash([]);
    ctx.lineDashOffset = 0;
    if (isNext) {
      // A counter-rotating inner ring and a glow make the target easy to find.
      ctx.setLineDash([4, 10]);
      ctx.lineDashOffset = g.clock * 30;
      lineStroke(ctx, '#ff2bd6', 1.4, () => circlePath(ctx, v, gp.x, gp.y, gate.r * 0.72), 0.7);
      ctx.setLineDash([]);
      ctx.lineDashOffset = 0;
      proj(v, gp.x, gp.y);
      const rr = gate.r * v.zoom;
      if (rr > 5 && !quality.low) {
        const gr = ctx.createRadialGradient(P.x, P.y, rr * 0.5, P.x, P.y, rr * 1.9);
        gr.addColorStop(0, hexA(final ? '#7dff6b' : '#ffb000', 0.22));
        gr.addColorStop(1, hexA(final ? '#7dff6b' : '#ffb000', 0));
        ctx.fillStyle = gr;
        ctx.beginPath();
        ctx.arc(P.x, P.y, rr * 1.9, 0, TAU);
        ctx.fill();
      }
    }
    proj(v, gp.x, gp.y);
    if (P.x > -40 && P.x < v.w + 40 && P.y > -40 && P.y < v.h + 40) {
      ctx.globalAlpha = isNext ? 1 : 0.6;
      text(ctx, final ? 'META' : String(i + 1), P.x - 6, P.y + 4, color, isNext ? 13 : 11);
      ctx.globalAlpha = 1;
    }
  }
  // The finish pad: a pulsing marker above it once the last gate is next or passed.
  if (next >= a.gates.length - 1) {
    const ang = a.finishPoint(gp);
    const lift = 26 + 4 * Math.sin(g.clock * 5);
    proj(v, gp.x + Math.cos(ang) * lift, gp.y + Math.sin(ang) * lift);
    const mx = P.x;
    const my = P.y;
    const bi = a.finish.body;
    const half = a.bodies[bi].def.pads?.[a.finish.pad]?.half ?? 30;
    const sa = screenAngle(v, ang);
    neonStroke(ctx, GOOD, 2, () => {
      ctx.save();
      ctx.translate(mx, my);
      ctx.rotate(sa + Math.PI / 2);
      ctx.moveTo(-8, -8);
      ctx.lineTo(0, 4);
      ctx.lineTo(8, -8);
      ctx.restore();
    }, 0.9);
    void half;
  }
}

function drawCells(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const a = g.mission.arena;
  const cp = { x: 0, y: 0 };
  for (const c of a.cells) {
    if (c.taken) continue;
    a.cellPos(c, cp);
    proj(v, cp.x, cp.y);
    const sx = P.x;
    const sy = P.y;
    if (sx < -20 || sx > v.w + 20 || sy < -20 || sy > v.h + 20) continue;
    const r = 7 + Math.sin(g.clock * 5) * 1.2;
    const sq = Math.abs(Math.cos(g.clock * 2.4));
    neonStroke(ctx, GOOD, 1.5, () => {
      ctx.moveTo(sx, sy - r);
      ctx.lineTo(sx + r * (0.35 + 0.65 * sq), sy);
      ctx.lineTo(sx, sy + r);
      ctx.lineTo(sx - r * (0.35 + 0.65 * sq), sy);
      ctx.closePath();
    });
    lineStroke(ctx, '#ffffff', 1, () => {
      ctx.moveTo(sx, sy - r * 0.5);
      ctx.lineTo(sx, sy + r * 0.5);
    }, 0.8);
    lineStroke(ctx, GOOD, 1, () => {
      ctx.moveTo(sx + r * 2.1, sy);
      ctx.arc(sx, sy, r * 2.1, 0, TAU);
    }, 0.18 + 0.12 * Math.sin(g.clock * 5));
  }
}

function drawAsteroids(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const rocks = g.mission.arena.asteroids;
  for (const tint of [0, 1]) {
  neonStroke(ctx, tint ? '#ff7a1a' : BAD, 1.4, () => {
    for (const a of rocks) {
      if (!a.alive || (a.id & 1) !== tint) continue;
      proj(v, a.x, a.y);
      const sx = P.x;
      const sy = P.y;
      if (sx < -30 || sx > v.w + 30 || sy < -30 || sy > v.h + 30) continue;
      const r = Math.max(3.5, a.r * v.zoom);
      for (let k = 0; k < 7; k++) {
        const ang = (k / 7) * TAU + a.id;
        const rr = r * (0.8 + 0.3 * Math.sin(k * 2.3 + a.id));
        const px = sx + Math.cos(ang) * rr;
        const py = sy + Math.sin(ang) * rr;
        if (k === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
    }
  }, 0.85);
  }
}

function drawBeacon(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const bp = g.mission.beaconPos();
  if (!bp || !g.mission.beacon) return;
  proj(v, bp.x, bp.y);
  const sx = P.x;
  const sy = P.y;
  const r = 10 + Math.sin(g.clock * 4) * 2;
  neonStroke(ctx, AMBER, 1.8, () => {
    ctx.moveTo(sx, sy - r);
    ctx.lineTo(sx + r, sy);
    ctx.lineTo(sx, sy + r);
    ctx.lineTo(sx - r, sy);
    ctx.closePath();
  });
  if (sx > 0 && sx < v.w && sy > 0 && sy < v.h) text(ctx, `${g.mission.beacon.data}`, sx + 12, sy + 4, AMBER, 11);
}

function drawPredictor(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const secs = g.predictorSeconds();
  const p = g.mission.player;
  if (secs <= 0 || p.status !== 'flying') return;
  const path = coastPath(g.mission.arena, p, secs);
  ctx.setLineDash([8, 6]);
  neonStroke(ctx, path.hits ? BAD : GOOD, 1.2, () => {
    for (let i = 0; i < path.points.length; i += 2) {
      proj(v, path.points[i], path.points[i + 1]);
      if (i === 0) ctx.moveTo(P.x, P.y);
      else ctx.lineTo(P.x, P.y);
    }
  }, 0.6);
  ctx.setLineDash([]);
}

function drawShip(ctx: CanvasRenderingContext2D, v: View, s: Ship, g: ArcadeGame): void {
  if (s.status === 'dead') return;
  proj(v, s.x, s.y);
  const sx = P.x;
  const sy = P.y;
  if (sx < -60 || sx > v.w + 60 || sy < -60 || sy > v.h + 60) return;
  const size = Math.max(18, SHIP_R * 2 * v.zoom * 1.1) / 14;
  const blink = s.invuln > 0 && Math.floor(g.clock * 12) % 2 === 0;
  const thr = s.status === 'flying' ? s.throttle : 0;
  const a = blink ? 0.35 : 1;
  const sec = s.isPlayer ? '#ff2bd6' : '#00f0ff';
  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(screenAngle(v, s.angle));
  ctx.scale(size, size);
  const px = 1 / size;
  // Engine glow behind the ship.
  if (thr > 0.02 && !quality.low) {
    const r = 16 + 18 * thr;
    const gr = ctx.createRadialGradient(-6, 0, 1, -6, 0, r);
    gr.addColorStop(0, hexA(s.isPlayer ? '#00f0ff' : '#ff2bd6', 0.55 * thr));
    gr.addColorStop(1, hexA(s.isPlayer ? '#00f0ff' : '#ff2bd6', 0));
    ctx.fillStyle = gr;
    ctx.beginPath();
    ctx.arc(-6, 0, r, 0, TAU);
    ctx.fill();
  }
  // Flame: a long outer cone, a shorter hot core and flickering sparks.
  if (thr > 0.02) {
    const f = 0.8 + 0.2 * Math.sin(g.clock * 40 + s.id) + 0.12 * Math.sin(g.clock * 91);
    const L = (6 + 22 * thr) * f;
    neonStroke(ctx, sec, 1.6 * px, () => {
      ctx.moveTo(-3.6, 2.6);
      ctx.lineTo(-3.6 - L, 0);
      ctx.lineTo(-3.6, -2.6);
    }, a * (0.5 + 0.5 * thr));
    neonStroke(ctx, s.color, 1.4 * px, () => {
      ctx.moveTo(-3.6, 1.5);
      ctx.lineTo(-3.6 - L * 0.62, 0);
      ctx.lineTo(-3.6, -1.5);
    }, a);
    lineStroke(ctx, '#ffffff', 1.4 * px, () => {
      ctx.moveTo(-3.6, 0);
      ctx.lineTo(-3.6 - L * 0.4, 0);
    }, 0.9 * a);
  }
  // Hull: arrow body, swept wings and a bright cockpit.
  neonStroke(ctx, s.color, 1.7 * px, () => {
    ctx.moveTo(10, 0);
    ctx.lineTo(-5, 5.5);
    ctx.lineTo(-3, 0);
    ctx.lineTo(-5, -5.5);
    ctx.closePath();
  }, a);
  lineStroke(ctx, sec, 1.2 * px, () => {
    ctx.moveTo(1, 2.4);
    ctx.lineTo(-4.4, 4.6);
    ctx.moveTo(1, -2.4);
    ctx.lineTo(-4.4, -4.6);
    ctx.moveTo(6, 0);
    ctx.lineTo(0.5, 0);
  }, 0.9 * a);
  ctx.restore();
}

/** Ribbon of recent positions, fading towards the tail. */
function drawTrails(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  for (const s of g.mission.arena.ships) {
    const t = g.trails.get(s.id);
    if (!t || t.length < 6) continue;
    const n = t.length / 2;
    const chunks = quality.low ? 2 : 4;
    for (let c = 0; c < chunks; c++) {
      const from = Math.floor((n - 1) * (c / chunks));
      const to = Math.floor((n - 1) * ((c + 1) / chunks)) + 1;
      lineStroke(ctx, s.color, 1.6 + c * 0.5, () => {
        for (let i = from; i <= to && i < n; i++) {
          proj(v, t[i * 2], t[i * 2 + 1]);
          if (i === from) ctx.moveTo(P.x, P.y);
          else ctx.lineTo(P.x, P.y);
        }
      }, 0.08 + 0.2 * ((c + 1) / chunks));
    }
  }
}

/** Expanding shock rings: gates, pickups, landings and explosions. */
function drawRings(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  for (const r of g.rings) {
    const k = 1 - r.life / r.max;
    neonStroke(ctx, r.color, 1.6, () => circlePath(ctx, v, r.x, r.y, r.r), Math.max(0, k));
  }
}

function drawParticles(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  for (const p of g.particles) {
    proj(v, p.x, p.y);
    if (P.x < -10 || P.x > v.w + 10 || P.y < -10 || P.y > v.h + 10) continue;
    const k = Math.min(1, p.life / p.max);
    const alpha = Math.max(0, 1 - k);
    if (p.kind === 'flame') {
      // White-hot at the nozzle, then the ship's colour, then violet.
      ctx.globalAlpha = alpha;
      ctx.fillStyle = k < 0.2 ? '#ffffff' : k < 0.6 ? p.color : '#7a5cff';
      const sz = p.size * (1.2 - 0.6 * k) * Math.max(0.7, Math.min(1.6, v.zoom * 2.4));
      ctx.fillRect(P.x - sz / 2, P.y - sz / 2, sz, sz);
    } else if (p.kind === 'spark') {
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = p.color;
      ctx.lineWidth = Math.max(1, p.size * 0.8);
      const sp = Math.hypot(p.vx, p.vy) || 1;
      const len = Math.min(12, sp * 0.05) * (1 - 0.5 * k);
      const ang = screenAngle(v, Math.atan2(p.vy, p.vx));
      ctx.beginPath();
      ctx.moveTo(P.x, P.y);
      ctx.lineTo(P.x - Math.cos(ang) * len, P.y - Math.sin(ang) * len);
      ctx.stroke();
    } else {
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.fillRect(P.x - p.size / 2, P.y - p.size / 2, p.size, p.size);
    }
  }
  ctx.globalAlpha = 1;
}

/** Edge arrow towards something off screen. */
function edgeArrow(ctx: CanvasRenderingContext2D, v: View, wx: number, wy: number, color: string, label: string): void {
  proj(v, wx, wy);
  const sx = P.x;
  const sy = P.y;
  if (sx > 10 && sx < v.w - 10 && sy > TOP + 64 && sy < v.h - 10) return;
  const cx = v.w / 2;
  const cy = (TOP + 64 + v.h) / 2;
  const ang = Math.atan2(sy - cy, sx - cx);
  const k = Math.min((v.w / 2 - 70) / Math.abs(Math.cos(ang) || 1e-9), ((v.h - TOP - 64) / 2 - 26) / Math.abs(Math.sin(ang) || 1e-9));
  const ex = cx + Math.cos(ang) * k;
  const ey = cy + Math.sin(ang) * k;
  neonStroke(ctx, color, 1.6, () => {
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - Math.cos(ang - 0.45) * 15, ey - Math.sin(ang - 0.45) * 15);
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - Math.cos(ang + 0.45) * 15, ey - Math.sin(ang + 0.45) * 15);
  });
  text(ctx, label, ex - Math.cos(ang) * 40 - 14, ey - Math.sin(ang) * 40 + 4, color, 10);
}

// ---------------------------------------------------------------- HUD

export function drawArcadeHud(ctx: CanvasRenderingContext2D, g: ArcadeGame, width: number, height: number): void {
  const m = g.mission;
  const p = m.player;
  const a = m.arena;
  const ui: Ui = g.ui;
  const v = g.view;

  drawFloatStick(ctx, g, width, height);

  // Left readout.
  const x = 10;
  const speed = Math.hypot(p.vx, p.vy);
  text(ctx, 'CASCO', x, TOP + 20, COLORS.dim);
  meter(ctx, x + 48, TOP + 11, 90, p.hull / p.stats.hullMax, p.hull / p.stats.hullMax < 0.35 ? BAD : GOOD);
  text(ctx, 'COMB', x, TOP + 36, COLORS.dim);
  meter(ctx, x + 48, TOP + 27, 90, p.fuel / p.stats.fuelMax, p.fuel / p.stats.fuelMax < 0.2 ? BAD : AMBER);
  text(ctx, `VEL ${speed.toFixed(0)}`, x, TOP + 52, COLORS.hud);
  text(ctx, `VIDAS ${'♥'.repeat(Math.max(0, m.lives))}${m.practice ? ' ∞' : ''}`, x, TOP + 68, m.lives <= 1 && !m.practice ? BAD : COLORS.hud);
  text(ctx, `DATOS ${m.carried}`, x, TOP + 84, m.carried > 0 ? AMBER : COLORS.dim);

  // Near a surface: height and speed relative to it, green when a touchdown would be safe.
  if (p.status === 'flying') {
    let best = -1;
    let bestAlt = 220;
    for (let i = 0; i < a.bodies.length; i++) {
      const bd = a.bodies[i].def;
      if (bd.star || bd.hole) continue;
      const alt = Math.hypot(p.x - a.bx[i], p.y - a.by[i]) - bd.r - SHIP_R;
      if (alt < bestAlt) {
        bestAlt = alt;
        best = i;
      }
    }
    if (best >= 0) {
      const rel = Math.hypot(p.vx - a.bvx[best], p.vy - a.bvy[best]);
      const ok = rel <= LAND_SPEED * 0.85;
      text(ctx, `ALT ${Math.max(0, bestAlt).toFixed(0)}  VEL REL ${rel.toFixed(0)}`, x, TOP + 100, ok ? GOOD : BAD);
    }
  }

  // Top centre: stage, rings, time and the lead over the rival.
  const cx = (150 + width - 8 - 3 * 50 - 8) / 2;
  const ringTxt = `ETAPA ${m.stageIdx + 1} · ${m.def.name.toUpperCase()}`;
  text(ctx, ringTxt, cx, TOP + 18, AMBER, 12, true);
  const total = a.gates.length;
  const done = (sh: Ship): string => (a.gatesDone(sh) ? 'ATERRIZAR' : `${sh.nextGate}/${total}`);
  text(ctx, `AROS ${done(p)}  ·  RIVAL ${done(m.rival)}  ·  ${Math.max(0, a.clock).toFixed(0)} s`, cx, TOP + 34, COLORS.hud, 12, true);
  const lead = m.gateLead();
  const padName = a.bodies[a.finish.body].def.pads?.[a.finish.pad]?.name ?? 'la meta';
  let leadTxt = 'RIVAL AL PAR';
  let leadColor = COLORS.hud;
  if (a.clock < 0) {
    leadTxt = `${m.rival.name}`;
  } else if (a.gatesDone(p)) {
    leadTxt = `ATERRIZÁ EN ${padName.toUpperCase()}`;
    leadColor = GOOD;
  } else if (lead > 0) {
    leadTxt = `ADELANTE +${lead} ${lead === 1 ? 'aro' : 'aros'}`;
    leadColor = GOOD;
  } else if (lead < 0) {
    leadTxt = `${m.rival.name} ADELANTE ${-lead} ${lead === -1 ? 'aro' : 'aros'}`;
    leadColor = '#ff2bd6';
  } else if (!a.gatesDone(p) && !a.gatesDone(m.rival)) {
    const gp = { x: 0, y: 0 };
    a.gatePos(p.nextGate, gp);
    const dp = Math.hypot(p.x - gp.x, p.y - gp.y);
    const dr = Math.hypot(m.rival.x - gp.x, m.rival.y - gp.y);
    leadTxt = dp <= dr ? 'VAS ADELANTE' : `${m.rival.name} VA ADELANTE`;
    leadColor = dp <= dr ? GOOD : '#ff2bd6';
  }
  text(ctx, leadTxt, cx, TOP + 50, leadColor, 12, true);

  // Buttons.
  const bw = 50;
  const bh = 34;
  const bx = width - 8 - 3 * bw - 8;
  btn(ctx, ui, 'pause', bx, TOP + 8, bw, bh, 'PAUSA');
  btn(ctx, ui, 'kit', bx + bw + 4, TOP + 8, bw, bh, `CÁP ${m.kits}`, { dim: m.kits <= 0 || m.kitCooldown > 0, color: GOOD });
  btn(ctx, ui, 'aim', bx + 2 * (bw + 4), TOP + 8, bw, bh, 'APUNTA', { on: g.autoAim });
  btn(ctx, ui, 'zoom', bx + 2 * (bw + 4), TOP + 8 + bh + 4, bw, bh, 'ZOOM', { on: !g.input.zoomManual });

  // Edge arrows.
  {
    const gp = { x: 0, y: 0 };
    a.objective(p, gp);
    edgeArrow(ctx, v, gp.x, gp.y, a.gatesDone(p) ? GOOD : AMBER, `${Math.round(Math.hypot(gp.x - p.x, gp.y - p.y))}`);
  }
  if (m.rival.status !== 'dead') edgeArrow(ctx, v, m.rival.x, m.rival.y, '#ff2bd6', m.rival.name);
  const bp = m.beaconPos();
  if (bp) edgeArrow(ctx, v, bp.x, bp.y, AMBER, 'BALIZA');

  // Toasts.
  let y = TOP + 88;
  for (const t of g.toasts) {
    text(ctx, t.text, cx, y, t.kind === 'bad' ? BAD : t.kind === 'good' ? GOOD : COLORS.hud, 12, true);
    y += 16;
  }

  if (a.clock > 0 && !m.rival.finished && total - m.rival.nextGate <= 2 && m.rival.status !== 'dead' && m.phase !== 'cleared') {
    const warn = total - m.rival.nextGate;
    text(ctx, warn <= 0 ? `¡${m.rival.name} ESTÁ ATERRIZANDO!` : `¡${m.rival.name} ESTÁ A ${warn} ${warn === 1 ? 'ARO' : 'AROS'} DE GANAR!`, cx, TOP + 66, BAD, 12, true);
  }

  // Centre messages.
  if (a.clock < 0) {
    const n = Math.ceil(-a.clock);
    text(ctx, String(n), width / 2 - 20, height * 0.32, AMBER, 56, true);
    text(ctx, 'ARRASTRÁ HACIA ARRIBA CUANDO DIGA ¡YA!', width / 2 - 20, height * 0.32 + 28, COLORS.hud, 12, true);
  } else if (a.clock < 0.8 && m.phase === 'race') {
    text(ctx, '¡YA!', width / 2 - 20, height * 0.32, GOOD, 52, true);
  }
  if (p.status === 'dead') {
    text(ctx, `NAVE PERDIDA · ${p.deathReason.toUpperCase()}`, width / 2 - 20, height * 0.66, BAD, 16, true);
    text(ctx, m.lives <= 0 && !m.practice ? 'SIN VIDAS' : `VIDAS RESTANTES: ${Math.max(0, m.lives)}`, width / 2 - 20, height * 0.66 + 22, COLORS.hud, 13, true);
  }
  void ROTATE_REACH;
}

/** The floating stick: a ring under the finger. Where the finger points is where the nose turns; pushing further burns harder. */
function drawFloatStick(ctx: CanvasRenderingContext2D, g: ArcadeGame, width: number, height: number): void {
  const input = g.input;
  const st = input.stick;
  const R = FLOAT_REACH;
  const ox = st ? st.ox : width * 0.8;
  const oy = st ? st.oy : height * 0.7;
  neonStroke(ctx, COLORS.hud, 1.2, () => {
    ctx.moveTo(ox + R, oy);
    ctx.arc(ox, oy, R, 0, TAU);
    ctx.moveTo(ox + 10, oy);
    ctx.arc(ox, oy, 10, 0, TAU);
  }, st ? 0.8 : 0.35);
  if (st) {
    const dx = st.x - st.ox;
    const dy = st.y - st.oy;
    const d = Math.hypot(dx, dy) || 1;
    const k = Math.min(R, d);
    const kx = ox + (dx / d) * k;
    const ky = oy + (dy / d) * k;
    neonStroke(ctx, input.aim ? COLORS.marker : COLORS.hud, 1.8, () => {
      ctx.moveTo(kx + 12, ky);
      ctx.arc(kx, ky, 12, 0, TAU);
    });
    // Mark the push that just lifts the ship off the ground.
    const lift = g.liftoffThrottle();
    if (lift !== null) {
      const rr = 10 + Math.min(1, lift) * R * 0.6;
      neonStroke(ctx, lift <= 1 ? GOOD : BAD, 1.4, () => {
        ctx.moveTo(ox + rr, oy);
        ctx.arc(ox, oy, rr, 0, TAU);
      }, 0.7);
    }
    // Where the nose is being told to point.
    const aim = input.aim;
    const p = g.mission.player;
    if (aim && p.status !== 'dead') {
      proj(g.view, p.x, p.y);
      const sx = P.x;
      const sy = P.y;
      const ex = sx + Math.cos(aim.phi) * 56;
      const ey = sy - Math.sin(aim.phi) * 56;
      lineStroke(ctx, COLORS.marker, 1, () => {
        ctx.moveTo(sx + Math.cos(aim.phi) * 22, sy - Math.sin(aim.phi) * 22);
        ctx.lineTo(ex, ey);
      }, 0.7);
    }
  } else {
    text(ctx, 'APOYÁ Y APUNTÁ', ox - 44, oy - R - 8, COLORS.dim, 10);
    text(ctx, 'ARRASTRÁ HACIA DONDE IR', ox - 58, oy + R + 16, COLORS.dim, 10);
  }
}
