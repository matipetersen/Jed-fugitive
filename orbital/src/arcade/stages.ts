import { type BodyDef, type GateDef, type StageDef } from './types';

const d2r = Math.PI / 180;
const on = (r: number, deg: number): { x: number; y: number } => ({ x: Math.round(r * Math.cos(deg * d2r)), y: Math.round(r * Math.sin(deg * d2r)) });
const gate = (r: number, deg: number, extra: Partial<GateDef> = {}): GateDef => ({ ...on(r, deg), ...extra });

const EARTH: BodyDef = {
  id: 'tierra',
  name: 'Tierra',
  r: 240,
  g: 85,
  color: '#2f7bff',
  x: 0,
  y: 0,
  atm: { h: 45, drag: 0.003 },
  pads: [
    { angle: 90 * d2r, half: 50, name: 'Cabo Cañaveral', bonfire: true },
    { angle: 55 * d2r, half: 50, name: 'Baikonur', bonfire: false },
  ],
};

/** Stage 1: one lap around the Earth. Teaches launching, thrust and gravity. */
const stage1: StageDef = {
  id: 1,
  name: 'Sputnik',
  year: 1957,
  blurb: 'Una vuelta a la Tierra. Despegá, ganá velocidad y no te quedes sin aire.',
  skulls: 1,
  bodies: [EARTH],
  gates: [
    gate(760, 78),
    gate(760, 33),
    gate(760, -12),
    gate(760, -57),
    gate(760, -102),
    gate(760, -147),
    gate(760, 168),
    gate(760, 123),
    gate(620, 88, { final: true }),
  ],
  fields: [],
  asteroids: [{ count: 8, seed: 11, around: 'tierra', rIn: 900, rOut: 1100, size: [4, 7], speed: 0.9 }],
  cells: [{ ...on(760, -80), fuel: 30 }],
  start: { body: 'tierra', angle: 90 * d2r },
  rivalStart: { body: 'tierra', angle: 55 * d2r },
  rival: { skill: 0.85, name: 'Sputnik-1', delay: 14, ai: { horizon: 1.2, dt: 0.05, interval: 0.25, noise: 0.25 } },
  par: 32,
};

/** Stage 2: Earth to the Moon, which moves. */
const stage2: StageDef = {
  id: 2,
  name: 'Luna',
  year: 1959,
  blurb: 'La Luna se mueve. Llegá donde va a estar, no donde está, y usá su gravedad.',
  skulls: 2,
  bodies: [
    EARTH,
    {
      id: 'luna',
      name: 'Luna',
      r: 75,
      g: 55,
      color: '#c8d4ff',
      orbit: { parent: 'tierra', a: 1500, phase: -0.35, omega: 0.04 },
      pads: [{ angle: 100 * d2r, half: 34, name: 'Mar de la Tranquilidad', bonfire: true }],
    },
  ],
  gates: [
    gate(560, 80),
    { x: 560, y: 520 },
    { x: 1000, y: 600 },
    { x: -150, y: 190, body: 'luna' },
    { x: 170, y: -150, body: 'luna' },
    { x: 700, y: -250, body: 'luna' },
    { x: 1500, y: 900, final: true },
  ],
  fields: [],
  asteroids: [{ count: 10, seed: 22, around: 'tierra', rIn: 700, rOut: 1700, size: [4, 8], speed: 0.85 }],
  cells: [{ x: 500, y: 450, fuel: 30 }, { x: 0, y: 260, body: 'luna', fuel: 30 }],
  start: { body: 'tierra', angle: 90 * d2r },
  rivalStart: { body: 'tierra', angle: 55 * d2r },
  rival: { skill: 0.85, name: 'Luna-2', delay: 10, ai: { horizon: 1.2, dt: 0.05, interval: 0.2, noise: 0.2 } },
  par: 45,
};

/** Stage 3: a star in the middle and two planets with the solar wind pushing. */
const stage3: StageDef = {
  id: 3,
  name: 'Marte',
  year: 1965,
  blurb: 'El Sol tira de vos y el viento solar te empuja. Pasá entre los planetas sin quemarte.',
  skulls: 3,
  bodies: [
    { id: 'sol', name: 'Sol', r: 230, g: 120, color: '#fff27a', x: 0, y: 0, star: true },
    {
      id: 'terra',
      name: 'Tierra',
      r: 90,
      g: 60,
      color: '#2f7bff',
      orbit: { parent: 'sol', a: 1500, phase: 0.2, omega: 0.032 },
      pads: [{ angle: 90 * d2r, half: 40, name: 'Plataforma', bonfire: true }, { angle: 60 * d2r, half: 40, name: 'Plataforma rival', bonfire: false }],
    },
    {
      id: 'marte',
      name: 'Marte',
      r: 70,
      g: 48,
      color: '#ff5a3c',
      orbit: { parent: 'sol', a: 2700, phase: 1.0, omega: 0.018 },
      pads: [{ angle: 270 * d2r, half: 34, name: 'Utopia Planitia', bonfire: true }],
    },
  ],
  gates: [
    { x: 0, y: 260, body: 'terra' },
    { x: 700, y: 400 },
    { x: 1500, y: 1400 },
    { x: 2200, y: 2000 },
    { x: -150, y: 0, body: 'marte' },
    { x: 200, y: 220, body: 'marte', final: true },
  ],
  fields: [{ x: 1500, y: 900, r: 700, kind: 'wind', ax: 40, ay: -25, color: '#ffb000', label: 'VIENTO SOLAR' }],
  asteroids: [{ count: 10, seed: 33, around: 'sol', rIn: 1900, rOut: 2300, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 1000, y: 700, fuel: 30 }, { x: 2000, y: 1700, fuel: 30 }],
  start: { body: 'terra', angle: 90 * d2r },
  rivalStart: { body: 'terra', angle: 60 * d2r },
  rival: { skill: 0.9, name: 'Mars-1', delay: 8, ai: { horizon: 1.2, dt: 0.05, interval: 0.2, noise: 0.2 } },
  par: 55,
};

/** Stage 4: thread an asteroid belt. */
const stage4: StageDef = {
  id: 4,
  name: 'Cinturón',
  year: 1972,
  blurb: 'Cientos de rocas se mueven bajo la gravedad del Sol. Hay una estación en Ceres para respirar.',
  skulls: 4,
  bodies: [
    { id: 'sol', name: 'Sol', r: 230, g: 120, color: '#fff27a', x: 0, y: 0, star: true },
    {
      id: 'marte',
      name: 'Marte',
      r: 70,
      g: 48,
      color: '#ff5a3c',
      orbit: { parent: 'sol', a: 1500, phase: 0.2, omega: 0.032 },
      pads: [{ angle: 90 * d2r, half: 34, name: 'Base Marte', bonfire: true }, { angle: 60 * d2r, half: 34, name: 'Plataforma rival', bonfire: false }],
    },
    {
      id: 'ceres',
      name: 'Ceres',
      r: 45,
      g: 38,
      color: '#b8a89a',
      orbit: { parent: 'sol', a: 2600, phase: 0.9, omega: 0.02 },
      pads: [{ angle: 90 * d2r, half: 28, name: 'Estación Ceres', bonfire: true }],
    },
    {
      id: 'jupiter',
      name: 'Júpiter',
      r: 160,
      g: 95,
      color: '#ff9a5a',
      orbit: { parent: 'sol', a: 4200, phase: 1.4, omega: 0.012 },
    },
  ],
  gates: [
    { x: 0, y: 200, body: 'marte' },
    { x: 700, y: 700 },
    { x: 1200, y: 1500 },
    { x: -110, y: 0, body: 'ceres' },
    { x: 100, y: 190, body: 'ceres' },
    { x: 2500, y: 2600 },
    { x: -250, y: 120, body: 'jupiter', final: true },
  ],
  fields: [],
  asteroids: [{ count: 46, seed: 44, around: 'sol', rIn: 1900, rOut: 3000, size: [4, 9], speed: 0.95 }],
  cells: [{ x: 500, y: 500, fuel: 30 }, { x: 1800, y: 2200, fuel: 30 }],
  start: { body: 'marte', angle: 90 * d2r },
  rivalStart: { body: 'marte', angle: 60 * d2r },
  rival: { skill: 0.9, name: 'Belt-3', delay: 5, ai: { horizon: 1.2, dt: 0.05, interval: 0.2, noise: 0.15 } },
  par: 55,
};

/** Stage 5: use Jupiter, then fall towards Pluto. */
const stage5: StageDef = {
  id: 5,
  name: 'Plutón',
  year: 1991,
  blurb: 'Júpiter te da la velocidad que no tenés. Plutón está lejos, es chico y es la meta.',
  skulls: 5,
  bodies: [
    { id: 'jupiter', name: 'Júpiter', r: 380, g: 150, color: '#ff9a5a', x: 0, y: 0, atm: { h: 70, drag: 0.002 } },
    {
      id: 'io',
      name: 'Ío',
      r: 55,
      g: 40,
      color: '#ffd37a',
      orbit: { parent: 'jupiter', a: 1100, phase: 0.2, omega: 0.07 },
      pads: [{ angle: 90 * d2r, half: 30, name: 'Estación Ío', bonfire: true }, { angle: 50 * d2r, half: 30, name: 'Plataforma rival', bonfire: false }],
    },
    {
      id: 'europa',
      name: 'Europa',
      r: 50,
      g: 36,
      color: '#cfe8ff',
      orbit: { parent: 'jupiter', a: 1700, phase: 2.4, omega: 0.045 },
    },
    {
      id: 'pluton',
      name: 'Plutón',
      r: 60,
      g: 30,
      color: '#b48cff',
      x: 7600,
      y: -3600,
      pads: [{ angle: 150 * d2r, half: 34, name: 'Sputnik Planitia', bonfire: true }],
    },
  ],
  gates: [
    { x: 0, y: 160, body: 'io' },
    gate(800, 20),
    gate(800, -60),
    { x: 90, y: -260, body: 'europa' },
    { x: 2600, y: -1200 },
    { x: 5200, y: -2500 },
    { x: -180, y: 150, body: 'pluton', final: true },
  ],
  fields: [{ x: 3400, y: -1500, r: 800, kind: 'radiation', dps: 8, color: '#ff2bd6', label: 'RADIACIÓN' }],
  asteroids: [{ count: 18, seed: 55, around: 'jupiter', rIn: 2000, rOut: 2800, size: [4, 9], speed: 0.9 }],
  cells: [{ x: 1500, y: -400, fuel: 30 }, { x: 4200, y: -2000, fuel: 30 }],
  start: { body: 'io', angle: 90 * d2r },
  rivalStart: { body: 'io', angle: 50 * d2r },
  rival: { skill: 0.9, name: 'Pluto-X', delay: 6, ai: { horizon: 1.2, dt: 0.05, interval: 0.15, noise: 0.1 } },
  par: 70,
};

export const STAGES: StageDef[] = [stage1, stage2, stage3, stage4, stage5];
