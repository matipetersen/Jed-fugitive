import { type ShipState } from './sim';
import { len, wrapAngle } from './vec';

export type AutopilotMode = 'off' | 'prograde' | 'retrograde';

/** Turn command (-1..1) that points the ship along or against its velocity. */
export function autopilotTurn(mode: AutopilotMode, ship: ShipState): number {
  if (mode === 'off' || ship.status !== 'flying' || len(ship.vel) < 1) return 0;
  const heading = Math.atan2(ship.vel.y, ship.vel.x) + (mode === 'retrograde' ? Math.PI : 0);
  const err = wrapAngle(heading - ship.angle);
  if (Math.abs(err) < 0.005) return 0;
  return Math.max(-1, Math.min(1, err * 4));
}
