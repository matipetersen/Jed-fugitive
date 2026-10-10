import { type BurnNode, type Prediction } from '../sim/predict';
import { type World } from '../sim/physics';

export interface Marker {
  body: number;
  theta: number;
}

export interface Scene {
  world: World;
  prediction: Prediction | null;
  /** Body whose frame the path is drawn in, or -1 for the plain inertial frame. */
  frameBody: number;
  node: BurnNode | null;
  target: number;
  refIndex: number;
  bases: Marker[];
  flags: Marker[];
  /** Real-time clock for animations, in seconds. */
  clock: number;
  /** Heat/drag intensity for the ship's visual effects, 0..1. */
  atmoGlow: number;
}
