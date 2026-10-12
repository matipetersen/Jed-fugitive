import { type BodyDef, type StageDef } from './types';
import { d2r, gate, near, pad, stage } from './build';
import { EARTH, JUP, SAT, TATOOINE, VENUS, comet, lap, startOn } from './more';

const landing = (body: string, padIdx: number): { x: number; y: number; landing: { body: string; pad: number } } => ({ x: 0, y: 0, landing: { body, pad: padIdx } });
const LUNA_R = 170;

// ======================================================================= Polo sur

export const polo_fall = stage({
  id: 0,
  name: 'Frenado lunar',
  year: 2023,
  blurb: 'Llegás cayendo hacia la Luna a mil kilómetros de altura. Frená a tiempo, rodeá y bajá al polo sur.',
  skulls: 3,
  bodies: [
    { id: 'luna', name: 'Luna', r: LUNA_R, g: 52, color: '#c8d4ff', x: 0, y: 0, pads: [pad('Polo sur', true, 32, 270)] },
  ],
  startAt: { body: 'luna', angle: 25, alt: 1100, speed: 0.4, dir: 1, inward: 70 },
  gates: [gate(760, -10), gate(560, -60), gate(470, -115), { x: 0, y: -290, final: true }],
  asteroids: [{ count: 10, seed: 201, around: 'luna', rIn: 450, rOut: 900, size: [3, 6], speed: 0.9 }],
  cells: [{ ...gate(700, -35), fuel: 30 }],
  start: startOn('luna', 270),
  rivalStart: startOn('luna', 270),
  tank: 0.7,
  rival: { skill: 0.88, name: 'Luna-25', delay: 4 },
  finish: { body: 'luna', pad: 0 },
  par: 40,
});

export const polo_double: StageDef = stage({
  id: 0,
  name: 'Doble alunizaje',
  year: 2023,
  blurb: 'Tres bases en la Luna. Aterrizá en la del este para recargar, volvé a despegar y buscá el polo sur.',
  skulls: 4,
  bodies: [
    { id: 'luna', name: 'Luna', r: LUNA_R, g: 52, color: '#c8d4ff', x: 0, y: 0, pads: [pad('Base oeste', true, 44, 180), pad('Plataforma rival', false, 44, 150), pad('Cabeus', true, 38, 0), pad('Polo sur', true, 26, 270)] },
  ],
  gates: [{ x: -300, y: 330 }, { x: 0, y: 440 }, { x: 300, y: 330 }, landing('luna', 2), { x: 420, y: -230 }, { x: 180, y: -420 }, { x: 0, y: -290, final: true }],
  asteroids: [{ count: 14, seed: 202, around: 'luna', rIn: 450, rOut: 750, size: [3, 6], speed: 0.9 }],
  cells: [{ x: 0, y: 470, fuel: 30 }],
  start: startOn('luna', 180),
  rivalStart: startOn('luna', 150),
  tank: 0.75,
  rival: { skill: 0.9, name: 'Luna-25', delay: 4, ai: { noise: 0.25 } },
  finish: { body: 'luna', pad: 3 },
  par: 50,
});

// ======================================================================= Venera

const VEN_PADS = (): BodyDef['pads'] => [pad('Valle Maxwell', true, 46), pad('Plataforma rival', false, 46, 120)];

export const venera_air = stage({
  id: 0,
  name: 'Aerofrenado',
  year: 1970,
  blurb: 'Entrás a Venus muy rápido. Rozá la parte alta de la atmósfera para frenar con el aire y bajá al valle.',
  skulls: 3,
  bodies: [VENUS(0, 0, VEN_PADS())],
  startAt: { body: 'venus', angle: 200, alt: 650, speed: 1.2, dir: 1, inward: 40 },
  gates: [gate(470, 250), gate(430, 300), gate(410, 350), gate(410, 40), { x: 0, y: 340, final: true }],
  fields: [{ body: 'venus', x: 0, y: 0, r: 440, kind: 'radiation', dps: 6, color: '#ff7a1a', label: 'CALOR' }],
  cells: [{ ...gate(450, 330), fuel: 30 }],
  start: startOn('venus', 90),
  rivalStart: startOn('venus', 120),
  tank: 0.8,
  rival: { skill: 0.9, name: 'Venera 8', delay: 4 },
  finish: { body: 'venus', pad: 0 },
  par: 40,
});

export const venera_balloon = stage({
  id: 0,
  name: 'Aerostato',
  year: 1985,
  blurb: 'Dos globos de la misión Vega flotan en las nubes. Posate en uno, recargá y bajá a la superficie.',
  skulls: 4,
  bodies: [
    VENUS(0, 0, VEN_PADS()),
    { id: 'orbital', name: 'Orbital', r: 25, g: 12, color: '#00f0ff', orbit: { parent: 'venus', a: 1050, phase: 0.2, omega: 0.04 }, pads: [pad('Orbital', true, 20), pad('Orbital 2', false, 20, 150)] },
    { id: 'aerostato', name: 'Aerostato', r: 40, g: 10, color: '#7dff6b', orbit: { parent: 'venus', a: 560, phase: 1.1, omega: 0.05 }, pads: [pad('Globo Vega', true, 24)] },
  ],
  gates: [landing('aerostato', 0), { x: -200, y: 520 }, { x: -60, y: 400 }, { x: 0, y: 340, final: true }],
  fields: [{ body: 'venus', x: 0, y: 0, r: 330, kind: 'radiation', dps: 4, color: '#ff7a1a', label: 'CALOR' }],
  cells: [{ x: 300, y: 600, fuel: 30 }],
  start: startOn('orbital'),
  rivalStart: startOn('orbital', 150),
  tank: 0.75,
  rival: { skill: 0.9, name: 'Vega 2', delay: 4 },
  finish: { body: 'venus', pad: 0 },
  par: 50,
});

// ======================================================================= Halley

export const halley_chase = stage({
  id: 0,
  name: 'Persecución',
  year: 1986,
  blurb: 'Salís de la órbita terrestre ya lanzado y con poco combustible. El cometa no espera: alcanzalo.',
  skulls: 4,
  bodies: [EARTH(), comet(40, 0.2)],
  startAt: { body: 'tierra', angle: -30, alt: 450, speed: 1.3, dir: 1 },
  gates: [{ x: 900, y: -1100 }, near('halley', 600, 200), near('halley', 320, -140), near('halley', 0, 110, { final: true })],
  fields: [{ body: 'halley', x: 0, y: 0, r: 420, kind: 'radiation', dps: 5, color: '#9be8ff', label: 'POLVO' }],
  asteroids: [{ count: 12, seed: 211, around: 'halley', rIn: 200, rOut: 650, size: [3, 6], speed: 0.9 }],
  cells: [{ x: 500, y: -900, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  tank: 0.7,
  rival: { skill: 0.9, name: 'Sakigake', delay: 5 },
  finish: { body: 'halley', pad: 0 },
  par: 50,
});

export const halley_cargo = stage({
  id: 0,
  name: 'Muestra de polvo',
  year: 1986,
  blurb: 'Despegá del núcleo, recogé la muestra en el chorro de polvo y llevala a la sonda que orbita arriba. Con la carga, la nave pesa.',
  skulls: 4,
  bodies: [
    { id: 'halley', name: 'Halley', r: 44, g: 7, color: '#9be8ff', x: 0, y: 0, pads: [pad('Núcleo', true, 36, 180), pad('Plataforma rival', false, 36, 150)] },
    { id: 'sonda', name: 'Sonda', r: 30, g: 9, color: '#00f0ff', orbit: { parent: 'halley', a: 900, phase: 1.0, omega: -0.05 }, pads: [pad('Sonda Vega', true, 26)] },
  ],
  gates: [{ x: -250, y: 260, cargo: true }, { x: -100, y: 520 }, near('sonda', -220, 90), near('sonda', 0, 90, { final: true })],
  fields: [{ x: 0, y: 0, r: 650, kind: 'radiation', dps: 8, color: '#9be8ff', label: 'CHORROS' }],
  asteroids: [{ count: 18, seed: 212, around: 'halley', rIn: 180, rOut: 700, size: [3, 6], speed: 0.9 }],
  cells: [{ x: -150, y: 380, fuel: 30 }],
  start: startOn('halley', 180),
  rivalStart: startOn('halley', 150),
  tank: 0.85,
  rival: { skill: 0.9, name: 'Vega 2', delay: 8 },
  finish: { body: 'sonda', pad: 0 },
  par: 45,
});

// ======================================================================= Voyager

export const voyager_belt = stage({
  id: 0,
  name: 'Cinturón de radiación',
  year: 1979,
  blurb: 'Júpiter está rodeado de un cinturón letal. Una vuelta completa a su alrededor, con radiación, y volvé a Ío.',
  skulls: 4,
  bodies: [
    JUP(0, 0),
    { id: 'io', name: 'Ío', r: 55, g: 40, color: '#ffd37a', orbit: { parent: 'jupiter', a: 2000, phase: 3.49, omega: 0.052 }, pads: [pad('Ío', true, 32), pad('Plataforma rival', false, 32, 40)] },
  ],
  gates: [gate(700, 230), gate(720, 290), gate(720, 350), gate(720, 50), gate(720, 110), gate(740, 170), near('io', -280, 40), near('io', 0, 160, { final: true })],
  fields: [{ body: 'jupiter', x: 0, y: 0, r: 1050, kind: 'radiation', dps: 4, color: '#ff2bd6', label: 'CINTURÓN DE RADIACIÓN' }],
  asteroids: [{ count: 14, seed: 221, around: 'jupiter', rIn: 800, rOut: 1400, size: [4, 8], speed: 0.95 }],
  cells: [{ ...gate(900, 320), fuel: 35 }, { ...gate(900, 100), fuel: 35 }],
  start: startOn('io'),
  rivalStart: startOn('io', 40),
  tank: 0.8,
  rival: { skill: 0.9, name: 'Voyager 2', delay: 8 },
  finish: { body: 'io', pad: 0 },
  par: 70,
});

export const voyager_rings = stage({
  id: 0,
  name: 'Anillos de Saturno',
  year: 1980,
  blurb: 'Cruzás los anillos a la deriva, con rocas que giran. Después de la última, Titán te espera abajo.',
  skulls: 5,
  bodies: [
    SAT(0, 0),
    { id: 'titan', name: 'Titán', r: 65, g: 42, color: '#e8a24a', orbit: { parent: 'saturno', a: 1900, phase: 4.3, omega: 0.0454 }, atm: { h: 45, drag: 0.006 }, pads: [pad('Titán', true, 34, 270)] },
  ],
  startAt: { body: 'saturno', angle: 100, alt: 520, speed: 1, dir: -1 },
  gates: [gate(620, 150), gate(700, 205), gate(760, 260), near('titan', -300, -60), near('titan', 0, -175, { final: true })],
  asteroids: [{ count: 44, seed: 222, around: 'saturno', rIn: 520, rOut: 900, size: [3, 7], speed: 1.0 }],
  cells: [{ ...gate(900, 280), fuel: 35 }],
  start: startOn('titan', 270),
  rivalStart: startOn('titan', 270),
  tank: 0.75,
  rival: { skill: 0.9, name: 'Voyager 2', delay: 4 },
  finish: { body: 'titan', pad: 0 },
  par: 55,
});

// ======================================================================= Marte 2020

const MARTE = (pads: BodyDef['pads']): BodyDef => ({ id: 'marte', name: 'Marte', r: 250, g: 55, color: '#ff5a3c', x: 0, y: 0, atm: { h: 60, drag: 0.0025 }, pads });
const FOBOS = (pads: BodyDef['pads']): BodyDef => ({ id: 'fobos', name: 'Fobos', r: 40, g: 8, color: '#b8a89a', orbit: { parent: 'marte', a: 1100, phase: 0.5, omega: 0.05 }, pads });

export const marte_entry = stage({
  id: 0,
  name: 'Captura marciana',
  year: 2021,
  blurb: 'Llegás con el motor casi apagado. Frená contra la gravedad de Marte, rodealo y posate en Fobos.',
  skulls: 3,
  bodies: [MARTE([pad('Cráter Jezero', true, 30), pad('Plataforma rival', false, 40, 60)]), FOBOS([pad('Fobos', true, 24, 270)])],
  startAt: { body: 'marte', angle: 150, alt: 900, speed: 0.9, dir: -1 },
  gates: [gate(650, 120), gate(600, 70), near('fobos', -260, -120), near('fobos', 0, -150, { final: true })],
  cells: [{ ...gate(640, 90), fuel: 30 }],
  start: startOn('marte', 90),
  rivalStart: startOn('marte', 60),
  tank: 0.7,
  rival: { skill: 0.9, name: 'Hope (EAU)', delay: 4 },
  finish: { body: 'fobos', pad: 0 },
  par: 45,
});

export const marte_cargo = stage({
  id: 0,
  name: 'Carga a Jezero',
  year: 2021,
  blurb: 'Fobos manda un cargamento al cráter. Recogelo en el despegue y llevalo hasta el suelo marciano.',
  skulls: 4,
  bodies: [
    MARTE([pad('Cráter Jezero', true, 28), pad('Plataforma rival', false, 40, 60)]),
    FOBOS([pad('Fobos', true, 24, 90), pad('Fobos 2', false, 24, 120)]),
  ],
  gates: [near('fobos', 0, 170, { cargo: true }), { x: 450, y: 800 }, { x: 160, y: 620 }, { x: 0, y: 360, final: true }],
  fields: [{ x: 0, y: 320, r: 240, kind: 'wind', ax: 20, ay: 0, color: '#ffb000', label: 'VIENTO' }],
  cells: [{ x: 500, y: 760, fuel: 30 }],
  start: startOn('fobos', 90),
  rivalStart: startOn('fobos', 120),
  tank: 0.75,
  rival: { skill: 0.9, name: 'Tianwen-1', delay: 4 },
  finish: { body: 'marte', pad: 0 },
  par: 45,
});

// ======================================================================= Reutilizables

export const reut_double = stage({
  id: 0,
  name: 'Dos vuelos en dos semanas',
  year: 2004,
  blurb: 'El reglamento exige dos vuelos con la misma nave. Subí, volvé a la pista dos, recargá y repetí.',
  skulls: 3,
  bodies: [EARTH([pad('Mojave', true, 55), pad('Pista 2', true, 50, 55)])],
  gates: [{ x: 0, y: 480 }, { x: 40, y: 680 }, { x: -20, y: 520 }, landing('tierra', 1), { x: 100, y: 520 }, { x: 60, y: 700 }, { x: 0, y: 380, final: true }],
  cells: [{ x: 30, y: 620, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 110),
  tank: 0.7,
  rival: { skill: 0.88, name: 'Armadillo Aerospace', delay: 6 },
  finish: { body: 'tierra', pad: 0 },
  par: 50,
});

export const reut_reentry = stage({
  id: 0,
  name: 'Reentrada',
  year: 2015,
  blurb: 'Volvés de la órbita a toda velocidad. El aire te calienta: bajá la velocidad y encontrá la barcaza.',
  skulls: 4,
  bodies: [EARTH([pad('Cabo Cañaveral', true, 50), pad('Barcaza', true, 20, 125)])],
  startAt: { body: 'tierra', angle: 200, alt: 900, speed: 0.9, dir: 1, inward: 150 },
  gates: [{ x: -750, y: 150 }, { x: -520, y: 360 }, { x: -200, y: 287, final: true }],
  fields: [{ body: 'tierra', x: 0, y: 0, r: 380, kind: 'radiation', dps: 6, color: '#ff7a1a', label: 'CALOR DE REENTRADA' }],
  cells: [{ x: -380, y: 380, fuel: 30 }],
  start: startOn('tierra'),
  rivalStart: startOn('tierra', 55),
  tank: 0.6,
  rival: { skill: 0.9, name: 'Falcon 9', delay: 3 },
  finish: { body: 'tierra', pad: 1 },
  par: 35,
});

// ======================================================================= Boonta Eve

export const boonta_night = stage({
  id: 0,
  name: 'Noche en las dunas',
  blurb: 'La vuelta al revés, desde el lado oscuro del planeta, con la nave a medio tanque.',
  skulls: 3,
  bodies: [TATOOINE([pad('Pozo oscuro', true, 52, 270), pad('Parrilla', false, 52, 235)])],
  gates: [...lap(430, 310, 590, 8), { x: 0, y: -410, final: true }],
  asteroids: [{ count: 16, seed: 231, around: 'tatooine', rIn: 520, rOut: 760, size: [4, 7], speed: 0.9 }],
  cells: [{ ...gate(430, 100), fuel: 30 }],
  start: startOn('tatooine', 270),
  rivalStart: startOn('tatooine', 235),
  tank: 0.7,
  rival: { skill: 0.9, name: 'Sebulba', delay: 6, ai: { noise: 0.1 } },
  finish: { body: 'tatooine', pad: 0 },
  par: 45,
});

export const boonta_run = stage({
  id: 0,
  name: 'Ruta de contrabando',
  blurb: 'Un desvío por la luna de Anchorhead: aterrizá para recoger el pago y terminá en Mos Eisley, al otro lado.',
  skulls: 4,
  bodies: [
    TATOOINE([pad('Mos Espa', true, 52, 180), pad('Pozo de Sebulba', false, 52, 150), pad('Mos Eisley', true, 52, 0)]),
    { id: 'anchorhead', name: 'Anchorhead', r: 70, g: 36, color: '#e8c9a0', orbit: { parent: 'tatooine', a: 900, phase: 0.5, omega: 0.03 }, pads: [pad('Anchorhead', true, 40)] },
  ],
  gates: [{ x: -480, y: 250 }, { x: -200, y: 620 }, landing('anchorhead', 0), { x: 560, y: 420 }, { x: 450, y: 150 }, { x: 410, y: 2, final: true }],
  asteroids: [{ count: 16, seed: 232, around: 'tatooine', rIn: 500, rOut: 800, size: [4, 7], speed: 0.9 }],
  cells: [{ x: -300, y: 420, fuel: 30 }, { x: 560, y: 300, fuel: 30 }],
  start: startOn('tatooine', 180),
  rivalStart: startOn('tatooine', 150),
  tank: 0.8,
  rival: { skill: 0.9, name: 'Sebulba', delay: 5, ai: { noise: 0.1 } },
  finish: { body: 'tatooine', pad: 2 },
  par: 55,
});

// ======================================================================= Redline

export const redline_fall = stage({
  id: 0,
  name: 'Caída al pozo',
  blurb: 'Salís de la nave nodriza cayendo hacia un agujero negro. Rodealo sin tocarlo y escapá hacia la meta.',
  skulls: 5,
  bodies: [
    { id: 'pozo', name: 'Pozo', r: 55, g: 320, color: '#b46bff', x: 0, y: 0, hole: true },
    { id: 'meta', name: 'Meta', r: 100, g: 48, color: '#7dff6b', x: 2500, y: -300, pads: [pad('Meta', true, 46)] },
  ],
  startAt: { body: 'pozo', angle: 160, alt: 1200, speed: 0.55, dir: 1, inward: 45 },
  gates: [gate(600, 215), gate(430, 275), gate(430, 340), { x: 1300, y: -250 }, { x: 2500, y: -90, final: true }],
  cells: [{ ...gate(520, 20), fuel: 35 }],
  asteroids: [{ count: 14, seed: 241, around: 'pozo', rIn: 400, rOut: 900, size: [4, 8], speed: 0.9 }],
  start: startOn('meta', 90),
  rivalStart: startOn('meta', 90),
  tank: 0.8,
  rival: { skill: 0.9, name: 'Sonoshee', delay: 4 },
  finish: { body: 'meta', pad: 0 },
  par: 50,
});

export const redline_cargo = stage({
  id: 0,
  name: 'Carga prohibida',
  blurb: 'Un paquete flota dentro de la corona de la estrella. Recogelo, aguantá el calor y entregalo antes que nadie.',
  skulls: 5,
  bodies: [
    { id: 'largada', name: 'Largada', r: 220, g: 70, color: '#ff2bd6', x: 0, y: 0, atm: { h: 40, drag: 0.003 }, pads: [pad('Largada', true, 50), pad('Parrilla', false, 50, 55)] },
    { id: 'sol', name: 'Estrella', r: 190, g: 110, color: '#ffd23a', x: 1600, y: 100, star: true },
    { id: 'meta', name: 'Meta', r: 100, g: 48, color: '#7dff6b', x: 3300, y: 600, pads: [pad('Meta', true, 44)] },
  ],
  gates: [gate(560, 80), { x: 700, y: 750 }, { x: 1600, y: 480, cargo: true }, { x: 2400, y: 500 }, { x: 3300, y: 810, final: true }],
  asteroids: [{ count: 20, seed: 242, around: 'sol', rIn: 500, rOut: 1100, size: [4, 8], speed: 0.95 }],
  cells: [{ x: 700, y: 600, fuel: 35 }, { x: 2600, y: 600, fuel: 35 }],
  start: startOn('largada'),
  rivalStart: startOn('largada', 55),
  tank: 0.75,
  rival: { skill: 0.92, name: 'Sonoshee', delay: 7 },
  finish: { body: 'meta', pad: 0 },
  par: 70,
});

void d2r;
