import { type App } from '../game/app';
import { type Campaign } from '../game/campaign';
import { BASE_CAPACITY, baseRate } from '../game/flight';
import { type RecordEntry, loadRecords, parseShareCode, recordFor, shareCode } from '../game/records';
import {
  LAUNCH_COST,
  MILESTONES,
  doneCount,
  playerName,
  rivalName,
  scoreBreakdown,
  totalScore,
  yearBudget,
} from '../game/rules';
import { BODIES } from '../sim/bodies';
import { ENGINES, TECHS, statsFor } from '../sim/tech';
import { DAY, fmtDate, fmtDuration, yearOf } from '../sim/units';
import { h } from './dom';

const bar = (frac: number, cls = ''): HTMLElement => h('div', { class: `bar ${cls}` }, h('i', { style: `width:${Math.max(0, Math.min(1, frac)) * 100}%` }));

function btn(label: string, onclick: () => void, cls = '', disabled = false): HTMLButtonElement {
  return h('button', { class: `btn ${cls}`, onclick, disabled }, label);
}

function kv(k: string, v: string, cls = ''): HTMLElement {
  return h('div', {}, h('span', { class: 'k' }, `${k} `), h('span', { class: `v ${cls}` }, v));
}

const OUTCOME = { won: 'VICTORIA', lost: 'DERROTA', retired: 'RETIRO' } as const;

function recordRow(r: RecordEntry, i: number): HTMLElement {
  return h('div', { class: 'panel' },
    h('div', { class: 'row' },
      h('span', { class: 'amber' }, `#${i + 1}`),
      h('span', { class: 'v' }, `${r.score} pts`),
      h('span', { class: r.outcome === 'won' ? 'good' : r.outcome === 'lost' ? 'bad' : 'k' }, OUTCOME[r.outcome]),
      h('span', { class: 'k' }, `${playerName(r.bloc)} · ${['fácil', 'normal', 'difícil'][r.difficulty]} · ${r.year}`),
    ),
    h('div', { class: 'k' }, shareCode(r)),
  );
}

const HELP: [string, string][] = [
  ['Objetivo', 'Ser el primero en aterrizar en Plutón y plantar la bandera. El rival avanza con el calendario: cada día que esperás, avanza.'],
  ['Empuje', 'Arrastrá en la franja izquierda. Tiene memoria: queda donde lo soltás.'],
  ['Giro', 'Arrastrá a los lados en la zona inferior derecha. PRO y RET apuntan la nave sola.'],
  ['Zoom', 'Pellizcá, o usá − y +. Alejá todo el zoom para ver el sistema solar.'],
  ['Tiempo', 'W+ y W− aceleran el tiempo. Con el motor encendido o dentro de una atmósfera queda en x1.'],
  ['Destino', 'OBJ elige un cuerpo (o tocalo en el mapa). MARCO dibuja la trayectoria vista desde otro cuerpo, que es como se ve un encuentro.'],
  ['Trayectoria', 'NODO abre el planificador. AUTO propone ventana y Δv, REFINA ajusta hasta un paso cercano y QUEMA acelera el tiempo, apunta y enciende sola. CIRC propone circularizar la órbita en el apogeo.'],
  ['Atmósfera', 'Frena, pero calienta. De costado frena más y se calienta más. Un escudo térmico sube el límite.'],
  ['Aterrizar', 'Despacio (menos de 12 u/s), derecho y sobre terreno poco inclinado. Las franjas amarillas son planas.'],
  ['Bandera y base', 'Aterrizado en una franja: BANDERA, BASE y RECARGA. Las bases producen combustible con el tiempo.'],
  ['Eventos', 'Asteroides, fallas y política interrumpen el tiempo. Hay aviso y siempre hay respuesta: una corrección pequeña, sellar una válvula, esperar.'],
  ['Teclado', 'A/D girar · W/S empuje · Z/X máximo/corte · P/R pro/retro · N nodo · . , tiempo · T objetivo · F marco · E sellar · B/U bandera/base'],
];

export const screens = {
  title(app: App, sel = { bloc: 'usa' as Campaign['bloc'], diff: 1 as 0 | 1 | 2 }): HTMLElement {
    const again = (): void => app.overlay.show(screens.title(app, sel));
    const bloc = (b: Campaign['bloc'], label: string): HTMLElement =>
      btn(label, () => { sel.bloc = b; again(); }, sel.bloc === b ? 'on' : '');
    const diff = (d: 0 | 1 | 2, label: string): HTMLElement =>
      btn(label, () => { sel.diff = d; again(); }, sel.diff === d ? 'on' : '');
    return h('div', { class: 'screen' },
      h('h1', {}, 'ORBITAL RACE'),
      h('p', { class: 'sub' }, 'Guerra Fría, 1957. Primero en aterrizar en Plutón.'),
      h('h2', {}, 'BANDO'),
      h('div', { class: 'row' }, bloc('usa', 'EE.UU.'), bloc('urss', 'URSS')),
      h('h2', {}, 'DIFICULTAD DEL RIVAL'),
      h('div', { class: 'row' }, diff(0, 'FÁCIL'), diff(1, 'NORMAL'), diff(2, 'DIFÍCIL')),
      h('h2', {}, 'JUGAR'),
      h('div', { class: 'row' },
        btn('NUEVA CAMPAÑA', () => app.newCampaign(sel.bloc, sel.diff), 'go'),
        app.hasSave() ? btn('CONTINUAR', () => app.continueGame(), 'go') : null,
        btn('VUELO LIBRE', () => app.startSandbox(), 'warn'),
      ),
      h('div', { class: 'row', style: 'margin-top:10px' },
        btn('RÉCORDS', () => app.openRecords()),
        btn('CÓMO SE JUEGA', () => app.openHelp(() => again())),
      ),
      h('p', { class: 'sub', style: 'margin-top:18px' }, 'Sistema solar a escala real comprimida: 1 u = 6,371 km, la Tierra tarda un año. El vuelo libre no guarda partida.'),
    );
  },

  help(back: () => void): HTMLElement {
    return h('div', { class: 'screen' },
      h('h1', {}, 'CÓMO SE JUEGA'),
      btn('VOLVER', back, 'go'),
      h('div', { class: 'panel' }, h('ul', { class: 'tight' }, ...HELP.map(([k, v]) => h('li', {}, h('span', { class: 'amber' }, `${k}: `), v)))),
    );
  },

  pause(app: App): HTMLElement {
    const c = app.campaign;
    const w = app.world;
    return h('div', { class: 'screen' },
      h('h1', {}, 'PAUSA'),
      c ? h('p', { class: 'sub' }, c.sandbox ? 'Vuelo libre' : `${fmtDate(c.time)} · fondos ${c.funds} · ${doneCount(c)}/10 hitos`) : null,
      h('div', { class: 'row' },
        btn('CONTINUAR', () => app.closeOverlay(), 'go'),
        c && !c.sandbox ? btn('CENTRO DE CONTROL', () => app.enterHQ(), 'warn') : null,
        c?.sandbox ? btn('NUEVA NAVE EN LA PLATAFORMA', () => { app.startSandbox(); }, 'warn') : null,
      ),
      h('div', { class: 'row', style: 'margin-top:10px' },
        btn(app.audio.muted ? 'SONIDO: NO' : 'SONIDO: SÍ', () => { app.audio.setMuted(!app.audio.muted); app.openPause(); }),
        btn('CÓMO SE JUEGA', () => app.openHelp(() => app.openPause())),
        app.flight ? btn(app.flight.coachOn ? 'CONSEJOS: SÍ' : 'CONSEJOS: NO', () => { app.flight!.coachOn = !app.flight!.coachOn; app.openPause(); }) : null,
        w && w.ship.status === 'flying' && c && !c.sandbox ? btn('ABANDONAR NAVE', () => app.abandonShip(), 'bad') : null,
        btn('MENÚ PRINCIPAL', () => { app.save(); app.showTitle(); }),
      ),
    );
  },

  records(app: App): HTMLElement {
    const list = loadRecords();
    const out = h('div', { class: 'k' }, 'Pegá un código para ver la partida de otra persona.');
    const input = h('input', { id: 'code', class: 'btn', style: 'min-width:240px;text-transform:uppercase', placeholder: 'ORB-…' }) as HTMLInputElement;
    return h('div', { class: 'screen' },
      h('h1', {}, 'RÉCORDS'),
      btn('VOLVER', () => (app.campaign && app.mode !== 'title' ? app.enterHQ() : app.showTitle()), 'go'),
      list.length === 0 ? h('p', { class: 'sub' }, 'Todavía no hay partidas terminadas.') : null,
      ...list.map(recordRow),
      h('h2', {}, 'COMPARAR CÓDIGO'),
      h('div', { class: 'row' }, input, btn('VER', () => {
        const r = parseShareCode(input.value);
        out.replaceChildren(r ? h('span', {}, `${r.score} pts · ${OUTCOME[r.outcome]} · ${playerName(r.bloc)} · ${['fácil', 'normal', 'difícil'][r.difficulty]} · ${r.year} · semilla ${r.seed}`) : h('span', { class: 'bad' }, 'Código inválido.'));
      })),
      out,
      h('p', { class: 'sub' }, 'El juego corre en tu dispositivo, así que un código no prueba que el puntaje sea legítimo: sirve para comparar y para repetir la misma semilla.'),
    );
  },

  end(app: App): HTMLElement {
    const c = app.campaign!;
    const won = c.status === 'won';
    const rec = app.lastRecord ?? recordFor(c, c.time);
    return h('div', { class: 'screen' },
      h('h1', { class: won ? 'good' : 'bad' }, won ? 'VICTORIA' : 'DERROTA'),
      h('p', { class: 'sub' }, won
        ? `${playerName(c.bloc)} aterrizó en Plutón primero. ${fmtDate(c.milestones[9].time)}.`
        : `${rivalName(c.bloc)} aterrizó en Plutón primero. La carrera terminó en ${Math.floor(yearOf(c.time))}.`),
      h('h2', {}, 'PUNTAJE'),
      h('div', { class: 'panel' },
        ...scoreBreakdown(c).map((r) => kv(r.label, `${r.value >= 0 ? '+' : ''}${r.value}`, r.value < 0 ? 'bad' : '')),
        h('div', { class: 'amber', style: 'margin-top:6px' }, `TOTAL ${totalScore(c)}`),
      ),
      h('p', { class: 'k' }, `Código: ${shareCode(rec)}`),
      h('div', { class: 'row' },
        btn('RÉCORDS', () => app.openRecords()),
        btn('MENÚ PRINCIPAL', () => { app.deleteSave(); app.showTitle(); }, 'go'),
      ),
    );
  },

  hq(app: App): HTMLElement {
    const c = app.campaign!;
    const w = app.world;
    const year = yearOf(c.time);
    const next = c.milestones.findIndex((m) => !m.done);
    const tab = (id: string, label: string): HTMLElement =>
      btn(label, () => { app.hqTab = id; app.refresh(); }, app.hqTab === id ? 'on' : '');

    const header = h('div', {},
      h('h1', {}, 'CENTRO DE CONTROL'),
      h('p', { class: 'sub' }, `${fmtDate(c.time)} · ${playerName(c.bloc)} contra ${rivalName(c.bloc)} · ${['fácil', 'normal', 'difícil'][c.difficulty]}`),
      h('div', { class: 'grid' },
        kv('FONDOS', String(c.funds), 'amber'),
        kv('HITOS', `${doneCount(c)}/10`),
        kv('PUNTAJE', String(totalScore(c))),
        kv('PRESUPUESTO ANUAL', `+${yearBudget(c)}`),
      ),
      h('div', { style: 'margin-top:8px' },
        h('div', { class: 'k' }, `${playerName(c.bloc)}: ${doneCount(c)} hitos`), bar(doneCount(c) / 10),
        h('div', { class: 'k', style: 'margin-top:4px' }, `${rivalName(c.bloc)}: ${c.rivalDone} hitos · Plutón previsto hacia ${c.rivalYears[9].toFixed(0)}`), bar(c.rivalDone / 10, 'rival'),
      ),
      h('div', { class: 'tabs' }, tab('mision', 'MISIÓN'), tab('nave', 'NAVE'), tab('tec', 'TECNOLOGÍA'), tab('bases', 'BASES'), tab('puntaje', 'PUNTAJE')),
    );

    let body: HTMLElement;
    if (app.hqTab === 'nave') body = hqShip(app);
    else if (app.hqTab === 'tec') body = hqTech(app);
    else if (app.hqTab === 'bases') body = hqBases(app);
    else if (app.hqTab === 'puntaje') body = hqScore(app);
    else body = hqMission(app, next, year, w);

    return h('div', { class: 'screen' }, header, body,
      h('div', { class: 'row', style: 'margin-top:18px' },
        btn('RÉCORDS', () => app.openRecords()),
        btn('CÓMO SE JUEGA', () => app.openHelp(() => app.enterHQ())),
        btn('MENÚ PRINCIPAL', () => { app.save(); app.showTitle(); }),
      ),
    );
  },
};

function hqMission(app: App, next: number, year: number, w: App['world']): HTMLElement {
  const c = app.campaign!;
  const flying = !!w && w.ship.status === 'flying';
  return h('div', {},
    h('div', { class: 'row' },
      w ? btn('CONTINUAR VUELO', () => app.closeOverlay(), 'go') : null,
      btn('PREPARAR NUEVA NAVE', () => { app.hqTab = 'nave'; app.refresh(); }, w ? '' : 'go'),
    ),
    flying ? h('p', { class: 'sub' }, 'La nave sigue en vuelo. El calendario corre con el tiempo del vuelo: acelerá con W+.') : h('div', {},
      h('h2', {}, 'ESPERAR'),
      h('div', { class: 'row' },
        btn('+1 DÍA', () => app.waitDays(1)),
        btn('+30 DÍAS', () => app.waitDays(30)),
        btn('+1 AÑO', () => app.waitDays(365)),
      ),
      h('p', { class: 'sub' }, 'Cada día que pasa el rival avanza, las bases producen y llega el presupuesto de enero.'),
    ),
    next >= 0 ? h('div', { class: 'panel' },
      h('div', { class: 'amber' }, `PRÓXIMO HITO · ${next + 1}. ${MILESTONES[next].name}`),
      h('div', {}, MILESTONES[next].desc),
      h('div', { class: 'k' }, `${rivalName(c.bloc)} lo logra hacia ${c.rivalYears[next].toFixed(1)} · hoy es ${year.toFixed(1)} · vale ${MILESTONES[next].points} (x2 si llegás primero)`),
    ) : null,
    h('h2', {}, 'ESCALERA DE HITOS'),
    h('div', { class: 'ladder' }, ...MILESTONES.map((m, i) => {
      const rec = c.milestones[i];
      const rivalPassed = year >= c.rivalYears[i];
      const cls = rec.done ? 'done' : i === next ? 'next' : '';
      const status = rec.done
        ? `${yearOf(rec.time).toFixed(1)} · ${rec.first ? 'primero' : 'segundo'} · +${rec.points}`
        : rivalPassed ? `${rivalName(c.bloc)} ya lo logró` : `${rivalName(c.bloc)} ${c.rivalYears[i].toFixed(1)}`;
      return h('div', { class: `step ${cls}` }, h('span', { class: 'k' }, String(m.id)), h('span', {}, m.name), h('span', { class: rec.done ? 'good' : rivalPassed ? 'bad' : 'k' }, status));
    })),
    h('h2', {}, 'NOTICIAS'),
    h('div', { class: 'news' }, ...(c.news.length ? c.news.slice(0, 10).map((n) => h('div', { class: n.kind === 'bad' || n.kind === 'rival' ? 'bad' : n.kind === 'good' ? 'good' : '' }, `${fmtDate(n.t)}  ${n.text}`)) : [h('div', {}, 'Sin novedades.')])),
  );
}

function hqShip(app: App): HTMLElement {
  const c = app.campaign!;
  const w = app.world;
  const sites = [{ label: `Plataforma (${BODIES[2].sites[c.bloc === 'usa' ? 0 : 1].name})`, idx: -1 }, ...c.bases.map((b, i) => ({ label: `${b.name} · depósito ${Math.round(b.stock)}`, idx: i }))];
  const engines = ENGINES.filter((e) => e.tech === null || c.techs.includes(e.tech));
  if (!engines.some((e) => e.id === app.plan.engine)) app.plan.engine = engines[0].id;
  if (app.plan.site >= c.bases.length) app.plan.site = -1;

  const info = h('div', { class: 'panel' });
  const launchBtn = h('button', { class: 'btn go' }, 'LANZAR');
  const fill = (): void => {
    const pi = app.planInfo();
    if (!pi) return;
    const st = pi.stats;
    const mass = st.dryMass + pi.fuel;
    const g = BODIES[pi.body].surfaceGravity;
    const dv = st.ve * Math.log(mass / st.dryMass);
    const twr = st.thrust / (mass * g);
    info.replaceChildren(
      kv('Sitio', pi.label),
      kv('Combustible', `${Math.round(pi.fuel)} / ${Math.round(st.fuelCap)}`, pi.fuel <= 0 ? 'bad' : ''),
      kv('ΔV total', `${dv.toFixed(0)} u/s`),
      kv('Relación empuje/peso', twr.toFixed(2), twr < 1.05 ? 'bad' : twr < 1.3 ? 'amber' : 'good'),
      kv('Motor', `empuje ${st.thrust / 1000}k · Isp ${st.ve}`),
      kv('Aterrizaje seguro', `hasta ${st.maxLandSpeed} u/s · calor máx. ${st.heatLimit}`),
      kv('Costo', c.sandbox ? 'libre' : `${pi.cost} fondos`),
    );
    const cannot = (!c.sandbox && c.funds < pi.cost) || pi.fuel <= 0 || twr <= 1;
    launchBtn.disabled = cannot;
    launchBtn.textContent = w && w.ship.status === 'flying' && !app.confirming ? 'LANZAR (ABANDONA LA NAVE ACTUAL)' : w && w.ship.status === 'flying' ? 'CONFIRMAR: ABANDONAR Y LANZAR' : 'LANZAR';
  };
  launchBtn.addEventListener('click', () => {
    if (w && w.ship.status === 'flying' && !app.confirming) {
      app.confirming = true;
      fill();
      return;
    }
    if (w && w.ship.status === 'flying') {
      c.shipsLost++;
    }
    app.launch();
  });
  const slider = h('input', { id: 'fuel', type: 'range', min: '10', max: '100', step: '5', value: String(Math.round(app.plan.fuelLoad * 100)), style: 'width:220px' }) as HTMLInputElement;
  slider.addEventListener('input', () => {
    app.plan.fuelLoad = Number(slider.value) / 100;
    fill();
  });
  fill();

  return h('div', {},
    h('h2', {}, 'SITIO DE LANZAMIENTO'),
    h('div', { class: 'row' }, ...sites.map((s) => btn(s.label, () => { app.plan.site = s.idx; app.refresh(); }, app.plan.site === s.idx ? 'on' : ''))),
    h('h2', {}, 'MOTOR'),
    h('div', { class: 'row' }, ...engines.map((e) => btn(e.name, () => { app.plan.engine = e.id; app.refresh(); }, app.plan.engine === e.id ? 'on' : ''))),
    h('h2', {}, 'CARGA DE COMBUSTIBLE'),
    h('div', { class: 'row' }, slider, h('span', { class: 'k' }, 'más carga pesa más y baja el empuje/peso')),
    info,
    h('div', { class: 'row' }, launchBtn),
    h('p', { class: 'sub' }, `Una nave nueva cuesta ${LAUNCH_COST} fondos. Desde una base se carga lo que haya en el depósito. Motores nuclear e iónico apenas levantan el peso: usalos desde la Luna, no desde la Tierra.`),
  );
}

function hqTech(app: App): HTMLElement {
  const c = app.campaign!;
  return h('div', {},
    h('h2', {}, 'INVESTIGACIÓN'),
    h('p', { class: 'sub' }, 'Se aplica a las naves que lances desde ahora. Cada tecnología pide un hito.'),
    ...TECHS.map((t) => {
      const owned = c.techs.includes(t.id);
      const locked = t.milestone > 0 && !c.milestones[t.milestone - 1].done;
      const needs = t.prereq && !c.techs.includes(t.prereq);
      const status = owned ? 'INSTALADA' : locked ? `PIDE HITO ${t.milestone}` : needs ? `PIDE ${TECHS.find((x) => x.id === t.prereq)!.name}` : `${t.cost} FONDOS`;
      return h('div', { class: 'panel' },
        h('div', { class: 'row' },
          h('span', { class: owned ? 'good' : 'v' }, t.name),
          h('span', { class: 'k' }, t.desc),
          btn(status, () => { if (app.buyTech(t.id)) app.refresh(); }, owned ? 'on' : 'go', owned || locked || !!needs || c.funds < t.cost),
        ),
      );
    }),
  );
}

function hqBases(app: App): HTMLElement {
  const c = app.campaign!;
  const stats = statsFor(c.techs, c.engine);
  return h('div', {},
    h('h2', {}, 'BASES'),
    c.bases.length === 0 ? h('p', { class: 'sub' }, 'Todavía no hay bases. Aterrizá en una franja plana, abajo aparece BASE. Producen combustible con el tiempo; sin hielo (Venus) no producen.') : null,
    ...c.bases.map((b) => h('div', { class: 'panel' },
      h('div', { class: 'row' }, h('span', { class: 'good' }, b.name), h('span', { class: 'k' }, `desde ${fmtDate(b.built)}`)),
      kv('Depósito', `${Math.round(b.stock)} / ${BASE_CAPACITY}`),
      bar(b.stock / BASE_CAPACITY),
      kv('Producción', `${(baseRate(c, b.body, stats.isru) * DAY).toFixed(0)} por día`),
    )),
    h('h2', {}, 'BANDERAS'),
    c.flags.length === 0 ? h('p', { class: 'sub' }, 'Ninguna.') : h('div', {}, ...c.flags.map((f) => h('div', {}, `${BODIES[f.body].name} · ${fmtDate(f.time)} (${fmtDuration(0)})`.replace(' (0s)', '')))),
  );
}

function hqScore(app: App): HTMLElement {
  const c = app.campaign!;
  const rec = recordFor(c, c.time);
  return h('div', {},
    h('h2', {}, 'PUNTAJE ACTUAL'),
    h('div', { class: 'panel' },
      ...scoreBreakdown(c).map((r) => kv(r.label, `${r.value >= 0 ? '+' : ''}${r.value}`, r.value < 0 ? 'bad' : '')),
      h('div', { class: 'amber', style: 'margin-top:6px' }, `TOTAL ${totalScore(c)}`),
    ),
    h('p', { class: 'k' }, `Código de esta partida: ${shareCode(rec)}`),
    h('p', { class: 'sub' }, 'Llegar primero duplica un hito, llegar segundo lo reduce a la mitad. Sobra combustible suma, perder naves resta.'),
  );
}
