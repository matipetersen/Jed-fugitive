/**
 * Tuning constants. Distances are game units (u), time is seconds.
 * Design target: low-orbit period around 40 s (see DESIGN.md section 3).
 */
export const PLANET = {
  radius: 1000,
  surfaceGravity: 25,
  /** Gravitational parameter, GM = g * R^2. */
  get gm(): number {
    return this.surfaceGravity * this.radius * this.radius;
  },
};

export const SHIP = {
  dryMass: 1000,
  fuelMass: 1000,
  /** Full-throttle thrust. Initial thrust/weight is about 1.6. */
  thrust: 80000,
  /** Effective exhaust velocity; gives a total delta-v of about 600 u/s. */
  exhaustVelocity: 866,
  /** Max rotation rate, rad/s. */
  turnRate: 2.2,
  /** Distance from the ship centre to the foot of the legs. */
  legLength: 8,
  /** Max touchdown speed (u/s) and tilt (rad) for a safe landing. */
  landingMaxSpeed: 12,
  landingMaxTilt: 0.35,
};

export const FIXED_DT = 1 / 120;
