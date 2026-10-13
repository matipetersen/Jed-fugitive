import { mulberry32 } from '../sim/rng';
import { generateStage, makeGrandPrix } from './procgen';
import { RACES } from './races';
import { makeSprintStage } from './sprint';
import { type RaceDef, type StageDef } from './types';

/** The kinds of mission the endless mode shuffles through. */
const KINDS = ['salto', 'sprint', 'clasica', 'gauntlet', 'escala', 'gran-premio', 'carga', 'caida', 'circuito', 'clasica'] as const;
type Kind = (typeof KINDS)[number];

const STAGES_IN_RUN = 120;
const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

/**
 * Difficulty of stage `i` (0-based): a slow climb with waves on top, so an easy breather follows a hard stage
 * and every third stage is a spike.
 */
export function endlessDifficulty(i: number): number {
  const base = 0.12 + i * 0.03;
  const wave = [0.65, 0.95, 1.3][i % 3];
  return clamp(base * wave, 0.05, 1);
}

/** The handcrafted stages of the real races, as a pool to draw from. */
function classicPool(): StageDef[] {
  return RACES.filter((r) => !r.endless && !['granpremio', 'diaria', 'sinfin', 'endless'].includes(r.id)).flatMap((r) => r.stages);
}

function pickClassic(rnd: () => number, d: number): StageDef {
  const pool = classicPool();
  const want = 1 + 4 * d;
  // Draw among the stages closest to the wanted difficulty.
  const sorted = [...pool].sort((a, b) => Math.abs(a.skulls - want) - Math.abs(b.skulls - want) || a.name.localeCompare(b.name));
  const top = sorted.slice(0, Math.max(6, Math.round(pool.length * 0.2)));
  return top[Math.floor(rnd() * top.length)];
}

/** One stage of the endless run. */
export function endlessStage(seed: number, i: number): StageDef {
  const d = endlessDifficulty(i);
  // Within each block of ten the kinds come in a different order.
  const block = Math.floor(i / KINDS.length);
  const order = [...KINDS];
  const shuffle = mulberry32(seed * 31 + block * 977);
  for (let k = order.length - 1; k > 0; k--) {
    const j = Math.floor(shuffle() * (k + 1));
    [order[k], order[j]] = [order[j], order[k]];
  }
  // Never open with something that needs a lot of reading: the first stage is a plain hop.
  const kind: Kind = i === 0 ? 'salto' : order[i % KINDS.length];
  const rnd = mulberry32(seed * 7 + i * 13);
  const sub = seed + i * 101;
  let def: StageDef;
  switch (kind) {
    case 'salto':
      def = generateStage(sub, i, d, 'hop');
      break;
    case 'gauntlet':
      def = generateStage(sub, i, d, 'gauntlet');
      break;
    case 'escala':
      def = generateStage(sub, i, d, 'double');
      break;
    case 'carga':
      def = generateStage(sub, i, d, 'cargo');
      break;
    case 'caida':
      def = generateStage(sub, i, d, 'fall');
      break;
    case 'circuito':
      def = generateStage(sub, i, d, 'circuit');
      break;
    case 'sprint':
      def = makeSprintStage(sub, d);
      break;
    case 'gran-premio':
      def = makeGrandPrix(sub).stages[0];
      break;
    default:
      def = pickClassic(rnd, d);
  }
  return { ...def, id: i + 1, kind: def.kind ?? 'Clásica' };
}

/** A fresh endless run: the same seed always gives the same sequence. */
export function makeEndlessRace(seed: number): RaceDef {
  return {
    id: 'endless',
    name: 'MODO ENDLESS',
    subtitle: 'Misiones y dificultades alternadas sin fin',
    blurb: 'Una racha de etapas de todos los tipos (saltos, sprints, gran premio, sobrevuelos, cargas, escalas) con la dificultad subiendo y bajando en olas. Tenés 3 continuaciones: perder una etapa gasta una, y cada 5 victorias seguidas ganás otra. Hasta dónde llegás.',
    stages: Array.from({ length: STAGES_IN_RUN }, (_, i) => endlessStage(seed, i)),
    endless: { continues: 3, maxContinues: 5 },
  };
}
