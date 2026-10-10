import { type Bloc, type Campaign } from './campaign';
import { totalScore } from './rules';
import { yearOf } from '../sim/units';

export interface RecordEntry {
  score: number;
  bloc: Bloc;
  difficulty: 0 | 1 | 2;
  outcome: 'won' | 'lost' | 'retired';
  year: number;
  seed: number;
}

const KEY = 'orbital.records.v1';

export function loadRecords(): RecordEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as RecordEntry[]) : [];
  } catch {
    return [];
  }
}

export function addRecord(entry: RecordEntry): RecordEntry[] {
  const list = [...loadRecords(), entry].sort((a, b) => b.score - a.score).slice(0, 10);
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* ignore */
  }
  return list;
}

export function recordFor(c: Campaign, time: number): RecordEntry {
  return {
    score: totalScore(c),
    bloc: c.bloc,
    difficulty: c.difficulty,
    outcome: c.status === 'won' ? 'won' : c.status === 'lost' ? 'lost' : 'retired',
    year: Math.floor(yearOf(time)),
    seed: c.seed,
  };
}

const checksum = (s: string): string => {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return (h % 46656).toString(36).padStart(3, '0');
};

/**
 * Compact code to compare runs: seed, difficulty, bloc, outcome, year and score.
 * It carries a checksum against typos only. The game runs on the client, so it
 * does not prove the score was earned.
 */
export function shareCode(e: RecordEntry): string {
  const body = [e.seed.toString(36), e.difficulty, e.bloc === 'usa' ? 'u' : 's', e.outcome[0], e.year.toString(36), e.score.toString(36)].join('-');
  return `ORB-${body}-${checksum(body)}`.toUpperCase();
}

export function parseShareCode(code: string): RecordEntry | null {
  const m = /^ORB-(.+)-([0-9A-Z]{3})$/.exec(code.trim().toUpperCase());
  if (!m) return null;
  const body = m[1].toLowerCase();
  if (checksum(body).toUpperCase() !== m[2]) return null;
  const parts = body.split('-');
  if (parts.length !== 6) return null;
  const [seed, diff, bloc, out, year, score] = parts;
  const outcome = out === 'w' ? 'won' : out === 'l' ? 'lost' : 'retired';
  return {
    seed: parseInt(seed, 36),
    difficulty: Number(diff) as 0 | 1 | 2,
    bloc: bloc === 'u' ? 'usa' : 'urss',
    outcome,
    year: parseInt(year, 36),
    score: parseInt(score, 36),
  };
}
