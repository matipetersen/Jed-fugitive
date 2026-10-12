import { type BodyDef, type RaceDef } from './types';
import { d2r, gate, near, pad, stage } from './build';

const KESSEL: BodyDef = {
  id: 'kessel',
  name: 'Kessel',
  r: 200,
  g: 70,
  color: '#d9a066',
  x: 0,
  y: 0,
  atm: { h: 40, drag: 0.004 },
  pads: [pad('Mina de Kessel', true, 50), pad('Muelle pirata', false, 50, 55)],
};

const hole = (id: string, name: string, x: number, y: number, r = 48, g = 290): BodyDef => ({ id, name, r, g, color: '#b46bff', x, y, hole: true });
const rock = (id: string, name: string, x: number, y: number, r = 70, color = '#9aa7b8'): BodyDef => ({ id, name, r, g: 45, color, x, y, pads: [pad(name, true, 40)] });

const k1 = stage({
  id: 1,
  name: 'Kessel',
  blurb: 'Salís de las minas de especia con la patrulla pisándote los talones. Sin agujeros negros todavía, pero el aire de Kessel es denso.',
  skulls: 1,
  bodies: [
    KESSEL,
    { id: 'aduana', name: 'Aduana', r: 55, g: 40, color: '#9aa7b8', orbit: { parent: 'kessel', a: 2200, phase: 0.5, omega: 0.02 }, pads: [pad('Aduana', true, 38, 100)] },
  ],
  gates: [gate(560, 80), { x: 330, y: 900 }, { x: 560, y: 1500 }, near('aduana', -300, -200), near('aduana', -130, 30), near('aduana', -27, 153, { final: true })],
  asteroids: [{ count: 10, seed: 71, around: 'kessel', rIn: 650, rOut: 1100, size: [4, 7], speed: 0.9 }],
  cells: [{ x: 250, y: 700, fuel: 35 }, { x: 0, y: 120, body: 'aduana', fuel: 35 }],
  start: { body: 'kessel', angle: 90 * d2r },
  rivalStart: { body: 'kessel', angle: 55 * d2r },
  rival: { skill: 0.85, name: 'Cañonera imperial', delay: 9 },
  finish: { body: 'aduana', pad: 0 },
  par: 45,
});

const k2 = stage({
  id: 2,
  name: 'Los Cúmulos',
  blurb: 'El primer agujero negro. Podés rodearlo lejos o rasparlo: la honda gravitatoria te regala velocidad, pero el disco quema.',
  skulls: 2,
  bodies: [KESSEL, hole('maw1', 'Maw I', 1350, 350), rock('roca', 'Roca pirata', 2700, 600)],
  gates: [gate(560, 80), { x: 500, y: 760 }, { x: 1000, y: 880 }, { x: 1400, y: 680 }, { x: 1750, y: 330 }, { x: 2150, y: 700 }, { x: 2700, y: 780, final: true }],
  asteroids: [{ count: 12, seed: 72, around: 'maw1', rIn: 320, rOut: 560, size: [4, 7], speed: 0.9 }],
  cells: [{ x: 900, y: 700, fuel: 35 }, { x: 1900, y: 520, fuel: 35 }],
  start: { body: 'kessel', angle: 90 * d2r },
  rivalStart: { body: 'kessel', angle: 55 * d2r },
  rival: { skill: 0.88, name: 'Contrabandista Pyke', delay: 10 },
  finish: { body: 'roca', pad: 0 },
  par: 55,
});

const k3 = stage({
  id: 3,
  name: 'Entrada al Maw',
  blurb: 'Dos agujeros negros y un pasillo entre ellos. Más cerca es más corto; los pársecs son distancia, no tiempo.',
  skulls: 3,
  bodies: [KESSEL, hole('maw1', 'Maw I', 1000, 300), hole('maw2', 'Maw II', 1900, -150, 52, 310), rock('estacion', 'Estación Pirata', 3100, 400)],
  gates: [gate(560, 80), { x: 500, y: 660 }, { x: 950, y: 760 }, { x: 1450, y: 110 }, { x: 1900, y: 380 }, { x: 2450, y: 250 }, { x: 3100, y: 580, final: true }],
  asteroids: [{ count: 18, seed: 73, around: 'maw2', rIn: 350, rOut: 800, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 700, y: 760, fuel: 35 }, { x: 1700, y: 300, fuel: 35 }, { x: 2800, y: 450, fuel: 35 }],
  start: { body: 'kessel', angle: 90 * d2r },
  rivalStart: { body: 'kessel', angle: 55 * d2r },
  rival: { skill: 0.9, name: 'Patrulla de Kessel', delay: 7 },
  finish: { body: 'estacion', pad: 0 },
  par: 65,
});

const k4 = stage({
  id: 4,
  name: 'Dentro del Maw',
  blurb: 'Tres agujeros negros y un campo de minas. Zigzagueá entre ellos sin perder el rumbo ni el combustible.',
  skulls: 4,
  bodies: [KESSEL, hole('maw1', 'Maw I', 900, 500), hole('maw2', 'Maw II', 1700, -100, 55, 320), hole('maw3', 'Maw III', 2200, 700), rock('cuartel', 'Cuartel', 3300, 300)],
  gates: [gate(560, 80), { x: 600, y: 950 }, { x: 1300, y: 560 }, { x: 1900, y: 400 }, { x: 2700, y: 600 }, { x: 3300, y: 480, final: true }],
  asteroids: [{ count: 34, seed: 74, around: 'maw2', rIn: 380, rOut: 1000, size: [4, 9], speed: 0.95 }],
  cells: [{ x: 500, y: 800, fuel: 35 }, { x: 1500, y: 450, fuel: 35 }, { x: 2500, y: 300, fuel: 35 }],
  start: { body: 'kessel', angle: 90 * d2r },
  rivalStart: { body: 'kessel', angle: 55 * d2r },
  rival: { skill: 0.9, name: 'Crucero imperial', delay: 6 },
  finish: { body: 'cuartel', pad: 0 },
  par: 70,
});

const k5 = stage({
  id: 5,
  name: 'La salida del Maw',
  blurb: 'Los agujeros se cierran sobre el pasillo y el rival te respira en la nuca. Savareen está al otro lado.',
  skulls: 5,
  bodies: [KESSEL, hole('maw1', 'Maw I', 1000, 400, 50, 300), hole('maw2', 'Maw II', 1900, 150, 55, 340), hole('maw3', 'Maw III', 2600, -400, 50, 300), { id: 'savareen', name: 'Savareen', r: 100, g: 50, color: '#7dff6b', x: 3500, y: -200, pads: [pad('Savareen', true, 46)] }],
  gates: [gate(560, 80), { x: 600, y: 800 }, { x: 1500, y: 650 }, { x: 1850, y: -150 }, { x: 2300, y: 180 }, { x: 3050, y: -250 }, { x: 3500, y: -2, final: true }],
  fields: [{ body: 'maw2', x: 0, y: 0, r: 450, kind: 'radiation', dps: 6, color: '#ff2bd6', label: 'DISCO' }],
  asteroids: [{ count: 30, seed: 75, around: 'maw2', rIn: 400, rOut: 1000, size: [4, 9], speed: 0.95 }],
  cells: [{ x: 600, y: 700, fuel: 35 }, { x: 1600, y: 450, fuel: 35 }, { x: 2900, y: -100, fuel: 35 }],
  start: { body: 'kessel', angle: 90 * d2r },
  rivalStart: { body: 'kessel', angle: 55 * d2r },
  rival: { skill: 0.9, name: 'Interdictor', delay: 11, ai: { interval: 0.15, noise: 0.12 } },
  finish: { body: 'savareen', pad: 0 },
  par: 80,
});

export const KESSEL_RACE: RaceDef = {
  id: 'kessel',
  name: 'LA CARRERA DE KESSEL',
  subtitle: 'Hace mucho tiempo, en una galaxia lejana',
  blurb: 'Contrabando a través del Maw, un cúmulo de agujeros negros. Cuanto más cerca pasás, más rápido vas y más fácil es morir.',
  stages: [k1, k2, k3, k4, k5],
};
