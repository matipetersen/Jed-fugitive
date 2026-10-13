import { type BodyDef, type GateDef, type RaceDef } from './types';
import { d2r, pad, stage } from './build';

const R = (n: number): number => Math.round(n);

/** A gas giant at the origin, with the start pad facing `padDeg`. */
const giant = (name: string, r: number, g: number, color: string, padDeg: number): BodyDef => ({
  id: 'gigante',
  name,
  r,
  g,
  color,
  x: 0,
  y: 0,
  atm: { h: 90, drag: 0.002 },
  pads: [pad(`Base ${name}`, true, 60, padDeg), pad('Parrilla rival', false, 60, padDeg + 28)],
});

/** The outpost at the end of the lane, `dist` from the giant along `deg`. */
const outpost = (dist: number, deg: number): BodyDef => ({
  id: 'puesto',
  name: 'Puesto avanzado',
  r: 70,
  g: 40,
  color: '#7dff6b',
  x: R(Math.cos(deg * d2r) * dist),
  y: R(Math.sin(deg * d2r) * dist),
  pads: [pad('Puesto', true, 44, deg + 180)],
});

/** Wide gates along the straight lane from the giant to the outpost; the last one is the finish line. */
function lane(r0: number, dist: number, deg: number, n: number): GateDef[] {
  const out: GateDef[] = [];
  const a = deg * d2r;
  for (let i = 0; i < n; i++) {
    const d = r0 + 420 + ((dist - 260 - (r0 + 420)) * i) / (n - 1);
    // A slight weave so it is not a ruler-straight line.
    const w = Math.sin(i * 1.7) * 120;
    out.push({ x: R(Math.cos(a) * d - Math.sin(a) * w), y: R(Math.sin(a) * d + Math.cos(a) * w), r: 52, final: i === n - 1 });
  }
  return out;
}

const rocks = (count: number, seed: number, rIn: number, rOut: number, speed: number, size: [number, number] = [6, 13]): NonNullable<Parameters<typeof stage>[0]['asteroids']>[number] => ({ count, seed, around: 'gigante', rIn, rOut, size, speed });

const s1 = stage({
  id: 1,
  name: 'Anillos de Júpiter',
  blurb: 'Salís de la base más pesada del sistema y los anillos están justo encima. Cien rocas en órbita cruzan tu camino: no frenes, esquivá.',
  skulls: 3,
  bodies: [giant('Júpiter', 520, 112, '#ff9a5a', 90), outpost(5000, 90)],
  gates: lane(520, 5000, 90, 7),
  asteroids: [rocks(270, 401, 820, 2400, 1.0), rocks(180, 402, 820, 2400, -0.9)],
  cells: [{ x: 120, y: 1700, fuel: 30 }, { x: -100, y: 3300, fuel: 30 }],
  start: { body: 'gigante', angle: 90 * d2r },
  rivalStart: { body: 'gigante', angle: 118 * d2r },
  sprint: true,
  rival: { skill: 0.95, name: 'Cometa Roja', delay: 4, ai: { noise: 0.12, interval: 0.15 } },
  finish: { body: 'puesto', pad: 0 },
  par: 40,
  kind: 'Sprint',
});

const s2 = stage({
  id: 2,
  name: 'Tormenta de escombros',
  blurb: 'Saturno se rompió hace millones de años y todavía tira pedazos. El doble de rocas, muchas de frente, y el puesto más lejos.',
  skulls: 4,
  bodies: [giant('Saturno', 540, 118, '#ffe0a0', 180), outpost(6200, 180)],
  gates: lane(540, 6200, 180, 8),
  asteroids: [rocks(430, 411, 840, 2800, 1.0), rocks(320, 412, 840, 2800, -0.85)],
  cells: [{ x: -1500, y: 150, fuel: 30 }, { x: -4000, y: -120, fuel: 30 }],
  start: { body: 'gigante', angle: 180 * d2r },
  rivalStart: { body: 'gigante', angle: 208 * d2r },
  sprint: true,
  rival: { skill: 0.96, name: 'Aguja', delay: 4, ai: { noise: 0.1, interval: 0.15 } },
  finish: { body: 'puesto', pad: 0 },
  par: 48,
  kind: 'Sprint',
});

const s3 = stage({
  id: 3,
  name: 'El muro',
  blurb: 'Un gigante helado rodeado de escombros que van en todas direcciones, algunos más rápido de lo que podés ir. Es el sprint más largo y más cargado.',
  skulls: 5,
  bodies: [giant('Neptuno', 560, 124, '#4b8bff', -35), outpost(7200, -35)],
  gates: lane(560, 7200, -35, 9),
  asteroids: [rocks(520, 421, 860, 3200, 1.0), rocks(380, 422, 860, 3200, -0.9), rocks(200, 423, 860, 3200, 1.38, [5, 10])],
  cells: [{ x: 1900, y: -1300, fuel: 30 }, { x: 4200, y: -2900, fuel: 30 }],
  start: { body: 'gigante', angle: -35 * d2r },
  rivalStart: { body: 'gigante', angle: -7 * d2r },
  sprint: true,
  tank: 0.9,
  rival: { skill: 0.97, name: 'Relámpago', delay: 4, ai: { noise: 0.08, interval: 0.12 } },
  finish: { body: 'puesto', pad: 0 },
  par: 55,
  kind: 'Sprint',
});

export const SPRINT: RaceDef = {
  id: 'sprint',
  name: 'SPRINT DEL GIGANTE',
  subtitle: 'Despegá de un gigante gaseoso y cruzá el campo de asteroides',
  blurb: 'Tres sprints de velocidad pura: salís de un planeta gigante, atravesás cientos de rocas en órbita y cruzás la línea sin aterrizar. Gana el que no frena y no choca.',
  stages: [s1, s2, s3],
};

const GIANTS: [string, string][] = [['Júpiter', '#ff9a5a'], ['Saturno', '#ffe0a0'], ['Neptuno', '#4b8bff'], ['Urano', '#7dffe8'], ['Kepler-9', '#ff2bd6']];

/** A sprint made on demand; d is difficulty (0 easy .. 1 brutal): more rocks, farther, more rocks flying head-on. */
export function makeSprintStage(seed: number, d: number): StageDefLike {
  const r = (k: number): number => {
    const x = Math.sin(seed * 12.9898 + k * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };
  const [name, color] = GIANTS[Math.floor(r(1) * GIANTS.length)];
  const deg = Math.round(r(2) * 360);
  const dist = R(4500 + 2800 * d);
  const rad = 520 + Math.round(r(3) * 60);
  const total = R(300 + 800 * d);
  const head = Math.round(total * (0.35 + 0.1 * d));
  const fast = d > 0.6 ? Math.round(total * 0.15) : 0;
  const specs = [rocks(total - head - fast, seed + 1, 820, 2400 + 900 * d, 1.0), rocks(head, seed + 2, 820, 2400 + 900 * d, -0.9)];
  if (fast) specs.push(rocks(fast, seed + 3, 820, 2400 + 900 * d, 1.38, [5, 10]));
  return stage({
    id: 1,
    name: `Sprint ${name}`,
    blurb: `Salís de ${name} y atravesás ${total} asteroides en órbita hasta el puesto, a ${dist} unidades. Cruzar el último aro termina la carrera.`,
    skulls: Math.max(2, Math.min(5, 2 + Math.round(d * 3))),
    bodies: [giant(name, rad, 110 + Math.round(r(4) * 14), color, deg), outpost(dist, deg)],
    gates: lane(rad, dist, deg, 7 + Math.round(d * 2)),
    asteroids: specs,
    cells: [{ x: R(Math.cos(deg * d2r) * 1700), y: R(Math.sin(deg * d2r) * 1700), fuel: 30 }],
    start: { body: 'gigante', angle: deg * d2r },
    rivalStart: { body: 'gigante', angle: (deg + 28) * d2r },
    sprint: true,
    rival: { skill: 0.94 + 0.03 * d, name: pickName(r(5)), delay: 4, ai: { noise: 0.13 - 0.05 * d, interval: 0.15 } },
    finish: { body: 'puesto', pad: 0 },
    par: 38 + R(17 * d),
    kind: 'Sprint',
  });
}

const RIVAL_NAMES = ['Cometa Roja', 'Aguja', 'Relámpago', 'Fantasma', 'Víbora', 'Sombra'];
const pickName = (x: number): string => RIVAL_NAMES[Math.floor(x * RIVAL_NAMES.length)];
type StageDefLike = ReturnType<typeof stage>;
