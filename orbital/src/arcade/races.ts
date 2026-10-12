import { STAGES } from './stages';
import { KESSEL_RACE } from './kessel';
import { BOONTA, HALLEY, MARTE2020, POLO_SUR, REDLINE, REUTILIZABLES, VENERA, VOYAGER } from './more';
import * as N from './more2';
import { ASISTENCIAS } from './assist';
import { type RaceDef } from './types';

/** A race with extra stages spliced in; stage numbers follow the new order. */
function extend(race: RaceDef, order: (s: RaceDef['stages']) => RaceDef['stages']): RaceDef {
  return { ...race, stages: order(race.stages).map((st, i) => ({ ...st, id: i + 1 })) };
}

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
  ASISTENCIAS,
  extend(POLO_SUR, (s) => [s[0], N.polo_fall, s[1], N.polo_double, s[2]]),
  extend(VENERA, (s) => [s[0], N.venera_air, s[1], N.venera_balloon, s[2]]),
  extend(HALLEY, (s) => [s[0], N.halley_chase, s[1], N.halley_cargo, s[2]]),
  extend(VOYAGER, (s) => [s[0], N.voyager_belt, s[1], N.voyager_rings, s[2]]),
  extend(MARTE2020, (s) => [s[0], s[1], N.marte_entry, N.marte_cargo, s[2]]),
  extend(REUTILIZABLES, (s) => [s[0], N.reut_double, s[1], N.reut_reentry, s[2]]),
  extend(BOONTA, (s) => [s[0], N.boonta_night, s[1], N.boonta_run, s[2]]),
  extend(REDLINE, (s) => [s[0], N.redline_fall, s[1], N.redline_cargo, s[2]]),
];

export const raceById = (id: string): RaceDef => RACES.find((r) => r.id === id) ?? RACES[0];

/** What the last screen says when a mission ends in each race. */
const ENDINGS: Record<string, { winTitle: string; win: string; lose: string }> = {
  guerra: {
    winTitle: 'LLEGASTE A PLUTÓN',
    win: 'El primer humano en Plutón. La Guerra Fría terminó en el borde del sistema solar.',
    lose: 'La bandera del rival ya flamea en Plutón. La carrera se decidió sin vos.',
  },
  kessel: {
    winTitle: 'SALISTE DEL MAW',
    win: 'Cruzaste el Maw y llegaste a Savareen con la carga intacta. Cerca de los agujeros negros, el camino corto se hace leyenda.',
    lose: 'El Interdictor te cerró el paso y la carga quedó atrás, en el Maw. La ruta corta cobra su peaje.',
  },
  asistencias: {
    winTitle: 'LLEGASTE SIN COMBUSTIBLE',
    win: 'Cinco misiones que no habrían llegado sin la gravedad de los planetas. La honda gravitatoria es la forma más barata de cruzar el sistema solar.',
    lose: 'El destino quedó lejos y el tanque no alcanzó. Cada curva cerrada alrededor de un planeta es combustible que no gastás.',
  },
  polosur: {
    winTitle: 'POLO SUR CONQUISTADO',
    win: 'Aterrizaste junto al polo sur lunar antes que Luna-25. Esta vez nadie se estrelló.',
    lose: 'El polo sur lunar quedó para otro. En 2023 solo una de las dos naves llegó entera.',
  },
  venera: {
    winTitle: 'SOBREVIVISTE A VENUS',
    win: 'Bajaste, subiste y volviste a la órbita con la nave aplastada pero entera. Venus no perdona, y vos tampoco.',
    lose: 'Venus se quedó con tu nave. Noventa atmósferas pesan más que cualquier motor.',
  },
  halley: {
    winTitle: 'TOCASTE EL NÚCLEO',
    win: 'Aterrizaste en el núcleo del Halley, a decenas de km/s del resto de las sondas. No vuelve hasta 2061.',
    lose: 'El polvo del cometa te ganó la partida. El Halley no vuelve hasta 2061: tendrás que esperar.',
  },
  voyager: {
    winTitle: 'GRAN TOUR COMPLETADO',
    win: 'Saltaste de gigante en gigante y llegaste a Neptuno. Una alineación así no se repite por casi dos siglos.',
    lose: 'La ventana se cerró. La próxima alineación de planetas está a casi doscientos años.',
  },
  marte2020: {
    winTitle: 'JEZERO ALCANZADO',
    win: 'Los siete minutos de terror terminaron con las ruedas en el suelo marciano. Ventana aprovechada.',
    lose: 'La ventana a Marte se cierra y no vuelve hasta dentro de 26 meses.',
  },
  reutilizables: {
    winTitle: 'EL COHETE VOLVIÓ',
    win: 'Subiste, cruzaste la línea y volviste a posarte sobre una plataforma diminuta. Lo imposible ahora es rutina.',
    lose: 'El cohete no volvió entero. Aterrizar sobre una plataforma así lleva muchos intentos.',
  },
  boonta: {
    winTitle: 'GANASTE LA BOONTA EVE',
    win: 'Cruzaste la meta rodeado de escombros y con Sebulba en la cola. Tatooine entera grita tu nombre.',
    lose: 'Sebulba cruzó primero, como siempre que hace trampa.',
  },
  redline: {
    winTitle: 'CRUZASTE LA META DE REDLINE',
    win: 'La carrera más peligrosa del universo y vos en el podio, con la nave humeando. Neón y velocidad hasta el final.',
    lose: 'Redline se lleva a los que no frenan a tiempo. La próxima, más lento en las curvas y más rápido en las rectas.',
  },
};

ENDINGS.granpremio = {
  winTitle: 'SUBISTE AL PODIO',
  win: 'Saliste de la grilla entre once naves, sobreviviste a las dos vueltas y aterrizaste entre los tres primeros. Hoy el podio tiene tu nombre.',
  lose: 'Entre los empujones y las rocas el podio se llenó sin vos. Mañana, otra grilla y otro planeta.',
};
ENDINGS.diaria = {
  winTitle: 'SECTOR DIARIO LIMPIO',
  win: 'Completaste los seis sectores de hoy. Mañana habrá otros, y más difíciles de adivinar.',
  lose: 'El rival se llevó la carrera de hoy. Mañana, otra semilla.',
};
ENDINGS.sinfin = {
  winTitle: 'SECTORES SUPERADOS',
  win: 'Los diez sectores al azar quedaron atrás. El próximo mapa no se parece a ninguno.',
  lose: 'El sector se te cerró. Los mapas cambian en cada misión: aprendés los principios, no las rutas.',
};

export const endingOf = (id: string): { winTitle: string; win: string; lose: string } => ENDINGS[id] ?? ENDINGS.guerra;
