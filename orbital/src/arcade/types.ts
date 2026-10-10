/** Data shapes for the arcade race mode. Units are screen-sized: a ship is about 14 u long. */

export interface PadDef {
  /** Angle of the pad centre around the body, radians from +x. */
  angle: number;
  /** Half width along the surface, in u. */
  half: number;
  name: string;
  /** Landing here restores the ship and sets the respawn point. */
  bonfire: boolean;
}

export interface BodyDef {
  id: string;
  name: string;
  r: number;
  /** Surface gravity in u/s^2. */
  g: number;
  color: string;
  /** Fixed position, used when there is no orbit. */
  x?: number;
  y?: number;
  orbit?: { parent: string; a: number; phase: number; omega: number };
  /** Thin atmosphere: scale height and drag coefficient. */
  atm?: { h: number; drag: number };
  pads?: PadDef[];
  /** Touching it is fatal and it burns nearby ships. */
  star?: boolean;
}

export interface GateDef {
  /** Absolute position, or an offset from `body` if attached. */
  x: number;
  y: number;
  body?: string;
  r?: number;
  final?: boolean;
}

export interface FieldDef {
  x: number;
  y: number;
  r: number;
  kind: 'wind' | 'radiation';
  /** Acceleration for wind, u/s^2. */
  ax?: number;
  ay?: number;
  /** Damage per second for radiation. */
  dps?: number;
  color: string;
  label?: string;
}

export interface AsteroidSpec {
  count: number;
  seed: number;
  /** Body the rocks orbit, or a fixed point. */
  around: string;
  rIn: number;
  rOut: number;
  size: [number, number];
  /** Fraction of circular speed. */
  speed: number;
}

export interface CellDef {
  x: number;
  y: number;
  body?: string;
  fuel: number;
}

export interface StageDef {
  id: number;
  name: string;
  year: number;
  blurb: string;
  skulls: number;
  bodies: BodyDef[];
  gates: GateDef[];
  fields: FieldDef[];
  asteroids: AsteroidSpec[];
  cells: CellDef[];
  /** Where the player and the rival start. */
  start: { body: string; angle: number };
  rivalStart: { body: string; angle: number };
  /** Rival tuning: thrust multiplier and decision interval. */
  rival: { skill: number; name: string; delay: number; ai?: { horizon: number; dt: number; interval: number; noise: number } };
  /** A good time in seconds, for scoring. */
  par: number;
}

export interface Controls {
  throttle: number;
  turn: number;
}

export type ShipStatus = 'landed' | 'flying' | 'dead';

export interface ShipStats {
  thrust: number;
  turnRate: number;
  fuelMax: number;
  hullMax: number;
}

export interface Ship {
  id: number;
  isPlayer: boolean;
  name: string;
  color: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  angle: number;
  throttle: number;
  fuel: number;
  hull: number;
  stats: ShipStats;
  status: ShipStatus;
  landedBody: number;
  landedAngle: number;
  /** Seconds until respawn while dead. */
  deadTimer: number;
  deathReason: string;
  invuln: number;
  nextGate: number;
  finished: boolean;
  finishTime: number;
  /** Infinite fuel for AI ships. */
  infiniteFuel: boolean;
  /** Last pad this ship landed on (body index, pad index) or null. */
  bonfire: { body: number; pad: number } | null;
}

export interface Asteroid {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  alive: boolean;
}

export type ArenaEvent =
  | { type: 'gate'; ship: number; index: number; final: boolean }
  | { type: 'die'; ship: number; reason: string; x: number; y: number }
  | { type: 'land'; ship: number; body: number; pad: number; bonfire: boolean }
  | { type: 'hit'; ship: number; damage: number; by: string }
  | { type: 'cell'; ship: number }
  | { type: 'bump'; a: number; b: number }
  | { type: 'slingshot'; ship: number; body: number };
