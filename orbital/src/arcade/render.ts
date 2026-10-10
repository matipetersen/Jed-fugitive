import { ROTATE_REACH } from '../input/input';
import { COLORS, lineStroke, neonStroke } from '../render/neon';
import { P, type View, proj, screenAngle } from '../render/view';
import { btn, drawStick, drawThrottle, meter, text } from '../render/hud';
import { circlePath, drawStars } from '../render/world';
import { type Ui } from '../ui/ui';
import { type ArcadeGame } from './game';
import { type Ship } from './types';
import { coastPath } from './predict';
import { SHIP_R } from './arena';

const TAU = Math.PI * 2;
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
  drawStars(ctx, view);
  drawBodies(ctx, view, g);
  drawFields(ctx, view, g);
  drawGates(ctx, view, g);
  drawCells(ctx, view, g);
  drawAsteroids(ctx, view, g);
  drawBeacon(ctx, view, g);
  drawPredictor(ctx, view, g);
  for (const s of g.mission.arena.ships) drawShip(ctx, view, s, g);
  drawParticles(ctx, view, g);
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
    neonStroke(ctx, b.def.color, 1.8, () => circlePath(ctx, v, x, y, b.def.r));
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
  for (const f of g.mission.arena.def.fields) {
    ctx.setLineDash([10, 8]);
    lineStroke(ctx, f.color, 1.4, () => circlePath(ctx, v, f.x, f.y, f.r), 0.5);
    ctx.setLineDash([]);
    if (f.kind === 'wind') {
      const n = 14;
      lineStroke(ctx, f.color, 1.2, () => {
        for (let i = 0; i < n; i++) {
          const a = (i / n) * TAU;
          const rr = f.r * (0.25 + 0.6 * ((i * 7) % n) / n);
          const x0 = f.x + Math.cos(a) * rr;
          const y0 = f.y + Math.sin(a) * rr;
          const len = 55;
          const l = Math.hypot(f.ax ?? 1, f.ay ?? 0) || 1;
          proj(v, x0, y0);
          ctx.moveTo(P.x, P.y);
          proj(v, x0 + ((f.ax ?? 0) / l) * len, y0 + ((f.ay ?? 0) / l) * len);
          ctx.lineTo(P.x, P.y);
        }
      }, 0.35);
    }
    proj(v, f.x, f.y - f.r - 14);
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
    if (isNext) ctx.setLineDash([9, 6]);
    neonStroke(ctx, color, isNext ? 2.2 : 1.4, () => circlePath(ctx, v, gp.x, gp.y, gate.r), pulse);
    ctx.setLineDash([]);
    proj(v, gp.x, gp.y);
    if (P.x > -40 && P.x < v.w + 40 && P.y > -40 && P.y < v.h + 40) {
      ctx.globalAlpha = isNext ? 1 : 0.6;
      text(ctx, final ? 'META' : String(i + 1), P.x - 6, P.y + 4, color, isNext ? 13 : 11);
      ctx.globalAlpha = 1;
    }
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
    neonStroke(ctx, GOOD, 1.5, () => {
      ctx.moveTo(sx, sy - r);
      ctx.lineTo(sx + r, sy);
      ctx.lineTo(sx, sy + r);
      ctx.lineTo(sx - r, sy);
      ctx.closePath();
    });
  }
}

function drawAsteroids(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  const rocks = g.mission.arena.asteroids;
  neonStroke(ctx, BAD, 1.4, () => {
    for (const a of rocks) {
      if (!a.alive) continue;
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
  if (sx < -40 || sx > v.w + 40 || sy < -40 || sy > v.h + 40) return;
  const size = Math.max(18, SHIP_R * 2 * v.zoom * 1.1) / 14;
  const blink = s.invuln > 0 && Math.floor(g.clock * 12) % 2 === 0;
  ctx.save();
  ctx.translate(sx, sy);
  ctx.rotate(screenAngle(v, s.angle));
  ctx.scale(size, size);
  const px = 1 / size;
  neonStroke(ctx, s.color, 1.7 * px, () => {
    ctx.moveTo(10, 0);
    ctx.lineTo(-5, 5.5);
    ctx.lineTo(-3, 0);
    ctx.lineTo(-5, -5.5);
    ctx.closePath();
  }, blink ? 0.35 : 1);
  ctx.restore();
}

function drawParticles(ctx: CanvasRenderingContext2D, v: View, g: ArcadeGame): void {
  for (const p of g.particles) {
    proj(v, p.x, p.y);
    if (P.x < -10 || P.x > v.w + 10 || P.y < -10 || P.y > v.h + 10) continue;
    ctx.globalAlpha = Math.max(0, 1 - p.life / p.max);
    ctx.fillStyle = p.color;
    ctx.fillRect(P.x - p.size / 2, P.y - p.size / 2, p.size, p.size);
  }
  ctx.globalAlpha = 1;
}

/** Edge arrow towards something off screen. */
function edgeArrow(ctx: CanvasRenderingContext2D, v: View, wx: number, wy: number, color: string, label: string): void {
  proj(v, wx, wy);
  const sx = P.x;
  const sy = P.y;
  if (sx > 10 && sx < v.w - 10 && sy > 10 && sy < v.h - 10) return;
  const cx = v.w / 2;
  const cy = v.h / 2;
  const ang = Math.atan2(sy - cy, sx - cx);
  const k = Math.min((v.w / 2 - 70) / Math.abs(Math.cos(ang) || 1e-9), (v.h / 2 - 34) / Math.abs(Math.sin(ang) || 1e-9));
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
  const L = g.input.layout;
  const v = g.view;

  drawThrottle(ctx, g.input.throttle, L.throttleW, L.throttleTop, L.throttleBottom, g.liftoffThrottle());
  drawStick(ctx, g.input, L);

  // Left readout.
  const x = L.throttleW + 10;
  const speed = Math.hypot(p.vx, p.vy);
  text(ctx, 'CASCO', x, 20, COLORS.dim);
  meter(ctx, x + 48, 11, 90, p.hull / p.stats.hullMax, p.hull / p.stats.hullMax < 0.35 ? BAD : GOOD);
  text(ctx, 'COMB', x, 36, COLORS.dim);
  meter(ctx, x + 48, 27, 90, p.fuel / p.stats.fuelMax, p.fuel / p.stats.fuelMax < 0.2 ? BAD : AMBER);
  text(ctx, `VEL ${speed.toFixed(0)}`, x, 52, COLORS.hud);
  text(ctx, `VIDAS ${'♥'.repeat(Math.max(0, m.lives))}${m.practice ? ' ∞' : ''}`, x, 68, m.lives <= 1 && !m.practice ? BAD : COLORS.hud);
  text(ctx, `DATOS ${m.carried}`, x, 84, m.carried > 0 ? AMBER : COLORS.dim);

  // Top centre: stage, rings, time and the lead over the rival.
  const cx = (L.throttleW + 150 + width - 8 - 3 * 50 - 8) / 2;
  const ringTxt = `ETAPA ${m.stageIdx + 1} · ${m.def.name.toUpperCase()}`;
  text(ctx, ringTxt, cx, 18, AMBER, 12, true);
  const total = a.gates.length;
  text(ctx, `AROS ${Math.min(p.nextGate, total)}/${total}  ·  ${Math.max(0, a.clock).toFixed(1)} s`, cx, 34, COLORS.hud, 12, true);
  const lead = m.gateLead();
  let leadTxt = 'RIVAL AL PAR';
  let leadColor = COLORS.hud;
  if (a.clock < 0) {
    leadTxt = `${m.rival.name}`;
  } else if (lead > 0) {
    leadTxt = `ADELANTE +${lead} ${lead === 1 ? 'aro' : 'aros'}`;
    leadColor = GOOD;
  } else if (lead < 0) {
    leadTxt = `${m.rival.name} ADELANTE ${-lead} ${lead === -1 ? 'aro' : 'aros'}`;
    leadColor = '#ff2bd6';
  } else if (p.nextGate < total) {
    const gp = { x: 0, y: 0 };
    a.gatePos(p.nextGate, gp);
    const dp = Math.hypot(p.x - gp.x, p.y - gp.y);
    const dr = Math.hypot(m.rival.x - gp.x, m.rival.y - gp.y);
    leadTxt = dp <= dr ? 'VAS ADELANTE' : `${m.rival.name} VA ADELANTE`;
    leadColor = dp <= dr ? GOOD : '#ff2bd6';
  }
  text(ctx, leadTxt, cx, 50, leadColor, 12, true);

  // Buttons.
  const bw = 50;
  const bh = 34;
  const bx = width - 8 - 3 * bw - 8;
  btn(ctx, ui, 'pause', bx, 8, bw, bh, 'PAUSA');
  btn(ctx, ui, 'kit', bx + bw + 4, 8, bw, bh, `CÁP ${m.kits}`, { dim: m.kits <= 0 || m.kitCooldown > 0, color: GOOD });
  btn(ctx, ui, 'aim', bx + 2 * (bw + 4), 8, bw, bh, 'APUNTA', { on: g.autoAim });
  btn(ctx, ui, 'zoom', bx + 2 * (bw + 4), 8 + bh + 4, bw, bh, 'ZOOM', { on: !g.input.zoomManual });

  // Edge arrows.
  if (p.nextGate < total) {
    const gp = { x: 0, y: 0 };
    a.gatePos(p.nextGate, gp);
    edgeArrow(ctx, v, gp.x, gp.y, AMBER, `${Math.round(Math.hypot(gp.x - p.x, gp.y - p.y))}`);
  }
  if (m.rival.status !== 'dead') edgeArrow(ctx, v, m.rival.x, m.rival.y, '#ff2bd6', m.rival.name);
  const bp = m.beaconPos();
  if (bp) edgeArrow(ctx, v, bp.x, bp.y, AMBER, 'BALIZA');

  // Toasts.
  let y = height * 0.2;
  for (const t of g.toasts) {
    text(ctx, t.text, cx, y, t.kind === 'bad' ? BAD : t.kind === 'good' ? GOOD : COLORS.hud, 12, true);
    y += 16;
  }

  // Centre messages.
  if (a.clock < 0) {
    const n = Math.ceil(-a.clock);
    text(ctx, String(n), width / 2 - 20, height * 0.32, AMBER, 56, true);
    text(ctx, 'SUBÍ EL EMPUJE Y ESPERÁ LA SEÑAL', width / 2 - 20, height * 0.32 + 28, COLORS.hud, 12, true);
  } else if (a.clock < 0.8 && m.phase === 'race') {
    text(ctx, '¡YA!', width / 2 - 20, height * 0.32, GOOD, 52, true);
  }
  if (p.status === 'dead') {
    text(ctx, `NAVE PERDIDA · ${p.deathReason.toUpperCase()}`, width / 2 - 20, height * 0.42, BAD, 16, true);
    text(ctx, m.lives <= 0 && !m.practice ? 'SIN VIDAS' : `VIDAS RESTANTES: ${Math.max(0, m.lives)}`, width / 2 - 20, height * 0.42 + 22, COLORS.hud, 13, true);
  }
  void ROTATE_REACH;
}
