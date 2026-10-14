/* Asentamiento y crónica del primer año. Espejo de caravana/settlement.py */
(function (CV) {
'use strict';
const D = CV.data;

class Settlement {
  constructor(g, siteId) {
    this.g = g; this.siteId = siteId;
    this.site = Object.assign({}, siteId === 'improvisado' ? D.MAKESHIFT : D.SITES[siteId]);
    if (siteId === 'improvisado') this.site.neighbor = g.currentTribe() || 'cayuse';
    this.built = [];
    if (g.profession === 'granjero') this.site.fertility += D.PROFESSIONS.granjero.farm;
    this.site.fertility += g.flags.farm_bonus || 0;
    CV.story.applyPurposeToSite(g, this);
  }
  neighbor() { return this.site.neighbor; }
  canBuild(key) {
    if (this.built.includes(key)) return [false, 'Ya construido.'];
    const s = this.g.sup;
    for (const [res, n] of Object.entries(D.BUILDINGS[key].cost)) if (s[res] < n) return [false, `Faltan recursos: ${n} de ${res}.`];
    if (key === 'tratado' && this.g.tribes[this.neighbor()].attitude < -35) return [false, 'Los vecinos aún no quieren sentarse a hablar contigo.'];
    if (key === 'puesto' && this.g.tribes[this.neighbor()].attitude < -15) return [false, 'Los vecinos no comerciarían contigo todavía.'];
    return [true, ''];
  }
  build(key) {
    const [ok, why] = this.canBuild(key);
    if (!ok) return [false, why];
    const s = this.g.sup;
    for (const [res, n] of Object.entries(D.BUILDINGS[key].cost)) s[res] -= n;
    this.built.push(key);
    const ts = this.g.tribes[this.neighbor()];
    if (key === 'tratado') { ts.attitude = Math.min(100, ts.attitude + 45); ts.treatyUntil = 1e6; }
    if (key === 'puesto') ts.attitude = Math.min(100, ts.attitude + 10);
    this.g.morale = Math.min(100, this.g.morale + 3);
    return [true, `Construido: ${D.BUILDINGS[key].name}.`];
  }
  simulate(seed) {
    const g = this.g, rng = new CV.RNG(((g.seed || 0) * 31 + this.built.length * 7 + g.day + (seed || 0)) >>> 0);
    const ch = {lines: [], survivors: 0, dead: [], score: 0, rank: '', breakdown: []};
    const site = this.site, ts = g.tribes[this.neighbor()], built = this.built, lines = ch.lines;
    let food = g.sup.food, morale = g.morale;
    const med = g.living().length ? g.best('medic') : 1;
    const farmPlan = built.includes('campos'), harvestMonth = 6;
    const startMonth = g.date().getMonth() + 1;
    const hardship = rng.uniform(.75, 1.3), sheltered = built.includes('cabana');
    const MN = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
    lines.push(`${g.leaderName} planta la bandera en ${site.name}. ${g.living().length} almas empiezan una nueva vida.`);
    for (let m = 0; m < 12; m++) {
      const alive = g.colonists.filter(c => c.alive);
      if (!alive.length) break;
      const mon = (startMonth - 1 + m) % 12, name = MN[mon], cap = name[0].toUpperCase() + name.slice(1);
      const winter = [11, 0, 1, 2].includes(mon);
      const need = alive.length * 36;
      let forage = alive.length * (10 + site.fertility * 2.5) + g.best('hunt') * 10;
      if (built.includes('establo')) forage += 60;
      if (built.includes('puesto')) forage += site.trade * 14;
      if (m >= harvestMonth && farmPlan) forage += alive.length * 18 * (site.fertility / 5) * (1 / hardship);
      if (winter) forage *= .6;
      food += forage - need;
      if (food < 0) {
        food = 0;
        const starve = alive.filter(c => c.group === 'niño' || c.group === 'anciano');
        if (rng.random() < .35) { const v = rng.choice(starve.length ? starve : alive); v.alive = false; v.cause = 'hambruna'; lines.push(`${cap}: el hambre se cobra a ${v.name}.`); morale -= 8; continue; }
        lines.push(`${cap}: se pasa hambre; el pueblo sobrevive a duras penas.`); morale -= 3;
      }
      if (winter && !sheltered) {
        const exposure = (g.wagons.length * 2 >= alive.length ? .2 : .28) * hardship;
        if (rng.random() < exposure) {
          const pool = alive.filter(c => c.group === 'niño' || c.group === 'anciano' || c.health < 70);
          const v = rng.choice(pool.length ? pool : alive); v.alive = false; v.cause = 'frío'; lines.push(`${cap}: sin cabañas, el frío mata a ${v.name}.`); morale -= 10; continue;
        }
      }
      const dp = .07 * hardship * (built.includes('pozo') ? .55 : 1) * (sheltered ? .7 : 1.3) * Math.max(.4, 1 - med / 14);
      if (rng.random() < dp) {
        const v = rng.choice(alive);
        if (rng.random() < .35 + (g.sup.medicine > 0 ? 0 : .15)) {
          if (g.sup.medicine > 0) { g.sup.medicine--; lines.push(`${cap}: ${v.name} enferma, pero las medicinas lo salvan.`); }
          else { v.alive = false; v.cause = 'enfermedad'; lines.push(`${cap}: ${v.name} muere de fiebre.`); morale -= 8; continue; }
        } else lines.push(`${cap}: ${v.name} cae enfermo/a, pero se recupera.`);
      }
      if (ts.attitude < 0 && !built.includes('tratado') && m < 9) {
        const p = .04 + Math.max(0, -ts.attitude) / 100 * .3;
        if (rng.random() < p) {
          const d = site.defense + (built.includes('empalizada') ? 4 : 0) + alive.filter(c => g.canShoot(c)).length * .7;
          const nm = g.tribeName(this.neighbor());
          if (rng.random() < d / (d + 7 + Math.max(0, -ts.attitude) / 12)) { lines.push(`${cap}: una partida de ${nm} ataca el asentamiento y es rechazada.`); ts.attitude -= 5; }
          else {
            food = Math.max(0, food - 80);
            let txt = `${cap}: los ${nm} saquean el almacén (-80 lb de comida).`;
            if (rng.random() < .4) { const v = rng.choice(alive); v.alive = false; v.cause = 'incursión'; txt += ` ${v.name} cae defendiéndolo.`; }
            lines.push(txt); morale -= 8;
          }
        }
      } else if (ts.attitude >= 30 && rng.random() < .3 && m % 3 === 1) { lines.push(`${cap}: los ${g.tribeName(this.neighbor())} visitan el asentamiento con regalos de pesca y ahumados.`); food += 40; morale += 3; }
      if (built.includes('puesto') && rng.random() < .3) g.sup.money += site.trade * 8;
      if (built.includes('iglesia')) morale += 1.5;
      else if (morale < 35 && rng.random() < .3 && alive.length > 4) {
        const pool = alive.filter(c => !c.isLeader), v = rng.choice(pool.length ? pool : alive);
        v.alive = false; v.cause = 'se marchó al oeste'; lines.push(`${cap}: ${v.name}, desmoralizado, se marcha hacia la costa y no vuelve.`); continue;
      }
      if (m === harvestMonth && farmPlan) { lines.push(`${cap}: la primera cosecha llena el granero.`); morale += 6; }
      if (m === 11) {
        const n = g.colonists.filter(c => c.alive).length;
        lines.push(n >= .8 * g.colonists.length && sheltered ? 'Un año después, el humo de las chimeneas sube recto en el aire de la mañana. Los que partieron de Independence ya son vecinos de esta tierra.'
          : n >= .5 * g.colonists.length ? 'Un año después quedan las cruces del primer invierno junto al arroyo, y quienes siguen en pie miran la primavera con cautela.'
          : 'Un año después, el asentamiento es apenas una promesa a medio cumplir. Quedan pocos para sostenerla.');
      }
    }
    const survivors = g.colonists.filter(c => c.alive);
    ch.survivors = survivors.length; ch.dead = g.colonists.filter(c => !c.alive);
    g.sup.food = food; g.morale = Math.max(0, Math.min(100, morale));
    const bd = ch.breakdown;
    bd.push(['Supervivientes', survivors.length * 120]);
    bd.push(['Edificios', built.length * 35]);
    bd.push(['Relación con los vecinos', Math.floor((ts.attitude + 100) / 2)]);
    if (built.includes('tratado')) bd.push(['Tratado de paz', 150]);
    if (ts.allied) bd.push(['Alianza', 80]);
    bd.push(['Comida almacenada', Math.floor(Math.min(400, food) / 8)]);
    bd.push(['Carretas y bienes', g.wagons.length * 10 + g.sup.goods * 3 + Math.floor(g.sup.money / 10)]);
    bd.push(['Moral', Math.floor(g.morale / 2)]);
    bd.push(['Fertilidad y agua del lugar', (site.fertility + site.water) * 4]);
    bd.push(['Llegada temprana', Math.max(0, Math.floor((D.FORCED_WINTER_DAY - g.day) / 3))]);
    const [epi, epiBd] = CV.story.epilogue(g, this);
    lines.push(...epi); bd.push(...epiBd);
    const sub = bd.reduce((a, b) => a + b[1], 0), mult = g.diff.score;
    if (Math.abs(mult - 1) > 1e-6) bd.push([`Dificultad ×${mult}`, Math.floor(sub * mult) - sub]);
    ch.score = Math.floor(sub * mult);
    const frac = survivors.length / Math.max(1, g.colonists.length);
    ch.rank = !survivors.length ? 'Olvidados' : (ch.score >= 1900 && frac >= .9 && ts.attitude >= 40) ? 'Fundadores de leyenda' : (ch.score >= 1450 && frac >= .7) ? 'Pioneros prósperos' : (ch.score >= 1000 && frac >= .5) ? 'Colonos tenaces' : ch.score >= 500 ? 'Supervivientes' : 'Un invierno amargo';
    g.over = true;
    return ch;
  }
}
CV.Settlement = Settlement;
})(globalThis.CV = globalThis.CV || {});
