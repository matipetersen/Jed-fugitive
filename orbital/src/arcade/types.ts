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
  /** A black hole: fatal inside its horizon, burns in its disc, and pulls hard. */
  hole?: boolean;
}

export interface GateDef {
  /** Absolute position, or an offset from `body` if attached. */
  x: number;
  y: number;
  body?: string;
  r?: number;
  final?: boolean;
  /** Satisfied by landing on this pad instead of flying through the ring. */
  landing?: { body: string; pad: number };
  /** Passing through picks up cargo: heavier ship until the stage ends. */
  cargo?: boolean;
}

export interface FieldDef {
  /** Offset from `body` when attached to one (a comet's dust cloud), else an absolute position. */
  body?: string;
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
  /** Year shown on the stage card; 0 for fiction. */
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
  /** Start already flying around a body instead of from a pad (the rival gets the same, a little behind). */
  startAt?: { body: string; angle: number; alt: number; speed?: number; dir?: 1 | -1; inward?: number };
  /** A mass start: many AI ships around one body. The stage is won with a place on the podium. */
  field?: { body: string; slots: number[]; podium: number; /** Laps of the ring in `gates`, run from each ship's own pad. */ laps: number; /** +1 counter-clockwise, -1 clockwise. */ dir: 1 | -1 };
  /** Fraction of the usual tank for the player in this stage. */
  tank?: number;
  /** Short label for the kind of stage, shown on the stage card. */
  kind?: string;
  /** Rival tuning: thrust multiplier and decision interval. */
  rival: { skill: number; name: string; delay: number; ai?: { horizon: number; dt: number; interval: number; noise: number } };
  /** The stage ends when a ship has passed every gate and then lands on this pad. */
  finish: { body: string; pad: number };
  /** A good time in seconds, for scoring. */
  par: number;
}

export interface Controls {
  throttle: number;
  turn: number;
  /** Afterburner request. */
  boost?: boolean;
}

export type ShipStatus = 'landed' | 'flying' | 'dead';

export interface ShipStats {
  thrust: number;
  turnRate: number;
  fuelMax: number;
  hullMax: number;
  /** Fraction of heat, radiation and disc damage the ship shrugs off. */
  shield: number;
  /** Afterburner level; 0 means none. */
  boost: number;
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
  cargo: boolean;
  /** This ship's own route (gates) and landing pad; the stage's by default. In a mass start each ship has its own, equal in length. */
  route: import('./arena').RGate[];
  finishPad: { body: number; pad: number };
  /** Frozen in place (a rival waiting for its head-start delay while already flying). */
  hold: boolean;
  /** Afterburner time left and cooldown, in seconds. */
  boostT: number;
  boostCd: number;
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
  | { type: 'cargo'; ship: number }
  | { type: 'boost'; ship: number }
  | { type: 'bump'; a: number; b: number }
  | { type: 'slingshot'; ship: number; body: number };

/** A series of stages with its own story, rival and hazards. */
export interface RaceDef {
  id: string;
  name: string;
  subtitle: string;
  blurb: string;
  stages: StageDef[];
}
