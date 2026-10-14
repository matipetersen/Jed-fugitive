/* Director de IA: mide la tensión de la caravana y ajusta el ritmo. Espejo de caravana/director.py */
(function (CV) {
'use strict';
const D = CV.data, clamp = CV.clamp;
const RELIEF = ['bison', 'trader', 'news', 'berries', 'road', 'music', 'stranger'];
const HARM = ['wheel', 'ox', 'storm', 'sick', 'lost', 'fire', 'thieves'];

class Director {
  constructor() {
    this.enabled = true; this.tension = .15; this.raw = .15;
    this.lastBattleDay = -99; this.lastDefeatDay = -99; this.lastLossDay = -99; this.lostSeen = 0;
    this.storyPostponed = 0; this.log = [];
    this.counts = {story_delayed: 0, wave_early: 0, wave_late: 0};
  }
  note(g, t) { this.log.push([g.day, t]); if (this.log.length > 40) this.log.shift(); }
  mercy(g) { return D.DIFFICULTY[g.difficulty || 'normal'].mercy; }
  measure(g) {
    const living = g.living();
    if (!living.length) return 1;
    const daysFood = g.sup.food / Math.max(.1, g.dailyNeed());
    let s = 0;
    s += daysFood < 4 ? .32 : daysFood < 9 ? .2 : daysFood < 16 ? .08 : 0;
    s += g.sup.ammo < 25 ? .16 : g.sup.ammo < 60 ? .07 : 0;
    const avg = living.reduce((a, c) => a + c.health, 0) / living.length;
    s += avg < 55 ? .16 : avg < 75 ? .07 : 0;
    s += Math.min(.15, .05 * living.filter(c => c.sick).length);
    s += g.morale < 30 ? .12 : g.morale < 50 ? .05 : 0;
    if (g.day - this.lastLossDay <= 8) s += .18;
    if (g.day - this.lastBattleDay <= 3) s += .14;
    if (g.wagons.length) { const wf = g.wagons.reduce((a, w) => a + w.hp / w.maxHp, 0) / g.wagons.length; s += wf < .5 ? .12 : wf < .75 ? .05 : 0; }
    if (g.oxenFactor() < .7) s += .1;
    if (g.familyLoyalty() < 40) s += .05;
    if (s < .12 && g.day - this.lastBattleDay > 9) s -= .1;
    return clamp(s, 0, 1);
  }
  update(g) {
    if (!this.enabled) return;
    if (g.stats.lost > this.lostSeen) { this.lastLossDay = g.day; this.lostSeen = g.stats.lost; }
    this.raw = this.measure(g);
    this.tension = clamp(.78 * this.tension + .22 * this.raw, 0, 1);
  }
  raidMult(g) {
    if (!this.enabled) return 1;
    const t = this.tension; let m = 1;
    if (g.day - this.lastDefeatDay <= 6) m = Math.min(.2 / this.mercy(g), .6);
    else if (t > .75) m = .45; else if (t > .55) m = .7;
    else if (t < .2 && g.day - this.lastBattleDay > 10) m = 1.45;
    if (m < .9) m = 1 - (1 - m) * Math.min(1.4, this.mercy(g));
    return Math.max(.05, m);
  }
  strengthMult(g) {
    if (!this.enabled) return 1;
    let m = 1.12 - .3 * this.tension;
    if (g.day - this.lastDefeatDay <= 10) m -= .08;
    if (m < 1) m = 1 - (1 - m) * this.mercy(g);
    return clamp(m, .7, 1.2);
  }
  reweight(g, table) {
    if (!this.enabled) return table;
    const t = this.tension;
    return table.map(([k, w]) => [k, RELIEF.includes(k) ? w * (1 + 2 * t * this.mercy(g)) : HARM.includes(k) ? w * Math.max(.2, 1.5 - 1.2 * t * this.mercy(g)) : w]);
  }
  allowStory(g) {
    if (!this.enabled) return true;
    if (this.tension > .72 && this.storyPostponed < 12) {
      this.storyPostponed++;
      if (this.storyPostponed === 1) { this.counts.story_delayed++; this.note(g, `Capítulo pospuesto (tensión ${this.tension.toFixed(2)})`); }
      return false;
    }
    this.storyPostponed = 0; return true;
  }
  onBattleEnd(g, res) {
    this.lastBattleDay = g.day;
    if (res.outcome === 'derrota') { this.lastDefeatDay = g.day; this.note(g, 'Derrota: periodo de gracia'); }
    this.update(g);
  }
  battlePressure(b) {
    const nw = Math.max(1, b.wagons.length), w = b.wagons.filter(x => x.destroyed).length / nw;
    const tot = Math.max(1, b.colonists.length);
    const down = b.colonists.filter(c => !c.ref.alive || c.ref.health < 30).length / tot;
    const inside = b.foes.filter(f => f.alive && !f.fled && f.state === 'inside').length;
    const ammo = b.game.sup.ammo < 12 ? .15 : 0, burning = .06 * b.wagons.filter(x => x.burning > 0).length;
    return clamp(.45 * w + .45 * down + .12 * inside + ammo + burning, 0, 1);
  }
  waveDecision(b, due) {
    if (!this.enabled) return null;
    const ft = b.fightTime, alive = b.aliveFoes().length;
    if (ft < due - 18) return null;
    if (ft >= due) {
      if (this.battlePressure(b) > .55 && b.delaysUsed < 2 && ft < due + 14) {
        b.delaysUsed++; b.waveShift += 7; this.counts.wave_late++;
        this.note(b.game, `Oleada retrasada (presión ${this.battlePressure(b).toFixed(2)})`); return 'wait';
      }
      return null;
    }
    if (b.spawnedTotal > 0 && alive <= Math.max(1, Math.floor(.2 * b.spawnedTotal)) && ft - b.lastSpawn >= 8 && this.battlePressure(b) < .35) {
      this.counts.wave_early++; this.note(b.game, 'Oleada adelantada: la anterior ya cayó'); return 'now';
    }
    return null;
  }
}
CV.Director = Director;
})(globalThis.CV = globalThis.CV || {});
