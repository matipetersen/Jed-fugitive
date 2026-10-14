"""Director de IA: mide la presión que soporta la caravana y ajusta el ritmo del viaje.

No hace trampas a favor ni en contra: sólo decide *cuándo* y *con cuánta dureza* llegan las cosas.
 * Tensión (0-1): hambre, munición, salud, moral, bajas recientes, carretas dañadas, familia descontenta.
 * Viaje: modula la probabilidad de ataques, su fuerza, el reparto de eventos buenos/malos y cuándo
   dejar pasar un capítulo de la historia.
 * Combate: adelanta la siguiente oleada si la anterior ya cayó, y la retrasa un poco si la defensa está desbordada.
Cada dificultad cambia su clemencia (`mercy`). Todo queda anotado en `log` (F3 muestra el panel de depuración).
"""
from __future__ import annotations

from . import data

RELIEF = {"_ev_bison", "_ev_trader", "_ev_news", "_ev_berries", "_ev_road", "_ev_music", "_ev_stranger"}
HARM = {"_ev_wheel", "_ev_ox", "_ev_storm", "_ev_sick", "_ev_lost", "_ev_fire", "_ev_thieves"}


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class Director:
    def __init__(self):
        self.enabled = True
        self.tension = 0.15
        self.raw = 0.15
        self.last_battle_day = -99
        self.last_defeat_day = -99
        self.last_loss_day = -99
        self.lost_seen = 0
        self.story_postponed = 0
        self.log: list[tuple] = []
        self.counts = {"story_delayed": 0, "wave_early": 0, "wave_late": 0}

    # ------------------------------------------------------------ utilidades
    def note(self, g, text: str):
        self.log.append((getattr(g, "day", 0), text))
        del self.log[:-40]

    def mercy(self, g) -> float:
        return data.DIFFICULTY[getattr(g, "difficulty", "normal")].get("mercy", 1.0)

    # ------------------------------------------------------------ medición
    def measure(self, g) -> float:
        living = g.living()
        if not living:
            return 1.0
        need = sum(data.RATIONS[g.rations] * (0.6 if c.group == "niño" else 0.8 if c.group == "anciano" else 1.0) for c in living)
        days_food = g.sup.food / max(0.1, need)
        s = 0.0
        s += 0.32 if days_food < 4 else 0.2 if days_food < 9 else 0.08 if days_food < 16 else 0.0
        s += 0.16 if g.sup.ammo < 25 else 0.07 if g.sup.ammo < 60 else 0.0
        avg_hp = sum(c.health for c in living) / len(living)
        s += 0.16 if avg_hp < 55 else 0.07 if avg_hp < 75 else 0.0
        s += min(0.15, 0.05 * sum(1 for c in living if c.sick))
        s += 0.12 if g.morale < 30 else 0.05 if g.morale < 50 else 0.0
        if g.day - self.last_loss_day <= 8:
            s += 0.18
        if g.day - self.last_battle_day <= 3:
            s += 0.14
        if g.wagons:
            wf = sum(w.hp / w.max_hp for w in g.wagons) / len(g.wagons)
            s += 0.12 if wf < 0.5 else 0.05 if wf < 0.75 else 0.0
        if g.oxen_factor() < 0.7:
            s += 0.1
        fl = g.family_loyalty()
        s += 0.05 if fl < 40 else 0.0
        # presión de calma: cuando todo va bien, la tensión baja del todo
        if s < 0.12 and g.day - self.last_battle_day > 9:
            s -= 0.1
        return clamp(s)

    def update(self, g):
        if not self.enabled:
            return
        lost = g.stats.get("lost", 0)
        if lost > self.lost_seen:
            self.last_loss_day = g.day
            self.lost_seen = lost
        self.raw = self.measure(g)
        self.tension = clamp(0.78 * self.tension + 0.22 * self.raw)

    # ------------------------------------------------------------ viaje
    def raid_mult(self, g) -> float:
        if not self.enabled:
            return 1.0
        t = self.tension
        m = 1.0
        if g.day - self.last_defeat_day <= 6:
            m = 0.2 * (1.0 / self.mercy(g))
            m = min(m, 0.6)
        elif t > 0.75:
            m = 0.45
        elif t > 0.55:
            m = 0.7
        elif t < 0.2 and g.day - self.last_battle_day > 10:
            m = 1.45
        if m < 0.9:
            m = 1.0 - (1.0 - m) * min(1.4, self.mercy(g))
        return max(0.05, m)

    def strength_mult(self, g) -> float:
        """Retoque de la fuerza de un ataque: más dura si vas sobrado, más llevadera si vas justo."""
        if not self.enabled:
            return 1.0
        t = self.tension
        m = 1.12 - 0.3 * t
        if g.day - self.last_defeat_day <= 10:
            m -= 0.08
        if m < 1.0:
            m = 1.0 - (1.0 - m) * self.mercy(g)
        return clamp(m, 0.7, 1.2)

    def reweight(self, g, table: list) -> list:
        """Ajusta la tabla de eventos aleatorios: más alivios con tensión alta, más contratiempos con tensión baja."""
        if not self.enabled:
            return table
        t = self.tension
        out = []
        for fn, w in table:
            name = getattr(fn, "__name__", "")
            if name in RELIEF:
                w = w * (1.0 + 2.0 * t * self.mercy(g))
            elif name in HARM:
                w = w * max(0.2, 1.5 - 1.2 * t * self.mercy(g))
            out.append((fn, w))
        return out

    def allow_story(self, g) -> bool:
        """Pospone un capítulo si la caravana está al límite, pero nunca más de 12 días seguidos."""
        if not self.enabled:
            return True
        if self.tension > 0.72 and self.story_postponed < 12:
            self.story_postponed += 1
            if self.story_postponed == 1:
                self.counts["story_delayed"] += 1
                self.note(g, f"Capítulo pospuesto (tensión {self.tension:.2f})")
            return False
        self.story_postponed = 0
        return True

    def on_raid(self, g, spec_strength: float):
        self.last_battle_day = g.day

    def on_battle_end(self, g, res):
        self.last_battle_day = g.day
        if res.outcome == "derrota":
            self.last_defeat_day = g.day
            self.note(g, "Derrota: periodo de gracia")
        self.update(g)

    # ------------------------------------------------------------ combate
    def battle_pressure(self, b) -> float:
        """0-1: qué desbordada está la defensa ahora mismo."""
        n_w = max(1, len(b.wagons))
        wagons = sum(1 for w in b.wagons if w.destroyed) / n_w
        total = max(1, len(b.colonists))
        down = sum(1 for c in b.colonists if (not c.ref.alive) or c.ref.health < 30) / total
        inside = sum(1 for f in b.foes if f.alive and not f.fled and f.state == "inside")
        ammo = 0.15 if b.game.sup.ammo < 12 else 0.0
        burning = 0.06 * sum(1 for w in b.wagons if w.burning > 0)
        return clamp(0.45 * wagons + 0.45 * down + 0.12 * inside + ammo + burning)

    def wave_decision(self, b, due: float):
        """'now' adelanta la oleada (la anterior ya cayó); 'wait' la retrasa un poco; None sigue el guion."""
        if not self.enabled:
            return None
        ft = b.fight_time
        alive = len(b.alive_foes())
        if ft < due - 18:
            return None
        if ft >= due:
            if self.battle_pressure(b) > 0.55 and b.delays_used < 2 and ft < due + 14:
                b.delays_used += 1
                b.wave_shift += 7.0
                self.counts["wave_late"] += 1
                self.note(b.game, f"Oleada retrasada (presión {self.battle_pressure(b):.2f})")
                return "wait"
            return None
        if b.spawned_total > 0 and alive <= max(1, int(0.2 * b.spawned_total)) and ft - b.last_spawn >= 8 \
                and self.battle_pressure(b) < 0.35:
            self.counts["wave_early"] += 1
            self.note(b.game, "Oleada adelantada: la anterior ya cayó")
            return "now"
        return None
