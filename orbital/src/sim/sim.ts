import { PLANET, SHIP } from './params';
import { type Vec2, dot, fromAngle, len, scale, vec, wrapAngle } from './vec';

export type ShipStatus = 'flying' | 'landed' | 'crashed';

export interface ShipState {
  pos: Vec2;
  vel: Vec2;
  /** Direction of the nose in world space, radians (0 = +x, counter-clockwise). */
  angle: number;
  fuel: number;
  throttle: number;
  status: ShipStatus;
  /** Touchdown speed of the last landing or crash, for the HUD. */
  impactSpeed: number;
}

export interface World {
  time: number;
  ship: ShipState;
}

export interface Controls {
  /** Desired throttle, 0..1. */
  throttle: number;
  /** Rotation command, -1..1, positive is counter-clockwise. */
  turn: number;
}

export const CONTACT_RADIUS = PLANET.radius + SHIP.legLength;

export function createWorld(): World {
  const up = Math.PI / 2;
  return {
    time: 0,
    ship: {
      pos: vec(0, CONTACT_RADIUS),
      vel: vec(0, 0),
      angle: up,
      fuel: SHIP.fuelMass,
      throttle: 0,
      status: 'landed',
      impactSpeed: 0,
    },
  };
}

export function gravityAt(pos: Vec2, gm: number = PLANET.gm): Vec2 {
  const r = len(pos);
  return scale(pos, -gm / (r * r * r));
}

const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

/** Advances the world by dt seconds. Planet is fixed at the origin for now. */
export function step(world: World, controls: Controls, dt: number): void {
  const ship = world.ship;
  world.time += dt;
  if (ship.status === 'crashed') return;

  ship.throttle = ship.fuel > 0 ? clamp(controls.throttle, 0, 1) : 0;
  if (ship.status === 'flying') {
    ship.angle = wrapAngle(ship.angle + clamp(controls.turn, -1, 1) * SHIP.turnRate * dt);
  }

  const mass = SHIP.dryMass + ship.fuel;
  const thrustAccel = (ship.throttle * SHIP.thrust) / mass;
  const nose = fromAngle(ship.angle);
  const burn = Math.min(ship.fuel, (ship.throttle * SHIP.thrust * dt) / SHIP.exhaustVelocity);

  if (ship.status === 'landed') {
    const up = scale(ship.pos, 1 / len(ship.pos));
    const lift = thrustAccel * dot(nose, up) - PLANET.surfaceGravity;
    ship.fuel -= burn;
    if (lift <= 0) return;
    ship.status = 'flying';
  }

  // Kick-drift-kick leapfrog: second order and symplectic, so orbits do not
  // gain or lose energy over time.
  const accel = (pos: Vec2): Vec2 => {
    const g = gravityAt(pos);
    return vec(g.x + nose.x * thrustAccel, g.y + nose.y * thrustAccel);
  };
  const a0 = accel(ship.pos);
  ship.vel = vec(ship.vel.x + a0.x * dt * 0.5, ship.vel.y + a0.y * dt * 0.5);
  ship.pos = vec(ship.pos.x + ship.vel.x * dt, ship.pos.y + ship.vel.y * dt);
  ship.fuel -= burn;
  const a1 = accel(ship.pos);
  ship.vel = vec(ship.vel.x + a1.x * dt * 0.5, ship.vel.y + a1.y * dt * 0.5);

  if (len(ship.pos) < CONTACT_RADIUS) touchdown(ship);
}

function touchdown(ship: ShipState): void {
  const r = len(ship.pos);
  const up = scale(ship.pos, 1 / r);
  const speed = len(ship.vel);
  const tilt = Math.abs(wrapAngle(ship.angle - Math.atan2(up.y, up.x)));
  const safe = speed <= SHIP.landingMaxSpeed && tilt <= SHIP.landingMaxTilt;
  ship.pos = scale(up, CONTACT_RADIUS);
  ship.vel = vec(0, 0);
  ship.impactSpeed = speed;
  ship.status = safe ? 'landed' : 'crashed';
}
