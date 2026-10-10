import { aiControl, newAi, type AiOptions, type AiState } from './ai';
import { type Mission } from './mission';
import { type Controls } from './types';

export interface BotProfile {
  name: string;
  opts: AiOptions;
  /** Use a repair capsule when hull or fuel drops below these. */
  kitHull: number;
  kitFuel: number;
}

/** A stand-in for a decent human pilot: slower reactions, a shorter look-ahead and sloppier aim. */
export const BOT_PROFILES: Record<string, BotProfile> = {
  expert: { name: 'experto', opts: { horizon: 1.6, dt: 0.05, interval: 0.1, noise: 0 }, kitHull: 30, kitFuel: 12 },
  good: { name: 'bueno', opts: { horizon: 1.3, dt: 0.05, interval: 0.2, noise: 0.12 }, kitHull: 30, kitFuel: 12 },
  average: { name: 'regular', opts: { horizon: 1.0, dt: 0.05, interval: 0.3, noise: 0.3 }, kitHull: 25, kitFuel: 8 },
};

export class PlayerBot {
  private ai: AiState = newAi();
  private lastStage = -1;

  constructor(
    private readonly rnd: () => number,
    readonly profile: BotProfile,
  ) {}

  control(m: Mission): Controls {
    if (this.lastStage !== m.stageIdx) {
      this.ai = newAi();
      this.lastStage = m.stageIdx;
    }
    const p = m.player;
    if (p.status === 'dead') return { throttle: 0, turn: 0 };
    if ((p.hull < this.profile.kitHull || p.fuel < this.profile.kitFuel) && m.kits > 0) m.useKit();
    return aiControl(m.arena, p, this.ai, this.rnd, this.profile.opts);
  }
}
