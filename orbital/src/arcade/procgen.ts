import { mulberry32 } from '../sim/rng';
import { type BodyDef, type GateDef, type RaceDef, type StageDef } from './types';
import { d2r, pad, stage } from './build';

type Rnd = () => number;
const TAU = Math.PI * 2;
const between = (r: Rnd, a: number, b: number): number => a + (b - a) * r();
const pick = <T>(r: Rnd, xs: T[]): T => xs[Math.floor(r() * xs.length)];
const round = (n: number): number => Math.round(n);

const NAMES = ['Oriax', 'Kepler', 'Talos', 'Nyx', 'Vesta', 'Hadar', 'Ceto', 'Lyra', 'Orsk', 'Tamsin', 'Brisa', 'Drav', 'Eris', 'Ilmar', 'Quor', 'Selva', 'Umbra', 'Zeph'];
const COLORS = ['#2f7bff', '#ff5a3c', '#ffb000', '#7dff6b', '#c8d4ff', '#ff2bd6', '#00f0ff', '#b48cff'];
const RIVALS = ['Fantasma', 'Cuervo', 'Halcón negro', 'Aguja', 'Relámpago', 'Víbora', 'Cometa', 'Sombra'];

interface P2 {
  x: number;
  y: number;
}

/** A point on the line from a to b, with a sideways offset. */
function along(a: P2, b: P2, t: number, side: number): P2 {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const l = Math.hypot(dx, dy) || 1;
  return { x: round(a.x + dx * t - (dy / l) * side), y: round(a.y + dy * t + (dx / l) * side) };
}

const TEMPLATES = ['hop', 'hop', 'circuit', 'gauntlet', 'double', 'cargo', 'fall'] as const;
type Template = (typeof TEMPLATES)[number];

/** Difficulty knobs shared by all templates; d runs from 0 (easy) to 1 (brutal). */
function knobs(d: number, r: Rnd): { padHalf: number; asteroids: number; tank: number; skill: number; delay: number; noise: number } {
  return {
    padHalf: round(46 - 22 * d),
    asteroids: round(8 + 24 * d + between(r, 0, 6)),
    tank: Math.round((1 - 0.35 * d) * 100) / 100,
    skill: Math.round((0.86 + 0.07 * d) * 100) / 100,
    delay: round(10 - 5 * d),
    noise: Math.round((0.25 - 0.13 * d) * 100) / 100,
  };
}

/**
 * One random stage. The geometry comes from a handful of vetted templates (a hop between planets,
 * a circuit, a slalom around holes, a hop with a mid-way landing, a hop with cargo, a fall), so
 * a stage is never impossible; `scripts/verify-races.ts` and the tests check that a pilot can fly them.
 */
export function generateStage(seed: number, index: number, d: number, template?: Template): StageDef {
  const r = mulberry32(seed * 7919 + index * 104729 + 17);
  const tpl: Template = template ?? pick(r, [...TEMPLATES]);
  const k = knobs(d, r);
  const aName = pick(r, NAMES);
  let bName = pick(r, NAMES);
  if (bName === aName) bName = pick(r, NAMES) + ' II';
  const rivalName = pick(r, RIVALS);
  const skulls = Math.max(1, Math.min(5, 1 + Math.round(d * 4)));

  // Planet A at the origin: where the ship starts (except for the fall template).
  const aR = round(between(r, 190, 270));
  const dir = between(r, 0, TAU);
  const D = round(between(r, 1900, 3100));
  const B: P2 = { x: round(Math.cos(dir) * D), y: round(Math.sin(dir) * D) };
  const startDeg = Math.round((dir / d2r) % 360);
  const backDeg = Math.round(((dir + Math.PI) / d2r) % 360);
  const bR = round(between(r, 70, 120));
  const A: BodyDef = {
    id: 'a',
    name: aName,
    r: aR,
    g: round(between(r, 60, 90)),
    color: pick(r, COLORS),
    x: 0,
    y: 0,
    atm: r() < 0.6 ? { h: 45, drag: 0.003 } : undefined,
    pads: [pad(`Base ${aName}`, true, 50, startDeg), pad('Parrilla rival', false, 50, startDeg + 35)],
  };
  const Bb: BodyDef = {
    id: 'b',
    name: bName,
    r: bR,
    g: round(between(r, 36, 52)),
    color: pick(r, COLORS),
    x: B.x,
    y: B.y,
    pads: [pad(`Puerto ${bName}`, true, k.padHalf, backDeg)],
  };
  const bodies: BodyDef[] = [A, Bb];
  const finalGate: GateDef = { x: round(B.x + Math.cos(dir + Math.PI) * (bR + 110)), y: round(B.y + Math.sin(dir + Math.PI) * (bR + 110)), final: true };
  const startAt = { x: round(Math.cos(dir) * (aR + 280)), y: round(Math.sin(dir) * (aR + 280)) };
  const path = (n: number, wiggle: number, from: P2 = startAt, to: P2 = finalGate): GateDef[] => {
    const out: GateDef[] = [];
    for (let i = 1; i <= n; i++) out.push({ ...along(from, to, i / (n + 1), (i % 2 ? 1 : -1) * between(r, wiggle * 0.3, wiggle)) });
    return out;
  };
  const fields: StageDef['fields'] = [];
  const asteroids: StageDef['asteroids'] = [{ count: k.asteroids, seed: seed + index * 13, around: r() < 0.5 ? 'a' : 'b', rIn: round(between(r, 450, 700)), rOut: round(between(r, 800, 1300)), size: [4, 8], speed: 0.9 }];
  const cells = [along(startAt, finalGate, 0.3, 80), along(startAt, finalGate, 0.7, -80)].map((c) => ({ ...c, fuel: 35 }));
  let gates: GateDef[];
  let blurb: string;
  let kind: string;
  let startSpec: Partial<StageDef> = {};
  let finish: StageDef['finish'] = { body: 'b', pad: 0 };
  let start = { body: 'a', angle: startDeg * d2r };
  let rivalStart = { body: 'a', angle: (startDeg + 35) * d2r };

  if (tpl === 'hop') {
    gates = [...path(3 + Math.round(d * 2), 260), finalGate];
    blurb = `Un salto de ${aName} a ${bName}. El rival sale de la parrilla de al lado.`;
    kind = 'Salto';
    if (r() < 0.4 + 0.3 * d) fields.push({ ...along(startAt, finalGate, 0.5, 0), r: 260, kind: 'wind', ax: round(between(r, -26, 26)), ay: round(between(r, -26, 26)), color: '#ffb000', label: 'VIENTO' });
  } else if (tpl === 'gauntlet') {
    // Two holes either side of the line, with the gates threading between them.
    const side1 = r() < 0.5 ? 1 : -1;
    const hole = (id: string, t: number, side: number, rr: number): BodyDef => ({ id, name: `Pozo ${id.toUpperCase()}`, r: rr, g: 290, color: '#b46bff', ...along(startAt, finalGate, t, side * between(r, 470, 560)), hole: true });
    bodies.push(hole('h1', 0.38, side1, 48), hole('h2', 0.66, -side1, 52));
    gates = [{ ...along(startAt, finalGate, 0.2, 0) }, { ...along(startAt, finalGate, 0.38, -side1 * 130) }, { ...along(startAt, finalGate, 0.52, 0) }, { ...along(startAt, finalGate, 0.66, side1 * 130) }, { ...along(startAt, finalGate, 0.82, 0) }, finalGate];
    blurb = `Dos agujeros negros entre ${aName} y ${bName}. El pasillo es angosto.`;
    kind = 'Gauntlet';
    fields.push({ body: 'h1', x: 0, y: 0, r: 330, kind: 'radiation', dps: 5, color: '#ff2bd6', label: 'DISCO' });
  } else if (tpl === 'double') {
    const side = r() < 0.5 ? 1 : -1;
    const mid = along(startAt, finalGate, 0.5, side * 340);
    bodies.push({ id: 'm', name: `Escala ${pick(r, NAMES)}`, r: 62, g: 36, color: pick(r, COLORS), x: mid.x, y: mid.y, pads: [pad('Escala', true, 40 - round(8 * d), Math.round((Math.atan2(-mid.y + (startAt.y + finalGate.y) / 2, -mid.x + (startAt.x + finalGate.x) / 2) / d2r + 360) % 360))] });
    gates = [{ ...along(startAt, finalGate, 0.2, side * 120) }, { x: 0, y: 0, landing: { body: 'm', pad: 0 } }, { ...along(mid, finalGate, 0.5, side * 120) }, finalGate];
    blurb = `Con escala: aterrizá a mitad de camino, recargá y seguí hacia ${bName}.`;
    kind = 'Dos aterrizajes';
  } else if (tpl === 'cargo') {
    gates = [...path(1, 200, startAt, along(startAt, finalGate, 0.45, 0)), { ...along(startAt, finalGate, 0.5, between(r, -160, 160)), cargo: true }, ...path(1, 200, along(startAt, finalGate, 0.55, 0), finalGate), finalGate];
    blurb = `Recogé la carga a mitad de camino y entregala en ${bName}. Pesa: el empuje baja.`;
    kind = 'Carga';
  } else if (tpl === 'circuit') {
    const n = 7 + Math.round(d * 3);
    const cw = r() < 0.5 ? 1 : -1;
    const rr = aR + 190;
    gates = [];
    for (let i = 1; i <= n; i++) {
      const a = (startDeg + cw * (360 * i) / (n + 1)) * d2r;
      gates.push({ x: round(Math.cos(a) * (rr + between(r, 0, 120))), y: round(Math.sin(a) * (rr + between(r, 0, 120))) });
    }
    gates.push({ x: round(Math.cos(startDeg * d2r) * (aR + 110)), y: round(Math.sin(startDeg * d2r) * (aR + 110)), final: true });
    bodies.length = 0;
    bodies.push({ ...A, pads: [pad(`Base ${aName}`, true, k.padHalf + 6, startDeg), pad('Parrilla rival', false, 50, startDeg + 35)] });
    bodies.push({ id: 'm', name: pick(r, NAMES), r: 55, g: 36, color: pick(r, COLORS), orbit: { parent: 'a', a: round(aR + between(r, 700, 1000)), phase: between(r, 0, TAU), omega: Math.round(between(r, 0.02, 0.04) * cw * 1000) / 1000 } });
    finish = { body: 'a', pad: 0 };
    asteroids[0].around = 'a';
    blurb = `Una vuelta completa a ${aName} y de regreso a la plataforma. Cuidado con la luna.`;
    kind = 'Circuito';
    cells.length = 0;
    cells.push({ x: round(Math.cos((startDeg + 140 * cw) * d2r) * (rr + 40)), y: round(Math.sin((startDeg + 140 * cw) * d2r) * (rr + 40)), fuel: 35 });
  } else {
    // Fall: no pad to leave; the ship drops towards a planet and has to brake and land on it.
    const cr = round(between(r, 160, 240));
    const padDeg = Math.round(between(r, 0, 360));
    bodies.length = 0;
    bodies.push({ id: 'b', name: bName, r: cr, g: round(between(r, 55, 80)), color: pick(r, COLORS), x: 0, y: 0, atm: r() < 0.5 ? { h: 40, drag: 0.003 } : undefined, pads: [pad(`Puerto ${bName}`, true, k.padHalf + 4, padDeg)] });
    const pn = padDeg * d2r;
    const a0 = padDeg + 70;
    gates = [
      { x: round(Math.cos((a0) * d2r) * (cr + 600)), y: round(Math.sin(a0 * d2r) * (cr + 600)) },
      { x: round(Math.cos((a0 - 40) * d2r) * (cr + 380)), y: round(Math.sin((a0 - 40) * d2r) * (cr + 380)) },
      { x: round(Math.cos(pn) * (cr + 110)), y: round(Math.sin(pn) * (cr + 110)), final: true },
    ];
    startSpec = { startAt: { body: 'b', angle: a0 + 40, alt: 1000, speed: 0.4, dir: 1, inward: 60 } };
    start = { body: 'b', angle: pn };
    rivalStart = { body: 'b', angle: pn };
    finish = { body: 'b', pad: 0 };
    asteroids[0].around = 'b';
    cells.length = 0;
    cells.push({ x: round(Math.cos((a0 - 10) * d2r) * (cr + 480)), y: round(Math.sin((a0 - 10) * d2r) * (cr + 480)), fuel: 30 });
    blurb = `Caés hacia ${bName} sin plataforma de salida. Frená, rodealo y posate.`;
    kind = 'Caída libre';
  }

  if (d > 0.45 && r() < 0.6 && tpl !== 'gauntlet') fields.push({ ...along(startAt, finalGate, 0.55, 150), r: 280, kind: 'radiation', dps: round(4 + 6 * d), color: '#ff2bd6', label: 'RADIACIÓN' });

  return stage({
    id: index + 1,
    name: bName,
    blurb: `${blurb}`,
    skulls,
    bodies,
    gates,
    fields,
    asteroids,
    cells,
    start,
    rivalStart,
    tank: k.tank,
    rival: { skill: k.skill, name: rivalName, delay: k.delay, ai: { noise: k.noise } },
    finish,
    par: 50,
    ...startSpec,
    kind,
  });
}

/** Days since the epoch, the same for everyone on the same day. */
export const dailySeed = (now = new Date()): number => Math.floor(now.getTime() / 86400000);
export const dailyLabel = (now = new Date()): string => (Number.isNaN(now.getTime()) ? 'al azar' : now.toISOString().slice(0, 10));

/** A whole random race. `kind` decides the length and how fast it ramps up. */
export function makeProceduralRace(kind: 'diaria' | 'sinfin', seed: number): RaceDef {
  const count = kind === 'diaria' ? 6 : 10;
  const stages = Array.from({ length: count }, (_, i) => generateStage(seed, i, (i / (count - 1)) * (kind === 'diaria' ? 0.85 : 1)));
  return kind === 'diaria'
    ? {
        id: 'diaria',
        name: 'CARRERA DIARIA',
        subtitle: `Semilla ${dailyLabel(new Date(seed * 86400000))} · la misma para todos hoy`,
        blurb: 'Seis sectores generados con la fecha de hoy, cada vez más difíciles. Mañana cambian.',
        stages,
      }
    : {
        id: 'sinfin',
        name: 'SECTOR ALEATORIO',
        subtitle: 'Cada misión genera sectores nuevos',
        blurb: 'Diez sectores al azar, de fáciles a brutales. No hay dos misiones iguales.',
        stages,
      };
}

/**
 * The daily Grand Prix: 9 to 12 ships start from pads all round one planet and race two laps through
 * the same gates before landing on a wide finish pad. The first three to land make the podium.
 */
export function makeGrandPrix(seed: number): RaceDef {
  const r = mulberry32(seed * 6151 + 99);
  const n = 9 + Math.floor(r() * 4);
  const aName = pick(r, NAMES);
  const R0 = 300;
  const a0 = Math.round(between(r, 0, 360));
  const step = 360 / n;
  const slotAngle = (k: number): number => (a0 + step * k) % 360;
  const pads = Array.from({ length: n }, (_, k) => pad(`Grilla ${k + 1}`, true, 30, slotAngle(k)));
  const playerSlot = Math.floor(r() * n);
  const aiSlots = Array.from({ length: n }, (_, k) => k).filter((k) => k !== playerSlot).map((k) => slotAngle(k));
  const dir = r() < 0.5 ? 1 : -1;
  const perLap = 8;
  const rr = R0 + 250;
  const ring0 = Math.round(between(r, 0, 360));
  // One lap of gates. Every ship runs it from its own pad, so nobody starts closer to the line than anybody else.
  const gates: GateDef[] = [];
  for (let i = 0; i < perLap; i++) {
    const ang = (ring0 + dir * (360 / perLap) * i) * d2r;
    const rad = rr + between(r, -40, 70);
    gates.push({ x: round(Math.cos(ang) * rad), y: round(Math.sin(ang) * rad) });
  }
  const theta0 = ring0;
  const moon = (id: string, a: number, om: number): BodyDef => ({ id, name: pick(r, NAMES), r: 58, g: 38, color: pick(r, COLORS), orbit: { parent: 'a', a, phase: between(r, 0, TAU), omega: om } });
  const bodies: BodyDef[] = [
    { id: 'a', name: aName, r: R0, g: 80, color: pick(r, COLORS), x: 0, y: 0, atm: { h: 45, drag: 0.003 }, pads },
    moon('m1', 1150, Math.round(between(r, 0.02, 0.035) * 1000) / 1000),
    moon('m2', 1550, -Math.round(between(r, 0.015, 0.03) * 1000) / 1000),
  ];
  const st = stage({
    id: 1,
    name: `Gran Premio de ${aName}`,
    blurb: `${n} naves salen de todos lados del planeta ${aName}. Cada una corre dos vueltas por los mismos aros desde su propia grilla y vuelve a aterrizar en ella: todas la misma distancia. Gana el podio quien aterriza primero.`,
    skulls: 4,
    bodies,
    gates,
    asteroids: [{ count: 14, seed: seed + 5, around: 'a', rIn: 760, rOut: 1050, size: [4, 7], speed: 0.9 }],
    cells: [0, 1, 2].map((k) => ({ x: round(Math.cos((theta0 + dir * 120 * k + 30) * d2r) * (rr + 40)), y: round(Math.sin((theta0 + dir * 120 * k + 30) * d2r) * (rr + 40)), fuel: 35 })),
    start: { body: 'a', angle: slotAngle(playerSlot) * d2r },
    rivalStart: { body: 'a', angle: slotAngle((playerSlot + 1) % n) * d2r },
    field: { body: 'a', slots: aiSlots, podium: 3, laps: 2, dir: dir as 1 | -1 },
    tank: 0.9,
    rival: { skill: 0.76, name: 'Piloto', delay: 1.4, ai: { noise: 0.25 } },
    finish: { body: 'a', pad: 0 },
    par: 90,
    kind: 'Gran Premio',
  });
  return {
    id: 'granpremio',
    name: 'GRAN PREMIO DIARIO',
    subtitle: `Semilla ${dailyLabel(new Date(seed * 86400000))} · ${n} naves`,
    blurb: 'Una grilla de 9 a 12 naves con salida desde todos los lados del planeta. Cada una hace dos vueltas desde su pad y vuelve a él: todas la misma distancia. Hay que llegar al podio.',
    stages: [st],
  };
}
