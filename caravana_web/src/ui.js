/* Capa de interfaz: canvas lógico 1280×720, texto, paneles, botones y gestor de escenas. */
(function (CV) {
'use strict';
const W = 1280, H = 720;
const UI = CV.ui = {W, H, touch: false, debugDirector: false};
const C = UI.C = {bg:'#1a140f', panel:'#34261a', panel2:'#46341f', edge:'#785a36', gold:'#eec060', text:'#f0e4c8', dim:'#aa9a7c', red:'#d6503e', green:'#78b864', blue:'#6ea0dc', parch:'#e2d0a4', ink:'#362618', orange:'#ee8c3c'};
const SERIF = 'Georgia, "Times New Roman", serif', SANS = 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
UI.font = (size, bold, serif) => `${bold ? 'bold ' : ''}${size}px ${serif ? SERIF : SANS}`;
let ctx = null;
UI.setCtx = c => { ctx = c; };

UI.text = function (s, x, y, o) {
  o = o || {};
  ctx.font = UI.font(o.size || 18, o.bold, o.serif);
  ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'top';
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  if (o.shadow) { ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillText(String(s), x + 1, y + 2); }
  ctx.fillStyle = o.color || C.text; ctx.fillText(String(s), x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = 1;
};
UI.measure = (s, size, bold, serif) => { ctx.font = UI.font(size, bold, serif); return ctx.measureText(s).width; };
UI.wrap = function (s, size, width, bold, serif) {
  ctx.font = UI.font(size, bold, serif);
  const lines = [];
  for (const para of String(s).split('\n')) {
    let cur = '';
    for (const w of para.split(' ')) {
      const t = cur ? cur + ' ' + w : w;
      if (ctx.measureText(t).width <= width || !cur) cur = t; else { lines.push(cur); cur = w; }
    }
    lines.push(cur);
  }
  return lines;
};
UI.para = function (s, x, y, width, size, color, o) {
  o = o || {};
  const lines = UI.wrap(s, size, width, o.bold, o.serif), lh = Math.round(size * 1.28) + (o.gap === undefined ? 3 : o.gap);
  const shown = o.maxLines ? lines.slice(0, o.maxLines) : lines;
  for (const ln of shown) { UI.text(ln, x, y, {size, color, bold: o.bold, serif: o.serif}); y += lh; }
  return y;
};
UI.paraHeight = (s, size, width, o) => UI.wrap(s, size, width, o && o.bold).length * (Math.round(size * 1.28) + 3);
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
UI.rr = rr;
UI.panel = function (x, y, w, h, fill, edge, r, alpha, lw) {
  r = r === undefined ? 8 : r;
  if (alpha !== undefined) ctx.globalAlpha = alpha;
  rr(x, y, w, h, r); ctx.fillStyle = fill || C.panel; ctx.fill();
  if (alpha !== undefined) ctx.globalAlpha = Math.min(1, alpha + .16);
  ctx.lineWidth = lw || 2; ctx.strokeStyle = edge || C.edge; ctx.stroke();
  ctx.globalAlpha = 1;
};
UI.bar = function (x, y, w, h, frac, color, back) {
  frac = Math.max(0, Math.min(1, frac));
  rr(x, y, w, h, 3); ctx.fillStyle = back || '#1e1610'; ctx.fill();
  if (frac > 0) { rr(x, y, Math.max(2, w * frac), h, 3); ctx.fillStyle = color; ctx.fill(); }
};
UI.veil = function (a, color) { ctx.fillStyle = color || `rgba(0,0,0,${a})`; ctx.fillRect(0, 0, W, H); };
UI.vgrad = function (x, y, w, h, top, bot) { const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, top); g.addColorStop(1, bot); ctx.fillStyle = g; ctx.fillRect(x, y, w, h); };
const lighten = (hex, k) => { const n = parseInt(hex.slice(1), 16); const f = c => Math.min(255, c + k); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; };

class Button {
  constructor(x, y, w, h, label, onClick, o) {
    o = o || {};
    Object.assign(this, {x, y, w, h, label, onClick, enabled: o.enabled !== false, size: o.size || 18, color: o.color || C.panel2, key: o.key || null, hint: o.hint || '', selected: false, hover: false});
  }
  hit(px, py) { return px >= this.x && px <= this.x + this.w && py >= this.y && py <= this.y + this.h; }
  draw() {
    let fill, edge, tc;
    if (!this.enabled) { fill = '#2c241c'; edge = '#50422e'; tc = '#6e6250'; }
    else { fill = this.hover && !UI.touch ? lighten(this.color, 22) : this.color; edge = (this.hover && !UI.touch) || this.selected ? C.gold : C.edge; tc = C.text; }
    rr(this.x, this.y, this.w, this.h, 7); ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = edge; ctx.stroke();
    if (this.selected) { rr(this.x + 3, this.y + 3, this.w - 6, this.h - 6, 5); ctx.lineWidth = 1; ctx.strokeStyle = C.gold; ctx.stroke(); }
    const lines = UI.wrap(this.label, this.size, this.w - 14).slice(0, 3), lh = Math.round(this.size * 1.25);
    let y = this.y + this.h / 2 - lines.length * lh / 2;
    for (const ln of lines) { UI.text(ln, this.x + this.w / 2, y, {size: this.size, color: tc, align: 'center'}); y += lh; }
  }
}
UI.Button = Button;
UI.handleButtons = function (btns, ev) {
  if (ev.type === 'move') { for (const b of btns) b.hover = b.hit(ev.x, ev.y); return false; }
  if (ev.type === 'down') { for (const b of btns) if (b.hit(ev.x, ev.y)) { if (b.enabled) { CV.sfx.play('click', .6, .03); b.onClick(); } return true; } }
  if (ev.type === 'key') { for (const b of btns) if (b.key && b.key === ev.key && b.enabled) { CV.sfx.play('click', .6, .03); b.onClick(); return true; } }
  return false;
};
UI.tooltip = function (s, x, y) {
  if (!s) return;
  const lines = UI.wrap(s, 15, 260), w = Math.max(...lines.map(l => UI.measure(l, 15))) + 16, h = lines.length * 20 + 10;
  x = Math.min(x + 14, W - w - 6); y = Math.min(y + 18, H - h - 6);
  UI.panel(x, y, w, h, '#1e1610', C.gold, 5, .94, 1);
  lines.forEach((l, i) => UI.text(l, x + 8, y + 6 + i * 20, {size: 15}));
};
UI.icon = function (kind, x, y, size) {
  const r = size / 2; ctx.save(); ctx.translate(x, y); ctx.lineWidth = 2;
  const el = (cx, cy, rx, ry, fill, stroke) => { ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, 7); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.stroke(); } };
  if (kind === 'food') { el(0, 0, r, r, '#be7846', '#6e3c24'); el(-r / 3, -r / 3, r / 3, r / 3, '#e6aa6e'); }
  else if (kind === 'ammo') { ctx.fillStyle = '#c8a046'; rr(-r / 2, -r, r, r * 2, 2); ctx.fill(); ctx.fillStyle = '#966e3c'; ctx.beginPath(); ctx.moveTo(-r / 2, -r); ctx.lineTo(r / 2, -r); ctx.lineTo(0, -r * 1.5); ctx.fill(); }
  else if (kind === 'goods') { ctx.fillStyle = '#966e46'; rr(-r, -r / 2, r * 2, r * 1.5, 2); ctx.fill(); ctx.strokeStyle = '#e6c878'; ctx.beginPath(); ctx.moveTo(-r, 0); ctx.lineTo(r, 0); ctx.moveTo(0, -r / 2); ctx.lineTo(0, r); ctx.stroke(); }
  else if (kind === 'parts') { ctx.strokeStyle = '#9696a0'; ctx.lineWidth = 3; el(0, 0, r, r, null, '#9696a0'); ctx.lineWidth = 1; for (let a = 0; a < 6; a++) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a * 1.047) * r, Math.sin(a * 1.047) * r); ctx.stroke(); } }
  else if (kind === 'medicine') { ctx.fillStyle = '#ebebeb'; rr(-r, -r, r * 2, r * 2, 3); ctx.fill(); ctx.fillStyle = '#d23232'; ctx.fillRect(-r / 4, -r + 3, r / 2, r * 2 - 6); ctx.fillRect(-r + 3, -r / 4, r * 2 - 6, r / 2); }
  else if (kind === 'oxen') { el(0, 0, r, r / 2, '#6e5036'); el(r, 0, r / 2, r / 2, '#5a402a'); ctx.strokeStyle = '#f0ecdc'; ctx.beginPath(); ctx.moveTo(r, -r / 3); ctx.lineTo(r + 4, -r / 2 - 4); ctx.stroke(); }
  else if (kind === 'money') { el(0, 0, r, r, '#f0c850', '#aa8228'); UI.text('$', 0, 0, {size: Math.max(12, size - 6), color: '#6e5014', bold: true, align: 'center', base: 'middle'}); }
  else if (kind === 'morale') { el(0, 0, r, r, '#f0c85a'); ctx.fillStyle = '#5a3c14'; ctx.fillRect(-r / 3 - 1, -r / 4, 3, 3); ctx.fillRect(r / 3 - 1, -r / 4, 3, 3); ctx.strokeStyle = '#5a3c14'; ctx.beginPath(); ctx.arc(0, 0, r / 2, 0.2 * Math.PI, 0.8 * Math.PI); ctx.stroke(); }
  else if (kind === 'wagon') { ctx.fillStyle = '#e6dcbe'; rr(-r, -r / 2, r * 2, r, r / 2); ctx.fill(); el(-r / 2, r / 2, r / 3, r / 3, '#32241a'); el(r / 2, r / 2, r / 3, r / 3, '#32241a'); }
  else if (kind === 'cannon') { ctx.fillStyle = '#505058'; rr(-r, -r / 3, r * 2, r / 1.5, 3); ctx.fill(); el(-r / 2, r / 3, r / 2, r / 2, '#32323a'); }
  else if (kind === 'sun') { el(0, 0, r / 2 + 1, r / 2 + 1, '#fad250'); ctx.strokeStyle = '#fad250'; for (let a = 0; a < 8; a++) { ctx.beginPath(); ctx.moveTo(Math.cos(a * .785) * (r / 2 + 3), Math.sin(a * .785) * (r / 2 + 3)); ctx.lineTo(Math.cos(a * .785) * r, Math.sin(a * .785) * r); ctx.stroke(); } }
  else if (kind === 'rain') { el(0, -r / 3, r, r / 2, '#aab4c3'); ctx.strokeStyle = '#6ea0e6'; for (const dx of [-r / 2, 0, r / 2]) { ctx.beginPath(); ctx.moveTo(dx, 2); ctx.lineTo(dx - 2, r - 1); ctx.stroke(); } }
  else if (kind === 'snow') { ctx.strokeStyle = '#dcebff'; for (let a = 0; a < 3; a++) { ctx.beginPath(); ctx.moveTo(Math.cos(a * 1.047) * r, Math.sin(a * 1.047) * r); ctx.lineTo(-Math.cos(a * 1.047) * r, -Math.sin(a * 1.047) * r); ctx.stroke(); } }
  else if (kind === 'storm') { el(0, -r / 3, r, r / 2, '#6e7282'); ctx.fillStyle = '#fae65a'; ctx.beginPath(); ctx.moveTo(0, -2); ctx.lineTo(-4, 4); ctx.lineTo(0, 3); ctx.lineTo(-2, r); ctx.lineTo(5, 1); ctx.lineTo(1, 2); ctx.fill(); }
  ctx.restore();
};

// ---------------------------------------------------------------- aplicación
class App {
  constructor(canvas) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d'); UI.setCtx(this.ctx);
    this.scenes = []; this.game = null; this.travel = null; this.last = 0; this.ptr = {x: 0, y: 0, down: false};
    canvas.width = W; canvas.height = H;
    const pos = e => { const r = canvas.getBoundingClientRect(); return {x: (e.clientX - r.left) * W / r.width, y: (e.clientY - r.top) * H / r.height}; };
    const send = (type, e, extra) => { const p = pos(e); this.ptr.x = p.x; this.ptr.y = p.y; if (e.pointerType === 'touch' && !UI.touch) UI.touch = true; const s = this.top; if (s) s.handle(Object.assign({type, x: p.x, y: p.y}, extra || {})); };
    canvas.addEventListener('pointerdown', e => { try { canvas.setPointerCapture(e.pointerId); } catch (err) {} this.ptr.down = true; send('down', e, {button: e.button}); e.preventDefault(); });
    canvas.addEventListener('pointermove', e => { send('move', e, {down: this.ptr.down}); });
    canvas.addEventListener('pointerup', e => { this.ptr.down = false; send('up', e, {button: e.button}); });
    canvas.addEventListener('pointercancel', e => { this.ptr.down = false; send('up', e, {button: 0}); });
    canvas.addEventListener('contextmenu', e => { e.preventDefault(); });
    canvas.addEventListener('wheel', e => { const s = this.top; if (s) s.handle({type: 'wheel', dy: e.deltaY, x: this.ptr.x, y: this.ptr.y}); e.preventDefault(); }, {passive: false});
    window.addEventListener('keydown', e => {
      if (document.activeElement && document.activeElement.id === 'nameInput') return;
      const s = this.top; if (!s) return;
      if (['Space', 'Enter', 'ArrowDown', 'ArrowUp'].includes(e.code)) e.preventDefault();
      s.handle({type: 'key', key: e.code, ch: e.key});
    });
  }
  get top() { return this.scenes[this.scenes.length - 1] || null; }
  push(s) { this.scenes.push(s); if (s.enter) s.enter(); }
  pop() { this.scenes.pop(); const t = this.top; if (t && t.resume) t.resume(); }
  replace(s) { this.scenes = []; this.push(s); }
  handleInterrupt(it) { if (this.travel) this.travel.handleInterrupt(it); }
  start() { requestAnimationFrame(t => this.frame(t)); }
  frame(t) {
    const dt = Math.min(.05, (t - this.last) / 1000 || 0); this.last = t;
    this.step(dt);
    requestAnimationFrame(t2 => this.frame(t2));
  }
  step(dt) {
    const s = this.top; if (s) s.update(dt);
    let start = 0;
    for (let i = this.scenes.length - 1; i >= 0; i--) if (!this.scenes[i].overlay) { start = i; break; }
    for (let i = start; i < this.scenes.length; i++) this.scenes[i].draw();
  }
  // guardado local (por visitante)
  saveExists() { try { return !!localStorage.getItem('caravana_save'); } catch (e) { return false; } }
  autosave() { if (!this.game || this.game.over) return; try { localStorage.setItem('caravana_save', JSON.stringify(this.game)); } catch (e) {} }
  loadSave() {
    try { const raw = localStorage.getItem('caravana_save'); if (!raw) return null; const o = JSON.parse(raw); const g = Object.assign(new CV.Game(o.seed), o); g.rng = Object.assign(new CV.RNG(1), o.rng); g.director = Object.assign(new CV.Director(), o.director); return g; } catch (e) { return null; }
  }
  clearSave() { try { localStorage.removeItem('caravana_save'); } catch (e) {} }
  addScore(name, score, rank) { try { const a = JSON.parse(localStorage.getItem('caravana_scores') || '[]'); a.push({name, score, rank}); a.sort((x, y) => y.score - x.score); localStorage.setItem('caravana_scores', JSON.stringify(a.slice(0, 10))); } catch (e) {} }
  scores() { try { return JSON.parse(localStorage.getItem('caravana_scores') || '[]'); } catch (e) { return []; } }
}
UI.App = App;
class Scene { constructor(app) { this.app = app; this.overlay = false; } enter() {} resume() {} handle() {} update() {} draw() {} }
UI.Scene = Scene;
})(globalThis.CV = globalThis.CV || {});
