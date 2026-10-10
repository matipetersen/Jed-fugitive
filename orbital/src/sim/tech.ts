export type EngineId = 'chem' | 'hyper' | 'nerva' | 'ion';

export interface ShipStats {
  dryMass: number;
  fuelCap: number;
  thrust: number;
  ve: number;
  turnRate: number;
  maxLandSpeed: number;
  maxLandTilt: number;
  heatLimit: number;
  /** Detection range for hazards, in u. */
  radarRange: number;
  /** ISRU production multiplier at bases. */
  isru: number;
}

export interface EngineDef {
  id: EngineId;
  name: string;
  thrust: number;
  ve: number;
  extraMass: number;
  tech: string | null;
}

export const ENGINES: EngineDef[] = [
  { id: 'chem', name: 'Químico', thrust: 80000, ve: 866, extraMass: 0, tech: null },
  { id: 'hyper', name: 'Hipergólico', thrust: 90000, ve: 1000, extraMass: 0, tech: 'hyper' },
  { id: 'nerva', name: 'Nuclear térmico', thrust: 60000, ve: 2000, extraMass: 250, tech: 'nerva' },
  { id: 'ion', name: 'Iónico', thrust: 10000, ve: 5500, extraMass: 150, tech: 'ion' },
];

export interface TechDef {
  id: string;
  name: string;
  desc: string;
  cost: number;
  /** Milestone number that must be done first (0 = none). */
  milestone: number;
  prereq?: string;
}

export const TECHS: TechDef[] = [
  { id: 'tanks1', name: 'Tanques ampliados', desc: '+600 de combustible', cost: 30, milestone: 1 },
  { id: 'hyper', name: 'Motor hipergólico', desc: 'Más empuje y Isp (1000)', cost: 45, milestone: 2 },
  { id: 'legs', name: 'Patas reforzadas', desc: 'Aterrizaje hasta 20 u/s', cost: 25, milestone: 3 },
  { id: 'radar1', name: 'Radar de largo alcance', desc: 'Detección de peligros x1.7', cost: 30, milestone: 3 },
  { id: 'tanks2', name: 'Tanques grandes', desc: '+1400 de combustible', cost: 70, milestone: 4, prereq: 'tanks1' },
  { id: 'isru', name: 'Extractores mejorados', desc: 'Las bases producen x2', cost: 60, milestone: 5 },
  { id: 'shield', name: 'Escudo térmico', desc: 'Límite de calor 170', cost: 50, milestone: 6 },
  { id: 'nerva', name: 'Motor nuclear térmico', desc: 'Isp 2000, empuje 60k', cost: 140, milestone: 7, prereq: 'hyper' },
  { id: 'radar2', name: 'Radar profundo', desc: 'Detección x3.7', cost: 70, milestone: 8, prereq: 'radar1' },
  { id: 'ion', name: 'Motor iónico', desc: 'Isp 5500, empuje bajo', cost: 200, milestone: 9, prereq: 'nerva' },
];

export const techById = (id: string): TechDef | undefined => TECHS.find((t) => t.id === id);
export const engineById = (id: EngineId): EngineDef => ENGINES.find((e) => e.id === id)!;

export const BASE_STATS: ShipStats = {
  dryMass: 1000,
  fuelCap: 1000,
  thrust: 80000,
  ve: 866,
  turnRate: 2.2,
  maxLandSpeed: 12,
  maxLandTilt: 0.35,
  heatLimit: 100,
  radarRange: 2400,
  isru: 1,
};

/** Builds ship stats from researched techs and the selected engine. */
export function statsFor(techs: readonly string[], engine: EngineId = 'chem'): ShipStats {
  const has = (id: string): boolean => techs.includes(id);
  const s: ShipStats = { ...BASE_STATS };
  const addTank = (fuel: number): void => {
    s.fuelCap += fuel;
    s.dryMass += fuel * 0.1;
  };
  if (has('tanks1')) addTank(600);
  if (has('tanks2')) addTank(1400);
  if (has('legs')) {
    s.maxLandSpeed = 20;
    s.maxLandTilt = 0.45;
  }
  if (has('shield')) s.heatLimit = 170;
  if (has('radar1')) s.radarRange = 4000;
  if (has('radar2')) s.radarRange = 9000;
  if (has('isru')) s.isru = 2;
  const e = engineById(engine);
  const usable = e.tech === null || has(e.tech) ? e : engineById('chem');
  s.thrust = usable.thrust;
  s.ve = usable.ve;
  s.dryMass += usable.extraMass;
  return s;
}
