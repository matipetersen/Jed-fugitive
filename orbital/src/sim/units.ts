/**
 * Unit system. Length: 1 u = 6.371 km, so Earth's radius is exactly 1000 u.
 * Time: one game second is T_S real seconds, chosen so that Earth's real GM
 * maps to the game's Earth GM (g = 25 u/s^2). Every body is then built from real
 * radii, masses and orbits, so periods and delta-v ratios are the real ones.
 */
export const TAU = Math.PI * 2;
export const L_M = 6371;
const EARTH_GM_SI = 3.986004418e14;
export const EARTH_GM = 25 * 1000 * 1000;
/** Real seconds per game second. */
export const T_S = Math.sqrt((L_M ** 3 * EARTH_GM) / EARTH_GM_SI);

export const kmToU = (km: number): number => (km * 1000) / L_M;
/** Converts a real GM in km^3/s^2 to game units. */
export const gmKm3ToU = (gm: number): number => (gm * 1e9 * T_S * T_S) / L_M ** 3;

/** Game seconds in a real year and day. */
export const YEAR = (365.25 * 86400) / T_S;
export const DAY = 86400 / T_S;
export const AU = kmToU(149597870.7);

export const EPOCH_YEAR = 1957;
const EPOCH_MS = Date.UTC(EPOCH_YEAR, 0, 1);

export function dateOf(t: number): Date {
  return new Date(EPOCH_MS + t * T_S * 1000);
}

export function fmtDate(t: number): string {
  return dateOf(t).toISOString().slice(0, 10);
}

/** Calendar year as a float, e.g. 1969.55. */
export function yearOf(t: number): number {
  return EPOCH_YEAR + t / YEAR;
}

/** Compact magnitude formatter: 950, 12.3k, 4.5M, 1.2G. */
export function fmtNum(v: number, digits = 1): string {
  const a = Math.abs(v);
  if (a >= 1e9) return `${(v / 1e9).toFixed(digits)}G`;
  if (a >= 1e6) return `${(v / 1e6).toFixed(digits)}M`;
  if (a >= 1e4) return `${(v / 1e3).toFixed(digits)}k`;
  return v.toFixed(a >= 100 ? 0 : digits);
}

/** Duration in game seconds as a readable string (days/years once large). */
export function fmtDuration(s: number): string {
  const a = Math.abs(s);
  if (a < 120) return `${s.toFixed(0)}s`;
  if (a < 7200) return `${(s / 60).toFixed(1)}m`;
  if (a < DAY * 2) return `${(s / 3600).toFixed(1)}h`;
  if (a < YEAR * 1.5) return `${(s / DAY).toFixed(0)}d`;
  return `${(s / YEAR).toFixed(1)}a`;
}
