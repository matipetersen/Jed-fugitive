import { STAGES } from './stages';
import { type BodyDef, type RaceDef } from './types';
import { d2r, gate, near, pad, stage } from './build';

export const EARTH = (pads: BodyDef['pads'] = [pad('Cabo Cañaveral', true, 50), pad('Baikonur', false, 50, 55)]): BodyDef => ({
  id: 'tierra',
  name: 'Tierra',
  r: 240,
  g: 85,
  color: '#2f7bff',
  x: 0,
  y: 0,
  atm: { h: 45, drag: 0.003 },
  pads,
});
export const startOn = (body: string, deg = 90): { body: string; angle: number } => ({ body, angle: deg * d2r });

// ======================================================================= Polo sur 2023

const LUNA_FAR: BodyDef = { id: 'luna', name: 'Luna', r: 80, g: 50, color: '#c8d4ff', orbit: { parent: 'tierra', a: 1700, phase: -0.3, omega: 0.03 }, pads: [pad('Polo sur', true, 38, 270)] };

const p1 = stage({
  id: 1,
  name: 'Hacia la Luna',
  year: 2023,
  blurb: 'Dos naves, un mismo objetivo: el polo sur lunar. Rodeá la Luna y bajá por debajo.',
  skulls: 2,
  bodies: [EARTH(), LUNA_FAR],
  gates: [gate(560, 80), { x: 500, y: 900 }, { x: 1000, y: 1200 }, near('luna', -340, 20), near('luna', -80, -250), near('luna', 0, -190, { final: true })],
  asteroids: [{ count: 10, seed: 81, around: 'tierra', rIn: 700, rOut: 1700, size: [4, 8], speed: 0.85 }],
  cells: [{ x: 500, y: 700, fuel: 35 }, { x: -120, y: -40, body: 'luna', fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.85, name: 'Luna-25', delay: 8 },
  finish: { body: 'luna', pad: 0 },
  par: 60,
});

const MOON_NEAR = (extraPads: BodyDef['pads'] = []): BodyDef[] => [
  { id: 'luna', name: 'Luna', r: 170, g: 52, color: '#c8d4ff', x: 0, y: 0, pads: [pad('Polo sur', true, 30, 270), ...extraPads] },
  { id: 'gateway', name: 'Gateway', r: 22, g: 14, color: '#00f0ff', orbit: { parent: 'luna', a: 430, phase: 1.2, omega: 0.05 }, pads: [pad('Gateway', true, 18), pad('Muelle', false, 18, 60)] },
];

const p2 = stage({
  id: 2,
  name: 'Órbita lunar',
  year: 2023,
  blurb: 'Salís de la estación Gateway y hay que bajar al polo sur. Una vuelta completa a la Luna antes de caer.',
  skulls: 3,
  bodies: MOON_NEAR(),
  gates: [{ x: 120, y: 560 }, { x: -380, y: 420 }, { x: -560, y: -60 }, { x: -350, y: -450 }, { x: 0, y: -290, final: true }],
  asteroids: [{ count: 10, seed: 82, around: 'luna', rIn: 550, rOut: 800, size: [3, 6], speed: 0.9 }],
  cells: [{ x: -430, y: 100, fuel: 35 }],
  start: startOn('gateway'),
  rivalStart: startOn('gateway', 60),
  rival: { skill: 0.88, name: 'Luna-25', delay: 6 },
  finish: { body: 'luna', pad: 0 },
  par: 50,
});

const p3 = stage({
  id: 3,
  name: 'Cráter del polo sur',
  year: 2023,
  blurb: 'Una plataforma diminuta en el fondo de un cráter. El rival llegó con prisa; vos, con precisión.',
  skulls: 4,
  bodies: [{ id: 'luna', name: 'Luna', r: 170, g: 52, color: '#c8d4ff', x: 0, y: 0, pads: [pad('Base ecuatorial', true, 44, 180), pad('Plataforma rival', false, 44, 150), pad('Cráter Shackleton', true, 20, 270)] }],
  gates: [{ x: -380, y: 280 }, { x: 0, y: 460 }, { x: 420, y: 250 }, { x: 440, y: -210 }, { x: 120, y: -400 }, { x: 0, y: -280, final: true }],
  fields: [{ x: 0, y: -380, r: 160, kind: 'wind', ax: 25, ay: 0, color: '#ffb000', label: 'POLVO LUNAR' }],
  asteroids: [{ count: 16, seed: 83, around: 'luna', rIn: 450, rOut: 700, size: [3, 6], speed: 0.9 }],
  cells: [{ x: 300, y: 330, fuel: 35 }],
  start: startOn('luna', 180),
  rivalStart: startOn('luna', 150),
  rival: { skill: 0.9, name: 'Luna-25', delay: 6, ai: { noise: 0.28 } },
  finish: { body: 'luna', pad: 2 },
  par: 55,
});

export const POLO_SUR: RaceDef = {
  id: 'polosur',
  name: 'POLO SUR LUNAR',
  subtitle: 'Agosto de 2023 · Chandrayaan-3 vs Luna-25',
  blurb: 'India y Rusia compiten por aterrizar cerca del polo sur de la Luna. Luna-25 se estrelló el 19; Chandrayaan-3 llegó el 23. Que no seas vos el que se estrella.',
  stages: [p1, p2, p3],
};

// ======================================================================= Venera

export const VENUS = (x: number, y: number, pads: BodyDef['pads']): BodyDef => ({ id: 'venus', name: 'Venus', r: 215, g: 78, color: '#ffd28a', x, y, atm: { h: 95, drag: 0.009 }, pads });

const v1 = stage({
  id: 1,
  name: 'Ventana a Venus',
  year: 1970,
  blurb: 'Venera 7 va a ser el primer aterrizaje blando en otro planeta. Primero hay que llegar.',
  skulls: 2,
  bodies: [EARTH(), VENUS(2900, 700, [pad('Valle Maxwell', true, 46)])],
  gates: [gate(560, 80), { x: 500, y: 800 }, { x: 1100, y: 1000 }, { x: 1800, y: 1200 }, { x: 2400, y: 1250 }, { x: 2900, y: 1010, final: true }],
  asteroids: [{ count: 12, seed: 91, around: 'tierra', rIn: 700, rOut: 1900, size: [4, 8], speed: 0.85 }],
  cells: [{ x: 700, y: 800, fuel: 35 }, { x: 2000, y: 1000, fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.88, name: 'Mariner 5', delay: 8 },
  finish: { body: 'venus', pad: 0 },
  par: 60,
});

const v2 = stage({
  id: 2,
  name: 'Descenso a Venus',
  year: 1970,
  blurb: 'Una atmósfera que aplasta y quema. Frená con el aire, no con el motor: el combustible no alcanza.',
  skulls: 3,
  bodies: [
    VENUS(0, 0, [pad('Valle Maxwell', true, 46), pad('Plataforma rival', false, 46, 120)]),
    { id: 'orbital', name: 'Venera-orbital', r: 25, g: 12, color: '#00f0ff', orbit: { parent: 'venus', a: 1000, phase: 0.2, omega: 0.04 }, pads: [pad('Orbital', true, 20), pad('Orbital 2', false, 20, 150)] },
  ],
  gates: [{ x: 700, y: 820 }, { x: 350, y: 780 }, { x: 220, y: 560 }, { x: 60, y: 420 }, { x: 0, y: 340, final: true }],
  fields: [{ body: 'venus', x: 0, y: 0, r: 330, kind: 'radiation', dps: 4, color: '#ff7a1a', label: 'CALOR' }],
  cells: [{ x: 500, y: 700, fuel: 35 }],
  start: startOn('orbital'),
  rivalStart: startOn('orbital', 150),
  rival: { skill: 0.9, name: 'Venera 7', delay: 5 },
  finish: { body: 'venus', pad: 0 },
  par: 50,
});

const v3 = stage({
  id: 3,
  name: 'Ascenso infernal',
  year: 1975,
  blurb: 'Subir desde la superficie con el aire pegado a la nave. Venera 9 mandó las primeras fotos; ahora necesitás regresar.',
  skulls: 4,
  bodies: [
    VENUS(0, 0, [pad('Venera 9', true, 46), pad('Plataforma rival', false, 46, 55)]),
    { id: 'vega', name: 'Estación Vega', r: 28, g: 12, color: '#00f0ff', orbit: { parent: 'venus', a: 900, phase: 1.45, omega: 0.045 }, pads: [pad('Vega', true, 22)] },
  ],
  gates: [{ x: 60, y: 420 }, { x: 200, y: 620 }, { x: 150, y: 820 }, near('vega', -130, 0), near('vega', 0, 120, { final: true })],
  fields: [{ body: 'venus', x: 0, y: 0, r: 330, kind: 'radiation', dps: 3, color: '#ff7a1a', label: 'CALOR' }],
  cells: [{ x: 120, y: 560, fuel: 40 }],
  start: startOn('venus'),
  rivalStart: startOn('venus', 55),
  rival: { skill: 0.92, name: 'Venera 9', delay: 5 },
  finish: { body: 'vega', pad: 0 },
  par: 50,
});

export const VENERA: RaceDef = {
  id: 'venera',
  name: 'VENERA: LA CARRERA A VENUS',
  subtitle: '1970 - 1975 · URSS vs EE.UU.',
  blurb: 'Presión de noventa atmósferas y 460 grados. El primer aterrizaje blando en otro planeta fue en Venus. Atmósfera espesa: el rozamiento manda.',
  stages: [v1, v2, v3],
};

// ======================================================================= Halley 1986

export const comet = (r: number, phase: number): BodyDef => ({ id: 'halley', name: 'Halley', r, g: 7, color: '#9be8ff', orbit: { parent: 'tierra', a: 2300, phase, omega: -0.045 }, pads: [pad('Núcleo', true, r * 0.9)] });

const h1 = stage({
  id: 1,
  name: 'La armada',
  year: 1986,
  blurb: 'Cinco naves persiguen un cometa que viaja al revés. Alcanzalo donde va a estar.',
  skulls: 3,
  bodies: [EARTH(), comet(36, 0.6)],
  gates: [gate(560, 80), { x: -300, y: 1100 }, near('halley', 520, 140), near('halley', 300, 60), near('halley', 0, 100, { final: true })],
  fields: [{ body: 'halley', x: 0, y: 0, r: 380, kind: 'radiation', dps: 5, color: '#9be8ff', label: 'POLVO' }],
  asteroids: [{ count: 10, seed: 101, around: 'tierra', rIn: 700, rOut: 1600, size: [3, 6], speed: 0.85 }],
  cells: [{ x: -100, y: 800, fuel: 35 }, { x: 150, y: 70, body: 'halley', fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.88, name: 'Vega 1', delay: 8 },
  finish: { body: 'halley', pad: 0 },
  par: 60,
});

const h2 = stage({
  id: 2,
  name: 'La coma',
  year: 1986,
  blurb: 'Giotto pasó a 600 km del núcleo y el polvo le averió la cámara. Atravesá la coma sin perder el casco.',
  skulls: 4,
  bodies: [EARTH(), comet(44, 1.0)],
  gates: [gate(560, 80), { x: -500, y: 1000 }, near('halley', 600, 200), near('halley', 330, -160), near('halley', 180, 120), near('halley', 0, 120, { final: true })],
  fields: [{ body: 'halley', x: 0, y: 0, r: 620, kind: 'radiation', dps: 8, color: '#9be8ff', label: 'COMA' }],
  asteroids: [{ count: 26, seed: 102, around: 'halley', rIn: 150, rOut: 650, size: [3, 6], speed: 0.9 }],
  cells: [{ x: -150, y: 750, fuel: 35 }, { x: 260, y: 40, body: 'halley', fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.9, name: 'Giotto', delay: 6 },
  finish: { body: 'halley', pad: 0 },
  par: 65,
});

const h3 = stage({
  id: 3,
  name: 'Tormenta de polvo',
  year: 1986,
  blurb: 'El núcleo despide chorros. Entrá por el lado oscuro y aterrizá en una roca que casi no tira.',
  skulls: 5,
  bodies: [EARTH(), comet(30, 1.4)],
  gates: [gate(560, 80), { x: -700, y: 900 }, near('halley', 700, -220), near('halley', 380, 200), near('halley', 200, -140), near('halley', 0, 105, { final: true })],
  fields: [{ body: 'halley', x: 0, y: 0, r: 650, kind: 'radiation', dps: 7, color: '#c8f4ff', label: 'CHORROS' }],
  asteroids: [{ count: 22, seed: 103, around: 'halley', rIn: 140, rOut: 700, size: [3, 7], speed: 0.9 }],
  cells: [{ x: -250, y: 700, fuel: 40 }, { x: 300, y: 0, body: 'halley', fuel: 40 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.92, name: 'Suisei', delay: 9, ai: { interval: 0.15, noise: 0.12 } },
  finish: { body: 'halley', pad: 0 },
  par: 70,
});

export const HALLEY: RaceDef = {
  id: 'halley',
  name: 'LA ARMADA DEL HALLEY',
  subtitle: 'Marzo de 1986 · cinco sondas, un cometa',
  blurb: 'El cometa Halley orbita al revés que los planetas, y se cruzó con las sondas a decenas de km/s. Perseguilo, atravesá su polvo y aterrizá en el núcleo.',
  stages: [h1, h2, h3],
};

// ======================================================================= Voyager

export const JUP = (x: number, y: number): BodyDef => ({ id: 'jupiter', name: 'Júpiter', r: 380, g: 150, color: '#ff9a5a', x, y, atm: { h: 70, drag: 0.002 } });
export const SAT = (x: number, y: number): BodyDef => ({ id: 'saturno', name: 'Saturno', r: 330, g: 130, color: '#ffe0a0', x, y, atm: { h: 70, drag: 0.002 } });
export const NEP = (x: number, y: number): BodyDef => ({ id: 'neptuno', name: 'Neptuno', r: 260, g: 115, color: '#4b8bff', x, y, atm: { h: 60, drag: 0.002 } });

const y1 = stage({
  id: 1,
  name: 'Júpiter',
  year: 1977,
  blurb: 'La alineación de los planetas exteriores se repite cada ~175 años. Voyager 2 salió primero; Voyager 1 salió después y la pasó.',
  skulls: 3,
  bodies: [
    EARTH(),
    JUP(3600, 1500),
    { id: 'io', name: 'Ío', r: 55, g: 40, color: '#ffd37a', orbit: { parent: 'jupiter', a: 2000, phase: 3.3, omega: 0.052 }, pads: [pad('Ío', true, 32)] },
  ],
  gates: [gate(560, 80), { x: 700, y: 900 }, { x: 1700, y: 1150 }, { x: 2700, y: 1400 }, near('io', -300, 150), near('io', -120, 90), near('io', 0, 160, { final: true })],
  asteroids: [{ count: 14, seed: 111, around: 'jupiter', rIn: 1500, rOut: 2300, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 1000, y: 1000, fuel: 35 }, { x: 2200, y: 1300, fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.9, name: 'Voyager 2', delay: 11 },
  finish: { body: 'io', pad: 0 },
  par: 75,
});

const y2 = stage({
  id: 2,
  name: 'Saturno',
  year: 1980,
  blurb: 'Ahora hay que usar la gravedad de Júpiter para llegar a Saturno y bajar en Titán, la luna con atmósfera.',
  skulls: 4,
  bodies: [
    JUP(0, 0),
    { id: 'io', name: 'Ío', r: 55, g: 40, color: '#ffd37a', orbit: { parent: 'jupiter', a: 2000, phase: 0.3, omega: 0.052 }, pads: [pad('Ío', true, 32), pad('Plataforma rival', false, 32, 40)] },
    SAT(5200, -1800),
    { id: 'titan', name: 'Titán', r: 65, g: 42, color: '#e8a24a', orbit: { parent: 'saturno', a: 1900, phase: 2.9, omega: 0.0454 }, atm: { h: 45, drag: 0.006 }, pads: [pad('Titán', true, 34)] },
  ],
  gates: [near('io', 0, 150), { x: 900, y: 500 }, { x: 1800, y: 100 }, { x: 3000, y: -700 }, { x: 4200, y: -1200 }, near('titan', -320, 120), near('titan', -100, 90), near('titan', 0, 175, { final: true })],
  fields: [],
  asteroids: [{ count: 16, seed: 112, around: 'saturno', rIn: 1700, rOut: 2400, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 1500, y: 200, fuel: 35 }, { x: 3500, y: -900, fuel: 35 }],
  start: startOn('io'),
  rivalStart: startOn('io', 40),
  rival: { skill: 0.9, name: 'Voyager 2', delay: 7 },
  finish: { body: 'titan', pad: 0 },
  par: 85,
});

const y3 = stage({
  id: 3,
  name: 'Neptuno',
  year: 1989,
  blurb: 'Doce años de viaje comprimidos en uno. Tritón gira al revés y tiene géiseres; la meta es una plataforma chica.',
  skulls: 5,
  bodies: [
    SAT(0, 0),
    { id: 'titan', name: 'Titán', r: 65, g: 42, color: '#e8a24a', orbit: { parent: 'saturno', a: 1900, phase: 0.4, omega: 0.0454 }, atm: { h: 45, drag: 0.006 }, pads: [pad('Titán', true, 34), pad('Plataforma rival', false, 34, 40)] },
    NEP(6200, 1200),
    { id: 'triton', name: 'Tritón', r: 60, g: 38, color: '#bfe8ff', orbit: { parent: 'neptuno', a: 1500, phase: 5.06, omega: -0.048 }, pads: [pad('Tritón', true, 26)] },
  ],
  gates: [near('titan', 0, 150), { x: 1100, y: 700 }, { x: 2400, y: 700 }, { x: 4000, y: 900 }, near('triton', 350, 80), near('triton', 130, 100), near('triton', 0, 165, { final: true })],
  fields: [{ body: 'neptuno', x: 0, y: 0, r: 700, kind: 'wind', ax: -22, ay: 18, color: '#7a9bff', label: 'VIENTOS' }],
  asteroids: [{ count: 18, seed: 113, around: 'neptuno', rIn: 1300, rOut: 2000, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 1800, y: 700, fuel: 35 }, { x: 3600, y: 900, fuel: 35 }],
  start: startOn('titan'),
  rivalStart: startOn('titan', 40),
  rival: { skill: 0.92, name: 'Voyager 2', delay: 7 },
  finish: { body: 'triton', pad: 0 },
  par: 95,
});

export const VOYAGER: RaceDef = {
  id: 'voyager',
  name: 'EL GRAN TOUR',
  subtitle: '1977 - 1989 · Voyager 1 y 2',
  blurb: 'Una alineación planetaria que no se repite en casi dos siglos. Usá la gravedad de cada gigante para saltar al siguiente.',
  stages: [y1, y2, y3],
};

// ======================================================================= Marte 2020

const m1 = stage({
  id: 1,
  name: 'La ventana de julio',
  year: 2020,
  blurb: 'Una ventana de lanzamiento cada 26 meses. Emiratos, China y EE. UU. salen en las mismas semanas.',
  skulls: 2,
  bodies: [EARTH([pad('Cabo Cañaveral', true, 50), pad('Wenchang', false, 50, 55)]), { id: 'estacion', name: 'Salto TMI', r: 60, g: 38, color: '#9aa7b8', orbit: { parent: 'tierra', a: 1700, phase: 0.2, omega: 0.025 }, pads: [pad('Nodo de salida', true, 38)] }],
  gates: [gate(560, 80), { x: 500, y: 1000 }, { x: 900, y: 1500 }, near('estacion', -300, -120), near('estacion', -100, 40), near('estacion', 0, 170, { final: true })],
  asteroids: [{ count: 12, seed: 121, around: 'tierra', rIn: 700, rOut: 1900, size: [4, 8], speed: 0.85 }],
  cells: [{ x: 300, y: 800, fuel: 35 }, { x: 0, y: 120, body: 'estacion', fuel: 35 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  rival: { skill: 0.88, name: 'Tianwen-1', delay: 8 },
  finish: { body: 'estacion', pad: 0 },
  par: 55,
});

const m2 = {
  ...STAGES[2],
  id: 2,
  name: 'Siete meses de tránsito',
  year: 2020,
  blurb: 'El Sol tira de vos y el viento solar te empuja. Llegá a Marte antes que la sonda de los Emiratos.',
  skulls: 4,
  rival: { ...STAGES[2].rival, name: 'Hope (EAU)', delay: 9 },
};

const m3 = stage({
  id: 3,
  name: 'Siete minutos de terror',
  year: 2021,
  blurb: 'El descenso a Jezero: aire fino, viento y un cráter donde casi no hay lugar. Perseverance lo logró el 18 de febrero.',
  skulls: 5,
  bodies: [
    { id: 'marte', name: 'Marte', r: 250, g: 55, color: '#ff5a3c', x: 0, y: 0, atm: { h: 60, drag: 0.0025 }, pads: [pad('Cráter Jezero', true, 26), pad('Plataforma rival', false, 40, 60)] },
    { id: 'orbita', name: 'Orbitador', r: 25, g: 12, color: '#00f0ff', orbit: { parent: 'marte', a: 1000, phase: 0.9, omega: 0.045 }, pads: [pad('Orbitador', true, 20), pad('Orbitador 2', false, 20, 150)] },
  ],
  gates: [{ x: 700, y: 700 }, { x: 420, y: 620 }, { x: 160, y: 520 }, { x: 60, y: 420, final: false }, { x: 0, y: 360, final: true }],
  fields: [{ x: 0, y: 330, r: 260, kind: 'wind', ax: 22, ay: 0, color: '#ffb000', label: 'VIENTO' }],
  cells: [{ x: 500, y: 650, fuel: 35 }],
  start: startOn('orbita'),
  rivalStart: startOn('orbita', 150),
  rival: { skill: 0.9, name: 'Perseverance', delay: 5 },
  finish: { body: 'marte', pad: 0 },
  par: 50,
});

export const MARTE2020: RaceDef = {
  id: 'marte2020',
  name: 'LA VENTANA A MARTE',
  subtitle: 'Julio de 2020 · Hope, Tianwen-1 y Perseverance',
  blurb: 'Tres misiones salen en las mismas semanas porque la órbita lo exige. Ventana, tránsito y un descenso con aire fino y mucho viento.',
  stages: [m1, m2, m3],
};

// ======================================================================= Reutilizables

const up = (dx = 0): { x: number; y: number }[] => [{ x: dx, y: 480 }, { x: dx + 25, y: 680 }];

const r1 = stage({
  id: 1,
  name: 'Ansari X Prize',
  year: 2004,
  blurb: 'Dos vuelos a 100 km en dos semanas, con la misma nave. Subí, pasá la línea de Kármán y volvé a la misma plataforma.',
  skulls: 2,
  bodies: [EARTH([pad('Mojave', true, 55)])],
  gates: [...up(), { x: -40, y: 560 }, { x: 0, y: 380, final: true }],
  asteroids: [],
  cells: [{ x: 60, y: 600, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 60),
  rival: { skill: 0.85, name: 'Armadillo Aerospace', delay: 9 },
  finish: { body: 'tierra', pad: 0 },
  par: 40,
});

const r2 = stage({
  id: 2,
  name: 'Aterrizaje vertical',
  year: 2015,
  blurb: 'Blue Origin aterrizó vertical en noviembre; SpaceX, con un cohete orbital, en diciembre. La plataforma mide quince pasos.',
  skulls: 3,
  bodies: [EARTH([pad('Cabo Cañaveral', true, 50), pad('Barcaza', false, 50, 60), pad('Zona de aterrizaje', true, 18, 125)])],
  gates: [{ x: 0, y: 500 }, { x: -110, y: 680 }, { x: -300, y: 560 }, { x: -200, y: 287, final: true }],
  fields: [{ x: -250, y: 330, r: 220, kind: 'wind', ax: 20, ay: 0, color: '#ffb000', label: 'VIENTO' }],
  cells: [{ x: -60, y: 640, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 60),
  rival: { skill: 0.88, name: 'New Shepard', delay: 8 },
  finish: { body: 'tierra', pad: 2 },
  par: 45,
});

const r3 = stage({
  id: 3,
  name: 'Carrera de multimillonarios',
  year: 2021,
  blurb: 'Branson voló el 11 de julio y Bezos el 20. Vuelo a 100 km, regreso con viento fuerte y una plataforma de seis metros.',
  skulls: 4,
  bodies: [EARTH([pad('Spaceport', true, 50), pad('Muelle rival', false, 50, 60), pad('Plataforma', true, 14, 118)])],
  gates: [{ x: 0, y: 500 }, { x: 40, y: 760 }, { x: -200, y: 800 }, { x: -380, y: 560 }, { x: -215, y: 285, final: true }],
  fields: [{ x: -200, y: 520, r: 260, kind: 'wind', ax: 32, ay: 8, color: '#ffb000', label: 'VIENTO' }],
  cells: [{ x: 10, y: 640, fuel: 30 }, { x: -320, y: 600, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 60),
  rival: { skill: 0.9, name: 'Unity', delay: 6 },
  finish: { body: 'tierra', pad: 2 },
  par: 50,
});

export const REUTILIZABLES: RaceDef = {
  id: 'reutilizables',
  name: 'LOS COHETES QUE VUELVEN',
  subtitle: '2004 - 2021 · vuelos suborbitales y aterrizajes verticales',
  blurb: 'Ansari X Prize, el primer aterrizaje vertical y la carrera de los multimillonarios. Subir es fácil: bajar en una plataforma diminuta, no.',
  stages: [r1, r2, r3],
};

// ======================================================================= Boonta Eve (fiction)

export const TATOOINE = (pads: BodyDef['pads']): BodyDef => ({ id: 'tatooine', name: 'Tatooine', r: 300, g: 48, color: '#ffc46b', x: 0, y: 0, atm: { h: 55, drag: 0.002 }, pads });

export const lap = (r: number, from: number, to: number, n: number): ReturnType<typeof gate>[] => {
  const out: ReturnType<typeof gate>[] = [];
  for (let i = 0; i < n; i++) out.push(gate(r, from + ((to - from) * i) / (n - 1)));
  return out;
};

const b1 = stage({
  id: 1,
  name: 'Mos Espa',
  blurb: 'Una vuelta rasante al planeta. Sebulba va a chocarte en cuanto pueda.',
  skulls: 2,
  bodies: [TATOOINE([pad('Mos Espa', true, 52), pad('Pozo de Sebulba', false, 52, 55)])],
  gates: [...lap(430, 80, -250, 9), { x: 0, y: 410, final: true }],
  asteroids: [{ count: 12, seed: 131, around: 'tatooine', rIn: 520, rOut: 760, size: [4, 7], speed: 0.9 }],
  cells: [{ ...gate(430, -70), fuel: 30 }],
  start: startOn('tatooine'),
  rivalStart: startOn('tatooine', 55),
  rival: { skill: 0.9, name: 'Sebulba', delay: 6, ai: { noise: 0.1 } },
  finish: { body: 'tatooine', pad: 0 },
  par: 50,
});

const b2 = stage({
  id: 2,
  name: 'Cañón del Mendigo',
  blurb: 'Dos lunas y un pasillo estrecho entre ellas. Hay que entrar, salir y volver sin tocar las paredes.',
  skulls: 3,
  bodies: [
    TATOOINE([pad('Mos Espa', true, 52), pad('Pozo de Sebulba', false, 52, 55)]),
    { id: 'luna1', name: 'Ghomrassen', r: 70, g: 40, color: '#e8c9a0', orbit: { parent: 'tatooine', a: 900, phase: 0.5, omega: 0.03 } },
    { id: 'luna2', name: 'Guermessa', r: 60, g: 36, color: '#d9a066', orbit: { parent: 'tatooine', a: 1250, phase: 2.2, omega: -0.025 } },
  ],
  gates: [...lap(440, 80, -20, 4), { x: 700, y: -420 }, { x: 0, y: -520 }, { x: -600, y: -150 }, { x: -430, y: 250 }, { x: 0, y: 410, final: true }],
  asteroids: [{ count: 18, seed: 132, around: 'tatooine', rIn: 500, rOut: 900, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 600, y: -300, fuel: 30 }],
  start: startOn('tatooine'),
  rivalStart: startOn('tatooine', 55),
  rival: { skill: 0.9, name: 'Sebulba', delay: 5, ai: { noise: 0.1 } },
  finish: { body: 'tatooine', pad: 0 },
  par: 60,
});

const b3 = stage({
  id: 3,
  name: 'La gran final',
  blurb: 'Vuelta rápida, tormenta de arena y escombros por todos lados. Ganás aterrizando; Sebulba, sabés cómo.',
  skulls: 4,
  bodies: [TATOOINE([pad('Mos Espa', true, 46), pad('Pozo de Sebulba', false, 52, 55)])],
  gates: [...lap(400, 80, -330, 12), { x: 0, y: 410, final: true }],
  fields: [{ x: 0, y: -300, r: 300, kind: 'wind', ax: 30, ay: 10, color: '#ffb000', label: 'TORMENTA' }],
  asteroids: [{ count: 20, seed: 133, around: 'tatooine', rIn: 480, rOut: 760, size: [4, 8], speed: 0.95 }],
  cells: [{ ...gate(400, 20), fuel: 30 }, { ...gate(400, -150), fuel: 30 }],
  start: startOn('tatooine'),
  rivalStart: startOn('tatooine', 55),
  rival: { skill: 0.92, name: 'Sebulba', delay: 8, ai: { noise: 0.08, interval: 0.15 } },
  finish: { body: 'tatooine', pad: 0 },
  par: 70,
});

export const BOONTA: RaceDef = {
  id: 'boonta',
  name: 'LA CARRERA DE BOONTA EVE',
  subtitle: 'Ficción · carrera de vainas en Tatooine',
  blurb: 'Vueltas rasantes a un planeta de arena, con un rival que te empuja contra las rocas. Pura velocidad cerca del piso.',
  stages: [b1, b2, b3],
};

// ======================================================================= Redline (fiction)

const SOL: BodyDef = { id: 'sol', name: 'Estrella', r: 190, g: 110, color: '#ffd23a', x: 0, y: 0, star: true };

const d1 = stage({
  id: 1,
  name: 'Clasificatoria',
  blurb: 'Una vuelta a una estrella enana. Cuanto más cerca pasás, más rápido vas; cuanto más cerca, más quema.',
  skulls: 3,
  bodies: [SOL, { id: 'pista', name: 'Pista', r: 100, g: 48, color: '#ff2bd6', orbit: { parent: 'sol', a: 1400, phase: 0.4, omega: 0.015 }, pads: [pad('Largada', true, 40), pad('Parrilla', false, 40, 60)] }],
  gates: [near('pista', 0, 250), { x: 800, y: 900 }, { x: 0, y: 1100 }, { x: -900, y: 600 }, { x: -900, y: -500 }, { x: 0, y: -900 }, { x: 800, y: -600 }, near('pista', 0, 210, { final: true })],
  asteroids: [{ count: 16, seed: 141, around: 'sol', rIn: 700, rOut: 1700, size: [4, 8], speed: 0.9 }],
  cells: [{ x: 700, y: 600, fuel: 30 }, { x: -800, y: 0, fuel: 30 }],
  start: startOn('pista'),
  rivalStart: startOn('pista', 60),
  rival: { skill: 0.9, name: 'Sonoshee', delay: 12 },
  finish: { body: 'pista', pad: 0 },
  par: 75,
});

const d2 = stage({
  id: 2,
  name: 'Roboworld',
  blurb: 'Un planeta que dispara contra la carrera. Mucha radiación y un pasillo de minas hasta la meta.',
  skulls: 4,
  bodies: [
    { id: 'robo', name: 'Roboworld', r: 260, g: 66, color: '#ff3b3b', x: 0, y: 0, pads: [pad('Entrada', true, 44), pad('Parrilla', false, 44, 55)] },
    { id: 'base', name: 'Base', r: 70, g: 40, color: '#00f0ff', orbit: { parent: 'robo', a: 1500, phase: 0.2, omega: 0.02 }, pads: [pad('Salida', true, 36)] },
  ],
  gates: [gate(600, 85), { x: 700, y: 900 }, { x: 1000, y: 1100 }, near('base', -350, -120), near('base', -140, 40), near('base', 0, 170, { final: true })],
  fields: [{ x: 500, y: 600, r: 400, kind: 'radiation', dps: 8, color: '#ff2bd6', label: 'FUEGO' }],
  asteroids: [{ count: 30, seed: 142, around: 'robo', rIn: 600, rOut: 1500, size: [4, 8], speed: 0.95 }],
  cells: [{ x: 300, y: 800, fuel: 35 }, { x: 0, y: 120, body: 'base', fuel: 35 }],
  start: startOn('robo'),
  rivalStart: startOn('robo', 55),
  rival: { skill: 0.9, name: 'Machinehead', delay: 9 },
  finish: { body: 'base', pad: 0 },
  par: 60,
});

const d3 = stage({
  id: 3,
  name: 'Redline',
  blurb: 'La carrera más peligrosa del universo: dos agujeros negros, una estrella y el rival que no frena.',
  skulls: 5,
  bodies: [
    { id: 'sol', name: 'Estrella', r: 170, g: 100, color: '#ffd23a', x: 1700, y: 0, star: true },
    { id: 'h1', name: 'Pozo A', r: 48, g: 300, color: '#b46bff', x: 900, y: 450, hole: true },
    { id: 'h2', name: 'Pozo B', r: 50, g: 310, color: '#b46bff', x: 2600, y: -500, hole: true },
    { id: 'salida', name: 'Meta', r: 100, g: 48, color: '#7dff6b', x: 3600, y: 100, pads: [pad('Meta', true, 46)] },
    { id: 'largada', name: 'Largada', r: 220, g: 70, color: '#ff2bd6', x: 0, y: 0, atm: { h: 40, drag: 0.003 }, pads: [pad('Largada', true, 50), pad('Parrilla', false, 50, 55)] },
  ],
  gates: [gate(560, 80), { x: 550, y: 800 }, { x: 1400, y: 700 }, { x: 1700, y: 400 }, { x: 2100, y: -500 }, { x: 3000, y: -300 }, { x: 3600, y: 210, final: true }],
  asteroids: [{ count: 24, seed: 143, around: 'sol', rIn: 500, rOut: 1200, size: [4, 9], speed: 0.95 }],
  cells: [{ x: 600, y: 700, fuel: 35 }, { x: 1500, y: 600, fuel: 35 }, { x: 3100, y: -200, fuel: 35 }],
  start: startOn('largada'),
  rivalStart: startOn('largada', 55),
  rival: { skill: 0.92, name: 'Sonoshee', delay: 10, ai: { interval: 0.15, noise: 0.1 } },
  finish: { body: 'salida', pad: 0 },
  par: 85,
});

export const REDLINE: RaceDef = {
  id: 'redline',
  name: 'REDLINE',
  subtitle: 'Ficción · la carrera más peligrosa del universo',
  blurb: 'Una carrera clandestina entre estrellas, planetas armados y agujeros negros. Neón, velocidad y muy poco margen.',
  stages: [d1, d2, d3],
};
