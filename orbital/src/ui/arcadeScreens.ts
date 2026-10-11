import { type ArcadeController } from '../arcade/controller';
import { type MissionRecord, UPGRADES, kitCount } from '../arcade/meta';
import { STAGES } from '../arcade/stages';
import { h } from './dom';

function btn(label: string, onclick: () => void, cls = '', disabled = false): HTMLButtonElement {
  return h('button', { class: `btn ${cls}`, onclick, disabled }, label);
}

const kv = (k: string, v: string, cls = ''): HTMLElement => h('div', {}, h('span', { class: 'k' }, `${k} `), h('span', { class: `v ${cls}` }, v));
const skulls = (n: number): string => '☠'.repeat(n) + '·'.repeat(5 - n);
const fmtT = (s: number): string => `${s.toFixed(1)} s`;

const ARCADE_HELP: [string, string][] = [
  ['Objetivo', 'Pasá por los aros en orden y aterrizá en la plataforma meta antes que la nave rival. Son 5 etapas: unos 3 a 5 minutos si todo sale bien.'],
  ['Gravedad', 'Todo cae hacia los planetas y los planetas se mueven. Usá su gravedad para ganar velocidad (honda gravitatoria) y no te acerques a ciegas.'],
  ['Controles', 'Apoyá el dedo donde quieras y arrastrá hacia donde querés ir: la nave gira hacia esa dirección y acelera cuando queda alineada; cuanto más lejos arrastrás, más empuje. Para frenar, apuntá en contra de tu movimiento. Soltá para planear. APUNTA gira solo hacia el próximo aro.'],
  ['Aterrizar', 'Despacio (menos de 40 u/s) y derecho. Las franjas amarillas con llama son estaciones: reparan, recargan, guardan tus datos y son tu punto de reaparición.'],
  ['Vidas', 'Tenés 3 por etapa. Si te quedás sin vidas, o el rival aterriza primero, perdés la etapa (cobrás menos) pero la misión sigue: se juegan las 5 etapas.'],
  ['Datos', 'Los ganás pasando aros, con hondas gravitatorias y adelantando al rival. Si morís perdés los que llevabas, pero quedan en una baliza: volvé a tocarla para recuperarlos. Cada nave que explota además deja telemetría (datos extra). Con los datos comprás mejoras entre etapas; al terminar la misión la tecnología se reinicia.'],
  ['Cápsulas', 'Tocá CÁP para recuperar combustible y casco. Se recargan en cada estación.'],
  ['Rival', 'Corre a la vez que vos y se pueden chocar. Un golpe fuerte lo frena a él también.'],
  ['Práctica', 'Las etapas que ya alcanzaste se pueden practicar sin vidas ni recompensas, con la nave básica.'],
];

/** Upgrade list, bought with saved data; used in the centre and between stages. */
function shop(c: ArcadeController): HTMLElement[] {
  const m = c.meta;
  return UPGRADES.map((u) => {
    const level = m.upgrades[u.id];
    const maxed = level >= u.max;
    return h('div', { class: 'panel' },
      h('div', { class: 'row' },
        h('span', { class: maxed ? 'good' : 'v' }, `${u.name} ${'■'.repeat(level)}${'□'.repeat(u.max - level)}`),
        h('span', { class: 'k' }, u.desc),
        btn(maxed ? 'AL MÁXIMO' : `${u.cost(level)} DATOS`, () => c.buy(u.id), 'go', maxed || m.data < u.cost(level)),
      ),
    );
  });
}

export const arcadeScreens = {
  hub(c: ArcadeController): HTMLElement {
    const m = c.meta;
    const next = Math.min(Math.max(m.cleared, m.reached - 1), STAGES.length - 1);
    return h('div', { class: 'screen' },
      h('h1', {}, 'CARRERA ESPACIAL'),
      h('p', { class: 'sub' }, `Etapas ganadas alguna vez ${m.cleared}/5 · misiones ${m.attempts} · naves perdidas ${m.deaths}`),
      h('div', { class: 'row' },
        btn('INICIAR MISIÓN', () => c.startMission(0, false), 'go'),
        btn('VOLVER AL INICIO', () => c.exit()),
      ),
      h('p', { class: 'sub' }, m.won
        ? 'Llegaste a Plutón primero. La carrera sigue abierta: probá mejorar tus tiempos.'
        : m.cleared === 0 ? 'La misión completa son 5 etapas contra la nave rival. Tenés 3 vidas.' : `Tu mejor avance: etapa ${m.cleared}. El rival no espera.`),
      h('h2', {}, 'PRÁCTICA'),
      h('div', { class: 'row' }, ...STAGES.map((s, i) => btn(`${s.id}. ${s.name}`, () => c.startMission(i, true), '', i > next))),
      h('h2', {}, 'TECNOLOGÍA'),
      h('p', { class: 'sub' }, 'Cada misión empieza con la nave básica. Los datos que ganás (y la telemetría de las naves que perdés) se gastan en mejoras entre etapa y etapa, pero solo valen para esa misión.'),
      h('h2', {}, 'MEJORES TIEMPOS'),
      h('div', { class: 'grid' }, ...STAGES.map((s, i) => kv(`${s.id}. ${s.name}`, m.best[i] === null ? '--' : fmtT(m.best[i]!)))),
      h('h2', {}, 'MEJORES MISIONES'),
      ...(m.records.length === 0
        ? [h('p', { class: 'sub' }, 'Todavía no terminaste ninguna misión.')]
        : m.records.slice(0, 5).map((r: MissionRecord, i) => h('div', { class: 'row' },
            h('span', { class: 'amber' }, `#${i + 1}`),
            h('span', { class: r.won ? 'good' : 'v' }, r.won ? 'VICTORIA' : `${r.stages}/5 etapas`),
            h('span', { class: 'k' }, `${fmtT(r.time)} · ${r.data} datos · ${r.deaths} muertes`),
          ))),
      h('div', { class: 'row', style: 'margin-top:14px' }, btn('CÓMO SE JUEGA', () => c.openHelp())),
    );
  },

  help(back: () => void): HTMLElement {
    return h('div', { class: 'screen' },
      h('h1', {}, 'CÓMO SE JUEGA'),
      btn('VOLVER', back, 'go'),
      h('div', { class: 'panel' }, h('ul', { class: 'tight' }, ...ARCADE_HELP.map(([k, v]) => h('li', {}, h('span', { class: 'amber' }, `${k}: `), v)))),
    );
  },

  intro(c: ArcadeController): HTMLElement {
    const m = c.mission;
    const def = m.def;
    return h('div', { class: 'screen' },
      h('p', { class: 'sub' }, `${def.year} · etapa ${def.id} de ${STAGES.length}${m.practice ? ' · PRÁCTICA' : ''}`),
      h('h1', {}, def.name.toUpperCase()),
      h('p', { class: 'amber' }, `Dificultad ${skulls(def.skulls)}`),
      h('p', {}, def.blurb),
      h('div', { class: 'panel' },
        kv('Rival', def.rival.name, 'bad'),
        kv('Aros', String(def.gates.length)),
        kv('Vidas', m.practice ? 'sin límite' : `${m.lives}`),
        kv('Cápsulas', String(m.kits)),
        kv('Datos que llevás', String(m.carried)),
      ),
      h('div', { class: 'row' },
        btn('LISTO', () => c.begin(), 'go'),
        btn('ABANDONAR', () => c.openPauseExit(), 'bad'),
      ),
    );
  },

  pause(c: ArcadeController): HTMLElement {
    const m = c.mission;
    return h('div', { class: 'screen' },
      h('h1', {}, 'PAUSA'),
      h('p', { class: 'sub' }, `Etapa ${m.def.id} · ${m.practice ? 'práctica' : `vidas ${m.lives}`} · datos en mano ${m.carried}`),
      h('div', { class: 'row' },
        btn('CONTINUAR', () => c.resume(), 'go'),
        m.practice ? btn('REINICIAR ETAPA', () => c.retry(), 'warn') : null,
        btn(m.practice ? 'SALIR DE LA PRÁCTICA' : 'ABANDONAR MISIÓN', () => c.abandon(), 'bad'),
      ),
      h('div', { class: 'row', style: 'margin-top:10px' },
        btn(c.audio.muted ? 'SONIDO: NO' : 'SONIDO: SÍ', () => { c.audio.setMuted(!c.audio.muted); c.openPause(); }),
        btn('CÓMO SE JUEGA', () => c.openHelp(() => c.openPause())),
      ),
    );
  },

  cleared(c: ArcadeController): HTMLElement {
    const m = c.mission;
    const r = m.result!;
    const last = m.stageIdx === STAGES.length - 1;
    const final = !!m.over;
    const title = final ? (r.won ? 'LLEGASTE A PLUTÓN' : 'MISIÓN TERMINADA') : r.won ? 'ETAPA SUPERADA' : 'ETAPA PERDIDA';
    const next = !last && !m.practice && !final ? STAGES[m.stageIdx + 1] : null;
    return h('div', { class: 'screen' },
      h('h1', { class: r.won ? 'good' : 'bad' }, title),
      h('p', { class: 'sub' }, r.won ? `Llegaste primero a ${m.def.name}.` : r.reason),
      h('div', { class: 'panel' },
        r.won ? kv('Tu tiempo', fmtT(r.time), 'good') : null,
        kv(m.rival.name, m.rival.finished ? fmtT(r.rivalTime) : 'no llegó', 'bad'),
        !m.practice ? kv(r.won ? 'Recompensa' : 'Recompensa reducida', `+${r.reward} datos`, 'amber') : null,
        !m.practice ? kv('Naves perdidas', `${m.deaths}`) : null,
        !m.practice ? kv('Datos de la misión', `${m.earned}`) : null,
        !m.practice ? kv('Etapas ganadas', `${m.stagesCleared}/${STAGES.length}`) : null,
      ),
      final && r.won ? h('p', {}, 'El primer humano en Plutón. La Guerra Fría terminó en el borde del sistema solar.') : null,
      final && !r.won ? h('p', {}, 'La carrera se decidió sin vos. Cada misión empieza de cero: la próxima vez ya sabés dónde cae la gravedad.') : null,
      h('div', { class: 'row' },
        next ? btn('SIGUIENTE ETAPA', () => c.nextStage(), 'go') : null,
        m.practice ? btn('REPETIR', () => c.retry(), 'warn') : null,
        final ? btn('NUEVA MISIÓN', () => c.startMission(0, false), 'go') : null,
        btn('CENTRO DE MISIÓN', () => c.openHub(), ''),
      ),
      ...(next
        ? [
            h('h2', {}, 'EQUIPAMIENTO PARA LA SIGUIENTE ETAPA'),
            h('p', { class: 'sub' }, `Datos disponibles: ${c.meta.data}. Lo que compres vale desde ya, pero solo en esta misión. Siguiente: ${next.name} (${skulls(next.skulls)}).`),
            ...shop(c),
            h('div', { class: 'row' }, btn('SIGUIENTE ETAPA', () => c.nextStage(), 'go')),
          ]
        : []),
    );
  },

  failed(c: ArcadeController): HTMLElement {
    const m = c.mission;
    const r = m.result;
    return h('div', { class: 'screen' },
      h('h1', { class: 'bad' }, 'MISIÓN FRACASADA'),
      h('p', { class: 'sub' }, r?.reason ?? ''),
      h('div', { class: 'panel' },
        kv('Etapas superadas', `${m.stagesCleared}/${STAGES.length}`),
        kv('Muertes', String(m.deaths)),
        kv('Datos ganados esta misión', String(m.earned), 'amber'),
        kv('Datos perdidos', `${m.carried}`, 'bad'),
      ),
      h('p', { class: 'sub' }, `Los datos guardados (${c.meta.data}) compran mejoras. Cada fracaso enseña dónde cae la gravedad.`),
      h('div', { class: 'row' },
        btn('CENTRO DE MISIÓN', () => c.openHub(), 'go'),
        btn('REINTENTAR', () => c.startMission(0, false), 'warn'),
      ),
    );
  },

  confirmExit(c: ArcadeController): HTMLElement {
    return h('div', { class: 'screen' },
      h('h1', {}, '¿ABANDONAR?'),
      h('p', { class: 'sub' }, 'Se pierde el avance de esta misión y los datos que llevás.'),
      h('div', { class: 'row' }, btn('SEGUIR', () => c.openIntro(), 'go'), btn('ABANDONAR', () => c.abandon(), 'bad')),
    );
  },
};

export { kitCount };
