import { STAGES } from './stages';
import { KESSEL_RACE } from './kessel';
import { BOONTA, HALLEY, MARTE2020, POLO_SUR, REDLINE, REUTILIZABLES, VENERA, VOYAGER } from './more';
import { type RaceDef } from './types';

/** Every race in the game. The first is the Cold War space race. */
export const RACES: RaceDef[] = [
  {
    id: 'guerra',
    name: 'LA CARRERA ESPACIAL',
    subtitle: '1957 - 1991 · EE.UU. vs URSS',
    blurb: 'De Sputnik a Plutón. Gravedad, honda gravitatoria y una nave rival que no te espera.',
    stages: STAGES,
  },
  KESSEL_RACE,
  POLO_SUR,
  VENERA,
  HALLEY,
  VOYAGER,
  MARTE2020,
  REUTILIZABLES,
  BOONTA,
  REDLINE,
];

export const raceById = (id: string): RaceDef => RACES.find((r) => r.id === id) ?? RACES[0];
