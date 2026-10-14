/* Efectos de sonido sintetizados con WebAudio (sin archivos). */
(function (CV) {
'use strict';
let ac = null, master = null; const last = {};
const S = CV.sfx = {volume: .5, enabled: true};
function ensure() {
  if (ac) return true;
  try { const A = window.AudioContext || window.webkitAudioContext; if (!A) return false; ac = new A(); master = ac.createGain(); master.gain.value = S.volume; master.connect(ac.destination); return true; } catch (e) { return false; }
}
S.unlock = () => { if (ensure() && ac.state === 'suspended') ac.resume(); };
function noise(dur, decay, lp, vol, t0) {
  const n = Math.floor(ac.sampleRate * dur), buf = ac.createBuffer(1, n, ac.sampleRate), d = buf.getChannelData(0); let prev = 0;
  for (let i = 0; i < n; i++) { const x = Math.random() * 2 - 1; prev += (x - prev) * (1 - lp); d[i] = prev * Math.exp(-i / ac.sampleRate * decay) * vol; }
  const src = ac.createBufferSource(); src.buffer = buf; return src;
}
function tone(freq, dur, decay, vol, sweep, type, t0, dest) {
  const o = ac.createOscillator(), g = ac.createGain(); o.type = type || 'sine'; o.frequency.setValueAtTime(freq, t0);
  if (sweep) o.frequency.linearRampToValueAtTime(Math.max(20, freq + sweep * dur), t0 + dur);
  g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(.0001, t0 + Math.min(dur, 6 / Math.max(.1, decay)));
  o.connect(g); g.connect(dest); o.start(t0); o.stop(t0 + dur); return o;
}
const DEF = {
  shot: t => [['n', .28, 16, .45, .9], ['t', 80, .2, 18, .7, -120]], rifle: t => [['n', .35, 12, .6, .7], ['t', 60, .3, 14, .5, -60]],
  cannon: t => [['n', .7, 6, .8, 1], ['t', 50, .6, 7, .9, -30]], hit: t => [['n', .07, 40, .3, .6]], thunk: t => [['n', .07, 50, .7, .5], ['t', 140, .08, 40, .5]],
  chop: t => [['n', .06, 60, .5, .5], ['t', 220, .06, 50, .4]], death: t => [['t', 300, .35, 6, .4, -600]], hurt: t => [['t', 220, .18, 12, .45, -200, 'square']],
  boom: t => [['n', .9, 5, .85, 1], ['t', 45, .8, 5, .9]], click: t => [['t', 660, .06, 40, .35]], bow: t => [['n', .12, 22, .1, .25]],
  horn: t => [['t', 196, .35, 3, .4, 0, 'square'], ['t', 262, .55, 2.5, .4, 0, 'square', .35]], win: t => [['t', 392, .16, 5, .4], ['t', 523, .16, 5, .4, 0, 'sine', .16], ['t', 659, .5, 3, .4, 0, 'sine', .32]],
  lose: t => [['t', 330, .25, 4, .4], ['t', 262, .25, 4, .4, 0, 'sine', .25], ['t', 196, .6, 3, .4, 0, 'sine', .5]], coin: t => [['t', 988, .07, 20, .35], ['t', 1319, .2, 10, .35, 0, 'sine', .07]],
};
S.play = function (name, vol, gap) {
  if (!S.enabled || !ensure() || ac.state === 'suspended') return;
  const def = DEF[name]; if (!def) return;
  const now = performance.now() / 1000;
  if (gap) { if (now - (last[name] || -9) < gap) return; last[name] = now; }
  try {
    const out = ac.createGain(); out.gain.value = Math.max(0, Math.min(1, (vol === undefined ? 1 : vol))); out.connect(master);
    const t0 = ac.currentTime;
    for (const p of def()) {
      if (p[0] === 'n') { const src = noise(p[1], p[2], p[3], p[4], t0); const g = ac.createGain(); g.gain.value = 1; src.connect(g); g.connect(out); src.start(t0); }
      else tone(p[1], p[2], p[3], p[4], p[5] || 0, p[6], t0 + (p[7] || 0), out);
    }
  } catch (e) {}
};
})(globalThis.CV = globalThis.CV || {});
