import { App } from './game/app';
import { Audio } from './game/audio';
import { Input } from './input/input';
import { Ui } from './ui/ui';
import { quality } from './render/neon';
import { Overlay, injectCss } from './ui/dom';

injectCss();
const canvas = document.getElementById('game') as HTMLCanvasElement;
const ctx = canvas.getContext('2d', { alpha: false })!;
const ui = new Ui();
const input = new Input(canvas, ui);
const overlay = new Overlay();
const audio = new Audio();
const app = new App(canvas, ctx, ui, input, overlay, audio);

let dprMax = 1.5;
function resize(): void {
  const width = window.innerWidth;
  const height = window.innerHeight;
  const dpr = Math.min(window.devicePixelRatio || 1, dprMax);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  input.resize(width, height);
  app.resize(width, height, dpr);
}
window.addEventListener('resize', resize);
resize();
app.onLowQuality = (stage) => {
  dprMax = stage >= 2 ? 1 : 1.25;
  resize();
};

document.addEventListener('visibilitychange', () => {
  if (document.hidden) app.save();
});
window.addEventListener('pagehide', () => app.save());

if (new URLSearchParams(location.search).has('debug')) {
  (window as unknown as Record<string, unknown>).__orbital = {
    app,
    get flight() {
      return app.flight;
    },
    input,
    quality,
  };
}

app.showTitle();

// Offline support when installed from a normal host; hosts that block service workers just skip it.
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => undefined);
  });
}

let last = performance.now();
function frame(now: number): void {
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  app.frame(now, dt);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
