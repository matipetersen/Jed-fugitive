import { type BodyDef, type GateDef, type RaceDef } from './types';
import { d2r, near, pad, stage } from './build';

const deg = (a: number): number => a * d2r;
const R = (n: number): number => Math.round(n);

/**
 * Gates that wrap a planet: the ship comes in on `hIn`, leaves on `hOut` (headings in degrees) and
 * the planet sits on the inside of the turn, which is where gravity bends the path for free.
 */
function flyby(body: string, hIn: number, hOut: number, rho: number, n = 3): GateDef[] {
  const turnLeft = ((hOut - hIn + 540) % 360) - 180 > 0;
  const off = turnLeft ? -90 : 90;
  // Unwrap so the arc goes the short way round for the turn direction.
  let a0 = hIn + off;
  let a1 = hOut + off;
  const delta = ((a1 - a0 + 540) % 360) - 180;
  a1 = a0 + delta;
  const out: GateDef[] = [];
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? 0.5 : i / (n - 1);
    const a = deg(a0 + (a1 - a0) * t);
    const k = i === 0 || i === n - 1 ? 1.45 : 1;
    out.push(near(body, R(Math.cos(a) * rho * k), R(Math.sin(a) * rho * k)));
  }
  return out;
}

/** Orbit that puts the body at `angle` degrees (seen from its parent) at time `t0`. */
const orbitAt = (parent: string, a: number, angle: number, t0: number, omega: number): NonNullable<BodyDef['orbit']> => ({ parent, a, phase: deg(angle) - omega * t0, omega });

const SOL = (x: number, y: number, r = 240): BodyDef => ({ id: 'sol', name: 'Sol', r, g: 110, color: '#ffd23a', x, y, star: true });
const planet = (id: string, name: string, x: number, y: number, r: number, g: number, color: string, extra: Partial<BodyDef> = {}): BodyDef => ({ id, name, r, g, color, x, y, ...extra });
const EARTH = (x: number, y: number, pads: BodyDef['pads']): BodyDef => planet('tierra', 'Tierra', x, y, 190, 68, '#2f7bff', { atm: { h: 40, drag: 0.003 }, pads });
const VENUS = (x: number, y: number): BodyDef => planet('venus', 'Venus', x, y, 170, 66, '#ffd28a', { atm: { h: 60, drag: 0.004 } });
const at = (x: number, y: number, deg0: number, r: number, extra = 0): { x: number; y: number } => ({ x: R(x + Math.cos(deg(deg0)) * (r + extra)), y: R(y + Math.sin(deg(deg0)) * (r + extra)) });

// ======================================================================= 1. Mariner 10

const MERC_PAD = 120;
const as1 = stage({
  id: 1,
  name: 'Mariner 10: Venus a Mercurio',
  year: 1973,
  blurb: 'La primera vez que una nave usó la gravedad de un planeta para llegar a otro. Rodeá Venus por arriba y dejá que te tire hacia Mercurio.',
  skulls: 2,
  bodies: [
    SOL(0, 0),
    EARTH(-4000, -200, [pad('Cabo Cañaveral', true, 50, 25), pad('Parrilla', false, 50, 60)]),
    { ...VENUS(0, 0), g: 150, orbit: orbitAt('sol', 1900, 69, 18, -0.05) },
    planet('mercurio', 'Mercurio', 3900, 500, 80, 44, '#b8a89a', { pads: [pad('Mercurio', true, 40, MERC_PAD)] }),
  ],
  gates: [
    { x: -3500, y: 20 },
    ...flyby('venus', 23, -21, 380),
    { x: 1900, y: 1300 },
    { x: 3000, y: 900 },
    { ...at(3900, 500, MERC_PAD, 80, 110), final: true },
  ],
  asteroids: [{ count: 8, seed: 301, around: 'venus', rIn: 500, rOut: 900, size: [4, 7], speed: 0.9 }],
  cells: [{ x: -2800, y: 350, fuel: 25 }],
  start: { body: 'tierra', angle: deg(25) },
  rivalStart: { body: 'tierra', angle: deg(60) },
  tank: 0.5,
  rival: { skill: 0.86, name: 'Mariner 9', delay: 8 },
  finish: { body: 'mercurio', pad: 0 },
  par: 70,
  kind: 'Honda gravitatoria',
});

// ======================================================================= 2. Galileo

const as2 = stage({
  id: 2,
  name: 'Galileo: Venus, Tierra, Tierra',
  year: 1989,
  blurb: 'Júpiter está demasiado lejos para el motor. Hay que dar una vuelta a Venus, volver a pasar por la Tierra y recién ahí salir disparado hacia el gigante.',
  skulls: 3,
  bodies: [
    SOL(0, 0),
    EARTH(-2500, -1000, [pad('Cabo Cañaveral', true, 50, 20), pad('Parrilla', false, 50, 55)]),
    { ...VENUS(0, 0), g: 150, orbit: orbitAt('sol', 1900, 250, 15, -0.07) },
    planet('jupiter', 'Júpiter', 9000, 300, 380, 150, '#ff9a5a', { atm: { h: 70, drag: 0.002 } }),
    planet('europa', 'Europa', 0, 0, 55, 40, '#cfe8ff', { orbit: { parent: 'jupiter', a: 1700, phase: 3.3, omega: 0.052 }, pads: [pad('Europa', true, 32, 180)] }),
  ],
  gates: [
    { x: -2000, y: -900 },
    ...flyby('venus', 20, 160, 360, 4),
    ...flyby('tierra', 160, 5, 330, 4),
    { x: 1500, y: -250 },
    { x: 4500, y: 0 },
    { x: 7200, y: 200 },
    near('europa', -330, 130),
    near('europa', 0, 110, { final: true }),
  ],
  asteroids: [{ count: 14, seed: 302, around: 'jupiter', rIn: 1300, rOut: 2300, size: [4, 8], speed: 0.9 }],
  cells: [{ x: -1200, y: -1400, fuel: 25 }, { x: 5500, y: 150, fuel: 25 }],
  start: { body: 'tierra', angle: deg(20) },
  rivalStart: { body: 'tierra', angle: deg(55) },
  tank: 1,
  rival: { skill: 0.88, name: 'Ulysses', delay: 10 },
  finish: { body: 'europa', pad: 0 },
  par: 90,
  kind: 'Honda gravitatoria',
});


// ======================================================================= 3. Cassini

const as3 = stage({
  id: 3,
  name: 'Cassini: de Júpiter a Saturno',
  year: 2000,
  blurb: 'Llegás a Júpiter ya lanzado. Cerrá la curva alrededor del gigante: te dobla la trayectoria sin gastar nada y te manda hacia Saturno, a trece mil unidades.',
  skulls: 4,
  bodies: [
    { id: 'sol', name: 'Sol', r: 120, g: 20, color: '#ffd23a', x: 0, y: 6000, star: true },
    planet('jupiter', 'Júpiter', 0, 0, 380, 220, '#ff9a5a', { orbit: orbitAt('sol', 6000, -90, 14, 0.025), atm: { h: 70, drag: 0.002 } }),
    planet('saturno', 'Saturno', 13000, -3800, 330, 130, '#ffe0a0', { atm: { h: 70, drag: 0.002 } }),
    planet('titan', 'Titán', 0, 0, 65, 42, '#e8a24a', { orbit: { parent: 'saturno', a: 1900, phase: 0.64, omega: 0.0454 }, atm: { h: 45, drag: 0.006 }, pads: [pad('Titán', true, 36, 90)] }),
  ],
  startAt: { body: 'jupiter', angle: 200, alt: 2200, speed: 3, dir: 1 },
  gates: [
    ...flyby('jupiter', -70, -16, 720, 3),
    { x: 3500, y: -1000 },
    { x: 7000, y: -2100 },
    { x: 10300, y: -3000 },
    near('titan', -330, 110),
    near('titan', 0, 175, { final: true }),
  ],
  asteroids: [{ count: 12, seed: 303, around: 'saturno', rIn: 1300, rOut: 2300, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 1500, y: -500, fuel: 25 }, { x: 9000, y: -2700, fuel: 25 }],
  start: { body: 'jupiter', angle: deg(90) },
  rivalStart: { body: 'jupiter', angle: deg(90) },
  tank: 0.45,
  rival: { skill: 0.9, name: 'Huygens', delay: 12 },
  finish: { body: 'titan', pad: 0 },
  par: 80,
  kind: 'Honda gravitatoria',
});

// ======================================================================= 4. MESSENGER

const as4 = stage({
  id: 4,
  name: 'MESSENGER: rodear el Sol',
  year: 2004,
  blurb: 'Mercurio corre y el Sol tira. Pasá por arriba de la estrella, sin quemarte, y caé sobre el planeta en movimiento.',
  skulls: 4,
  bodies: [
    SOL(0, 0, 300),
    planet('venus', 'Venus', -2600, -200, 170, 66, '#ffd28a', { atm: { h: 60, drag: 0.004 }, pads: [pad('Venus', true, 46, 20), pad('Parrilla', false, 46, 55)] }),
    planet('mercurio', 'Mercurio', 0, 0, 80, 44, '#b8a89a', { orbit: { parent: 'sol', a: 1400, phase: -3.22, omega: 0.06 }, pads: [pad('Mercurio', true, 40, 90)] }),
  ],
  gates: [
    { x: -1900, y: 330 },
    { x: -1000, y: 780 },
    { x: 0, y: 960 },
    { x: 1000, y: 650 },
    near('mercurio', 0, 300),
    near('mercurio', 0, 190, { final: true }),
  ],
  fields: [],
  asteroids: [{ count: 16, seed: 304, around: 'sol', rIn: 800, rOut: 1700, size: [4, 8], speed: 0.95 }],
  cells: [{ x: -1500, y: 600, fuel: 25 }, { x: 600, y: 900, fuel: 25 }],
  start: { body: 'venus', angle: deg(20) },
  rivalStart: { body: 'venus', angle: deg(55) },
  tank: 0.5,
  rival: { skill: 0.9, name: 'BepiColombo', delay: 8 },
  finish: { body: 'mercurio', pad: 0 },
  par: 60,
  kind: 'Honda gravitatoria',
});

// ======================================================================= 5. New Horizons

const as5 = stage({
  id: 5,
  name: 'New Horizons: Plutón',
  year: 2006,
  blurb: 'La nave más rápida que salió de la Tierra. Júpiter la empuja y la manda a Plutón, veinte mil unidades más allá. Después hay que frenar y aterrizar en un mundo chico.',
  skulls: 5,
  bodies: [
    SOL(0, 0, 200),
    planet('tierra', 'Tierra', -4200, 0, 190, 68, '#2f7bff', { atm: { h: 40, drag: 0.003 }, pads: [pad('Cabo Cañaveral', true, 50, 0), pad('Parrilla', false, 50, 35)] }),
    planet('jupiter', 'Júpiter', 0, 0, 380, 300, '#ff9a5a', { orbit: orbitAt('sol', 3000, -50, 20, 0.05), atm: { h: 70, drag: 0.002 } }),
    planet('pluton', 'Plutón', 16500, 9900, 60, 30, '#b48cff', { pads: [pad('Sputnik Planitia', true, 46, 220)] }),
  ],
  gates: [
    { x: -3500, y: 20 },
    ...flyby('jupiter', -21, 40, 700, 3),
    { x: 5572, y: 750 },
    { x: 9215, y: 3800 },
    { x: 12857, y: 6850 },
    { x: 16355, y: 10000, final: true },
  ],
  asteroids: [{ count: 14, seed: 305, around: 'jupiter', rIn: 1300, rOut: 2300, size: [4, 8], speed: 0.9 }],
  cells: [{ x: -2500, y: 120, fuel: 25 }, { x: 7400, y: 2200, fuel: 25 }, { x: 14500, y: 8300, fuel: 25 }],
  start: { body: 'tierra', angle: deg(0) },
  rivalStart: { body: 'tierra', angle: deg(35) },
  tank: 0.6,
  rival: { skill: 0.92, name: 'Pluto-X', delay: 20 },
  finish: { body: 'pluton', pad: 0 },
  par: 100,
  kind: 'Honda gravitatoria',
});

export const ASISTENCIAS: RaceDef = {
  id: 'asistencias',
  name: 'LA HONDA GRAVITATORIA',
  subtitle: 'Mariner 10, Galileo, Cassini, MESSENGER y New Horizons',
  blurb: 'Naves con el tanque casi vacío que llegan a destinos lejanísimos usando la gravedad de los planetas. Rodeá, ganá velocidad y apuntá lejos.',
  stages: [as1, as2, as3, as4, as5],
};
