import { type Flight, type HudData } from '../game/flight';
import { ROTATE_REACH } from '../input/input';
import { type Ui } from '../ui/ui';
import { COLORS, neonStroke } from './neon';
import { TAU } from '../sim/units';

const FONT = '12px ui-monospace, Menlo, monospace';

interface BtnOpts {
  on?: boolean;
  dim?: boolean;
  repeat?: boolean;
  color?: string;
}

function btn(ctx: CanvasRenderingContext2D, ui: Ui, id: string, x: number, y: number, w: number, h: number, label: string, o: BtnOpts = {}): void {
  ui.register(id, { x, y, w, h }, o.repeat ?? false);
  const color = o.color ?? (o.on ? COLORS.marker : COLORS.hud);
  neonStroke(ctx, color, 1.3, () => ctx.rect(x, y, w, h), o.on ? 0.95 : o.dim ? 0.25 : 0.5);
  ctx.fillStyle = color;
  ctx.globalAlpha = o.dim ? 0.5 : 1;
  ctx.font = FONT;
  ctx.fillText(label, x + (w - ctx.measureText(label).width) / 2, y + h / 2 + 4);
  ctx.globalAlpha = 1;
}

function text(ctx: CanvasRenderingContext2D, s: string, x: number, y: number, color: string, size = 12, center = false): void {
  ctx.font = `${size}px ui-monospace, Menlo, monospace`;
  ctx.fillStyle = color;
  const w = center ? ctx.measureText(s).width / 2 : 0;
  ctx.fillText(s, x - w, y);
}

export function drawHud(ctx: CanvasRenderingContext2D, f: Flight, width: number, height: number): void {
  const ui = f.ui;
  const input = f.input;
  const L = input.layout;
  const h = f.hud();

  drawThrottle(ctx, input.throttle, L.throttleW, L.throttleTop, L.throttleBottom, h.liftoff);
  drawStick(ctx, input, L);
  drawReadout(ctx, h, L.throttleW + 10);
  drawButtons(ctx, ui, f, h, width);
  drawContext(ctx, ui, f, width, height, L.throttleW, L.rotateX);
  if (f.nodePanel && h.node) drawNodePanel(ctx, ui, f, h, width, height, L.throttleW, L.rotateX);
  drawAlerts(ctx, f, h, width, height);
  if (h.coach) drawCoach(ctx, h.coach, L.throttleW + 8, L.rotateX - 8, f.nodePanel, f.contextActions().length > 0, height);
  ui.commit();
}

function drawThrottle(ctx: CanvasRenderingContext2D, thr: number, zoneW: number, top: number, bottom: number, liftoff: number | null): void {
  const x = zoneW / 2;
  neonStroke(ctx, COLORS.hud, 1.3, () => {
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    for (const k of [0, 0.25, 0.5, 0.75, 1]) {
      const y = bottom - (bottom - top) * k;
      ctx.moveTo(x - (k % 0.5 === 0 ? 9 : 5), y);
      ctx.lineTo(x + (k % 0.5 === 0 ? 9 : 5), y);
    }
  }, 0.5);
  if (liftoff !== null) {
    // Mark the throttle the engine needs just to leave the ground.
    const ok = liftoff <= 1;
    const my = bottom - (bottom - top) * Math.min(1, liftoff);
    neonStroke(ctx, ok ? COLORS.good : COLORS.danger, 1.6, () => {
      ctx.moveTo(x - 26, my);
      ctx.lineTo(x + 26, my);
    });
    text(ctx, ok ? 'DESPEGUE' : 'NO LEVANTA', x + 28 > zoneW - 30 ? 2 : x + 28, my - 4, ok ? COLORS.good : COLORS.danger, 9);
  }
  const hy = bottom - (bottom - top) * thr;
  neonStroke(ctx, thr > 0 ? COLORS.marker : COLORS.hud, 1.8, () => ctx.rect(x - 18, hy - 8, 36, 16));
  text(ctx, 'EMPUJE', x - 20, top - 10, COLORS.hud, 10);
  text(ctx, `${Math.round(thr * 100)}%`, x - 12, bottom + 18, COLORS.hud, 11);
}

function drawStick(ctx: CanvasRenderingContext2D, input: Flight['input'], L: Flight['input']['layout']): void {
  const stick = input.stick;
  const ox = stick ? stick.ox : L.rotateHomeX;
  const oy = stick ? stick.oy : L.rotateHomeY;
  neonStroke(ctx, COLORS.hud, 1.2, () => {
    ctx.moveTo(ox + ROTATE_REACH * 0.5, oy);
    ctx.arc(ox, oy, ROTATE_REACH * 0.5, 0, TAU);
    for (const s of [-1, 1]) {
      const ex = ox + s * ROTATE_REACH;
      ctx.moveTo(ex - s * 10, oy - 6);
      ctx.lineTo(ex, oy);
      ctx.lineTo(ex - s * 10, oy + 6);
    }
  }, stick ? 1 : 0.5);
  if (stick) {
    const kx = ox + Math.max(-ROTATE_REACH, Math.min(ROTATE_REACH, stick.x - ox));
    neonStroke(ctx, COLORS.marker, 1.8, () => {
      ctx.moveTo(kx + 12, oy);
      ctx.arc(kx, oy, 12, 0, TAU);
    });
  } else text(ctx, 'GIRO', ox - 14, oy + ROTATE_REACH * 0.5 + 16, COLORS.dim, 10);
}

function drawReadout(ctx: CanvasRenderingContext2D, h: HudData, x: number): void {
  const rows: [string, string, string?][] = [
    ['REF', h.ref],
    [h.altLabel, h.alt],
    ['VEL', h.speed],
    ['RAD', h.radial],
    ['TAN', h.tangential],
    ['AP', h.ap],
    ['PE', h.pe, h.peDanger ? COLORS.danger : undefined],
    ['COMB', `${h.fuelPct}%  ΔV ${h.dv}`, h.fuelPct < 10 ? COLORS.danger : undefined],
  ];
  ctx.font = FONT;
  ctx.globalAlpha = 0.95;
  rows.forEach(([k, v, c], i) => {
    text(ctx, k, x, 22 + i * 15, COLORS.dim);
    text(ctx, v, x + 46, 22 + i * 15, c ?? COLORS.hud);
  });
  let y = 22 + rows.length * 15;
  if (h.heat > 0.02) {
    text(ctx, 'CALOR', x, y, COLORS.dim);
    meter(ctx, x + 46, y - 9, 70, h.heat, h.heat > 0.7 ? COLORS.danger : COLORS.marker);
    y += 15;
  }
  if (h.hull < 99.5) {
    text(ctx, 'CASCO', x, y, COLORS.dim);
    meter(ctx, x + 46, y - 9, 70, h.hull / 100, h.hull < 40 ? COLORS.danger : COLORS.good);
    y += 15;
  }
  text(ctx, h.date, x, y, COLORS.hud);
  const warpTxt = h.warp > 1 ? `  x${h.warp >= 1000 ? `${h.warp / 1000}k` : h.warp}${h.warpEff < h.warp * 0.9 && h.warp > 1 ? ` (${Math.round(h.warpEff)})` : ''}` : '';
  text(ctx, warpTxt, x + 76, y, h.warp > 1 ? COLORS.marker : COLORS.hud);
  ctx.globalAlpha = 1;
}

function meter(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, frac: number, color: string): void {
  const n = 10;
  neonStroke(ctx, color, 1.1, () => {
    for (let i = 0; i < n; i++) {
      if (i / n < Math.min(1, frac)) {
        ctx.moveTo(x + (w * i) / n, y);
        ctx.lineTo(x + (w * i) / n, y + 8);
      }
    }
  }, 0.9);
  neonStroke(ctx, COLORS.dim, 1, () => ctx.rect(x - 2, y - 2, w + 2, 12), 0.5);
}

function drawButtons(ctx: CanvasRenderingContext2D, ui: Ui, f: Flight, h: HudData, width: number): void {
  const bw = 46;
  const bh = 32;
  const gap = 4;
  const x0 = width - 8 - 4 * bw - 3 * gap;
  const cell = (r: number, c: number): [number, number] => [x0 + c * (bw + gap), 8 + r * (bh + gap)];
  const ap = h.autopilot;
  let [x, y] = cell(0, 0);
  btn(ctx, ui, 'pro', x, y, bw, bh, 'PRO', { on: ap === 'prograde' });
  [x, y] = cell(0, 1);
  btn(ctx, ui, 'ret', x, y, bw, bh, 'RET', { on: ap === 'retrograde' });
  [x, y] = cell(0, 2);
  btn(ctx, ui, 'node', x, y, bw, bh, 'NODO', { on: f.nodePanel });
  [x, y] = cell(0, 3);
  btn(ctx, ui, 'menu', x, y, bw, bh, 'MENU');
  [x, y] = cell(1, 0);
  btn(ctx, ui, 'wdn', x, y, bw, bh, 'W−');
  [x, y] = cell(1, 1);
  btn(ctx, ui, 'wup', x, y, bw, bh, 'W+', { on: h.warp > 1 });
  [x, y] = cell(1, 2);
  btn(ctx, ui, 'frame', x, y, bw, bh, 'MARCO', { on: f.frameIdx !== 0 });
  [x, y] = cell(1, 3);
  btn(ctx, ui, 'tgt', x, y, bw, bh, 'OBJ', { on: f.target >= 0 });
  [x, y] = cell(2, 0);
  btn(ctx, ui, 'zout', x, y, bw, bh, '−', { repeat: true });
  [x, y] = cell(2, 1);
  btn(ctx, ui, 'zin', x, y, bw, bh, '+', { repeat: true });
  [x, y] = cell(2, 2);
  btn(ctx, ui, 'zauto', x, y, bw, bh, 'ZOOM', { on: !f.input.zoomManual });
  [x, y] = cell(2, 3);
  btn(ctx, ui, 'foc', x, y, bw, bh, 'FOCO', { on: f.focusTarget });
  [x, y] = cell(3, 3);
  btn(ctx, ui, 'hor', x, y, bw, bh, h.horizon === 'AUTO' ? 'PRED' : h.horizon, { on: h.horizon !== 'AUTO' });
  // Frame/target readout under the buttons.
  text(ctx, `MARCO ${h.frame}`, x0 - 4, 8 + 4 * (bh + gap) + 8, COLORS.dim, 10);
  text(ctx, `OBJ ${h.target}`, x0 - 4, 8 + 4 * (bh + gap) + 21, h.target === '--' ? COLORS.dim : COLORS.marker, 10);
  if (h.closest) text(ctx, h.closest, x0 - 4, 8 + 4 * (bh + gap) + 34, COLORS.marker, 10);
}

function drawContext(ctx: CanvasRenderingContext2D, ui: Ui, f: Flight, width: number, height: number, left: number, right: number): void {
  const acts = f.contextActions();
  if (acts.length === 0) return;
  const bw = 88;
  const bh = 34;
  const total = acts.length * bw + (acts.length - 1) * 6;
  let x = left + (right - left - total) / 2;
  const y = height - bh - 10;
  for (const a of acts) {
    btn(ctx, ui, a.id, x, y, bw, bh, a.label, { color: COLORS.good });
    x += bw + 6;
  }
  void width;
}

function drawNodePanel(
  ctx: CanvasRenderingContext2D,
  ui: Ui,
  f: Flight,
  h: HudData,
  width: number,
  height: number,
  left: number,
  right: number,
): void {
  const n = h.node!;
  const hasCtx = f.contextActions().length > 0;
  const availW = Math.min(440, right - left - 16);
  const x0 = left + (right - left - availW) / 2;
  const bh = 30;
  const panelH = 18 + 2 * (bh + 4);
  const y0 = height - (hasCtx ? 52 : 12) - panelH;
  neonStroke(ctx, COLORS.marker, 1, () => ctx.rect(x0 - 4, y0 - 4, availW + 8, panelH + 4), 0.35);
  const head = `NODO T${n.tPast ? '+' : '-'}${n.tMinus.replace('-', '')}  PRO ${n.pro}  RAD ${n.rad}${n.remaining !== null ? `  ΔV REST ${n.remaining}` : ''}`;
  text(ctx, head, x0, y0 + 10, COLORS.marker, 11);
  const row1 = y0 + 18;
  const w1 = Math.floor((availW - 7 * 4) / 8);
  const b1: [string, string, BtnOpts?][] = [
    ['nt-', 'T−', { repeat: true }],
    ['nt+', 'T+', { repeat: true }],
    ['nts', n.tStep],
    ['np-', 'P−', { repeat: true }],
    ['np+', 'P+', { repeat: true }],
    ['nr-', 'R−', { repeat: true }],
    ['nr+', 'R+', { repeat: true }],
    ['nds', `Δ${n.dvStep}`],
  ];
  b1.forEach(([id, label, o], i) => btn(ctx, ui, id, x0 + i * (w1 + 4), row1, w1, bh, label, o));
  const row2 = row1 + bh + 4;
  const w2 = Math.floor((availW - 5 * 4) / 6);
  const b2: [string, string, BtnOpts?][] = [
    ['nauto', 'AUTO', { color: COLORS.good }],
    ['ncirc', 'CIRC', { color: COLORS.good }],
    ['nref', 'REFINA', { color: COLORS.good }],
    ['nburn', 'QUEMA', { on: n.aiming, color: COLORS.good }],
    ['nwarp', 'IR NODO'],
    ['ndel', 'BORRAR', { color: COLORS.danger }],
  ];
  b2.forEach(([id, label, o], i) => btn(ctx, ui, id, x0 + i * (w2 + 4), row2, w2, bh, label, o));
  void width;
}

function drawAlerts(ctx: CanvasRenderingContext2D, f: Flight, h: HudData, width: number, height: number): void {
  const cx = width / 2 - 20;
  let y = 24;
  for (const a of f.alerts) {
    text(ctx, a.text, cx, y, a.kind === 'bad' ? COLORS.danger : COLORS.hud, 14, true);
    y += 18;
  }
  for (const t of f.toasts) {
    text(ctx, t.text, cx, y, t.kind === 'bad' ? COLORS.danger : t.kind === 'good' ? COLORS.good : COLORS.hud, 13, true);
    y += 17;
  }
  const mid = height * 0.4;
  if (h.status === 'crashed') {
    const why: Record<string, string> = {
      speed: 'DEMASIADO RÁPIDO',
      tilt: 'MAL INCLINADA',
      slope: 'TERRENO EMPINADO',
      burn: 'CONSUMIDA POR EL CALOR',
      crush: 'APLASTADA POR LA PRESIÓN',
      sun: 'INCINERADA POR EL SOL',
      asteroid: 'IMPACTO DE ASTEROIDE',
      hull: 'CASCO DESTRUIDO',
      abandoned: 'ABANDONADA',
    };
    text(ctx, `NAVE PERDIDA · ${why[h.crashReason] ?? h.crashReason.toUpperCase()} (${h.impactSpeed.toFixed(0)} u/s)`, cx, mid, COLORS.danger, 15, true);
    text(ctx, 'TOCÁ EL CENTRO O MENU', cx, mid + 22, COLORS.hud, 13, true);
  } else if (h.status === 'landed' && f.hasFlown) {
    text(ctx, `ATERRIZAJE CORRECTO (${h.impactSpeed.toFixed(1)} u/s)`, cx, mid, COLORS.good, 15, true);
  } else if (h.status === 'landed') {
    text(ctx, 'SUBÍ EL EMPUJE (IZQUIERDA) PARA DESPEGAR', cx, mid, COLORS.hud, 14, true);
  }
  if (height > width) text(ctx, 'GIRÁ EL TELÉFONO A HORIZONTAL', cx, height * 0.12, COLORS.marker, 14, true);
}

/** One-line advice near the bottom, wrapped to the free width between the two control zones. */
function drawCoach(ctx: CanvasRenderingContext2D, msg: string, left: number, right: number, panelOpen: boolean, hasCtx: boolean, height: number): void {
  ctx.font = '12px ui-monospace, Menlo, monospace';
  const maxW = Math.max(160, right - left);
  const words = msg.split(' ');
  const lines: string[] = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? `${cur} ${w}` : w;
    if (ctx.measureText(t).width > maxW && cur) {
      lines.push(cur);
      cur = w;
    } else cur = t;
  }
  if (cur) lines.push(cur);
  const base = height - (panelOpen ? 150 : hasCtx ? 58 : 14) - (lines.length - 1) * 15;
  const cx = left + maxW / 2;
  lines.forEach((l, i) => text(ctx, l, cx, base + i * 15, COLORS.marker, 12, true));
}
