/* Historia familiar, cutscenes, origen y reclutamiento. Espejo de caravana/story.py, cutscenes.py y origin.py */
(function (CV) {
'use strict';
const D = CV.data, clamp = CV.clamp, prompt = CV.prompt, info = CV.info, opt = CV.opt;
const S = CV.story = {};

// ============================================================== reparto
S.CAST = [
  ['esposa','Martha','adulto',{shoot:3,medic:7,build:4,talk:7,hunt:3},'prudente','Maestra de escuela. Soñó con esta ruta desde que murió su hermano. Cree en hablar antes que en disparar.',62],
  ['hijo','Samuel','joven',{shoot:6,medic:1,build:4,talk:2,hunt:5},'impulsivo','Dieciséis años, un rifle y poca paciencia. Quiere que lo trates como a un adulto.',50],
  ['hija','Clara','niño',{shoot:1,medic:1,build:1,talk:4,hunt:2},'curiosa','Diez años. Pregunta por todo y lo anota en una libreta; todavía no sabe tener miedo.',70],
  ['abuelo','Eli','anciano',{shoot:5,medic:3,build:3,talk:4,hunt:3},'veterano','El padre de Martha. Luchó en una vieja guerra de frontera y nunca volvió a fiarse de nadie. Quiere ver el Pacífico.',55],
  ['tomas','Thomas Brooks','adulto',{shoot:6,medic:2,build:6,talk:2,hunt:4},'intransigente','Vecino y socio. Cree que a quien cede lo desplumáis. Paga su parte y exige voz.',45],
  ['ruth','Ruth Brooks','adulto',{shoot:3,medic:5,build:3,talk:5,hunt:3},'devota','Esposa de Thomas. Reza, cura y reparte pan. Es la primera en tender la mano a quien llega.',55],
  ['ada','Ada Brooks','niño',{shoot:1,medic:1,build:1,talk:2,hunt:2},'tímida','Siete años; sigue a Clara a todas partes.',60],
  ['silas','Silas Reed','adulto',{shoot:8,medic:2,build:4,talk:2,hunt:5},'soldado','Peón contratado. Habla poco; cuando lo hace, es sobre ángulos de tiro. Algo le pesa del pasado.',40],
  ['mary','Mary Reed','joven',{shoot:6,medic:2,build:3,talk:3,hunt:8},'rastreadora','Hermana de Silas. Lee huellas como otros leen cartas.',50],
  ['josiah','Josiah Cole','adulto',{shoot:5,medic:2,build:7,talk:3,hunt:3},'trabajador','Carretero y herrero. No pide nada.',55],
  ['hannah','Hannah Cole','adulto',{shoot:4,medic:6,build:3,talk:4,hunt:3},'serena','Esposa de Josiah, partera.',55],
  ['lucas','Lucas Cole','niño',{shoot:1,medic:1,build:1,talk:2,hunt:3},'travieso','Ocho años y siempre sucio.',60],
  ['emma','Emma Cole','joven',{shoot:5,medic:3,build:3,talk:3,hunt:4},'soñadora','Diecisiete. Quiere ver el mar y casarse allí.',55],
];
S.populate = function (g) {
  const rng = g.rng, sur = rng.choice(D.SURNAMES), leader = g.byRole('lider');
  leader.name = `${g.leaderName} ${sur}`; leader.loyalty = 100; leader.trait = 'líder';
  for (const [role, name, group, sk0, trait, bio, loy] of S.CAST) {
    const cole = ['lucas', 'emma', 'josiah', 'hannah'].includes(role);
    const full = name.includes(' ') ? name : `${name} ${D.FAMILY_ROLES.includes(role) ? sur : cole ? 'Cole' : ''}`.trim();
    const sk = {};
    for (const k in sk0) sk[k] = clamp(sk0[k] + (group === 'adulto' ? rng.choice([-1, 0, 0, 1]) : 0), 1, 10);
    const c = g.make(group, full, sk);
    c.roleId = role; c.trait = trait; c.bio = bio; c.loyalty = loy;
  }
  g.flags = {}; g.storyDone = []; g.talked = {};
};
const bump = S.bump = (g, role, d) => { const c = g.member(role); if (c) c.loyalty = clamp(c.loyalty + d, 0, 100); };
const ok = (title, text, tone, then) => info(title, text, tone || 'info', then);
const first = (g, r) => { const c = g.byRole(r); return c ? c.name.split(' ')[0] : r; };
function kill(g, role, cause) {
  const c = g.member(role);
  if (c) { c.alive = false; c.cause = cause; c.post = null; g.stats.lost++; g.normalizePosts(); g.log(`${c.name} ha muerto (${cause}).`); }
}

// ============================================================== consejos
S.voices = function (g) {
  const eliP = g.flags.eli_friend ? 'parley' : 'fight';
  const table = [
    ['esposa','parley','«Hablemos antes de disparar. Hay niños en estas carretas.»'],
    ['ruth','parley','«Que vean pan en nuestras manos antes que plomo.»'],
    ['hijo','fight','«¡Tenemos rifles! Yo no me escondo.»'],
    ['tomas','fight','«Si cedes una vez, te lo quitan todo. Al círculo.»'],
    ['silas','fight','«Cerrad el círculo ya y poned buenos tiradores del lado del polvo.»'],
    ['mary','flee','«Aún les sacamos ventaja. Si forzamos la marcha, no nos alcanzan.»'],
    ['abuelo', eliP, eliP === 'parley' ? '«Conozco a ese hombre de ahí; hablemos.»' : '«Yo vi esa formación una vez. Nadie volvió a confiar.»'],
  ];
  let out = [];
  for (const [role, stance, text0] of table) {
    const c = g.member(role); if (!c) continue;
    let text = text0;
    if (c.loyalty < 25) text = text.slice(0, -1) + ' …y haz lo que quieras, como siempre.»';
    out.push([role, c.name.split(' ')[0], text, stance]);
  }
  if (out.length > 3) {
    const head = out.filter(v => v[0] === 'esposa'), rest = out.filter(v => v[0] !== 'esposa');
    const k = (g.day * 7) % rest.length;
    out = head.concat(rest.slice(k).concat(rest.slice(0, k)).slice(0, 3 - head.length));
  }
  return out;
};
S.voicesText = vs => vs.map(v => `${v[1]}: ${v[2]}`).join('\n');
S.backers = (vs, stance) => vs.filter(v => v[3] === stance).map(v => v[1]);
S.follow = function (g, vs, chosen) {
  const opp = {fight: 'parley', parley: 'fight'};
  for (const [role, , , stance] of vs) { if (stance === chosen) bump(g, role, 3); else if (opp[chosen] === stance) bump(g, role, -2); }
};
S.talkBonus = function (g) {
  let b = 0; const m = g.member('esposa');
  if (m && m.loyalty >= 60) b++;
  if (g.flags.clara_words && g.member('hija')) b++;
  return b;
};

// ============================================================== origen y reclutamiento
S.MOTIVES = {
  tierra:{name:'Una tierra propia', tag:'land', promise:'tierra', text:'Arrendatarios toda la vida. La carta del valle prometía 320 acres a quien llegara. Martha lleva años guardando esa carta.', perks:'+1 fertilidad en el asentamiento · Martha y Clara confían más'},
  deudas:{name:'Huir de las deudas', tag:'escape', promise:'fortuna', text:'El banco ya no espera. Vendisteis la finca por lo que dieron; más vale cruzar el Misuri antes de que lleguen los alguaciles.', perks:'+$180 de la venta de la finca · moral baja al partir · los peones confían menos'},
  fe:{name:'Fe y comunidad', tag:'faith', promise:'paz', text:'Vuestro pastor habló de una tierra donde fundar algo distinto: una congregación que conviva con quien ya vive allí, sin armas en la mesa.', perks:'+3 de trato con todos los pueblos · +2 medicinas · Ruth y Martha confían más'},
  oro:{name:'Fortuna y comercio', tag:'gold', promise:'fortuna', text:'En cada taberna se oye lo mismo: pieles, harina, tierra que se revaloriza. Quien llegue primero y con la carga bien repartida, hará fortuna.', perks:'+6 mercancías y +$60 · Samuel y Silas confían más'},
};
S.PURPOSES = {
  granja:{name:'Una granja familiar', text:'Arar, sembrar, construir un hogar. Que el próximo invierno huela a pan.', perks:'+1 fertilidad · puntúan campos y establo'},
  comercio:{name:'Un puesto de comercio', text:'Un mostrador en el cruce de caminos: cambiar sal por pieles, herramientas por pescado.', perks:'+2 comercio del sitio · puntúa el puesto de trueque'},
  comunidad:{name:'Una comunidad en paz', text:'Una escuela, una iglesia, y un pacto honrado con los vecinos de esa tierra.', perks:'+6 de trato con los vecinos al fundar · puntúan tratado e iglesia'},
  fortaleza:{name:'Un fuerte defendible', text:'Un lugar con empalizada donde nadie pueda tocar a los vuestros.', perks:'+2 defensa del sitio · puntúa la empalizada'},
};
S.applyOrigin = function (g, motive, purpose) {
  const m = S.MOTIVES[motive];
  g.flags.motive = motive; g.flags.purpose = purpose; g.flags.promise = m.promise;
  if (motive === 'tierra') { g.flags.farm_bonus = (g.flags.farm_bonus || 0) + 1; bump(g, 'esposa', 6); bump(g, 'hija', 3); }
  else if (motive === 'deudas') { g.sup.money += 180; g.morale = Math.max(0, g.morale - 6); for (const r of ['silas', 'mary', 'josiah']) bump(g, r, -4); }
  else if (motive === 'fe') { for (const t of D.TERRITORY_TRIBES) g.tribes[t].attitude += 3; g.sup.medicine += 2; bump(g, 'ruth', 5); bump(g, 'esposa', 5); bump(g, 'tomas', -3); }
  else { g.sup.goods += 6; g.sup.money += 60; bump(g, 'hijo', 5); bump(g, 'silas', 4); bump(g, 'esposa', -3); }
  g.log(`Motivo: ${m.name}. Propósito: ${S.PURPOSES[purpose].name}.`);
};
S.purposeKept = function (g, st) {
  const p = g.flags.purpose; if (!p) return null;
  if (p === 'granja') return st.built.includes('campos') && st.site.fertility >= 6;
  if (p === 'comercio') return st.built.includes('puesto');
  if (p === 'comunidad') return (st.built.includes('tratado') || g.tribes[st.neighbor()].attitude >= 45) && st.built.includes('iglesia');
  return st.built.includes('empalizada') && st.site.defense >= 6;
};
S.applyPurposeToSite = function (g, st) {
  const p = g.flags.purpose;
  if (p === 'granja') st.site.fertility++;
  else if (p === 'comercio') st.site.trade += 2;
  else if (p === 'fortaleza') st.site.defense += 2;
  else if (p === 'comunidad' && g.tribes[st.neighbor()]) g.tribes[st.neighbor()].attitude = Math.min(100, g.tribes[st.neighbor()].attitude + 6);
};
S.MAX_PARTY = 18;
S.CANDIDATES = [
  {id:'medico', names:['Abel Finch'], groups:['adulto'], skills:{shoot:3,medic:8,build:3,talk:5,hunt:2}, trait:'reservado', fee:70, hard:.45, likes:['escape','faith'], pitch:'Médico sin consulta. Dice que lo dejó «por motivos de conciencia» y no añade nada más.', join:'Finch carga un maletín de cuero y dos cajas de frascos. «Procuraré que no los necesite.»'},
  {id:'cazadora', names:['Nora Quill'], groups:['joven'], skills:{shoot:7,medic:2,build:3,talk:3,hunt:9}, trait:'independiente', fee:30, hard:.35, likes:['land','gold'], pitch:'Cazadora de pieles sin compañía. Conoce la pradera mejor que los mapas.', join:'Nora asiente una sola vez y va a ensillar su mula. «Yo abro la marcha, si no os importa.»'},
  {id:'herrero', names:['Gideon Marsh'], groups:['adulto'], skills:{shoot:4,medic:2,build:9,talk:3,hunt:2}, trait:'manitas', fee:40, hard:.4, likes:['land'], pitch:'Herrero que perdió el taller en una inundación. Una carreta rota para él es un rato de entretenimiento.', join:'Marsh deja caer su yunque portátil en la bodega con un golpe sordo. «Ahora sí tenemos taller.»'},
  {id:'predicador', names:['Tobias Lamb'], groups:['adulto'], skills:{shoot:2,medic:3,build:3,talk:8,hunt:2}, trait:'devoto', fee:0, hard:.5, likes:['faith'], pitch:'Un predicador sin parroquia que quiere fundar una iglesia «donde quepa todo el que llegue».', join:'Lamb estrecha tu mano con ambas. «Prometo que no predicaré en el camino. Mucho.»'},
  {id:'mercenario', names:['Isaiah Cobb'], groups:['adulto'], skills:{shoot:9,medic:1,build:3,talk:2,hunt:5}, trait:'mercenario', fee:95, hard:.3, likes:['gold'], loyalty:35, pitch:'Pistolero retirado. Cobra por adelantado y no hace preguntas, pero tampoco responde a las tuyas.', join:'Cobb guarda el dinero sin contarlo. «Dispararé donde me digas. Mientras me pagues.»'},
  {id:'traductora', names:['Lena Voss'], groups:['adulto'], skills:{shoot:2,medic:3,build:2,talk:9,hunt:3}, trait:'políglota', fee:60, hard:.55, likes:['faith','escape'], pitch:'Hija de un comerciante de pieles y de una mujer Cheyenne. Habla tres lenguas y callaría una cuarta.', join:'Lena asiente. «Si alguien aprende a escuchar antes de gritar, quizá lleguemos todos.»'},
  {id:'gemelos', names:['Jonas Hart','Jude Hart'], groups:['joven','joven'], skills:{shoot:5,medic:2,build:4,talk:3,hunt:4}, trait:'inseparables', fee:0, hard:.25, likes:['gold','escape'], pitch:'Dos hermanos de diecisiete años sin un dólar y con mucha prisa por irse.', join:'Los gemelos se miran, sonríen a la vez y suben a la carreta sin esperar a que termines la frase.'},
  {id:'partera', names:['Rosa Ibarra','Mateo Ibarra'], groups:['adulto','niño'], skills:{shoot:2,medic:7,build:3,talk:4,hunt:3}, trait:'serena', fee:20, hard:.4, likes:['land','faith'], pitch:'Partera viuda con un hijo de nueve años. Ha asistido a medio condado.', join:'Rosa sube a Mateo a la carreta antes de preguntar nada más. «Para la gente de mi oficio, cualquier camino es corto.»'},
  {id:'carretero', names:['Walter Pike'], groups:['adulto'], skills:{shoot:5,medic:2,build:7,talk:3,hunt:4}, trait:'terco', fee:25, hard:.3, likes:['gold'], pitch:'Carretero con deudas de juego. Conduce una yunta mejor que nadie.', join:'Pike escupe en la tierra y se frota las manos. «Los bueyes saben quién manda. Yo, claro.»'},
  {id:'viuda', names:['Eliza Marlow'], groups:['adulto'], skills:{shoot:4,medic:4,build:3,talk:6,hunt:4}, trait:'entera', fee:0, hard:.3, likes:['land','escape'], pitch:'Viuda reciente, con las cuentas saldadas y las ganas intactas de empezar de nuevo.', join:'Eliza lleva una caja de semillas pegada al pecho. «No vengo a que me cuiden. Vengo a plantar.»'},
];
S.joinCandidate = function (g, tpl, loyalty) {
  const out = [];
  tpl.names.forEach((name, i) => {
    const group = tpl.groups[i];
    const sk = group === 'niño' ? {shoot:1,medic:1,build:1,talk:2,hunt:2} : Object.assign({}, tpl.skills);
    const c = g.make(group, name, sk);
    c.roleId = i === 0 ? tpl.id : tpl.id + '_' + i; c.trait = tpl.trait; c.bio = tpl.pitch; c.loyalty = loyalty;
    out.push(c);
  });
  (g.flags.recruits = g.flags.recruits || []).push(tpl.id);
  g.log(`${tpl.names.join(', ')} se une a la caravana.`);
  g.autoAssign();
  return out;
};
class Recruitment {
  constructor(g) {
    this.g = g;
    const r = new CV.RNG((g.seed || 0) * 97 + 13), pool = r.shuffle(S.CANDIDATES.slice());
    this.cands = pool.slice(0, 6).map(tpl => ({tpl, state: 'libre'}));
    this.approaches = 4 + (g.best('talk') >= 7 ? 1 : 0);
    this.msg = '';
  }
  room() { return S.MAX_PARTY - this.g.living().length; }
  motiveTag() { const m = this.g.flags.motive; return m && S.MOTIVES[m] ? S.MOTIVES[m].tag : ''; }
  chance(i) { const t = this.cands[i].tpl; return clamp(.78 - t.hard + .05 * this.g.best('talk') + (t.likes.includes(this.motiveTag()) ? .18 : 0), .1, .95); }
  canAct(i) {
    const c = this.cands[i];
    if (c.state !== 'libre') return [false, 'Ya no está disponible.'];
    if (c.tpl.names.length > this.room()) return [false, 'La caravana no tiene sitio para tanta gente (máx. 18).'];
    return [true, ''];
  }
  persuade(i) {
    const [okk, why] = this.canAct(i); if (!okk) return [false, why];
    if (this.approaches <= 0) return [false, 'Se acabó el tiempo: ya no hay más gente a quien hablar.'];
    this.approaches--;
    const c = this.cands[i], tpl = c.tpl;
    if (this.g.rng.random() < this.chance(i)) {
      S.joinCandidate(this.g, tpl, tpl.loyalty || 55 + (tpl.likes.includes(this.motiveTag()) ? 8 : 0));
      c.state = 'unido'; this.msg = tpl.join; return [true, tpl.join];
    }
    c.state = 'rechazo'; this.msg = `${tpl.names[0]} no se deja convencer: «Pensaré en otra caravana.»`; return [false, this.msg];
  }
  hire(i) {
    const [okk, why] = this.canAct(i); if (!okk) return [false, why];
    const tpl = this.cands[i].tpl;
    if (tpl.fee <= 0) return this.persuade(i);
    if (this.g.sup.money < tpl.fee) return [false, `Faltan $${tpl.fee - Math.floor(this.g.sup.money)}.`];
    this.g.sup.money -= tpl.fee;
    S.joinCandidate(this.g, tpl, Math.min(tpl.loyalty || 45, 45));
    this.cands[i].state = 'unido'; this.msg = tpl.join; return [true, tpl.join];
  }
}
S.Recruitment = Recruitment;

// ============================================================== cutscenes (guiones)
const ME = 'tu';
function scene(g, title, bg, cast, lines) {
  cast = cast.filter(r => g.member(r));
  const beats = lines.map(ln => {
    let who = ln[0];
    if (who !== '' && who !== ME && !g.member(who)) who = '';
    return {bg, text: ln[1], speaker: who, mood: ln[2] || 'neutral', cast, fx: ln[3] || ''};
  });
  return {kind: 'cutscene', title, beats, then: null};
}
const CS = S.cutscenes = {
  prologue(g) {
    const m = g.flags.motive || 'tierra';
    const carta = {tierra: ['«320 acres a quien llegue». Llevo seis años guardando esta carta. Ya no cabe en el bolsillo del delantal.', 'alegre'], deudas: ['No voy a mirar atrás. Si miro atrás, veré la finca. Y a los alguaciles.', 'serio'],
      fe: ['El pastor dijo que hay sitio para todos allí. Para todos. Quiero comprobarlo.', 'alegre'], oro: ['Me da miedo cuánto quiero esto. Quien llegue primero y con la carga bien repartida… hará fortuna.', 'serio']}[m];
    return scene(g, 'Independence', 'alba', ['esposa', 'hijo', 'hija', 'abuelo'], [
      ['', '15 de abril de 1848. Independence, Misuri. Un cartel sobre la herrería: «Último día de civilización».'],
      ['esposa', carta[0], carta[1]],
      ['hijo', '¿Y si nos atacan? El rifle está limpio. Y yo, también.', 'serio'],
      ['esposa', 'Por eso no se lo has dejado ni a la mula, Samuel.', 'alegre'],
      ['hija', 'He dibujado la salida del sol en la libreta. Cuando lleguemos, lo comparo con el otro.', 'alegre'],
      ['abuelo', 'Veintidós años sin cruzar ese río. Me dijeron que la pradera no tiene fin. No me dijeron cuánta gente la tiene por casa.', 'serio'],
      ['', `${g.leaderName} levanta el brazo. Siete carretas se ponen en marcha, con una sacudida y un crujir de madera. El viaje empieza.`, 'neutral', 'flash'],
    ]);
  },
  samuel_noche: g => scene(g, 'Una manta vacía', 'noche', ['esposa', 'silas'], [
    ['', 'Amanece sin sol todavía. Martha te sacude el hombro con la mano helada.'],
    ['esposa', 'Samuel no está. Ni el rifle. Ni la mula.', 'miedo'],
    ['silas', 'Huellas hacia el río. Un solo par de botas, y con prisa. Tierra Pawnee.', 'serio'],
    ['esposa', 'Ve tú. Por favor. No se lo mandes a nadie más.', 'triste'],
    ['', 'A lo lejos, un perro ladra. Nadie contesta.'],
  ]),
  clara_amiga: g => scene(g, 'Dos niñas junto al río', 'rio', ['hija', 'esposa'], [
    ['', 'En la orilla, Clara y una niña Cheyenne comparten una piedra pulida y una cinta. No hablan el mismo idioma. Se entienden.'],
    ['hija', 'Se llama… creo que Sol-Que-Llega. Le he enseñado «agua». Me ha dicho «mni». ¡Lo he apuntado!', 'alegre'],
    ['esposa', 'Clara, no te alejes. Aquí no sabemos…', 'serio'],
    ['hija', 'Mamá. Ella tampoco sabe nada de nosotros. Es un trato justo.', 'risa'],
    ['', 'Al otro lado, unos adultos vigilan sin moverse. Esperan tu gesto.'],
  ]),
  eli_roca: g => scene(g, 'La roca de los nombres', 'roca', ['abuelo', 'hijo', 'hija'], [
    ['', 'Al pie de la gran aguja de piedra, cientos de nombres tallados. Eli saca el cuchillo.'],
    ['abuelo', 'Aquí lo dejo: «Eli». Que algo mío llegue hasta el mar aunque el resto se quede en el camino.', 'serio'],
    ['hijo', '¿De verdad no te fías de ninguno, abuelo? ¿De ninguno?'],
    ['abuelo', 'Vi arder una aldea en mil ochocientos treinta y dos. Vi lo que hizo cada bando. Después de eso… uno aprende a contar los rifles antes que las palabras.', 'triste'],
    ['hija', 'Pero ¿alguien te ayudó alguna vez? Lo apunto.', 'serio'],
    ['abuelo', '…Pregúntame mañana. Hoy hay que terminar esta E.', 'triste'],
  ]),
  martha_fiebre: g => scene(g, 'Fiebre', 'tienda', ['hija', 'ruth'], [
    ['', 'Martha arde. Ruth le mantiene un paño frío sobre la frente. La luz del farol tiembla.'],
    ['hija', 'No me conoce. Le he dicho «mamá» tres veces y ha dicho «Eli».', 'miedo'],
    ['ruth', 'Las fiebres de pradera suben de noche. Si baja al amanecer, es buena señal. Si no…', 'triste'],
    ['', 'Fuera, Thomas ya está uncido. La fila del vado no espera a nadie.'],
  ]),
  silas: g => scene(g, 'Lo que Silas no cuenta', 'noche', ['silas'], [
    ['', 'Silas lleva una hora mirando el fuego sin parpadear. Cuando por fin habla, no te mira.'],
    ['silas', 'Servía en una columna de caballería. Una madrugada nos mandaron a un campamento. Mujeres. Niños. Dijeron: «órdenes».', 'serio'],
    ['silas', 'Yo apunté al aire. Esa misma noche cogí un caballo y no volví.', 'triste'],
    ['silas', 'Si alguien de entonces me reconoce, os pongo a todos en peligro. Mejor que lo sepas tú.', 'serio'],
    ['', 'Chisporrotea la leña. Nadie más está despierto.'],
  ]),
  samuel_paso(g) {
    const s = g.member('hijo');
    if (s && s.loyalty < 35) return scene(g, 'Lo alto del paso', 'montana', ['hijo'], [
      ['', 'South Pass. El viento arrastra la hierba. Samuel espera junto a la mula, cargada.'],
      ['hijo', 'Hay una partida de tramperos. Van a California. Dicen que me llevan.', 'serio'],
      ['hijo', 'Aquí no soy nada. Soy «el hijo». Allí podría ser alguien.', 'enojado'],
      ['', 'Detrás de ti, Martha se tapa la boca con la mano.'],
    ]);
    return scene(g, 'Lo alto del paso', 'montana', ['hijo', 'mary'], [
      ['', 'South Pass. El viento arrastra la hierba. Samuel y Mary esperan con una cuerda al hombro.'],
      ['hijo', 'Déjanos adelantarnos a explorar el camino. Volvemos antes del anochecer. Lo prometo.', 'serio'],
      ['mary', 'Yo sé leer rastro. Él sabe leer cielo. Entre los dos, ni un oso nos sorprende.', 'alegre'],
      ['', 'Hay algo distinto en la mirada de Samuel: ha dejado de pedir permiso para ser alguien.'],
    ]);
  },
  eli_ultimo: g => scene(g, 'El mar', 'dia', ['abuelo', 'esposa', 'hijo'], [
    ['', 'Eli lleva días dormitando sobre la mula. Hoy no despierta del todo.'],
    ['abuelo', '…Rosario…', 'triste'],
    ['esposa', 'Padre, soy Martha. Estás en el camino. Falta poco para el mar.', 'triste'],
    ['abuelo', 'El mar. Siempre pensé que sonaría como el trigo. ¿Tú qué crees?', 'alegre'],
    ['hijo', 'Suena a tu voz, abuelo. Nunca he oído nada tan fuerte.', 'triste'],
    ['', 'Eli sonríe. Cierra los ojos un momento. Todos esperáis.'],
  ]),
  clara_montanas: g => scene(g, 'La libreta en el barro', 'bosque', ['esposa', 'ada'], [
    ['', 'Una hora sin ver a Clara. En el barro del camino, su libreta abierta. Un dibujo de las carretas. Otro, de un halcón.'],
    ['esposa', '¡CLARA!', 'miedo', 'shake'],
    ['ada', 'Estaba mirando un pájaro azul… Fue por ahí… ¿Es culpa mía?', 'miedo'],
    ['', 'El bosque es denso. A lo lejos, un hilo de humo.'],
  ]),
  cobb_paga: g => scene(g, 'La paga de Cobb', 'dia', ['mercenario'], [
    ['', 'Isaiah Cobb se planta delante de tu carreta con los pulgares en el cinturón.'],
    ['mercenario', 'Hace semanas que cobré por adelantado y las semanas son largas. Un tirador contento dispara mejor.', 'serio'],
    ['mercenario', 'No es una amenaza. Es una observación.'],
  ]),
  finch_cayuse: g => scene(g, 'Niños con fiebre', 'bosque', ['medico'], [
    ['', 'Una mujer Cayuse espera junto al camino con un niño en brazos. Respira como un fuelle roto.'],
    ['medico', 'Sarampión. Lo conozco. Lo vi en la ciudad de donde me fui.', 'triste'],
    ['medico', 'No es mi gente. No es mi lengua. Pero es un niño. Dame tres medicinas y no preguntes más.', 'serio'],
  ]),
  fork(g) {
    const e = g.member('abuelo');
    return scene(g, 'La bifurcación', 'bifurcacion', ['esposa', 'hija', 'abuelo', 'hijo'], [
      ['', '1.950 millas después, un poste de madera con tres flechas. Nadie dice nada durante un minuto entero.'],
      ['hija', 'Aquí termina la libreta. O empieza otra.', 'alegre'],
      ['esposa', 'El valle de la carta. Si algo se parece a lo que prometimos, es esto.', 'alegre'],
      e ? ['abuelo', 'Cerca. Elijan algo cerca. Los viejos cuentan con las manos.', 'serio'] : ['', 'Alguien talla un nombre en el poste: «Eli».'],
      ['hijo', 'Los riscos del Columbia. Desde allí se ve todo el que viene.', 'serio'],
      ['', 'Tú decides. Los demás eligen creer en ti.'],
    ]);
  },
};

// ============================================================== capítulos
function c_samuel_noche(g) {
  const s = g.member('hijo');
  return prompt('Samuel no está en su manta', `Al amanecer, la manta de ${s.name.split(' ')[0]} está vacía. Falta el rifle y una mula. Hay huellas hacia el río, en tierra Pawnee.\n\nMartha te sujeta del brazo: «Ve tú. Por favor.»`, [
    opt('Salir a buscarlo tú mismo (1 día)', () => {
      g.day++; g.dailyUpkeep(); bump(g, 'hijo', 5); bump(g, 'esposa', 4);
      if (g.rng.random() < .6) { g.tribes.pawnee.attitude += 6; g.flags.samuel_friend = true; return ok('Lo encuentras junto al río', 'Samuel está sentado con un muchacho Pawnee que le enseña a trenzar cuerda. Se avergüenza al verte, pero el otro chico sonríe y os acompaña hasta la loma. La patrulla Pawnee os mira con menos recelo (+6).', 'good'); }
      g.tribes.pawnee.attitude -= 4; g.sup.food += 80;
      return ok('Lo encuentras cazando', 'Samuel ha abatido un ciervo… en las tierras de maíz de los Pawnee. Traes 80 lb de carne y una mala impresión (-4 de trato).');
    }, 'Cuesta un día', ['Martha']),
    opt('Enviar a Silas y Mary a seguir el rastro', () => {
      bump(g, 'silas', 2); bump(g, 'hijo', -4);
      if (g.rng.random() < .5) { g.sup.food += 60; return ok('Lo traen de vuelta', 'Silas y Mary lo traen al mediodía, con una pieza cobrada (+60 lb). Samuel no abre la boca en todo el día.'); }
      return ok('Lo traen de vuelta', 'Silas y Mary lo traen al mediodía. «Me tratáis como a un crío», murmura Samuel.');
    }, 'Sin perder tiempo', ['Silas']),
    opt('Dejarlo: volverá cuando tenga hambre', () => {
      bump(g, 'hijo', -8); bump(g, 'esposa', -5);
      if (g.rng.random() < .3) { const s2 = g.member('hijo'); if (s2) s2.health = Math.max(5, s2.health - 25); g.tribes.pawnee.attitude -= 5; return ok('Vuelve cojeando', 'Samuel regresa a la tarde con un tobillo hinchado y la mula perdida. Los Pawnee lo vieron en su campo de maíz (-5).', 'danger'); }
      return ok('Vuelve solo', 'Samuel regresa cuando tiene hambre. Martha no te dirige la palabra en toda la tarde.');
    }, 'Riesgo', ['Thomas']),
  ], 'danger');
}
function c_clara_amiga(g) {
  return prompt('Clara ha hecho una amiga', 'Junto al río, Clara juega con una niña Cheyenne. No comparten una palabra, pero ya han intercambiado una cinta y una piedra pulida. La libreta de Clara se llena de dibujos y de palabras nuevas.\n\nA unos pasos, los adultos de la niña vigilan. Y Thomas ya ha dicho en voz alta lo que piensa.', [
    opt('Dejarlas jugar; Martha las acompaña', () => { g.flags.clara_words = true; bump(g, 'hija', 6); bump(g, 'esposa', 2); bump(g, 'tomas', -2); g.tribes.cheyenne.attitude += 6;
      return ok('Una amistad sin idioma', 'Martha se sienta con las madres a ver jugar a las niñas. Al anochecer Clara sabe contar hasta diez en Cheyenne. Los Cheyenne os mirarán distinto (+6). Clara podrá ayudaros a entenderos (+1 de labia).', 'good'); }, '+6 trato, Clara ayuda a traducir', ['Martha']),
    opt('Prohibirlo: es peligroso', () => { bump(g, 'hija', -8); bump(g, 'esposa', -2); bump(g, 'tomas', 2); return ok('«Aquí no se juega con extraños»', 'Clara llora en silencio y esa noche no escribe nada en su libreta. Nadie corre peligro, pero algo se ha enfriado.'); }, 'Sin riesgo', ['Thomas']),
    opt('Invitar a la familia a cenar (1 mercancía, 30 lb)', () => {
      if (g.sup.goods < 1 || g.sup.food < 30) return ok('No hay con qué', 'No tenéis ni lo mínimo para una cena de invitados: 1 mercancía y 30 lb de comida.');
      g.sup.goods--; g.sup.food -= 30; g.flags.clara_words = true; g.tribes.cheyenne.attitude += 12; bump(g, 'hija', 8); bump(g, 'esposa', 4); bump(g, 'tomas', -4); g.sup.food += 25;
      return ok('Una cena con invitados', 'La familia de la niña trae pescado ahumado (+25 lb) y se sienta a vuestro fuego. Thomas come con la mandíbula apretada. Los Cheyenne hablarán bien de vosotros (+12).', 'good');
    }, '+12 trato', ['Ruth', 'Martha']),
  ], 'info');
}
function c_eli_roca(g) {
  return prompt('Eli talla su nombre en la piedra', 'Eli se detiene ante la gran aguja de piedra con un cuchillo en la mano. «Aquí lo dejo», dice, y empieza a tallar su nombre. Cuando termina habla de la guerra de su juventud: de una aldea en llamas, de un vecino sin cabellera, de por qué no se fía de nadie con una pluma en el pelo. Samuel escucha con la boca abierta. Clara, con la libreta.\n\nTe mira esperando una respuesta.', [
    opt('Escuchar en silencio', () => { bump(g, 'abuelo', 8); g.flags.eli_listened = true; return ok('Lo escuchas entero', 'Eli habla hasta que se apaga el fuego. Al final te aprieta el hombro: «Eres el único que no me ha corregido.» (Eli +8)'); }, 'Eli +8', ['Martha']),
    opt('Preguntarle si nadie lo salvó nunca', () => { bump(g, 'abuelo', 5); g.flags.eli_friend = true; return ok('«¿Nadie te salvó nunca a ti?»', 'Eli calla mucho rato. «Un hombre Lakota. Sombra del Roble. Me sacó del río con la pierna rota… y nunca volví a hablar de él.» Se queda mirando el río. Si os encontráis con los Lakota, quizá quiera hablar por vosotros.', 'good'); }, 'Puede abrir una puerta en tierra Lakota', ['Ruth', 'Martha']),
    opt('Pedirle que enseñe a Samuel a disparar', () => { bump(g, 'abuelo', 5); bump(g, 'hijo', 5); const s = g.member('hijo'); if (s) s.shoot = Math.min(10, s.shoot + 1); return ok('Una lección de tiro', 'Al caer la tarde, Eli le enseña a Samuel a contener la respiración y a esperar el momento. «Dispara cuando ya no quieras hacerlo.» (Puntería de Samuel +1)', 'good'); }, 'Puntería de Samuel +1', ['Samuel', 'Silas']),
  ], 'info');
}
function c_martha_fiebre(g) {
  const m = g.member('esposa'); m.sick = 'fiebre tifoidea'; m.health = Math.min(m.health, 45);
  const retry = () => prompt('Sin médico', 'Sin dinero para el médico, sólo quedan dos caminos.', [opt('Detener la caravana tres días', () => { g.restDay(3); const x = g.member('esposa'); if (x) { x.sick = ''; x.health = Math.max(x.health, 65); } bump(g, 'esposa', 5); return ok('Tres días de cuidados', 'Martha mejora lentamente.', 'good'); }), opt('Seguir; Ruth la cuida en el carro', () => ok('Resiste', 'Martha aguanta. Por ahora.'))], 'danger');
  return prompt('Martha arde de fiebre', 'Martha ha ardido toda la noche. Ya no reconoce a Clara. Ruth le moja la frente. El fuerte está a media jornada; allí hay un médico del ejército… y una fila de carretas esperando turno para el vado.\n\nThomas ya está uncido: «Cada día perdido es dinero perdido.»', [
    opt('Detener la caravana tres días', () => { g.restDay(3); const x = g.member('esposa'); if (x) { x.sick = ''; x.health = Math.max(x.health, 70); } bump(g, 'esposa', 6); bump(g, 'tomas', -3); bump(g, 'hija', 3); g.morale = Math.min(100, g.morale + 5); return ok('Tres días de cuidados', 'Martha despierta al tercer día pidiendo agua y su libreta. La caravana pierde tiempo, pero no a ella.', 'good'); }, 'Tiempo y comida', ['Ruth', 'Clara']),
    opt('Seguir; Ruth la cuida en el carro', () => {
      bump(g, 'ruth', 4); bump(g, 'tomas', 2); const x = g.member('esposa');
      if (x && g.rng.random() < .4) { x.health -= 40;
        if (x.health <= 0) { kill(g, 'esposa', 'fiebre'); g.morale = Math.max(0, g.morale - 25); for (const r of ['hijo', 'hija', 'abuelo']) bump(g, r, -8); return ok('Martha no despierta', 'Ruth la acompaña hasta el último aliento, sobre el colchón del carro. Se la entierra junto al camino, con la libreta de Clara en las manos.', 'danger'); }
        return ok('Empeora', 'Ruth la cuida a trompicones durante la marcha. Martha sobrevive, pero queda muy débil.', 'danger'); }
      if (x) x.health = Math.min(100, x.health + 15);
      bump(g, 'esposa', -3); return ok('Resiste', 'Martha aguanta los baches con los dientes apretados. Ruth no se aparta de su lado.');
    }, '40 % de empeorar', ['Thomas']),
    opt('Pagar al médico del fuerte ($45)', () => {
      if (g.sup.money < 45) return ok('Sin dinero', 'El médico del fuerte cobra $45 y no los tienes. Hay que decidir de otro modo.', 'danger', retry);
      g.sup.money -= 45; g.day++; g.dailyUpkeep(); const x = g.member('esposa'); if (x) { x.sick = ''; x.health = Math.max(x.health, 65); } bump(g, 'esposa', 5);
      return ok('El médico del ejército', 'Un día y quinina bastan. Martha, aún pálida, sonríe. «Me debes la cuenta», murmura.', 'good');
    }, 'Un día', ['Hannah']),
  ], 'danger');
}
function c_canon(g) {
  return prompt('Thomas quiere un cañón', 'En Fort Laramie, Thomas deja caer una bolsa de cuero sobre la mesa. «Nuestros ahorros juntos compran un cañón de campaña. Yo no cruzo esas montañas sin uno.» Ruth baja la mirada; Martha, si está, dice que el dinero es de los niños.', [
    opt('Comprarlo ($230)', () => { g.sup.money -= 230; g.cannonStock++; bump(g, 'tomas', 7); bump(g, 'esposa', -2); return ok('Un cañón para el círculo', 'Se carga el cañón en la bodega. Móntalo en una carreta desde el Plan de defensa. Thomas sonríe por primera vez en semanas.', 'good'); }, 'Un cañón para la defensa', ['Thomas', 'Silas']),
    opt('Rechazarlo: el dinero es para llegar', () => { bump(g, 'tomas', -5); bump(g, 'esposa', 2); return ok('«El dinero es para llegar»', 'Thomas se guarda la bolsa sin una palabra. Esa noche cena aparte.'); }, 'Ahorras el dinero', ['Martha']),
  ], 'info');
}
function c_silas(g) {
  return prompt('Lo que Silas no cuenta', 'Silas no ha dormido. Te espera junto al fuego y habla sin mirarte: sirvió en el ejército y desertó cuando le ordenaron disparar contra un campamento de mujeres y niños. Nadie le preguntó; nadie lo sabe. «Si alguien de ahí viene a buscarme, os pongo a todos en peligro.»', [
    opt('Protegerlo: «es uno de los nuestros»', () => { bump(g, 'silas', 10); bump(g, 'esposa', 2); g.flags.silas_trust = true; for (const c of g.living()) if (g.canShoot(c) && c.roleId !== 'silas' && c.shoot < 7) c.shoot++; return ok('«Eres de los nuestros»', 'Silas asiente. A partir de esa noche instruye en voz baja a los tiradores: cómo respirar, cómo cargar más rápido. (+1 de puntería a los tiradores flojos)', 'good'); }, 'Silas +10, instruye a los tiradores', ['Martha', 'Ruth']),
    opt('«Con que dispares bien me basta»', () => { bump(g, 'silas', 2); return ok('«Dispara bien y no hables de más»', 'Silas se encoge de hombros. Algo se cierra dentro de él, pero seguirá en su puesto.'); }, 'Silas +2', ['Thomas']),
    opt('Pedirle que se vaya en el próximo fuerte', () => { bump(g, 'esposa', 3); bump(g, 'tomas', -2); const s = g.member('silas'); if (s) { s.alive = false; s.cause = 'se marchó en Fort Bridger'; s.post = null; g.normalizePosts(); } return ok('«Mejor que te vayas en Fort Bridger»', 'Silas recoge su manta antes del alba. Mary lo sigue con la mirada, pero se queda. Hay un tirador menos.', 'danger'); }, 'Pierdes un gran tirador', ['Thomas']),
  ], 'info');
}
function c_samuel_paso(g) {
  const s = g.member('hijo');
  if (s.loyalty < 35) {
    const leave = () => { const sm = g.member('hijo'); if (sm) { sm.alive = false; sm.cause = 'se fue con los tramperos'; sm.post = null; g.sup.ammo = Math.max(0, g.sup.ammo - 30); g.normalizePosts(); } bump(g, 'esposa', -8); bump(g, 'hija', -6); g.morale = Math.max(0, g.morale - 12); return ok('Samuel se va', 'Lo ves alejarse por el paso con la mula y 30 balas. Clara apunta algo en su libreta, y no lo enseña.', 'danger'); };
    return prompt('Samuel quiere irse', 'Samuel te espera en lo alto del paso con la mula cargada. Una partida de cazadores de pieles va hacia California y ha ofrecido llevarlo. «Allí nadie me manda», dice. Martha no puede hablar.', [
      opt('Convencerlo con palabras', () => { const p = .35 + .05 * g.best('talk') + .006 * s.loyalty; if (g.rng.random() < p) { bump(g, 'hijo', 12); bump(g, 'esposa', 4); return ok('Se queda', 'Hablas con él sin levantar la voz hasta que se rompe la tensión. Samuel baja la cabeza: «Está bien. Pero cuéntame lo que decidas.»', 'good'); } return leave(); }, 'Depende de tu labia y su lealtad', ['Martha']),
      opt('Darle el mando de la guardia nocturna', () => { bump(g, 'hijo', 12); g.flags.samuel_guard = true; return ok('«Toma el mando de la guardia»', 'Samuel se queda mudo. Luego se cuadra, como lo haría Silas. Desde esa noche la guardia es más atenta (más avisos).', 'good'); }, 'Samuel +12', ['Silas', 'Eli']),
      opt('Dejarlo ir', leave, 'Se va', ['Thomas']),
    ], 'danger');
  }
  return prompt('Samuel pide explorar', 'Samuel te espera en lo alto del paso con Mary y una cuerda al hombro. «Déjanos adelantarnos a explorar el camino. Prometo volver antes del anochecer.» Hay algo distinto en su mirada: ha dejado de pedir permiso para ser alguien.', [
    opt('Dejarlo ir con Mary', () => { bump(g, 'hijo', 6); bump(g, 'mary', 3); g.flags.samuel_scout = true; return ok('Los exploradores', 'Vuelven al anochecer con un mapa dibujado a carbón: dónde hay agua y dónde acampar. Los próximos pasos de montaña serán menos peligrosos.', 'good'); }, 'Menos peligro en las montañas', ['Silas', 'Mary']),
    opt('«Todavía no»', () => { bump(g, 'hijo', -4); return ok('«Todavía no»', 'Samuel traga saliva y asiente. Ha entendido, pero no le ha gustado.'); }, 'Samuel -4', ['Martha']),
  ], 'info');
}
function c_eli_ultimo(g) {
  const e = g.member('abuelo'); e.sick = 'agotamiento'; e.health = Math.min(e.health, 35);
  const lastWords = how => { kill(g, 'abuelo', 'murió de viejo'); g.morale = Math.max(0, g.morale - 8); bump(g, 'esposa', -2); bump(g, 'hijo', 2); bump(g, 'hija', 2); g.flags.eli_dead = true; const s = g.member('hijo'); if (s) s.shoot = Math.min(10, s.shoot + 1);
    return ok('Eli', `Eli muere ${how}. Antes dijo algo a Clara y le dio su cuchillo a Samuel: «Sé mejor que yo.» Se le entierra a la sombra de un pino, con vistas al oeste. Samuel guarda su rifle (+1 puntería).`, 'danger'); };
  const night = () => { bump(g, 'abuelo', 10); bump(g, 'esposa', 5); bump(g, 'hijo', 4); const ee = g.member('abuelo');
    if (ee && g.rng.random() < .45) return lastWords('al amanecer, tras una noche de historias');
    if (ee) { ee.sick = ''; ee.health = 50; } return ok('Una noche de historias', 'Eli habla hasta el alba: de su aldea, de la guerra, de Sombra del Roble. Al salir el sol pide café. Ha ganado más días.', 'good'); };
  return prompt('Eli no despierta bien', 'Eli se ha quedado dormido sobre la mula y no despierta del todo. Murmura el nombre de su mujer y el del mar. Martha te mira: él pidió ver el Pacífico y aún quedan semanas de camino.', [
    opt('Darle 2 medicinas y dos días de reposo', () => {
      if (g.sup.medicine < 2) return ok('Sin medicinas', 'No quedan dos medicinas para él. Sólo puedes velarlo.', 'danger', night);
      g.sup.medicine -= 2; g.restDay(2); bump(g, 'abuelo', 6); bump(g, 'esposa', 4); const ee = g.member('abuelo');
      if (ee && g.rng.random() < .7) { ee.sick = ''; ee.health = 60; return ok('Se recupera', 'Eli abre los ojos al segundo día y pide el tabaco. «Todavía me debéis el mar.»', 'good'); }
      return lastWords('en paz, tras dos días de cuidados');
    }, '70 % de recuperarse', ['Martha', 'Hannah']),
    opt('Seguir: él pidió llegar al mar', () => { bump(g, 'abuelo', -2); bump(g, 'esposa', -4); const ee = g.member('abuelo'); if (ee && g.rng.random() < .5) return lastWords('durante la marcha, mirando hacia el oeste'); if (ee) ee.health = Math.min(ee.health + 5, 45); return ok('Aguanta', 'Eli va dormitando sobre el carro. Cada vez que despierta pregunta cuánto falta.'); }, '50 % de empeorar', ['Thomas']),
    opt('Velarlo toda la noche, hablando', night, 'Eli +10', ['Clara', 'Samuel']),
  ], 'danger');
}
function c_clara_montanas(g) {
  const friend = g.flags.clara_words;
  const search = () => { g.day++; g.dailyUpkeep(); bump(g, 'hija', 3); const cl = g.member('hija');
    if (friend && g.tribes.cayuse.attitude > -30) { g.tribes.cayuse.attitude += 12; g.sup.food += 60; return ok('«Ella nos llamó por nuestro nombre»', 'Un grupo Cayuse la trae sana y salva: Clara le preguntó el camino a una anciana con las pocas palabras que había anotado. Os dejan 60 lb de pescado. (+12 de trato con los Cayuse)', 'good'); }
    if (cl) cl.health = Math.max(10, cl.health - 25);
    return ok('Medio helada, pero viva', 'La encontráis acurrucada bajo un abeto caído. Tiene los labios azules y una rama de pino en la mano. Costará varios días recuperarla.'); };
  return prompt('Clara se ha perdido', 'Tras una hora sin ver a Clara, la libreta aparece abierta en el barro del camino. El bosque es espeso; a lo lejos, humo. Martha corre sin zapatos. Ada llora. Nadie dice lo que todos piensan.', [
    opt('Buscarla entre todos (1 día)', search, 'Con ayuda de quienes la conozcan', ['Martha', 'Ruth']),
    opt('Pedir ayuda a los Cayuse', () => {
      if (g.tribes.cayuse.attitude < -15) { g.tribes.cayuse.attitude -= 4; return ok('No quieren oírte', 'Los Cayuse se encogen de hombros: no confían en forasteros que llegan pidiendo ayuda a gritos. (-4)', 'danger', search); }
      g.tribes.cayuse.attitude += 10; bump(g, 'hija', 3); return ok('Pides ayuda', 'Los Cayuse pidieron un solo favor: que no os quedéis donde cazan. En una hora, un muchacho trae a Clara en brazos. (+10 de trato)', 'good');
    }, 'Depende de su trato', ['Eli', 'Ruth']),
    opt('Que Mary siga el rastro', () => { bump(g, 'mary', 6);
      if (g.rng.random() < .75) return ok('Mary lee el bosque', 'Mary la sigue por una rama quebrada, una piedra volteada y un trozo de cinta. Clara estaba dormida junto a un arroyo.', 'good');
      g.day++; const cl = g.member('hija'); if (cl) cl.health = Math.max(8, cl.health - 35);
      return ok('Se pierde un día', 'Mary pierde la pista junto al arroyo. La noche cae. Al amanecer, Clara aparece sola, tiritando.', 'danger'); }, '75 % de éxito', ['Mary', 'Silas']),
  ], 'danger');
}
function c_cobb(g) {
  const promise = () => { bump(g, 'mercenario', -3); return ok('«En Fort Hall»', 'Cobb asiente muy despacio. Hay cosas que se quedan apuntadas.'); };
  return prompt('Cobb reclama su paga', 'Cobb espera su paga. «Hace semanas que cobré por adelantado y las semanas son largas. Un tirador contento dispara mejor.» No hay amenaza en su voz, pero tampoco ninguna broma.', [
    opt('Pagarle $25 ahora', () => { if (g.sup.money < 25) return ok('Sin dinero', 'No llegas a los $25. Cobb se encoge de hombros: «Entonces, a ver cuánto me aguanto.»', 'danger', promise); g.sup.money -= 25; bump(g, 'mercenario', 14); return ok('Paga recibida', 'Cobb cuenta los billetes dos veces, con la boca cerrada. «Así da gusto.» Esa noche dispara mejor que nunca.', 'good'); }, 'Cobb +14', ['Silas']),
    opt('Prometerle la paga en Fort Hall', promise, 'Cobb -3', ['Martha']),
    opt('Negarte: ya cobró por adelantado', () => { bump(g, 'mercenario', -16); return ok('«Ya cobraste»', 'Cobb no discute. Se limpia las manos en los pantalones y se aleja. Algunos hombres dejan de ser leales sin hacer ruido.', 'danger'); }, 'Cobb -16 (puede desertar)', ['Thomas']),
  ], 'info');
}
function c_finch(g) {
  return prompt('Niños con fiebre', 'Una mujer Cayuse espera junto al camino con un niño febril en brazos. Dr. Finch lo mira un segundo: sarampión. «Lo vi en la ciudad de donde me fui. No es mi gente, pero es un niño. Dame tres medicinas y no preguntes más.»', [
    opt('Darle las 3 medicinas', () => { g.sup.medicine -= 3; g.tribes.cayuse.attitude += 18; bump(g, 'medico', 10); g.morale = Math.min(100, g.morale + 4); return ok('Una deuda de gratitud', 'El niño duerme esa noche sin toser. Al amanecer, los Cayuse han dejado un saco de pescado y una pluma azul en tu carreta. (+18 de trato)', 'good'); }, '+18 de trato con los Cayuse', ['Ruth', 'Martha']),
    opt('Negarte: son para los nuestros', () => { bump(g, 'medico', -12); g.tribes.cayuse.attitude -= 3; return ok('«Nos hacen falta»', 'Finch no te discute, pero esa noche duerme apartado del fuego. La mujer se marcha sin una palabra. (-3)', 'danger'); }, 'Finch -12', ['Thomas']),
  ], 'info');
}
S.CHAPTERS = [
  ['samuel_noche', g => g.mile >= 140 && g.member('hijo'), c_samuel_noche],
  ['clara_amiga', g => g.mile >= 340 && g.member('hija') && g.currentTribe() === 'cheyenne', c_clara_amiga],
  ['eli_roca', g => g.mile >= 470 && g.member('abuelo'), c_eli_roca],
  ['martha_fiebre', g => g.mile >= 650 && g.member('esposa'), c_martha_fiebre],
  ['canon', g => g.mile >= 640 && g.sup.money >= 230 && g.cannonStock === 0 && !g.wagons.some(w => w.cannon) && g.member('tomas'), c_canon],
  ['silas', g => g.mile >= 880 && g.member('silas'), c_silas],
  ['samuel_paso', g => g.mile >= 1030 && g.member('hijo'), c_samuel_paso],
  ['eli_ultimo', g => g.mile >= 1500 && g.member('abuelo'), c_eli_ultimo],
  ['clara_montanas', g => g.mile >= 1700 && g.member('hija'), c_clara_montanas],
  ['cobb_paga', g => g.mile >= 640 && g.member('mercenario'), c_cobb],
  ['finch_cayuse', g => g.mile >= 1550 && g.member('medico') && g.sup.medicine >= 3, c_finch],
];
const safe = (fn, g) => { try { return !!fn(g); } catch (e) { return false; } };
S.check = function (g, scenes) {
  const pending = S.CHAPTERS.filter(c => !g.storyDone.includes(c[0]) && safe(c[1], g));
  if (pending.length && !g.director.allowStory(g)) return null;
  for (const [key, when, build] of S.CHAPTERS) {
    if (g.storyDone.includes(key)) continue;
    let w = false; try { w = !!when(g); } catch (e) { w = false; }
    if (!w) continue;
    g.storyDone.push(key);
    let p = null; try { p = build(g); } catch (e) { p = null; }
    if (!p) continue;
    g.log(`Historia: ${p.title}`);
    if (scenes && g.flags.cutscenes !== false && CS[key]) { const cs = CS[key](g); if (cs) { cs.then = () => p; return cs; } }
    return p;
  }
  return null;
};

// ============================================================== charlas de campamento
S.familyTalk = function (g, role) {
  const c = g.member(role);
  if (!c) return ok('Silencio', 'Ya no está.');
  const nm = c.name.split(' ')[0];
  if (g.day - (g.talked[role] === undefined ? -99 : g.talked[role]) < 5) return ok(nm, `Ya hablasteis hace poco. ${nm} te sonríe y vuelve a lo suyo.`);
  g.talked[role] = g.day;
  const T = {
    esposa: ['Martha repasa contigo las cuentas con una calma que no tiene. «Lo que decidas, lo sostendré. Pero cuéntame lo que piensas antes de hacerlo.»', 'Escucharla', 'Pedirle consejo'],
    hijo: ['Samuel limpia el rifle sin mirarte. «¿Cuándo me vas a dejar decidir algo?»', 'Escucharlo', 'Darle una tarea'],
    hija: ['Clara te enseña la libreta: dibujos de las carretas, de un halcón, de palabras que no entiende. «¿Por qué hay gente que no quiere que pasemos?»', 'Explicárselo con calma', 'Escribir juntos'],
    abuelo: ['Eli te hace sitio junto al fuego. «Siéntate. Te cuento lo que pasó el día que dejé de confiar. Y cómo estuve a punto de volver a hacerlo.»', 'Escucharlo', 'Pedirle un consejo militar'],
  }[role] || [`${c.name} te cuenta cómo lleva el viaje.`, 'Escuchar', 'Pedir consejo'];
  const mood = c.loyalty >= 70 ? 'te mira con confianza.' : c.loyalty >= 35 ? 'te escucha a medias.' : 'responde con monosílabos.';
  return prompt(`Una charla con ${nm}`, `${c.bio}\n\n${nm} ${mood}\n\n${T[0]}`, [
    opt(T[1], () => { bump(g, role, 4); g.morale = Math.min(100, g.morale + 2); return ok(nm, 'Hablas un buen rato. Nada se arregla, pero algo pesa menos. (Lealtad +4, moral +2)', 'good'); }, 'Lealtad +4, moral +2'),
    opt(T[2], () => {
      bump(g, role, 2);
      if (role === 'esposa') { const nxt = g.nextTribe(), a = nxt ? g.tribes[nxt].attitude : 0; return ok('Martha', `«He oído a las otras mujeres: los ${g.tribeName(nxt)} andan ${a < -30 ? 'hostiles' : a < 0 ? 'recelosos' : a < 25 ? 'cautos' : 'amistosos'}. Si podemos, hablemos primero.»`); }
      if (role === 'hijo') { bump(g, role, 3); g.sup.food += 20; return ok('Samuel', 'Le pides que salga a cazar con Mary; vuelve orgulloso con una pieza (+20 lb). (Lealtad +5)', 'good'); }
      if (role === 'hija') { g.flags.clara_words = true; return ok('Clara', 'Escribís juntos tres frases en otra lengua. «Si lo practico, seré tu intérprete.» (+labia en diplomacia)', 'good'); }
      if (role === 'abuelo') { g.flags.eli_tip = true; return ok('Eli', '«Los jinetes dan vueltas y disparan; lo que de verdad mata es el hueco en el círculo. Tapadlo cuanto antes.» (Sabio consejo)'); }
      return ok(nm, 'Te da un consejo breve y sensato.');
    }, 'Lealtad +2 y un detalle útil'),
  ], 'info');
};

// ============================================================== epílogo
S.epilogue = function (g, st) {
  const lines = [], bd = [];
  const promise = g.flags.promise, text = {tierra: 'una tierra propia', paz: 'un lugar sin guerra', fortuna: 'fortuna'};
  let kept = null;
  if (promise) {
    if (promise === 'tierra') kept = st.site.fertility >= 7 && st.built.includes('campos');
    else if (promise === 'paz') kept = st.built.includes('tratado') || g.tribes[st.neighbor()].attitude >= 40;
    else kept = (g.sup.money + g.sup.goods * 6) >= 250 || st.built.includes('puesto');
  }
  if (kept === true) { lines.push(`Lo prometido en la mesa de Independence —${text[promise]}— se cumplió, aunque costó más de lo que nadie imaginaba.`); bd.push(['Palabra cumplida', 120]); }
  else if (kept === false) lines.push(`La promesa de ${text[promise]} se quedó a medio camino. Martha lo recuerda sin reproches. Casi.`);
  const pk = S.purposeKept(g, st);
  if (pk !== null) {
    const pname = S.PURPOSES[g.flags.purpose].name.toLowerCase();
    if (pk) { lines.push(`Y se cumplió el propósito de la expedición: ${pname}.`); bd.push(['Propósito cumplido', 100]); }
    else lines.push(`El propósito de ${pname} quedó pendiente: el siguiente año dirá si se logra.`);
  }
  const RL = {medico:'Finch abre una consulta en la casa común; nadie le pregunta por su pasado.', predicador:'Lamb levanta una pequeña iglesia de troncos cuyas puertas nunca se cierran.', traductora:'Lena traduce los primeros tratos del valle y firma, en tres idiomas, el acta del asentamiento.', herrero:'Marsh monta su fragua junto al arroyo y no deja de martillar hasta que cae la nieve.', partera:'Rosa asiste a los primeros nacimientos del asentamiento, uno de ellos en pleno invierno.', cazadora:'Nora cuelga las pieles de su primera temporada sobre la puerta; la despensa nunca queda vacía.'};
  for (const r in RL) if (g.member(r)) lines.push(RL[r]);
  const m = g.byRole('esposa'), s = g.byRole('hijo'), c = g.byRole('hija'), e = g.byRole('abuelo');
  if (m && m.alive) lines.push(m.loyalty >= 50 ? 'Martha abre una escuela bajo un techo de troncos, con seis niños y la libreta de Clara como primer libro.' : 'Martha trabaja sin descanso; habla poco, y a veces mira hacia el este.');
  else if (m) lines.push('Martha duerme en una loma junto al camino. Cada año, Clara le lleva flores del valle.');
  if (s && s.alive) lines.push(s.loyalty >= 50 ? 'Samuel, con las manos curtidas, levanta la empalizada junto a los hombres y dirige la guardia.' : 'Samuel apenas habla en la mesa y mira a menudo hacia las montañas.');
  else if (s) lines.push(s.cause === 'se fue con los tramperos' ? 'De Samuel llegó una carta en otoño: «Estoy bien. No me busquéis.»' : 'Samuel descansa en tierra extraña.');
  if (c && c.alive) lines.push(g.flags.clara_words ? 'Clara llena su libreta de palabras en tres lenguas y se convierte, antes de cumplir doce años, en la intérprete de media colonia.' : 'Clara dibuja el valle entero en su libreta.');
  if (e && e.alive) lines.push('Eli llega a ver el agua grande de lejos, un día claro de otoño. «Ya está», dijo, y pidió un café.');
  else if (e && g.flags.eli_dead) lines.push('Eli no llegó al mar, pero Samuel talló su nombre en el primer poste del asentamiento: «Con vistas al oeste».');
  const fl = g.familyLoyalty();
  if (fl >= 70) { lines.push('La familia sigue unida: las cartas que escriben a los que quedaron atrás dicen todas lo mismo, «Estamos bien. Venid.»'); bd.push(['Familia unida', Math.floor(fl)]); }
  else if (fl < 35) lines.push('En la casa nueva hay silencios más grandes que las habitaciones.');
  else bd.push(['Familia', Math.floor(fl / 2)]);
  return [lines, bd];
};
})(globalThis.CV = globalThis.CV || {});
