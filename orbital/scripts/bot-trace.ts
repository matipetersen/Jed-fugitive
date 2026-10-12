// Dev tool: follow a bot through one stage. RACE=voyager S=0 P=expert npx vite-node scripts/bot-trace.ts
import { mulberry32 } from '../src/sim/rng';
import { BOT_PROFILES, PlayerBot } from '../src/arcade/bot';
import { newMeta } from '../src/arcade/meta';
import { Mission } from '../src/arcade/mission';
import { RACES } from '../src/arcade/races';

const race = RACES.find((r) => r.id === (process.env.RACE ?? 'guerra'))!;
const S = Number(process.env.S ?? 0) | 0;
const m = new Mission(newMeta(), { stage: S, race });
const bot = new PlayerBot(mulberry32(100 + S), BOT_PROFILES[process.env.P ?? 'expert']);
let last = -1;
for (let f = 0; f < 60 * 260 && m.phase !== 'cleared'; f++) {
  m.update(1 / 60, bot.control(m));
  const a = m.arena;
  const p = m.player;
  if (Math.floor(a.clock / 3) !== last && a.clock > 0) {
    last = Math.floor(a.clock / 3);
    const g = { x: 0, y: 0 };
    a.objective(p, g);
    console.log(a.clock.toFixed(0), p.status, 'g', p.nextGate, 'pos', p.x.toFixed(0), p.y.toFixed(0), 'v', Math.hypot(p.vx, p.vy).toFixed(0), 'fuel', p.fuel.toFixed(0), 'hull', p.hull.toFixed(0), 'dObj', Math.hypot(g.x - p.x, g.y - p.y).toFixed(0), p.deathReason);
  }
}
console.log(m.phase, m.result?.reason);
