import { Flight } from './game/flight';
import { newCampaign } from './game/campaign';
import { Input } from './input/input';
import { drawHud } from './render/hud';
import { drawAsteroids, drawShip, drawStars, drawWorld } from './render/world';
import { createWorld } from './sim/physics';
import { statsFor } from './sim/tech';
import { indexOf } from './sim/bodies';
import { Ui } from './ui/ui';
import { Overlay, h, injectCss } from './ui/dom';

injectCss();
const canvas = document.getElementById('game') as HTMLCanvasElement;
const ctx = canvas.getContext('2d', { alpha: false })!;
const ui = new Ui();
const input = new Input(canvas, ui);
const overlay = new Overlay();

let width = 0;
let height = 0;
let dpr = 1;

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

const campaign = newCampaign({ sandbox: true });
function freshWorld() {
  return createWorld(statsFor(campaign.techs, campaign.engine), indexOf('earth'), Math.PI / 2, 0);
}
const flight = new Flight(freshWorld(), campaign, input, ui);
let paused = false;

function restart(): void {
  flight.world = freshWorld();
  flight.node = null;
  flight.nodePanel = false;
  flight.hasFlown = false;
  flight.warpIdx = 0;
  input.reset();
}

const HELP: [string, string][] = [
  ['Empuje', 'Arrastrá en la franja izquierda. Tiene memoria: dejalo donde lo soltás.'],
  ['Giro', 'Arrastrá a los lados en la zona inferior derecha. PRO y RET apuntan la nave sola.'],
  ['Zoom', 'Pellizcá, o usá − y +. Alejá todo el zoom para ver el sistema solar.'],
  ['Tiempo', 'W+ y W− aceleran el tiempo. Con motor encendido o dentro de la atmósfera queda en x1.'],
  ['Destino', 'OBJ elige un cuerpo (o tocalo en el mapa). MARCO dibuja la trayectoria vista desde otro cuerpo.'],
  ['Trayectoria', 'NODO abre el planificador: AUTO propone la ventana de salida, REFINA ajusta hasta un paso cercano, IR NODO acelera el tiempo, APUNTA orienta la nave, y encendés el motor.'],
  ['Aterrizar', 'Hacia abajo, lento (menos de 12 u/s) y derecho. Las franjas amarillas del suelo son terreno plano.'],
  ['Bandera y base', 'Ya aterrizado en una franja: BANDERA, BASE y RECARGA aparecen abajo.'],
  ['Teclado', 'A/D girar · W/S empuje · Z/X máximo/corte · P/R pro/retro · N nodo · . , tiempo · T objetivo · F marco · +/− zoom'],
];

function showMenu(first = false): void {
  paused = true;
  input.enabled = false;
  const close = (): void => {
    overlay.hide();
    paused = false;
    input.enabled = true;
    ui.clear();
    try {
      localStorage.setItem('orbital.seen', '1');
    } catch {
      /* ignore */
    }
  };
  overlay.show(
    h('div', { class: 'screen' },
      h('h1', {}, first ? 'ORBITAL RACE' : 'PAUSA'),
      h('p', { class: 'sub' }, 'Vuelo libre · sistema solar a escala real comprimida'),
      h('div', { class: 'row' },
        h('button', { class: 'btn go', onclick: close }, 'CONTINUAR'),
        h('button', { class: 'btn warn', onclick: () => { restart(); close(); } }, 'NUEVA NAVE EN LA PLATAFORMA'),
      ),
      h('h2', {}, 'CÓMO SE JUEGA'),
      h('div', { class: 'panel' },
        h('ul', { class: 'tight' }, ...HELP.map(([k, v]) => h('li', {}, h('span', { class: 'amber' }, `${k}: `), v))),
      ),
    ),
  );
}
flight.hooks.onMenu = () => showMenu();
flight.hooks.onRestart = restart;

let seen = false;
try {
  seen = localStorage.getItem('orbital.seen') === '1';
} catch {
  /* ignore */
}
if (!seen) showMenu(true);

if (new URLSearchParams(location.search).has('debug')) {
  (window as unknown as Record<string, unknown>).__orbital = { flight, input, overlay };
}

let last = performance.now();

function frame(now: number): void {
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  if (!paused) flight.update(dt, now / 1000);
  const v = flight.view;
  v.w = width;
  v.h = height;

  ctx.globalCompositeOperation = 'source-over';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#02020a';
  ctx.fillRect(0, 0, width, height);
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  const scene = flight.scene();
  drawStars(ctx, v);
  drawWorld(ctx, v, scene);
  drawAsteroids(ctx, v, scene);
  drawShip(ctx, v, scene);
  drawHud(ctx, flight, width, height);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
