import { mulberry32 } from '../src/sim/rng';
import { RivalDriver } from '../src/arcade/ai';
import { Arena, BASE_STATS, STEP } from '../src/arcade/arena';
import { RACES } from '../src/arcade/races';

const i = Number(process.env.S ?? 0) | 0;
const def = RACES.find((r) => r.id === (process.env.RACE ?? 'guerra'))!.stages[i];
const arena = new Arena(def);
const ship = arena.addShip({ isPlayer: false, name: 'r', color: '#f0f', stats: { ...BASE_STATS, thrust: BASE_STATS.thrust * def.rival.skill }, start: def.rivalStart, infiniteFuel: true });
const d = new RivalDriver(mulberry32(7 + i));
let last = -1;
while (arena.t < 120 && !ship.finished) {
  const c = d.control(arena, ship);
  arena.step([c], STEP);
  for (const e of arena.events) if (e.type === 'die' || e.type === 'land') console.log(arena.t.toFixed(1), e.type, JSON.stringify(e));
  arena.events.length = 0;
  if (Math.floor(arena.t) !== last && ship.nextGate >= def.gates.length - 2) {
    last = Math.floor(arena.t);
    const bi = arena.finish.body;
    console.log(arena.t.toFixed(1), ship.status, 'gate', ship.nextGate, 'pos', ship.x.toFixed(0), ship.y.toFixed(0), 'relv', (ship.vx - arena.cur.vx[bi]).toFixed(0), (ship.vy - arena.cur.vy[bi]).toFixed(0), 'thr', ship.throttle.toFixed(2), 'ang', ship.angle.toFixed(2));
  }
}
console.log('finished', ship.finished, ship.finishTime.toFixed(1));
