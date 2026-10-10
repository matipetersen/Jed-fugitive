import { Input } from './input/input';
import { type Camera } from './render/camera';
import { drawFrame } from './render/draw';
import { autopilotTurn } from './sim/autopilot';
import { orbitElements } from './sim/orbit';
import { FIXED_DT, PLANET } from './sim/params';
import { predictCoast } from './sim/predict';
import { createWorld, step } from './sim/sim';
import { wrapAngle } from './sim/vec';

const canvas = document.getElementById('game') as HTMLCanvasElement;
const ctx = canvas.getContext('2d', { alpha: false })!;
const input = new Input(canvas);

let world = createWorld();
let hasFlown = false;
let width = 0;
let height = 0;
let dpr = 1;

const camera: Camera = { center: { ...world.ship.pos }, zoom: input.zoom, up: Math.PI / 2 };

function resize(): void {
  width = window.innerWidth;
  height = window.innerHeight;
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  input.resize(width, height);
}
window.addEventListener('resize', resize);
resize();

if (new URLSearchParams(location.search).has('debug')) {
  (window as unknown as Record<string, unknown>).__orbital = {
    get world() {
      return world;
    },
    input,
    camera,
  };
}

let last = performance.now();
let acc = 0;

function frame(now: number): void {
  const dt = Math.min((now - last) / 1000, 0.25);
  last = now;

  input.update(dt);
  const wantsRestart = input.consumeRestart();
  if (world.ship.status === 'crashed' && wantsRestart) {
    world = createWorld();
    hasFlown = false;
    input.reset();
  }

  if (input.turn !== 0) input.autopilot = 'off';
  acc += dt;
  while (acc >= FIXED_DT) {
    const turn = input.turn !== 0 ? input.turn : autopilotTurn(input.autopilot, world.ship);
    step(world, { throttle: input.throttle, turn }, FIXED_DT);
    acc -= FIXED_DT;
  }
  if (world.ship.status === 'flying') hasFlown = true;
  if (world.ship.status === 'crashed') input.throttle = 0;

  const ship = world.ship;
  camera.zoom = input.zoom;
  camera.center = { x: ship.pos.x, y: ship.pos.y };
  const followUp = camera.zoom > 0.12 ? Math.atan2(ship.pos.y, ship.pos.x) : Math.PI / 2;
  camera.up = wrapAngle(camera.up + wrapAngle(followUp - camera.up) * (1 - Math.exp(-6 * dt)));

  const orbit = orbitElements(ship.pos, ship.vel, PLANET.gm);
  const prediction = predictCoast(ship);
  drawFrame({ ctx, width, height, dpr, time: now / 1000, world, camera, prediction, orbit, input, hasFlown });
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
