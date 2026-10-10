import { type BodyDef } from './bodies';

/** Reference terminal velocity of the nose-first ship at Earth sea level. */
const TERMINAL_V = 80;
const DRAG_C0 = 25 / (TERMINAL_V * TERMINAL_V);
const REF_MASS = 2000;
/** Heating coefficient: heat units per second per (density * speed^3). */
export const HEAT_K = 1.8e-5;
/** Fraction of stored heat radiated away per second. */
export const HEAT_COOL = 0.04;
/** Gas scoop: fuel gained per second per (density * speed). */
export const SCOOP_K = 100;

/** Relative air density at altitude alt above the body's mean radius. */
export function density(b: BodyDef, alt: number): number {
  const a = b.atmosphere;
  if (!a) return 0;
  return a.density * Math.exp(-alt / a.scaleHeight);
}

/** Altitude above which the atmosphere is treated as vacuum. */
export function atmosphereTop(b: BodyDef): number {
  return b.atmosphere ? b.atmosphere.scaleHeight * 8 : 0;
}

/** Cross-section factor: 1 nose-first, up to 3.5 broadside. */
export function areaFactor(angleOfAttack: number): number {
  return 1 + 2.5 * Math.abs(Math.sin(angleOfAttack));
}

/** Heating multiplier: the shielded nose takes less than the flanks. */
export function heatFactor(angleOfAttack: number): number {
  return 1 + 1.5 * Math.abs(Math.sin(angleOfAttack));
}

/** Drag deceleration magnitude per unit speed squared. */
export function dragCoefficient(rho: number, aoa: number, mass: number): number {
  return DRAG_C0 * rho * areaFactor(aoa) * (REF_MASS / mass);
}
