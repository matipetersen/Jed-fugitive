import { type Input } from '../input/input';
import { ROTATE_REACH } from '../input/layout';
import { PLANET, SHIP } from '../sim/params';
import { type OrbitElements } from '../sim/orbit';
import { type Prediction } from '../sim/predict';
import { CONTACT_RADIUS, type World } from '../sim/sim';
import { len } from '../sim/vec';
import { applyCamera, type Camera } from './camera';
import { COLORS, neonStroke } from './neon';

export interface Frame {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  dpr: number;
  time: number;
  world: World;
  camera: Camera;
  prediction: Prediction;
  orbit: OrbitElements;
  input: Input;
  hasFlown: boolean;
}

const TAU = Math.PI * 2;

export function drawFrame(f: Frame): void {
  const { ctx, width, height, dpr } = f;
  ctx.globalCompositeOperation = 'source-over';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#02020a';
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  drawStars(f);

  applyCamera(ctx, f.camera, width, height, dpr);
  const unit = 1 / f.camera.zoom;
  drawPlanet(f, unit);
  drawPrediction(f, unit);
  drawMarkers(f, unit);
  drawShip(f, unit);

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  drawControls(f);
  drawHud(f);
}

function drawStars(f: Frame): void {
  const { ctx, width, height, camera } = f;
  ctx.setTransform(f.dpr, 0, 0, f.dpr, 0, 0);
  ctx.strokeStyle = '#6a8cff';
  ctx.lineWidth = 1;
  // Deterministic scatter; drifts slightly with the camera for parallax.
  let seed = 1234567;
  const rnd = (): number => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const ox = camera.center.x * 0.01;
  const oy = camera.center.y * 0.01;
  for (let i = 0; i < 90; i++) {
    const x = (((rnd() * width - ox) % width) + width) % width;
    const y = (((rnd() * height + oy) % height) + height) % height;
    const a = 0.15 + rnd() * 0.45;
    ctx.globalAlpha = a;
    ctx.beginPath();
    ctx.moveTo(x - 1.5, y);
    ctx.lineTo(x + 1.5, y);
    ctx.moveTo(x, y - 1.5);
    ctx.lineTo(x, y + 1.5);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

function drawPlanet(f: Frame, unit: number): void {
  const { ctx, camera } = f;
  const R = PLANET.radius;
  neonStroke(ctx, COLORS.planet, 1.6, unit, () => ctx.arc(0, 0, R, 0, TAU));

  if (camera.zoom > 0.12) {
    // Hatching under the surface gives a sense of motion near the ground.
    const depth = Math.min(18, 60 / camera.zoom);
    neonStroke(ctx, COLORS.planet, 1, unit, () => {
      for (let i = 0; i < 360; i++) {
        const a = (i / 360) * TAU;
        const c = Math.cos(a);
        const s = Math.sin(a);
        ctx.moveTo(c * R, s * R);
        ctx.lineTo(c * (R - depth), s * (R - depth));
      }
    }, Math.min(0.5, camera.zoom * 2));
  }

  // Launch pad at the top of the planet.
  neonStroke(ctx, COLORS.marker, 2, unit, () => {
    ctx.moveTo(-26, R + 1);
    ctx.lineTo(26, R + 1);
  });
}

function drawPrediction(f: Frame, unit: number): void {
  const { ctx, prediction: p, world } = f;
  if (world.ship.status !== 'flying' || p.count < 2) return;
  ctx.setLineDash([10 * unit, 7 * unit]);
  neonStroke(ctx, p.impact ? COLORS.danger : COLORS.path, 1.2, unit, () => {
    ctx.moveTo(p.points[0]!, p.points[1]!);
    for (let i = 1; i < p.count; i++) ctx.lineTo(p.points[i * 2]!, p.points[i * 2 + 1]!);
  }, 0.5);
  ctx.setLineDash([]);
}

function drawMarkers(f: Frame, unit: number): void {
  const { ctx, orbit, world } = f;
  if (world.ship.status !== 'flying') return;
  const mark = (x: number, y: number, label: string): void => {
    const s = 7 * unit;
    neonStroke(ctx, COLORS.marker, 1.4, unit, () => {
      ctx.moveTo(x, y + s);
      ctx.lineTo(x + s, y);
      ctx.lineTo(x, y - s);
      ctx.lineTo(x - s, y);
      ctx.closePath();
    });
    labelWorld(f, x, y, label);
  };
  if (orbit.periapsis > CONTACT_RADIUS) {
    mark(orbit.periDir.x * orbit.periapsis, orbit.periDir.y * orbit.periapsis, 'PE');
  }
  if (orbit.apoapsis !== null) {
    mark(-orbit.periDir.x * orbit.apoapsis, -orbit.periDir.y * orbit.apoapsis, 'AP');
  }
}

/** Draws screen-space text next to a world point. */
function labelWorld(f: Frame, wx: number, wy: number, text: string): void {
  const { ctx, camera, width, height, dpr } = f;
  const theta = Math.PI / 2 - camera.up;
  const qx = (wx - camera.center.x) * camera.zoom;
  const qy = (wy - camera.center.y) * camera.zoom;
  const sx = width / 2 + Math.cos(theta) * qx - Math.sin(theta) * qy;
  const sy = height / 2 - (Math.sin(theta) * qx + Math.cos(theta) * qy);
  ctx.save();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = COLORS.marker;
  ctx.font = '11px ui-monospace, Menlo, monospace';
  ctx.fillText(text, sx + 11, sy - 9);
  ctx.restore();
}

function drawShip(f: Frame, unit: number): void {
  const { ctx, world, camera, time } = f;
  const ship = world.ship;
  if (ship.status === 'crashed') {
    drawWreck(f, unit);
    return;
  }
  const s = Math.max(1, 30 / (14 * camera.zoom));
  ctx.save();
  ctx.translate(ship.pos.x, ship.pos.y);
  ctx.rotate(ship.angle);
  ctx.scale(s, s);
  const u = unit / s;
  neonStroke(ctx, COLORS.ship, 1.6, u, () => {
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
  if (ship.throttle > 0) {
    const flicker = 0.75 + 0.25 * Math.sin(time * 70) * Math.cos(time * 41);
    const l = 6 + 16 * ship.throttle * flicker;
    neonStroke(ctx, '#ffb000', 1.4, u, () => {
      ctx.moveTo(-4, 3);
      ctx.lineTo(-4 - l, 0);
      ctx.lineTo(-4, -3);
    });
  }
  ctx.restore();
}

function drawWreck(f: Frame, unit: number): void {
  const { ctx, world, time } = f;
  const p = world.ship.pos;
  neonStroke(ctx, COLORS.danger, 1.6, unit, () => {
    for (let i = 0; i < 9; i++) {
      const a = (i / 9) * TAU + 0.3;
      const r1 = 6 + Math.sin(time * 5 + i) * 2;
      const r2 = 18 + 8 * ((i * 7) % 3);
      ctx.moveTo(p.x + Math.cos(a) * r1, p.y + Math.sin(a) * r1);
      ctx.lineTo(p.x + Math.cos(a) * r2, p.y + Math.sin(a) * r2);
    }
  });
}

function drawControls(f: Frame): void {
  const { ctx, input } = f;
  const L = input.layout;
  const t = L.throttleTrack;

  // Throttle slider.
  neonStroke(ctx, COLORS.hud, 1.4, 1, () => {
    ctx.moveTo(t.x, t.top);
    ctx.lineTo(t.x, t.bottom);
    for (const k of [0, 0.5, 1]) {
      const y = t.bottom - (t.bottom - t.top) * k;
      ctx.moveTo(t.x - 8, y);
      ctx.lineTo(t.x + 8, y);
    }
  }, 0.5);
  const hy = t.bottom - (t.bottom - t.top) * input.throttle;
  neonStroke(ctx, input.throttle > 0 ? COLORS.marker : COLORS.hud, 1.8, 1, () => {
    ctx.rect(t.x - 18, hy - 8, 36, 16);
  });
  ctx.fillStyle = COLORS.hud;
  ctx.font = '11px ui-monospace, Menlo, monospace';
  ctx.fillText('THR', t.x - 12, t.top - 8);
  ctx.fillText(`${Math.round(input.throttle * 100)}%`, t.x - 12, t.bottom + 18);

  // Rotation stick.
  const stick = input.stick;
  const ox = stick ? stick.ox : L.rotateHome.x;
  const oy = stick ? stick.oy : L.rotateHome.y;
  neonStroke(ctx, COLORS.hud, 1.2, 1, () => {
    ctx.arc(ox, oy, ROTATE_REACH * 0.5, 0, TAU);
    ctx.moveTo(ox - ROTATE_REACH, oy);
    ctx.lineTo(ox - ROTATE_REACH + 10, oy - 6);
    ctx.moveTo(ox - ROTATE_REACH, oy);
    ctx.lineTo(ox - ROTATE_REACH + 10, oy + 6);
    ctx.moveTo(ox + ROTATE_REACH, oy);
    ctx.lineTo(ox + ROTATE_REACH - 10, oy - 6);
    ctx.moveTo(ox + ROTATE_REACH, oy);
    ctx.lineTo(ox + ROTATE_REACH - 10, oy + 6);
  }, stick ? 1 : 0.55);
  if (stick) {
    const kx = ox + Math.max(-ROTATE_REACH, Math.min(ROTATE_REACH, stick.x - ox));
    neonStroke(ctx, COLORS.marker, 1.8, 1, () => ctx.arc(kx, oy, 12, 0, TAU));
  }

  // Autopilot buttons.
  for (const b of L.buttons) {
    const on = input.autopilot === b.id;
    neonStroke(ctx, on ? COLORS.marker : COLORS.hud, 1.4, 1, () => ctx.rect(b.x, b.y, b.w, b.h), on ? 0.9 : 0.4);
    ctx.fillStyle = on ? COLORS.marker : COLORS.hud;
    ctx.font = '13px ui-monospace, Menlo, monospace';
    ctx.fillText(b.label, b.x + 16, b.y + 24);
  }
}

function drawHud(f: Frame): void {
  const { ctx, world, orbit, width, height, input } = f;
  const ship = world.ship;
  const r = len(ship.pos);
  const radial = (ship.pos.x * ship.vel.x + ship.pos.y * ship.vel.y) / r;
  const speed = len(ship.vel);
  const tangential = Math.sqrt(Math.max(0, speed * speed - radial * radial));
  const alt = r - CONTACT_RADIUS;
  const pe = orbit.periapsis - PLANET.radius;
  const ap = orbit.apoapsis !== null ? orbit.apoapsis - PLANET.radius : null;

  const x = Math.max(124, input.layout.throttleZone.w + 12);
  const rows: [string, string][] = [
    ['ALT', alt.toFixed(0)],
    ['V.RAD', radial.toFixed(1)],
    ['V.TAN', tangential.toFixed(1)],
    ['COMB', `${((ship.fuel / SHIP.fuelMass) * 100).toFixed(0)}%`],
    ['AP', ap === null ? '--' : ap.toFixed(0)],
    ['PE', pe < 0 ? 'SUELO' : pe.toFixed(0)],
    ['T', world.time.toFixed(0)],
  ];
  ctx.font = '12px ui-monospace, Menlo, monospace';
  ctx.globalAlpha = 0.95;
  rows.forEach(([k, v], i) => {
    ctx.fillStyle = COLORS.dim;
    ctx.fillText(k, x, 24 + i * 16);
    ctx.fillStyle = k === 'PE' && pe < 0 && ship.status === 'flying' ? COLORS.danger : COLORS.hud;
    ctx.fillText(v, x + 52, 24 + i * 16);
  });

  const centre = (text: string, y: number, color: string): void => {
    ctx.font = '15px ui-monospace, Menlo, monospace';
    ctx.fillStyle = color;
    ctx.fillText(text, width / 2 - ctx.measureText(text).width / 2, y);
  };
  if (ship.status === 'crashed') {
    centre(`ESTRELLADO  (${ship.impactSpeed.toFixed(0)} u/s)`, height * 0.4, COLORS.danger);
    centre('TOCA PARA REINICIAR', height * 0.4 + 24, COLORS.hud);
  } else if (ship.status === 'landed') {
    if (f.hasFlown) centre(`ATERRIZAJE CORRECTO  (${ship.impactSpeed.toFixed(1)} u/s)`, height * 0.4, COLORS.path);
    else centre('SUBE EL ACELERADOR (IZQ) PARA DESPEGAR', height * 0.4, COLORS.hud);
  }
  if (height > width) centre('GIRA EL TELEFONO A HORIZONTAL', height * 0.12, COLORS.marker);
  ctx.globalAlpha = 1;
}
