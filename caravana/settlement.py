"""Fase final: fundar el asentamiento, construir y sobrevivir el primer año."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import data
from .model import Game

MAKESHIFT = dict(name="Campamento de invierno improvisado", extra=0, fertility=3, defense=3, water=4,
                 neighbor="", trade=2,
                 text="Un claro resguardado donde el invierno os ha detenido. No es lo que soñabais, pero es lo que hay.")


@dataclass
class Chronicle:
    lines: list = field(default_factory=list)
    survivors: int = 0
    dead: list = field(default_factory=list)
    score: int = 0
    rank: str = ""
    breakdown: list = field(default_factory=list)


class Settlement:
    def __init__(self, game: Game, site_id: str):
        self.game = game
        self.site_id = site_id
        self.site = dict(MAKESHIFT) if site_id == "improvisado" else dict(data.SITES[site_id])
        if site_id == "improvisado":
            self.site["neighbor"] = game.current_tribe() or "cayuse"
        self.built: set[str] = set()
        self.notes: list[str] = []
        if game.profession == "granjero":
            self.site["fertility"] += data.PROFESSIONS["granjero"]["farm"]

    @property
    def neighbor(self) -> str:
        return self.site["neighbor"]

    def cost_of(self, key: str) -> dict:
        return dict(data.BUILDINGS[key]["cost"])

    def can_build(self, key: str) -> tuple[bool, str]:
        if key in self.built:
            return False, "Ya construido."
        s = self.game.sup
        for res, n in self.cost_of(key).items():
            if getattr(s, res) < n:
                return False, f"Faltan recursos: {n} de {res}."
        if key == "tratado" and self.game.tribes[self.neighbor].attitude < -35:
            return False, "Los vecinos aún no quieren sentarse a hablar contigo."
        if key == "puesto" and self.game.tribes[self.neighbor].attitude < -15:
            return False, "Los vecinos no comerciarían contigo todavía."
        return True, ""

    def build(self, key: str) -> tuple[bool, str]:
        ok, why = self.can_build(key)
        if not ok:
            return False, why
        s = self.game.sup
        for res, n in self.cost_of(key).items():
            setattr(s, res, getattr(s, res) - n)
        self.built.add(key)
        ts = self.game.tribes[self.neighbor]
        if key == "tratado":
            ts.attitude = min(100, ts.attitude + 45)
            ts.treaty_until = 10 ** 6
        if key == "puesto":
            ts.attitude = min(100, ts.attitude + 10)
        self.game.morale = min(100, self.game.morale + 3)
        return True, f"Construido: {data.BUILDINGS[key]['name']}."

    # ------------------------------------------------------------ el primer año
    def simulate(self, seed: int = 0) -> Chronicle:
        g = self.game
        rng = random.Random((g.seed or 0) * 31 + len(self.built) * 7 + g.day + seed)
        ch = Chronicle()
        site = self.site
        pop = g.living()
        lines = ch.lines
        ts = g.tribes[self.neighbor]
        built = self.built
        food = g.sup.food
        morale = g.morale
        med = g.best("medic") if pop else 1
        farm_plan = "campos" in built
        harvest_month = 6
        month_names = ["octubre", "noviembre", "diciembre", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                       "julio", "agosto", "septiembre"]
        start_month = g.date().month
        raided = 0
        lost_goods = 0
        hardship = rng.uniform(0.75, 1.3)
        sheltered = "cabana" in built
        lines.append(f"{g.leader_name} planta la bandera en {site['name']}. {len(pop)} almas empiezan una nueva vida.")
        for m in range(12):
            alive = [c for c in g.colonists if c.alive]
            if not alive:
                break
            mon = (start_month - 1 + m) % 12
            name = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                    "octubre", "noviembre", "diciembre"][mon]
            winter = mon in (11, 0, 1, 2)
            # consumo
            need = len(alive) * 36.0
            forage = len(alive) * (10 + site["fertility"] * 2.5) + (g.best("hunt") * 10)
            if "establo" in built:
                forage += 60
            if "puesto" in built:
                forage += site["trade"] * 14
            if m >= harvest_month and farm_plan:
                forage += len(alive) * 18 * (site["fertility"] / 5.0) * (1.0 / hardship)
            if winter:
                forage *= 0.6
            food += forage - need
            if food < 0:
                food = 0
                starve = [c for c in alive if c.group in ("niño", "anciano")] or alive
                if rng.random() < 0.35:
                    v = rng.choice(starve)
                    v.alive = False
                    v.cause = "hambruna"
                    lines.append(f"{name.capitalize()}: el hambre se cobra a {v.name}.")
                    morale -= 8
                    continue
                lines.append(f"{name.capitalize()}: se pasa hambre; el pueblo sobrevive a duras penas.")
                morale -= 3
            # frío
            if winter and not sheltered:
                exposure = (0.2 if len(g.wagons) * 2 >= len(alive) else 0.28) * hardship
                if rng.random() < exposure:
                    v = rng.choice([c for c in alive if c.group in ("niño", "anciano") or c.health < 70] or alive)
                    v.alive = False
                    v.cause = "frío"
                    lines.append(f"{name.capitalize()}: sin cabañas, el frío mata a {v.name}.")
                    morale -= 10
                    continue
            # enfermedad
            dp = 0.07 * hardship * (0.55 if "pozo" in built else 1.0) * (0.7 if sheltered else 1.3) * max(0.4, 1 - med / 14)
            if rng.random() < dp:
                v = rng.choice(alive)
                if rng.random() < 0.35 + (0.0 if g.sup.medicine > 0 else 0.15):
                    if g.sup.medicine > 0:
                        g.sup.medicine -= 1
                        lines.append(f"{name.capitalize()}: {v.name} enferma, pero las medicinas lo salvan.")
                    else:
                        v.alive = False
                        v.cause = "enfermedad"
                        lines.append(f"{name.capitalize()}: {v.name} muere de fiebre.")
                        morale -= 8
                        continue
                else:
                    lines.append(f"{name.capitalize()}: {v.name} cae enfermo/a, pero se recupera.")
            # vecinos
            if ts.attitude < 0 and "tratado" not in built and m < 9:
                p = 0.04 + max(0, -ts.attitude) / 100 * 0.3
                if rng.random() < p:
                    raided += 1
                    d = site["defense"] + (4 if "empalizada" in built else 0) + len([c for c in alive if c.can_shoot]) * 0.7
                    nm = g.tribe_name(self.neighbor)
                    if rng.random() < d / (d + 7 + max(0, -ts.attitude) / 12):
                        lines.append(f"{name.capitalize()}: una partida de {nm} ataca el asentamiento y es rechazada.")
                        ts.attitude -= 5
                    else:
                        loss = rng.randint(2, 6)
                        food = max(0, food - 80)
                        lost_goods += loss
                        v = rng.choice(alive) if rng.random() < 0.4 else None
                        txt = f"{name.capitalize()}: los {nm} saquean el almacén (-80 lb de comida)."
                        if v:
                            v.alive = False
                            v.cause = "incursión"
                            txt += f" {v.name} cae defendiéndolo."
                        lines.append(txt)
                        morale -= 8
            elif ts.attitude >= 30 and rng.random() < 0.3 and m % 3 == 1:
                lines.append(f"{name.capitalize()}: los {g.tribe_name(self.neighbor)} visitan el asentamiento con regalos de pesca y ahumados.")
                food += 40
                morale += 3
            if "puesto" in built and rng.random() < 0.3:
                g.sup.money += site["trade"] * 8
            if "iglesia" in built:
                morale += 1.5
            elif morale < 35 and rng.random() < 0.3 and len(alive) > 4:
                v = rng.choice([c for c in alive if not c.is_leader] or alive)
                v.alive = False
                v.cause = "se marchó al oeste"
                lines.append(f"{name.capitalize()}: {v.name}, desmoralizado, se marcha hacia la costa y no vuelve.")
                continue
            if m == harvest_month and farm_plan:
                lines.append(f"{name.capitalize()}: la primera cosecha llena el granero.")
                morale += 6
            if m == 11:
                n_alive = len([c for c in g.colonists if c.alive])
                if n_alive >= 0.8 * len(g.colonists) and sheltered:
                    lines.append("Un año después, el humo de las chimeneas sube recto en el aire de la mañana. Los que partieron de Independence ya son vecinos de esta tierra.")
                elif n_alive >= 0.5 * len(g.colonists):
                    lines.append("Un año después quedan las cruces del primer invierno junto al arroyo, y quienes siguen en pie miran la primavera con cautela.")
                else:
                    lines.append("Un año después, el asentamiento es apenas una promesa a medio cumplir. Quedan pocos para sostenerla.")
        # recuento
        survivors = [c for c in g.colonists if c.alive]
        ch.survivors = len(survivors)
        ch.dead = [c for c in g.colonists if not c.alive]
        g.sup.food = food
        g.morale = max(0, min(100, morale))
        # puntuación
        bd = []
        bd.append(("Supervivientes", len(survivors) * 120))
        bd.append(("Edificios", len(built) * 35))
        bd.append(("Relación con los vecinos", int((ts.attitude + 100) / 2)))
        if "tratado" in built:
            bd.append(("Tratado de paz", 150))
        if ts.allied:
            bd.append(("Alianza", 80))
        bd.append(("Comida almacenada", int(min(400, food) / 8)))
        bd.append(("Carretas y bienes", len(g.wagons) * 10 + g.sup.goods * 3 + int(g.sup.money / 10)))
        bd.append(("Moral", int(g.morale / 2)))
        bd.append(("Fertilidad y agua del lugar", (site["fertility"] + site["water"]) * 4))
        early = max(0, int((data.FORCED_WINTER_DAY - g.day) / 3))
        bd.append(("Llegada temprana", early))
        subtotal = sum(v for _, v in bd)
        mult = g.diff["score"]
        if abs(mult - 1.0) > 1e-6:
            bd.append((f"Dificultad ×{mult:g}", int(subtotal * mult) - subtotal))
        ch.breakdown = bd
        ch.score = int(subtotal * mult)
        total_pop = len(g.colonists)
        frac = len(survivors) / max(1, total_pop)
        if not survivors:
            ch.rank = "Olvidados"
        elif ch.score >= 1900 and frac >= 0.9 and ts.attitude >= 40:
            ch.rank = "Fundadores de leyenda"
        elif ch.score >= 1450 and frac >= 0.7:
            ch.rank = "Pioneros prósperos"
        elif ch.score >= 1000 and frac >= 0.5:
            ch.rank = "Colonos tenaces"
        elif ch.score >= 500:
            ch.rank = "Supervivientes"
        else:
            ch.rank = "Un invierno amargo"
        g.over = True
        return ch
