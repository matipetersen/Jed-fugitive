// Dev tool: how often do bots of three skill levels clear each arcade stage and the whole mission?
// Run: npx vite-node scripts/calibrate-arcade.ts   (N, FB, FG environment variables tune it)
import { mulberry32 } from '../src/sim/rng';
import { FUEL_PRICE } from '../src/arcade/ai';
import { BOT_PROFILES, PlayerBot } from '../src/arcade/bot';
import { newMeta } from '../src/arcade/meta';
import { Mission } from '../src/arcade/mission';
import { STAGES } from '../src/arcade/stages';

const L = (s: string): void => console.log(s);

function play(profile: string, seed: number, startStage: number, full: boolean) {
  const m = new Mission(newMeta(), { stage: startStage });
  const bot = new PlayerBot(mulberry32(seed), BOT_PROFILES[profile]);
  const times: number[] = [];
  const rivalTimes: number[] = [];
  let stageDeaths = 0;
  for (let f = 0; f < 60 * 60 * 6 && !m.over; f++) {
    m.update(1 / 60, bot.control(m));
    m.checkBeacon();
    if (m.phase === 'cleared' && !m.over) {
      times.push(m.result!.time);
      rivalTimes.push(m.result!.rivalTime);
      if (!full) break;
      m.nextStage();
    }
  }
  if (m.over === 'won') times.push(m.result?.time ?? 0);
  return { stages: m.stagesCleared, deaths: m.deaths, over: m.over, reason: m.result?.reason ?? '', times, rivalTimes, stageDeaths };
}

function main(): void {
  const N = Number(process.env.N ?? 8);
  FUEL_PRICE.base = Number(process.env.FB ?? 2);
  FUEL_PRICE.gain = Number(process.env.FG ?? 8);
  for (const profile of ['expert', 'good', 'average']) {
    const line: string[] = [];
    for (let i = 0; i < STAGES.length; i++) {
      let clears = 0, deaths = 0, tsum = 0, rsum = 0;
      for (let s = 0; s < N; s++) {
        const r = play(profile, 100 + s * 13 + i, i, false);
        if (r.stages >= 1) { clears++; tsum += r.times[0]; rsum += r.rivalTimes[0]; }
        deaths += r.deaths;
      }
      line.push(`S${i + 1} ${clears}/${N} t=${clears ? (tsum / clears).toFixed(0) : '-'} rv=${clears ? (rsum / clears).toFixed(0) : '-'} d=${(deaths / N).toFixed(1)}`);
    }
    L(`${profile.padEnd(8)} ${line.join(' | ')}`);
  }
  // Full missions.
  for (const profile of ['expert', 'good', 'average']) {
    let won = 0, stagesSum = 0;
    const reasons: Record<string, number> = {};
    for (let s = 0; s < N; s++) {
      const r = play(profile, 900 + s, 0, true);
      if (r.over === 'won') won++;
      stagesSum += r.stages;
      reasons[r.reason || r.over || '?'] = (reasons[r.reason || r.over || '?'] || 0) + 1;
    }
    L(`full ${profile}: won ${won}/${N}, avg stages ${(stagesSum / N).toFixed(1)} ${JSON.stringify(reasons)}`);
  }
}
main();
