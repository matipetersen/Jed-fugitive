// Dev tool: can the rival fly randomly generated stages? SEEDS=30 npx vite-node scripts/verify-procgen.ts
import { mulberry32 } from '../src/sim/rng';
import { RivalDriver } from '../src/arcade/ai';
import { Arena, BASE_STATS, STEP } from '../src/arcade/arena';
import { generateStage } from '../src/arcade/procgen';

const seeds = Number(process.env.SEEDS ?? 20);
const tpls = ['hop', 'circuit', 'gauntlet', 'double', 'cargo', 'fall'] as const;
for (const tpl of tpls) {
  let ok = 0, tsum = 0, dsum = 0;
  const bad: number[] = [];
  for (let s = 1; s <= seeds; s++) {
    const d = (s % 5) / 4;
    const def = generateStage(s, 1, d, tpl);
    const arena = new Arena(def);
    const ship = arena.addShip({ isPlayer: false, name: 'r', color: '#f0f', stats: { ...BASE_STATS, thrust: BASE_STATS.thrust * def.rival.skill }, start: def.rivalStart, orbit: def.startAt, infiniteFuel: true });
    const dr = new RivalDriver(mulberry32(7 + s), def.rival.ai);
    let deaths = 0;
    while (arena.t < 140 && !ship.finished) {
      arena.step([dr.control(arena, ship)], STEP);
      for (const e of arena.events) if (e.type === 'die') deaths++;
      arena.events.length = 0;
    }
    if (ship.finished) { ok++; tsum += ship.finishTime; } else bad.push(s);
    dsum += deaths;
  }
  console.log(`${tpl.padEnd(9)} ${ok}/${seeds} avg ${ok ? (tsum / ok).toFixed(0) : '-'}s deaths ${(dsum / seeds).toFixed(1)} failed seeds ${bad.join(',')}`);
}
