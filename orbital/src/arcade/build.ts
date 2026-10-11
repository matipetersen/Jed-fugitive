import { type BodyDef, type GateDef, type StageDef } from './types';

export const d2r = Math.PI / 180;
export const on = (r: number, deg: number): { x: number; y: number } => ({ x: Math.round(r * Math.cos(deg * d2r)), y: Math.round(r * Math.sin(deg * d2r)) });
export const gate = (r: number, deg: number, extra: Partial<GateDef> = {}): GateDef => ({ ...on(r, deg), ...extra });
/** A gate attached to a body, offset from its centre. */
export const near = (body: string, x: number, y: number, extra: Partial<GateDef> = {}): GateDef => ({ x, y, body, ...extra });

export const AI = { horizon: 1.2, dt: 0.05, interval: 0.2, noise: 0.2 };

type StageSpec = Omit<StageDef, 'year' | 'fields' | 'asteroids' | 'cells' | 'rival'> &
  Partial<Pick<StageDef, 'year' | 'fields' | 'asteroids' | 'cells'>> & { rival: Omit<StageDef['rival'], 'ai'> & { ai?: Partial<NonNullable<StageDef['rival']['ai']>> } };

/** A stage with the usual defaults filled in. */
export function stage(s: StageSpec): StageDef {
  return { year: 0, fields: [], asteroids: [], cells: [], ...s, rival: { ...s.rival, ai: { ...AI, ...s.rival.ai } } };
}

/** A pad on the top of a body, the usual start and finish. */
export const pad = (name: string, bonfire = true, half = 40, deg = 90): NonNullable<BodyDef['pads']>[number] => ({ angle: deg * d2r, half, name, bonfire });
