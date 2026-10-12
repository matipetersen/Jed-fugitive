// Dev tool: can the rival fly each stage alone, and how do bots of different skill fare?
// Run: RACE=kessel N=3 npx vite-node scripts/verify-races.ts
import { mulberry32 } from '../src/sim/rng';
import { RivalDriver } from '../src/arcade/ai';
import { Arena, BASE_STATS, STEP } from '../src/arcade/arena';
import { BOT_PROFILES, PlayerBot } from '../src/arcade/bot';
import { newMeta } from '../src/arcade/meta';
import { Mission } from '../src/arcade/mission';
import { RACES } from '../src/arcade/races';

const only = process.env.RACE;
const N = Number(process.env.N ?? 3);
const profiles = (process.env.P ?? 'expert,average').split(',');

for (const race of RACES) {
  if (only && race.id !== only) continue;
  console.log(`== ${race.name}`);
  race.stages.forEach((def, i) => {
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: false, name: 'r', color: '#f0f', stats: { ...BASE_STATS, thrust: BASE_STATS.thrust * def.rival.skill }, start: def.rivalStart, orbit: def.startAt ? { ...def.startAt, angle: def.startAt.angle + 9 * (def.startAt.dir ?? 1) } : undefined, infiniteFuel: true });
    const d = new RivalDriver(mulberry32(7 + i), def.rival.ai);
    let deaths = 0;
    while (arena.t < 260 && !ship.finished) {
      arena.step([d.control(arena, ship)], STEP);
      for (const e of arena.events) if (e.type === 'die') deaths++;
      arena.events.length = 0;
    }
    const parts = [`S${i + 1} ${def.name.padEnd(18)} rival ${ship.finished ? ship.finishTime.toFixed(0) + 's' : 'NO'} d${deaths} par ${def.par}`];
    for (const pf of profiles) {
      let wins = 0, tsum = 0, dsum = 0, reasons = '';
      for (let s = 0; s < N; s++) {
        const m = new Mission(newMeta(), { stage: i, race });
        const bot = new PlayerBot(mulberry32(100 + s * 13 + i), BOT_PROFILES[pf]);
        for (let f = 0; f < 60 * 260 && m.phase !== 'cleared'; f++) {
          m.update(1 / 60, bot.control(m));
          m.checkBeacon();
        }
        if (m.result?.won) { wins++; tsum += m.result.time; } else reasons = (m.result?.reason ?? 'timeout').slice(0, 40);
        dsum += m.deaths;
      }
      parts.push(`${pf} ${wins}/${N} t${wins ? (tsum / wins).toFixed(0) : '-'} d${(dsum / N).toFixed(1)}${wins < N ? ' [' + reasons + ']' : ''}`);
    }
    console.log(parts.join(' | '));
  });
}
