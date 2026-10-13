// Dev tool: a bot plays the endless mode. SEED=5 P=expert MAX=30 npx vite-node scripts/endless-run.ts
import { mulberry32 } from '../src/sim/rng';
import { BOT_PROFILES, PlayerBot } from '../src/arcade/bot';
import { makeEndlessRace } from '../src/arcade/endless';
import { newMeta } from '../src/arcade/meta';
import { Mission } from '../src/arcade/mission';

const race = makeEndlessRace(Number(process.env.SEED ?? 5));
const m = new Mission(newMeta(), { stage: 0, race });
const bot = new PlayerBot(mulberry32(3), BOT_PROFILES[process.env.P ?? 'expert']);
const max = Number(process.env.MAX ?? 30);
for (let n = 0; n < max && !m.over; n++) {
  const t0 = Date.now();
  for (let f = 0; f < 60 * 240 && m.phase !== 'cleared'; f++) {
    m.update(1 / 60, bot.control(m));
    m.checkBeacon();
  }
  const d = m.def;
  console.log(`${String(d.id).padStart(3)} ${d.name.slice(0, 26).padEnd(26)} ${(d.kind ?? '').padEnd(16)} skulls ${d.skulls} ${m.result?.won ? 'WIN ' : 'LOSS'} t=${(m.result?.time ?? 0).toFixed(0)}s cont=${m.continues} streak=${m.streak} cpu=${Date.now() - t0}ms`);
  if (m.over) break;
  if (!m.nextStage()) break;
}
console.log('over', m.over, 'cleared', m.stagesCleared);
