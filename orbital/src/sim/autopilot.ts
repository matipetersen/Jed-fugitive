import { type ShipState } from './physics';
import { wrapAngle } from './vec';

export type AutopilotMode = 'off' | 'prograde' | 'retrograde' | 'node' | 'radial';

/**
 * Turn command (-1..1) that points the ship along a heading. `vx`/`vy` is the
 * velocity relative to the reference body, and `nodeDir` the burn direction.
 */
export function autopilotTurn(
  mode: AutopilotMode,
  ship: ShipState,
  vx: number,
  vy: number,
  nodeDir: number | null,
  radialDir: number,
): number {
  if (mode === 'off' || ship.status !== 'flying') return 0;
  let heading: number;
  if (mode === 'node') {
    if (nodeDir === null) return 0;
    heading = nodeDir;
  } else if (mode === 'radial') {
    heading = radialDir;
  } else {
    if (Math.hypot(vx, vy) < 0.5) return 0;
    heading = Math.atan2(vy, vx) + (mode === 'retrograde' ? Math.PI : 0);
  }
  const err = wrapAngle(heading - ship.angle);
  if (Math.abs(err) < 0.004) return 0;
  return Math.max(-1, Math.min(1, err * 4));
}
