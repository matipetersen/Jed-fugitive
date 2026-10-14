/* Arranque: crea la aplicación, conecta audio/táctil y muestra el título. */
(function (CV) {
'use strict';
const canvas = document.getElementById('game');
const app = new CV.ui.App(canvas);
CV.ui.app = app;
try { if (window.matchMedia && matchMedia('(pointer: coarse)').matches) CV.ui.touch = true; } catch (e) {}
const step = app.step;
app.step = function (dt) {
  const el = CV.nameInput.el;
  if (el && el.style.display !== 'none' && !(this.top instanceof CV.scenes1.SetupScene)) CV.nameInput.hide();
  step.call(this, dt);
};
window.addEventListener('pointerdown', () => CV.sfx.unlock(), {passive: true});
window.addEventListener('keydown', () => CV.sfx.unlock(), {passive: true});
window.addEventListener('error', e => {
  const b = document.getElementById('err'); if (b) { b.style.display = 'block'; b.textContent = 'Error: ' + (e.message || e.error) + ' (' + (e.lineno || '?') + ')'; }
});
const rot = document.getElementById('rotate');
if (rot) rot.addEventListener('pointerdown', () => { rot.style.display = 'none'; });
app.push(new CV.scenes1.TitleScene(app));
app.start();
CV.app = app;
})(globalThis.CV = globalThis.CV || {});
