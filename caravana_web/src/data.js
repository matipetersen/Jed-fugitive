/* LA CARAVANA (web) — datos estáticos. Espejo de caravana/data.py */
(function (CV) {
'use strict';
const D = CV.data = {};
CV.clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

D.START = new Date(1848, 3, 15);
D.FORCED_WINTER_DAY = Math.round((new Date(1848, 11, 15) - D.START) / 86400000);
D.TRAIL_END = 1950;
D.MONTHS = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];

D.WAYPOINTS = [
  {name:'Independence', mile:0, kind:'post', price:1.00, text:'Los últimos carteles de «Oregón o nada». Aquí se compra todo.'},
  {name:'Río Kansas', mile:100, kind:'river', depth:3, text:'El primer río serio. Las lluvias de primavera lo han hinchado.'},
  {name:'Fort Kearny', mile:280, kind:'post', price:1.15, text:'Un fortín del ejército en el río Platte. Precios razonables.'},
  {name:'Chimney Rock', mile:480, kind:'landmark', text:'La aguja de piedra que todos describen en sus cartas. Quedan 1.500 millas.'},
  {name:'Fort Laramie', mile:640, kind:'post', price:1.35, cannon:true, text:'El gran puesto de comercio de pieles. Aquí se firman tratados y se venden cañones viejos.'},
  {name:'Independence Rock', mile:880, kind:'landmark', text:'«La lápida del desierto». Cientos de nombres tallados. Hay que cruzarla antes de julio.'},
  {name:'South Pass', mile:1020, kind:'mountain', danger:0.35, text:'El paso de la Divisoria Continental. Suave pero ventoso y sin agua.'},
  {name:'Fort Bridger', mile:1150, kind:'post', price:1.60, text:'Un puesto de montañeses. Todo es caro, nada sobra.'},
  {name:'Fort Hall', mile:1400, kind:'post', price:1.80, cannon:true, text:'Último puesto grande antes de las Montañas Azules.'},
  {name:'Río Snake', mile:1550, kind:'river', depth:4, text:'Un río ancho y traicionero entre cañones de basalto.'},
  {name:'Montañas Azules', mile:1750, kind:'mountain', danger:0.55, text:'Bosques cerrados, barro y laderas empinadas. Aquí mueren las caravanas tardías.'},
  {name:'Misión Whitman', mile:1900, kind:'post', price:2.0, text:'Una misión junto a los Cayuse. Últimas provisiones antes del valle.'},
  {name:'Bifurcación del Columbia', mile:1950, kind:'fork', text:'El final del camino. Hay que decidir dónde fundar el asentamiento.'},
];
D.TERRITORIES = [[0,300,'pawnee'],[300,620,'cheyenne'],[620,1000,'lakota'],[1000,1500,'shoshone'],[1500,2100,'cayuse']];
D.TERRITORY_TRIBES = ['pawnee','cheyenne','lakota','shoshone','cayuse'];

D.TRIBES = {
  pawnee:{name:'Pawnee', color:'#c47840', aggression:.8, pride:3, strength:.9, style:{guerrero:6,jinete:2,fuego:2},
    greet:'Un grupo de exploradores Pawnee observa la caravana desde una loma.', wants:'food', lore:'Agricultores y cazadores de las llanuras; defienden sus aldeas de maíz.'},
  cheyenne:{name:'Cheyenne', color:'#b43c3c', aggression:1.0, pride:4, strength:1.0, style:{jinete:7,guerrero:2,fuego:1},
    greet:'Jinetes Cheyenne aparecen en la cresta, inmóviles contra el cielo.', wants:'goods', lore:'Jinetes magníficos. Respetan a quien habla con firmeza y cumple.'},
  lakota:{name:'Lakota', color:'#4678be', aggression:1.2, pride:5, strength:1.2, style:{jinete:6,fuego:3,guerrero:2},
    greet:'Una partida Lakota cabalga paralela a la caravana, a distancia de flecha.', wants:'ammo', lore:'Señores de las llanuras. Los emigrantes han ahuyentado el bisonte.'},
  shoshone:{name:'Shoshone', color:'#5aa064', aggression:.6, pride:3, strength:.9, style:{jinete:4,guerrero:4,fuego:2},
    greet:'Un hombre Shoshone se acerca solo, con la mano en alto, desde el sendero.', wants:'goods', lore:'Comerciantes y guías. Conocen cada paso de las montañas.'},
  cayuse:{name:'Cayuse', color:'#d2aa3c', aggression:.8, pride:4, strength:1.0, style:{jinete:5,guerrero:2,bandido:3},
    greet:'Un grupo de jinetes Cayuse, con caballos soberbios, sale del bosque.', wants:'medicine', lore:'Criadores de caballos. Las epidemias de sarampión han roto su confianza.'},
  kalapuya:{name:'Kalapuya', color:'#789658', aggression:.2, pride:2, strength:.5, style:{guerrero:1}, greet:'', wants:'goods', lore:''},
  chinook:{name:'Chinook', color:'#6e8caa', aggression:.2, pride:2, strength:.5, style:{guerrero:1}, greet:'', wants:'goods', lore:''},
};
D.FOES = {
  guerrero:{name:'Guerrero', hp:45, speed:72, cost:.8},
  jinete:{name:'Jinete', hp:50, speed:150, cost:1.1},
  fuego:{name:'Arquero de fuego', hp:40, speed:70, cost:1.5},
  bandido:{name:'Bandido', hp:55, speed:66, cost:1.5},
  jefe:{name:'Jefe de guerra', hp:160, speed:120, cost:5.0},
};
D.PROFESSIONS = {
  granjero:{name:'Granjero', money:800, desc:'Sabe de tierra y semillas. Asentamiento más fértil y mejor caza menor.', skills:{shoot:4,medic:3,build:5,talk:4,hunt:6}, farm:2},
  carpintero:{name:'Carpintero', money:750, desc:'Repara carretas con la mitad de repuestos y levanta barricadas rápido.', skills:{shoot:4,medic:2,build:9,talk:4,hunt:3}, farm:0},
  medico:{name:'Médico', money:850, desc:'Menos muertes por enfermedad y heridas. Cura durante el combate.', skills:{shoot:3,medic:9,build:3,talk:6,hunt:2}, farm:0},
  soldado:{name:'Ex-soldado', money:700, desc:'Excelente tirador, +40 balas. Los pueblos lo respetan… o lo temen.', skills:{shoot:9,medic:3,build:4,talk:3,hunt:6}, farm:0},
  comerciante:{name:'Comerciante', money:1250, desc:'Mejores precios (-12%) y buen lenguaje. Frágil en combate.', skills:{shoot:3,medic:3,build:2,talk:9,hunt:2}, farm:0},
};
D.ITEMS = {
  food:{name:'Comida', unit:'50 lb', price:8, per:50},
  ammo:{name:'Munición', unit:'20 balas', price:9, per:20},
  goods:{name:'Mercancías', unit:'1 lote', price:6, per:1},
  parts:{name:'Repuestos', unit:'1 juego', price:12, per:1},
  medicine:{name:'Medicinas', unit:'1 dosis', price:10, per:1},
  oxen:{name:'Bueyes', unit:'1 par', price:45, per:2},
  wagon:{name:'Carreta', unit:'1 carreta', price:95, per:1},
  cannon:{name:'Cañón', unit:'1 pieza', price:230, per:1},
};
D.SELL = .45;
D.PACES = {lento:14, normal:20, rapido:27};
D.PACE_LABEL = {lento:'Lento', normal:'Normal', rapido:'Rápido'};
D.RATIONS = {escasas:.7, normales:1.2, abundantes:1.8};
D.RATION_LABEL = {escasas:'Escasas', normales:'Normales', abundantes:'Abundantes'};
D.WATCH_LABEL = {ninguna:'Sin guardia', normal:'Guardia normal', reforzada:'Guardia reforzada'};
D.DISEASES = ['disentería','cólera','fiebre tifoidea','sarampión','mordedura de serpiente','pierna rota','agotamiento'];
D.DIFFICULTY = {
  facil:{name:'Relajada', raid:.75, money:1.25, disease:.7, score:.8, mercy:1.3, desc:'Menos enemigos, más dinero y menos enfermedades.'},
  normal:{name:'Normal', raid:1, money:1, disease:1, score:1, mercy:1, desc:'La experiencia pensada.'},
  dificil:{name:'Implacable', raid:1.3, money:.9, disease:1.3, score:1.3, mercy:.6, desc:'Ataques más duros, escasez y puntuación ×1,3.'},
};
D.ROLE_NAMES = {lider:'Líder',esposa:'Esposa',hijo:'Hijo',hija:'Hija',abuelo:'Abuelo',tomas:'Vecino',ruth:'Vecina',ada:'Niña',silas:'Peón',mary:'Peón',josiah:'Peón',hannah:'Peona',lucas:'Niño',emma:'Joven',
  medico:'Médico',cazadora:'Cazadora',herrero:'Herrero',predicador:'Predicador',mercenario:'Mercenario',traductora:'Intérprete',gemelos:'Joven',partera:'Partera',carretero:'Carretero',viuda:'Viuda'};
D.FAMILY_ROLES = ['lider','esposa','hijo','hija','abuelo'];
D.SURNAMES = ['Hale','Whitaker','Marlow','Pryor','Dunn','Ellis'];
D.SITES = {
  willamette:{name:'Valle Willamette', extra:120, fertility:9, defense:4, water:9, neighbor:'kalapuya', trade:5, text:'El valle de las cartas: tierra negra, lluvia suave y bosques de abeto. Está a 120 millas más, con el invierno acechando.'},
  walla:{name:'Meseta del Walla Walla', extra:30, fertility:6, defense:6, water:6, neighbor:'cayuse', trade:4, text:'A un paso de aquí. Suelo decente y buenas vistas, pero los Cayuse son vecinos inmediatos, y de ti depende cómo.'},
  columbia:{name:'Riscos del Columbia', extra:70, fertility:7, defense:8, water:8, neighbor:'chinook', trade:8, text:'Un promontorio defendible sobre el gran río, con comercio fluvial de salmón y pieles. Tierra algo más pobre.'},
};
D.MAKESHIFT = {name:'Campamento de invierno improvisado', extra:0, fertility:3, defense:3, water:4, neighbor:'', trade:2, text:'Un claro resguardado donde el invierno os ha detenido. No es lo que soñabais, pero es lo que hay.'};
D.BUILDINGS = {
  cabana:{name:'Cabañas de troncos', cost:{parts:3,goods:2}, desc:'Refugio para el invierno. Imprescindible.'},
  pozo:{name:'Pozo y despensa', cost:{parts:1,goods:2}, desc:'Agua limpia: menos enfermedades; guarda más comida.'},
  campos:{name:'Campos y huerto', cost:{food:150,goods:1}, desc:'Siembra de trigo y patatas. Cosecha el próximo año.'},
  empalizada:{name:'Empalizada', cost:{parts:4,ammo:20}, desc:'Defensa contra incursiones y lobos.'},
  establo:{name:'Establo y corral', cost:{parts:2,goods:2}, desc:'Protege a los bueyes, carne y leche.'},
  iglesia:{name:'Escuela e iglesia', cost:{parts:2,goods:3}, desc:'Moral y cohesión: la comunidad perdura.'},
  puesto:{name:'Puesto de trueque', cost:{parts:2,goods:6}, desc:'Comercio con los vecinos: riqueza y alianza.'},
  tratado:{name:'Tratado con los vecinos', cost:{goods:8,food:60}, desc:'Regalos y festín para sellar la paz con el pueblo vecino.'},
};
D.TERRAIN_COLORS = {pradera:'#608a44',llanura:'#8c924e',estepa:'#9c905e',montaña:'#6c745e',desierto:'#bea474',cañón:'#a87652',bosque:'#385e3a',valle:'#548c4a'};
})(globalThis.CV = globalThis.CV || {});
