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

export const endingOf = (id: string): { winTitle: string; win: string; lose: string } => ENDINGS[id] ?? ENDINGS.guerra;
