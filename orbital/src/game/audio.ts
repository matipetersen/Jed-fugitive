import { type Flight } from './flight';

/** Procedural sound: engine rumble, alarms and chimes. Starts after the first user gesture. */
export class Audio {
  muted = false;
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private engine: GainNode | null = null;
  private engineFilter: BiquadFilterNode | null = null;
  private wind: GainNode | null = null;
  private lastAlarm = 0;

  constructor() {
    const unlock = (): void => {
      this.init();
      window.removeEventListener('pointerdown', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('pointerdown', unlock);
    window.addEventListener('keydown', unlock);
    try {
      this.muted = localStorage.getItem('orbital.muted') === '1';
    } catch {
      /* ignore */
    }
  }

  private init(): void {
    if (this.ctx) return;
    try {
      const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AC) return;
      const ctx = new AC();
      this.ctx = ctx;
      this.master = ctx.createGain();
      this.master.gain.value = this.muted ? 0 : 0.6;
      this.master.connect(ctx.destination);

      const buf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      const mk = (type: BiquadFilterType, freq: number): { g: GainNode; f: BiquadFilterNode } => {
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.loop = true;
        const f = ctx.createBiquadFilter();
        f.type = type;
        f.frequency.value = freq;
        const g = ctx.createGain();
        g.gain.value = 0;
        src.connect(f).connect(g).connect(this.master!);
        src.start();
        return { g, f };
      };
      const e = mk('lowpass', 200);
      this.engine = e.g;
      this.engineFilter = e.f;
      this.wind = mk('highpass', 1200).g;
    } catch {
      this.ctx = null;
    }
  }

  setMuted(m: boolean): void {
    this.muted = m;
    try {
      localStorage.setItem('orbital.muted', m ? '1' : '0');
    } catch {
      /* ignore */
    }
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(m ? 0 : 0.6, this.ctx.currentTime, 0.05);
  }

  /** Engine rumble for the arcade mode, 0..1, and an optional wind level. */
  engineLevel(thr: number, wind: number): void {
    if (!this.ctx || !this.engine || !this.engineFilter || !this.wind) return;
    const t = this.ctx.currentTime;
    this.engine.gain.setTargetAtTime(thr * 0.5, t, 0.05);
    this.engineFilter.frequency.setTargetAtTime(120 + thr * 500, t, 0.05);
    this.wind.gain.setTargetAtTime(Math.min(0.25, wind * 0.6), t, 0.1);
  }

  update(f: Flight): void {
    if (!this.ctx || !this.engine || !this.engineFilter || !this.wind) return;
    const s = f.world.ship;
    const thr = s.status === 'flying' || s.status === 'landed' ? s.throttle : 0;
    const t = this.ctx.currentTime;
    this.engine.gain.setTargetAtTime(thr * 0.5, t, 0.05);
    this.engineFilter.frequency.setTargetAtTime(120 + thr * 500, t, 0.05);
    const heat = Math.min(1, s.heat / f.world.stats.heatLimit);
    this.wind.gain.setTargetAtTime(Math.min(0.25, heat * 0.6), t, 0.1);
  }

  silence(): void {
    if (!this.ctx || !this.engine || !this.wind) return;
    const t = this.ctx.currentTime;
    this.engine.gain.setTargetAtTime(0, t, 0.05);
    this.wind.gain.setTargetAtTime(0, t, 0.05);
  }

  private beep(freq: number, start: number, dur: number, type: OscillatorType, vol: number): void {
    if (!this.ctx || !this.master) return;
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.setValueAtTime(0, start);
    g.gain.linearRampToValueAtTime(vol, start + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    o.connect(g).connect(this.master);
    o.start(start);
    o.stop(start + dur + 0.02);
  }

  alarm(): void {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    if (now - this.lastAlarm < 1) return;
    this.lastAlarm = now;
    this.beep(880, now, 0.14, 'square', 0.12);
    this.beep(660, now + 0.18, 0.14, 'square', 0.12);
    this.beep(880, now + 0.36, 0.14, 'square', 0.12);
  }

  chime(): void {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    this.beep(523, now, 0.25, 'sine', 0.15);
    this.beep(659, now + 0.12, 0.25, 'sine', 0.15);
    this.beep(784, now + 0.24, 0.45, 'sine', 0.15);
  }
}
