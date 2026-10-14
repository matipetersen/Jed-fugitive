"""Modelo de juego de LA CARAVANA (sin pygame): estado, viaje, eventos y diplomacia."""
from __future__ import annotations

import datetime
import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from . import data
from .director import Director


# ====================================================================== Estructuras
@dataclass
class Colonist:
    cid: int
    name: str
    group: str  # adulto | joven | niño | anciano
    shoot: int = 3
    medic: int = 2
    build: int = 3
    talk: int = 3
    hunt: int = 3
    health: float = 100.0
    sick: str = ""
    alive: bool = True
    post: Optional[tuple] = None  # (indice_carreta, 'tirador'|'ayuda')
    is_leader: bool = False
    kills: int = 0
    cause: str = ""
    role_id: str = ""      # personaje de la historia ('esposa', 'hijo', ...)
    loyalty: int = 50      # 0-100: confianza en el líder
    trait: str = ""
    bio: str = ""

    @property
    def can_shoot(self) -> bool:
        return self.alive and self.group in ("adulto", "joven") and self.health > 20

    @property
    def role_label(self) -> str:
        if self.is_leader:
            return "Líder"
        if self.role_id and "_" not in self.role_id and self.role_id in data.ROLE_NAMES:
            return data.ROLE_NAMES[self.role_id]
        return {"adulto": "Adulto", "joven": "Joven", "niño": "Niño/a", "anciano": "Anciano/a"}[self.group]


@dataclass
class Wagon:
    hp: float = 240.0
    max_hp: float = 240.0
    reinforced: int = 0
    platform: bool = False
    lantern: bool = False
    cannon: bool = False

    def reinforce(self):
        self.reinforced += 1
        self.max_hp += 120
        self.hp += 120


@dataclass
class Supplies:
    food: float = 0
    ammo: int = 0
    goods: int = 0
    parts: int = 0
    medicine: int = 0
    oxen: int = 0
    money: float = 0


@dataclass
class TribeState:
    attitude: float = 0.0
    treaty_until: int = -1
    allied: bool = False
    arms: float = 0.0  # armamento que les hemos dado/vendido
    met: bool = False
    kills: int = 0
    last_raid: int = -99
    raids: int = 0
    first_contact_done: bool = False


@dataclass
class Option:
    label: str
    action: Callable[[], Any]
    hint: str = ""
    who: tuple = ()        # nombres de quienes respaldan esta opción


@dataclass
class Prompt:
    title: str
    body: str
    options: list = field(default_factory=list)
    tone: str = "info"  # info | good | danger

    @staticmethod
    def info(title: str, body: str, tone: str = "info", then: Optional[Callable[[], Any]] = None) -> "Prompt":
        return Prompt(title, body, [Option("Continuar", then or (lambda: None))], tone)


@dataclass
class Beat:
    """Una viñeta de cutscene: fondo, quién habla, qué dice y quién está en escena."""
    bg: str
    text: str
    speaker: str = ""      # id de personaje; "" = narrador; "tu" = el protagonista (de espaldas)
    mood: str = "neutral"  # neutral | alegre | risa | triste | enojado | miedo
    cast: tuple = ()       # ids de personajes en escena, de izquierda a derecha
    fx: str = ""           # "", "shake", "flash", "fade"


@dataclass
class CutsceneSpec:
    title: str
    beats: list
    then: Optional[Callable[[], Any]] = None


@dataclass
class BattleSpec:
    foe: str  # id de tribu o 'bandidos'
    strength: float
    night: bool = False
    prep_time: float = 25.0
    waves: list = field(default_factory=list)  # (t, angulo, {tipo: n})
    allies: int = 0
    reason: str = ""
    tense: bool = False  # si hubo oportunidad de parlamentar


@dataclass
class ContactSpec:
    tribe: str
    kind: str  # visit | patrol | tense
    prep_text: str = ""


@dataclass
class ShopSpec:
    name: str
    mult: float = 1.0
    cannon: bool = False
    barter_tribe: Optional[str] = None
    wagons: bool = True
    inventory: Optional[dict] = None  # para comerciantes ambulantes: item -> unidades


@dataclass
class ArrivalSpec:
    waypoint: dict


@dataclass
class ForkSpec:
    pass


@dataclass
class EndSpec:
    title: str
    body: str
    victory: bool = False


@dataclass
class BattleResult:
    outcome: str = "victoria"  # victoria | huida | paz | derrota
    foes_killed: int = 0
    foes_total: int = 0
    dead: list = field(default_factory=list)
    wagons_lost: int = 0
    ammo_used: int = 0
    time: float = 0.0
    loot_text: str = ""
    parley_gift: int = 0


# ====================================================================== Juego
class Game:
    def __init__(self, seed: Optional[int] = None):
        self.difficulty = "normal"
        self.seed = seed
        self.rng = random.Random(seed)
        self.day = 0
        self.mile = 0.0
        self.colonists: list[Colonist] = []
        self.wagons: list[Wagon] = []
        self.sup = Supplies()
        self.pace = "normal"
        self.rations = "normales"
        self.watch = "normal"
        self.morale = 75.0
        self.weather = "despejado"
        self.leader_name = "Jed"
        self.profession = "granjero"
        self.tribes: dict[str, TribeState] = {k: TribeState() for k in data.TRIBES}
        self.journal: list[tuple[int, str]] = []
        self.notices: list[str] = []
        self.visited: set[str] = {"Independence"}
        self.next_wp = 1
        self.guide_until = -1.0
        self.guide_tribe = ""
        self.last_bandit_day = -99
        self.stats = dict(raids=0, kills=0, parleys=0, gifts=0, hunted=0.0, lost=0, treaties=0)
        self.next_cid = 0
        self.cannon_stock = 0
        self.over = False
        self.arrived_site: Optional[str] = None
        self.forced_winter = False
        self.starving = False
        self.flags: dict = {}
        self.story_done: set = set()
        self.talked: dict = {}
        self.director = Director()

    def __setstate__(self, state):
        self.__dict__.update(state)
        if "director" not in state:
            self.director = Director()
        for k, v in (("flags", {}), ("story_done", set()), ("talked", {}), ("difficulty", "normal")):
            if k not in state:
                setattr(self, k, v)

    # ------------------------------------------------------------ creación
    @classmethod
    def new(cls, leader_name: str = "Jed", profession: str = "granjero", seed: Optional[int] = None,
            difficulty: str = "normal") -> "Game":
        g = cls(seed)
        g.difficulty = difficulty
        g.leader_name = leader_name or "Jed"
        g.profession = profession
        prof = data.PROFESSIONS[profession]
        g.sup.money = float(prof["money"]) * data.DIFFICULTY[difficulty]["money"]
        rng = g.rng

        leader = g._make("adulto", g.leader_name, **prof["skills"])
        leader.is_leader = True
        leader.role_id = "lider"
        from . import story
        story.populate(g)

        g.wagons = [Wagon() for _ in range(7)]
        g.sup.oxen = 14
        if profession == "carpintero":
            for w in g.wagons[:3]:
                w.reinforce()
        g.sup.ammo = 40 if profession == "soldado" else 0
        starts = dict(pawnee=5, cheyenne=0, lakota=-10, shoshone=10, cayuse=8, kalapuya=10, chinook=10)
        for k, v in starts.items():
            g.tribes[k].attitude = float(v)
        if profession == "soldado":
            for k in ("pawnee", "cheyenne", "lakota", "shoshone", "cayuse"):
                g.tribes[k].attitude -= 8
        if profession == "comerciante":
            for k in g.tribes:
                g.tribes[k].attitude += 5
        g.auto_assign()
        g.log(f"La caravana de {g.leader_name} parte de Independence, Misuri.")
        return g

    def _make(self, group, name, **skills) -> Colonist:
        base = dict(shoot=3, medic=2, build=3, talk=3, hunt=3)
        base.update(skills)
        c = Colonist(self.next_cid, name, group, **base)
        self.next_cid += 1
        self.colonists.append(c)
        return c

    # ------------------------------------------------------------ utilidades
    def log(self, text: str):
        self.journal.append((self.day, text))

    def note(self, text: str):
        self.notices.append(text)
        self.log(text)

    def date(self) -> datetime.date:
        return data.START_DATE + datetime.timedelta(days=self.day)

    def date_text(self) -> str:
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                 "septiembre", "octubre", "noviembre", "diciembre"]
        d = self.date()
        return f"{d.day} de {meses[d.month - 1]} de {d.year}"

    def by_role(self, role: str) -> Optional[Colonist]:
        for c in self.colonists:
            if c.role_id == role:
                return c
        return None

    def member(self, role: str) -> Optional[Colonist]:
        c = self.by_role(role)
        return c if c is not None and c.alive else None

    def family_loyalty(self) -> float:
        fam = [c.loyalty for c in self.living() if c.role_id in data.FAMILY_ROLES]
        return sum(fam) / len(fam) if fam else 50.0

    def living(self) -> list[Colonist]:
        return [c for c in self.colonists if c.alive]

    def dead(self) -> list[Colonist]:
        return [c for c in self.colonists if not c.alive]

    def tribe_at(self, mile: float) -> Optional[str]:
        for a, b, t in data.TERRITORIES:
            if a <= mile < b:
                return t
        return None

    def terrain(self, mile: Optional[float] = None) -> str:
        m = self.mile if mile is None else mile
        if m < 280:
            return "pradera"
        if m < 640:
            return "llanura"
        if m < 900:
            return "estepa"
        if m < 1100:
            return "montaña"
        if m < 1500:
            return "desierto"
        if m < 1650:
            return "cañón"
        if m < 1900:
            return "bosque"
        return "valle"

    def in_mountains(self) -> bool:
        return 900 <= self.mile < 1100 or 1650 <= self.mile < 1900

    def next_waypoint(self) -> Optional[dict]:
        if self.next_wp < len(data.WAYPOINTS):
            return data.WAYPOINTS[self.next_wp]
        return None

    def miles_to_next(self) -> float:
        wp = self.next_waypoint()
        return max(0.0, wp["mile"] - self.mile) if wp else 0.0

    def has_guide(self) -> bool:
        return self.mile < self.guide_until and self.day >= 0

    def best(self, skill: str) -> int:
        vals = [getattr(c, skill) for c in self.living() if c.group != "niño"]
        return max(vals) if vals else 1

    def shooters(self) -> list[Colonist]:
        return [c for c in self.living() if c.can_shoot]

    # ------------------------------------------------------------ puestos
    def normalize_posts(self):
        n = len(self.wagons)
        used = set()
        for c in self.colonists:
            if c.post and (not c.alive or c.post[0] >= n or c.post in used):
                c.post = None
            elif c.post:
                used.add(c.post)

    def auto_assign(self, threat: Optional[dict] = None):
        """Mejores tiradores a las carretas (las más amenazadas primero); ayudantes después."""
        for c in self.colonists:
            c.post = None
        n = len(self.wagons)
        order = [i for i in range(n) if self.wagons[i].hp > 0]
        if not order:
            return
        threat = threat or {}
        order.sort(key=lambda i: (-(threat.get(i, 0.0)), not self.wagons[i].cannon, i))
        sh = sorted([c for c in self.living() if c.can_shoot], key=lambda c: -c.shoot)
        rest = [c for c in self.living() if c not in sh]
        for i in order:
            if sh:
                sh.pop(0).post = (i, "tirador")
        helpers = sh + sorted(rest, key=lambda c: (c.group == "niño", -c.build))
        for i, h in zip(order, helpers):
            h.post = (i, "ayuda")

    def post_of(self, wagon: int, slot: str) -> Optional[Colonist]:
        for c in self.living():
            if c.post == (wagon, slot):
                return c
        return None

    def assign(self, colonist: Colonist, wagon: int, slot: str) -> bool:
        if wagon >= len(self.wagons):
            return False
        if slot == "tirador" and not colonist.can_shoot:
            return False
        other = self.post_of(wagon, slot)
        if other and other is not colonist:
            other.post = colonist.post
            if other.post and other.post[1] == "tirador" and not other.can_shoot:
                other.post = None
        colonist.post = (wagon, slot)
        return True

    # ------------------------------------------------------------ tienda
    def price(self, item: str, mult: float = 1.0, selling: bool = False) -> float:
        base = data.ITEMS[item][2]
        if self.profession == "comerciante":
            mult *= 0.88
        p = base * mult
        if selling:
            return round(p * data.SELL_FACTOR, 2)
        return round(p, 2)

    def stock_of(self, item: str) -> int:
        s = self.sup
        per = data.ITEMS[item][3]
        if item == "wagon":
            return len(self.wagons)
        if item == "cannon":
            return self.cannon_stock
        return int(getattr(s, {"food": "food", "ammo": "ammo", "goods": "goods", "parts": "parts",
                               "medicine": "medicine", "oxen": "oxen"}[item]) // per)

    def buy(self, item: str, mult: float = 1.0, qty: int = 1) -> tuple[bool, str]:
        cost = self.price(item, mult) * qty
        if cost > self.sup.money + 1e-6:
            return False, "No tienes dinero suficiente."
        if item == "wagon" and len(self.wagons) + qty > 12:
            return False, "Un círculo de más de 12 carretas es inmanejable."
        self.sup.money -= cost
        per = data.ITEMS[item][3]
        if item == "wagon":
            for _ in range(qty):
                self.wagons.append(Wagon())
        elif item == "cannon":
            self.cannon_stock += qty
        else:
            attr = item
            setattr(self.sup, attr, getattr(self.sup, attr) + per * qty)
        return True, f"Compras {qty} × {data.ITEMS[item][0]} por ${cost:.0f}."

    def sell(self, item: str, mult: float = 1.0, qty: int = 1) -> tuple[bool, str]:
        if item == "wagon":
            if len(self.wagons) <= 3:
                return False, "No puedes quedarte con menos de 3 carretas."
            for _ in range(qty):
                self.wagons.pop()
            self.normalize_posts()
        elif item == "cannon":
            if self.cannon_stock < qty:
                return False, "No tienes cañones en el almacén."
            self.cannon_stock -= qty
        else:
            per = data.ITEMS[item][3]
            have = getattr(self.sup, item)
            if have < per * qty:
                return False, "No tienes tanto para vender."
            setattr(self.sup, item, have - per * qty)
        gain = self.price(item, mult, True) * qty
        self.sup.money += gain
        return True, f"Vendes {qty} × {data.ITEMS[item][0]} por ${gain:.0f}."

    # ------------------------------------------------------------ cálculos de viaje
    def oxen_factor(self) -> float:
        need = max(1, 2 * len(self.wagons))
        return min(1.0, self.sup.oxen / need)

    def update_weather(self):
        m = self.date().month
        r = self.rng.random()
        w = "despejado"
        if m in (4, 5, 6):
            w = "tormenta" if r < 0.08 else "lluvia" if r < 0.28 else "despejado"
        elif m in (7, 8):
            w = "calor" if r < 0.22 else "tormenta" if r < 0.27 else "despejado"
        elif m in (9, 10):
            w = "nieve" if (r < 0.10 and self.in_mountains()) else "lluvia" if r < 0.25 else "despejado"
        else:
            w = "nieve" if r < 0.40 else "frío"
        self.weather = w

    def travel_speed(self) -> float:
        base = data.PACES[self.pace]
        wf = dict(despejado=1.0, lluvia=0.8, tormenta=0.5, calor=0.9, nieve=0.55, frío=0.8)[self.weather]
        tf = 0.78 if self.terrain() in ("montaña", "bosque", "cañón") else 1.0
        sick = [c for c in self.living() if c.sick]
        sf = 1.0 - min(0.3, 0.04 * len(sick))
        wag = 1.0 if all(w.hp > 40 for w in self.wagons) else 0.85
        return base * wf * tf * sf * wag * self.oxen_factor()

    # ------------------------------------------------------------ día de viaje
    def advance_day(self) -> Optional[Any]:
        """Avanza un día. Devuelve una interrupción (Prompt/Spec) o None."""
        if self.over:
            return None
        self.day += 1
        self.update_weather()

        end = self._check_winter()
        if end:
            return end

        wp = self.next_waypoint()
        miles = self.travel_speed()
        stuck = miles < 1.0
        if stuck:
            self.note("Sin bueyes suficientes, las carretas no pueden avanzar. Necesitas comprar o comerciar bueyes.")
            miles = 0
        arrived = None
        if wp and self.mile + miles >= wp["mile"]:
            miles = wp["mile"] - self.mile
            arrived = wp
        self.mile += miles

        self._daily_upkeep()
        died = self._daily_health()
        self.director.update(self)
        self._desertions()
        self.wagons_wear(miles)
        if not self.living():
            return self._game_over("La caravana ha perecido por completo en el camino.")

        if died:
            names = ", ".join(c.name for c in died)
            return Prompt.info("Luto en la caravana",
                               f"{names} no sobrevivió. Se cava una tumba junto al camino y se reza en silencio.",
                               "danger")

        if arrived:
            self.next_wp += 1
            self.visited.add(arrived["name"])
            return self.arrival_interrupt(arrived)

        # historia familiar
        from . import story
        evt = story.check(self, scenes=True)
        if evt:
            return evt
        # eventos
        evt = self._roll_tribe_events()
        if evt:
            return evt
        evt = self._roll_bandits()
        if evt:
            return evt
        return self._roll_random_event()

    def arrival_interrupt(self, wp: dict) -> Any:
        kind = wp["kind"]
        self.log(f"Se llega a {wp['name']}.")
        if kind == "river":
            return self.river_prompt(wp)
        if kind == "mountain":
            return self.mountain_prompt(wp)
        if kind == "fork":
            return ForkSpec()
        if kind == "post":
            return ArrivalSpec(wp)
        self.morale = min(100, self.morale + 5)
        return Prompt.info(wp["name"], wp["text"] + " La moral sube al ver el hito.", "good")

    def _desertions(self):
        for c in self.living():
            if c.trait == "mercenario" and c.loyalty < 25 and self.rng.random() < 0.05:
                c.alive = False
                c.cause = "desertó"
                c.post = None
                g_ = min(self.sup.goods, 3)
                self.sup.goods -= g_
                self.sup.ammo = max(0, self.sup.ammo - 15)
                self.stats["lost"] += 1
                self.normalize_posts()
                self.note(f"{c.name} desaparece de madrugada con 15 balas y {g_} mercancías.")

    def wagons_wear(self, miles: float):
        for w in self.wagons:
            if miles > 0 and self.rng.random() < 0.01:
                w.hp = max(10.0, w.hp - self.rng.randint(5, 20))

    def _check_winter(self) -> Optional[Any]:
        if self.day >= data.FORCED_WINTER_DAY and not self.forced_winter and self.mile < data.TRAIL_END:
            self.forced_winter = True
            return Prompt(
                "El invierno os alcanza",
                "Las primeras nevadas cierran los pasos. Es imposible continuar: hay que fundar aquí "
                "con lo que se tiene, en un lugar improvisado.",
                [Option("Fundar el asentamiento aquí", lambda: ForkSpec())], "danger")
        return None

    def _daily_upkeep(self):
        living = self.living()
        ration = data.RATIONS[self.rations]
        need = sum(ration * (0.6 if c.group == "niño" else 0.8 if c.group == "anciano" else 1.0) for c in living)
        if self.sup.food >= need:
            self.sup.food -= need
            self.starving = False
        else:
            self.sup.food = 0
            self.starving = True
            self.note("¡La comida se ha agotado! Todos pasan hambre.")
            self.morale = max(0, self.morale - 4)
        # recuperación de moral
        target = (70 + (self.family_loyalty() - 50) / 8.0 + (3 if self.member("predicador") else 0)) if not self.starving else 20
        self.morale += (target - self.morale) * 0.02
        if self.pace == "rapido":
            self.morale -= 0.5
        if self.rations == "abundantes":
            self.morale += 0.5
        self.morale = max(0.0, min(100.0, self.morale))

    def _daily_health(self, resting: bool = False) -> list[Colonist]:
        died = []
        medic = self.best("medic") if self.living() else 1
        ration_d = dict(escasas=-1.6, normales=0.4, abundantes=1.4)[self.rations]
        pace_d = dict(lento=0.6, normal=0.0, rapido=-1.0)[self.pace]
        weather_d = dict(despejado=0, lluvia=-0.3, tormenta=-0.8, calor=-0.6, nieve=-1.2, frío=-0.7)[self.weather]
        if resting:
            pace_d = 1.5
        for c in self.living():
            d = ration_d + pace_d + weather_d
            if self.starving:
                d -= 4
            if c.sick:
                d -= 3.0
                if self.sup.medicine > 0 and c.health < 45:
                    self.sup.medicine -= 1
                    c.health += 25
                    self.note(f"{c.name} recibe medicinas contra {c.sick}.")
                    d += 2
                p_rec = 0.10 + 0.02 * medic + (0.08 if resting else 0)
                if self.profession == "medico":
                    p_rec += 0.08
                if self.rng.random() < p_rec:
                    self.note(f"{c.name} se ha recuperado de {c.sick}.")
                    c.sick = ""
            else:
                p = 0.004 + (0.006 if self.rations == "escasas" else 0) + (0.003 if self.pace == "rapido" else 0)
                p += 0.003 if self.weather in ("lluvia", "tormenta", "nieve") else 0
                if c.group in ("niño", "anciano"):
                    p *= 1.6
                p *= max(0.4, 1 - medic / 18) * self.diff["disease"]
                if self.profession == "medico":
                    p *= 0.7
                if resting:
                    p *= 0.5
                if self.rng.random() < p:
                    c.sick = self.rng.choice(data.DISEASES[:6])
                    self.note(f"{c.name} cae enfermo/a: {c.sick}.")
            c.health = max(0.0, min(100.0, c.health + d))
            if c.health <= 0:
                c.alive = False
                c.post = None
                c.cause = c.sick or ("hambre" if self.starving else "agotamiento")
                self.stats["lost"] += 1
                self.morale = max(0, self.morale - 10)
                self.note(f"{c.name} ha muerto ({c.cause}).")
                died.append(c)
        if died:
            self.normalize_posts()
        return died

    def _game_over(self, text: str) -> EndSpec:
        self.over = True
        return EndSpec("Fin del viaje", text, False)

    # ------------------------------------------------------------ tribus y asaltos
    def current_tribe(self) -> Optional[str]:
        return self.tribe_at(self.mile)

    def tribe_name(self, tid: str) -> str:
        return data.TRIBES[tid]["name"]

    def raid_probability(self, tid: str) -> float:
        ts = self.tribes[tid]
        t = data.TRIBES[tid]
        if ts.allied:
            return 0.0
        p = t["aggression"] * max(0.0, (25 - ts.attitude)) / 100.0 * 0.22
        if self.day <= ts.treaty_until:
            p *= 0.08
        if self.has_guide() and self.guide_tribe == tid:
            p *= 0.6
        return p * self.director.raid_mult(self)

    def _roll_tribe_events(self) -> Optional[Any]:
        tid = self.current_tribe()
        if not tid or self.mile < 20:
            return None
        ts = self.tribes[tid]
        t = data.TRIBES[tid]
        rng = self.rng
        # primer contacto garantizado a 70 millas dentro del territorio
        start = next(a for a, b, x in data.TERRITORIES if x == tid)
        if not ts.first_contact_done and self.mile >= start + 70:
            ts.first_contact_done = True
            ts.met = True
            kind = "visit" if ts.attitude >= 8 else "patrol"
            return ContactSpec(tid, kind, t["greet"])
        # contactos ocasionales
        if rng.random() < 0.05 and self.day > ts.last_raid + 4:
            kind = "visit" if ts.attitude >= 15 else "patrol"
            ts.met = True
            return ContactSpec(tid, kind, t["greet"])
        # incursión
        if self.day > ts.last_raid + 3 and rng.random() < self.raid_probability(tid):
            return self._raid_warning(tid)
        return None

    def _raid_warning(self, tid: str) -> Any:
        ts = self.tribes[tid]
        ts.last_raid = self.day
        warn = {"ninguna": 0.3, "normal": 0.6, "reforzada": 0.92}[self.watch]
        if self.has_guide():
            warn += 0.2
        spec = self.make_raid(tid)
        if self.rng.random() < warn:
            spec.tense = True
            name = self.tribe_name(tid)

            from . import story
            vs = story.voices(self)

            def prepare():
                story.follow(self, vs, "fight")
                return spec

            def parley():
                story.follow(self, vs, "parley")
                return ContactSpec(tid, "tense", "Envías un emisario con las manos vacías hacia la partida de guerra.")

            def flee():
                story.follow(self, vs, "flee")
                return self.flee(spec)

            body = (f"Los vigías divisan una partida de guerra {name} que se aproxima, unos "
                    f"{max(5, int(spec.strength * 1.1))} guerreros. Todavía hay tiempo de decidir.")
            if vs:
                body += "\n\n" + story.voices_text(vs)
            return Prompt(
                f"¡{name} se acercan!", body,
                [Option("Cerrar el círculo y prepararse", prepare, "Combate (tendrás tiempo de organizar posiciones)", story.backers(vs, "fight")),
                 Option("Salir a parlamentar", parley, "Diplomacia: última oportunidad de evitar la sangre", story.backers(vs, "parley")),
                 Option("Forzar la marcha y huir", flee, "Arriesgado: bueyes y carretas pueden sufrir", story.backers(vs, "flee"))],
                "danger")
        spec.night = self.rng.random() < 0.5
        spec.prep_time = 6.0
        spec.reason = "¡Ataque por sorpresa! Los vigías no vieron venir a la partida."
        self.note(spec.reason)
        return spec

    def flee(self, spec: BattleSpec) -> Any:
        rng = self.rng
        chance = 0.45 + 0.1 * (self.sup.oxen / max(1, 2 * len(self.wagons))) - 0.02 * spec.strength / 4
        if self.pace == "rapido":
            chance += 0.1
        if rng.random() < chance and self.oxen_factor() > 0.4:
            lost = []
            if rng.random() < 0.5 and self.sup.oxen > 2:
                self.sup.oxen -= 2
                lost.append("dos bueyes")
            if rng.random() < 0.4:
                self.sup.food = max(0, self.sup.food - 80)
                lost.append("80 lb de comida")
            if rng.random() < 0.4 and self.wagons:
                w = rng.choice(self.wagons)
                w.hp = max(20, w.hp - 80)
                lost.append("daños en una carreta")
            self.mile += 8
            self.morale -= 5
            return Prompt.info("¡Escapasteis!", "A latigazos, la caravana se pierde entre el polvo y la partida desiste. "
                               + ("Perdisteis: " + ", ".join(lost) + "." if lost else "Sin pérdidas."), "info")
        spec.prep_time = 4.0
        spec.reason = "La huida fracasa: los jinetes os alcanzan antes de cerrar el círculo."
        return spec

    def make_raid(self, tid: str, extra: float = 0.0) -> BattleSpec:
        t = data.TRIBES[tid]
        ts = self.tribes[tid]
        rng = self.rng
        progress = self.mile / 2000.0
        strength = (7 + progress * 12 + ts.arms * 1.1 + rng.uniform(0, 3) + extra) * t["strength"]
        if self.day <= ts.treaty_until:
            strength *= 0.45
        return self.compose_battle(tid, strength)

    @property
    def diff(self) -> dict:
        return data.DIFFICULTY[getattr(self, "difficulty", "normal")]

    def compose_battle(self, tid: str, strength: float) -> BattleSpec:
        rng = self.rng
        strength *= self.diff["raid"] * self.director.strength_mult(self)
        style = data.TRIBES[tid]["style"] if tid in data.TRIBES else {"bandido": 6, "guerrero": 2}
        if tid == "bandidos":
            style = {"bandido": 6, "guerrero": 3, "jinete": 1}
        kinds = list(style.keys())
        weights = [style[k] for k in kinds]
        n_waves = 1 if strength < 8 else 2 if strength < 15 else 3 if strength < 24 else 4
        budget = strength
        waves = []
        base_angle = rng.uniform(0, 2 * math.pi)
        t = 0.0
        boss = strength >= 16 and tid != "bandidos"
        for wi in range(n_waves):
            wb = budget / (n_waves - wi) * rng.uniform(0.8, 1.2)
            comp: dict[str, int] = {}
            while wb > 0.8:
                k = rng.choices(kinds, weights)[0]
                cost = data.FOES[k]["cost"]
                if cost > wb + 1.0:
                    k = "guerrero"
                    cost = data.FOES[k]["cost"]
                comp[k] = comp.get(k, 0) + 1
                wb -= cost
                budget -= cost
            if boss and wi == n_waves - 1:
                comp["jefe"] = 1
            if comp:
                if wi == 0:
                    angle = base_angle
                elif wi % 2 == 1:
                    angle = base_angle + math.pi + rng.uniform(-0.5, 0.5)
                else:
                    angle = base_angle + rng.choice([-1, 1]) * math.pi / 2 + rng.uniform(-0.4, 0.4)
                waves.append((t, angle, comp))
            t += rng.uniform(22, 38)
        # los más fuertes llegan por varios lados a la vez
        if strength > 12 and waves:
            t0, a0, c0 = waves[0]
            split = {}
            for k in list(c0.keys()):
                if c0[k] >= 2:
                    half = c0[k] // 2
                    c0[k] -= half
                    split[k] = half
            if split:
                waves.insert(1, (t0 + 1.5, a0 + rng.choice([-1, 1]) * rng.uniform(1.8, 2.6), split))
        allies = 4 * len([k for k, s in self.tribes.items() if s.allied and k != tid and k in data.TERRITORY_TRIBES])
        return BattleSpec(foe=tid, strength=strength, waves=waves, allies=allies,
                          night=rng.random() < 0.18, prep_time=28.0,
                          reason="" if tid != "bandidos" else "Una banda de salteadores os ha tendido una emboscada.")

    def _roll_bandits(self) -> Optional[Any]:
        if self.mile < 300 or self.day - self.last_bandit_day < 14:
            return None
        p = 0.012 * (1.8 if self.watch == "ninguna" else 0.6 if self.watch == "reforzada" else 1.0) * self.director.raid_mult(self)
        if self.rng.random() < p:
            self.last_bandit_day = self.day
            spec = self.compose_battle("bandidos", 5 + self.mile / 2000 * 7 + self.rng.uniform(0, 2))
            spec.night = self.rng.random() < 0.4
            spec.prep_time = 10.0 if self.watch != "reforzada" else 25.0
            spec.reason = "Un grupo de salteadores aprovecha la oscuridad del camino y os asalta."
            return Prompt("¡Bandoleros!", "Hombres armados salen de entre las rocas gritando que dejéis la carga y os marchéis.",
                          [Option("¡Al círculo! Defendernos", lambda: spec),
                           Option("Pagar el rescate (6 mercancías, 20 balas)", lambda: self._pay_bandits())], "danger")
        return None

    def _pay_bandits(self) -> Any:
        if self.sup.goods >= 6 and self.sup.ammo >= 20:
            self.sup.goods -= 6
            self.sup.ammo -= 20
            self.morale -= 8
            return Prompt.info("Un mal trato", "Los bandidos toman el pago y se esfuman. La rabia pesa más que la pérdida.", "info")
        spec = self.compose_battle("bandidos", 5 + self.mile / 2000 * 7)
        spec.prep_time = 6
        spec.reason = "No podéis pagar. Los bandidos atacan de todos modos."
        return spec

    # ------------------------------------------------------------ eventos aleatorios
    def _roll_random_event(self) -> Optional[Any]:
        rng = self.rng
        if rng.random() > 0.17:
            return None
        table = [
            (self._ev_wheel, 3), (self._ev_ox, 2), (self._ev_storm, 2), (self._ev_sick, 2),
            (self._ev_bison, 3), (self._ev_trader, 2), (self._ev_news, 1), (self._ev_lost, 1),
            (self._ev_road, 1), (self._ev_stranger, 2), (self._ev_music, 1), (self._ev_fire, 1),
            (self._ev_berries, 2), (self._ev_thieves, 1),
        ]
        table = self.director.reweight(self, table)
        fn = rng.choices([t[0] for t in table], [t[1] for t in table])[0]
        return fn()

    def _ev_wheel(self):
        if self.sup.parts > 0:
            if self.profession == "carpintero" and self.rng.random() < 0.5:
                self.note("Se rompe una rueda; con su oficio, reparas sin gastar repuestos.")
            else:
                self.sup.parts -= 1
                self.note("Se rompe una rueda. Gastas un juego de repuestos.")
        else:
            self.day += 2
            self.note("Se rompe un eje y no hay repuestos: perdéis dos días improvisando uno.")
        return None

    def _ev_ox(self):
        if self.sup.oxen > 2:
            self.sup.oxen -= 1
            self.note("Un buey cae muerto de agotamiento.")
        return None

    def _ev_storm(self):
        self.day += 1
        for c in self.living():
            c.health = max(1, c.health - 3)
        self.note("Una tormenta eléctrica os obliga a detener todo un día.")
        return None

    def _ev_sick(self):
        healthy = [c for c in self.living() if not c.sick]
        if healthy:
            c = self.rng.choice(healthy)
            c.sick = self.rng.choice(data.DISEASES)
            c.health -= 15
            self.note(f"{c.name} cae enfermo/a: {c.sick}.")
        return None

    def _ev_berries(self):
        n = self.rng.randint(25, 60)
        self.sup.food += n
        self.note(f"Los niños encuentran bayas y raíces comestibles: +{n} lb de comida.")
        return None

    def _ev_bison(self):
        tid = self.current_tribe()
        if self.mile < 200 or self.sup.ammo < 8:
            return None
        trespass = tid is not None and self.day > self.tribes[tid].treaty_until and not self.tribes[tid].allied

        def hunt():
            skill = self.best("hunt")
            used = self.rng.randint(6, 10)
            used = min(used, self.sup.ammo)
            self.sup.ammo -= used
            gain = int(used * self.rng.uniform(25, 38) * (0.7 + skill / 14))
            self.sup.food += gain
            self.stats["hunted"] += gain
            txt = f"La cacería da {gain} lb de carne seca ({used} balas)."
            if trespass and self.rng.random() < 0.5:
                self.tribes[tid].attitude -= 7
                txt += f" Pero los {self.tribe_name(tid)} consideran esa manada suya… y lo han visto."
            return Prompt.info("Cacería de bisontes", txt, "good")
        extra = " Cazarla en estas tierras puede ofender." if trespass else ""
        return Prompt("¡Una manada de bisontes!",
                      "Una manada enorme cruza el valle a media milla de la caravana." + extra,
                      [Option("Cazar (6-10 balas)", hunt), Option("Dejarlos pasar", lambda: None)], "good")

    def _ev_trader(self):
        tm = 1.25
        return Prompt("Comerciante ambulante",
                      "Un mulero con un carro cargado de mercancías os alcanza por el camino.",
                      [Option("Comerciar", lambda: ShopSpec("Comerciante ambulante", tm, wagons=False)),
                       Option("Seguir adelante", lambda: None)], "info")

    def _ev_news(self):
        t = self.current_tribe()
        nxt = self.next_tribe()
        if nxt:
            att = self.tribes[nxt].attitude
            mood = "muy hostiles" if att < -30 else "recelosos" if att < 0 else "tranquilos" if att < 30 else "amistosos"
            self.note(f"Unos viajeros que vuelven al este cuentan que los {self.tribe_name(nxt)} andan {mood} con los blancos.")
        return None

    def next_tribe(self) -> Optional[str]:
        cur = self.current_tribe()
        for a, b, t in data.TERRITORIES:
            if a > self.mile:
                return t
        return cur

    def _ev_lost(self):
        self.day += 1
        self.note("Os desorientáis en una bifurcación sin señales. Perdéis un día.")
        return None

    def _ev_road(self):
        self.mile += 12
        self.note("Encontráis un atajo excelente: ganáis 12 millas.")
        return None

    def _ev_music(self):
        self.morale = min(100, self.morale + 12)
        self.note("Esa noche suena el violín junto al fuego. La moral mejora.")
        return None

    def _ev_fire(self):
        if self.sup.goods > 0:
            n = min(self.sup.goods, self.rng.randint(1, 3))
            self.sup.goods -= n
            self.note(f"Una chispa quema parte de la carga: -{n} mercancías.")
        return None

    def _ev_thieves(self):
        if self.watch == "reforzada" and self.rng.random() < 0.7:
            self.note("La guardia reforzada sorprende a unos ladrones y los ahuyenta.")
            return None
        n = self.rng.randint(1, 3)
        self.sup.goods = max(0, self.sup.goods - n)
        self.sup.ammo = max(0, self.sup.ammo - 8)
        self.note("Ladrones nocturnos se llevan mercancías y munición.")
        return None

    def _ev_stranger(self):
        if self.mile < 200:
            return None
        deserter = self.rng.random() < 0.2

        def take():
            if self.sup.food < 40:
                return Prompt.info("Sin comida que ofrecer", "No podéis alimentar a otra boca; el extraño sigue su camino.")
            self.sup.food -= 40
            if deserter:
                lost = min(self.sup.goods, 4)
                self.sup.goods -= lost
                self.sup.ammo = max(0, self.sup.ammo - 15)
                return Prompt.info("Un desertor", "Al amanecer, el 'superviviente' ha desaparecido con parte de vuestras mercancías y munición.", "danger")
            c = self._make("joven", f"{self.rng.choice(data.MALE + data.FEMALE)} Walker",
                           shoot=self.rng.randint(4, 8), build=self.rng.randint(3, 6), hunt=self.rng.randint(3, 6))
            self.note(f"{c.name} se une a la caravana.")
            return Prompt.info("Un nuevo colono", f"{c.name} agradece la comida y se ofrece a trabajar. Se une a la caravana.", "good")
        return Prompt("Un superviviente",
                      "Un joven andrajoso, único sobreviviente de otra caravana, os pide comida y unirse al grupo.",
                      [Option("Acogerlo (40 lb de comida)", take), Option("Seguir adelante", lambda: None)], "info")

    # ------------------------------------------------------------ cruces y pasos
    def river_prompt(self, wp: dict) -> Prompt:
        depth = wp["depth"] + (1 if self.weather in ("lluvia", "tormenta") else 0) + (1 if self.date().month <= 5 else 0)
        guide = 0.7 if self.has_guide() else 1.0
        fee = 25 + 8 * len(self.wagons)

        def ford():
            risk = (0.06 + 0.07 * depth) * guide
            return self._river_result("vadeas", risk, 2)

        def caulk():
            risk = (0.03 + 0.05 * depth) * guide
            self.day += 1
            return self._river_result("calafateas y flotas", risk, 1)

        def ferry():
            if self.sup.money < fee:
                return Prompt.info("Sin dinero", f"El barquero pide ${fee} y no los tienes.", "danger")
            self.sup.money -= fee
            self.day += 1
            return Prompt.info("Cruce seguro", f"Pagas ${fee} y la balsa pasa carreta por carreta sin incidentes.", "good")

        def wait():
            self.day += 2
            self._daily_upkeep_n(2)
            return self.river_prompt({**wp, "depth": max(1, wp["depth"] - 1)})

        return Prompt(f"{wp['name']} — profundidad {depth}",
                      f"{wp['text']} El cauce ronda los {depth} pies de profundidad.",
                      [Option("Vadear", ford, "Rápido pero arriesgado"),
                       Option("Calafatear las carretas y flotar", caulk, "1 día, riesgo medio"),
                       Option(f"Pagar la balsa (${fee})", ferry, "Seguro"),
                       Option("Esperar 2 días a que baje", wait, "Consume comida")], "info")

    def _daily_upkeep_n(self, n: int):
        for _ in range(n):
            self._daily_upkeep()

    def _river_result(self, how: str, risk: float, dmg: int) -> Prompt:
        rng = self.rng
        if rng.random() < risk:
            lost = []
            f = int(self.sup.food * rng.uniform(0.15, 0.3))
            self.sup.food -= f
            lost.append(f"{f} lb de comida")
            if self.sup.oxen > 2:
                self.sup.oxen -= 2
                lost.append("2 bueyes")
            if self.sup.ammo > 0:
                a = int(self.sup.ammo * 0.2)
                self.sup.ammo -= a
                lost.append(f"{a} balas")
            if rng.random() < 0.35:
                victims = [c for c in self.living() if c.group in ("niño", "anciano", "joven")]
                if victims:
                    v = rng.choice(victims)
                    v.health -= 45
                    lost.append(f"{v.name} casi se ahoga")
                    if v.health <= 0:
                        v.alive = False
                        v.cause = "ahogado"
                        v.post = None
                        self.stats["lost"] += 1
                        lost[-1] = f"{v.name} se ahoga"
                        self.normalize_posts()
            self.morale -= 8
            return Prompt.info("Desastre en el cruce", f"Al cruzar ({how}), la corriente arrastra la carga. Perdéis: {', '.join(lost)}.", "danger")
        self.log(f"Cruzaste el río ({how}) sin problemas.")
        return Prompt.info("Cruce completado", f"Cruzáis el río ({how}) y todos llegan a la otra orilla.", "good")

    def mountain_prompt(self, wp: dict) -> Prompt:
        danger = wp["danger"] + (0.2 if self.date().month >= 10 else 0)
        danger *= 0.65 if self.has_guide() else 1.0

        def careful():
            self.day += 2
            self._daily_upkeep_n(2)
            return self._mountain_result(danger * 0.45)

        def push():
            return self._mountain_result(danger)

        def lighten():
            lose = min(self.sup.goods, 4)
            self.sup.goods -= lose
            return self._mountain_result(danger * 0.55, f"Dejáis {lose} lotes de mercancías atrás. ")
        return Prompt(wp["name"], wp["text"],
                      [Option("Cruzar con cautela (+2 días)", careful, "Riesgo bajo"),
                       Option("Forzar el paso", push, "Riesgo alto"),
                       Option("Aligerar la carga (-4 mercancías)", lighten, "Riesgo medio")], "info")

    def _mountain_result(self, risk: float, pre: str = "") -> Prompt:
        rng = self.rng
        if rng.random() < risk:
            msgs = []
            if self.wagons:
                w = rng.choice(self.wagons)
                w.hp = max(15, w.hp - rng.randint(80, 160))
                msgs.append("una carreta queda muy dañada")
            if self.sup.oxen > 2:
                self.sup.oxen -= 2
                msgs.append("pierdes dos bueyes en un barranco")
            self.sup.food = max(0, self.sup.food - 60)
            self.morale -= 6
            return Prompt.info("Paso accidentado", pre + "El camino se cobra su peaje: " + "; ".join(msgs) + ".", "danger")
        return Prompt.info("Paso superado", pre + "La caravana cruza el paso y respira hondo.", "good")

    # ------------------------------------------------------------ campamento
    def rest_day(self, days: int = 1):
        for _ in range(days):
            self.day += 1
            self.update_weather()
            self._daily_upkeep()
            self._daily_health(resting=True)
            self.director.update(self)
            self.morale = min(100, self.morale + 3)
            for w in self.wagons:
                w.hp = min(w.max_hp, w.hp + 18)

    def camp_event(self) -> Optional[Any]:
        """Posibles visitas o ataques mientras se acampa."""
        if self.over:
            return None
        evt = self._roll_tribe_events()
        if evt:
            return evt
        return self._roll_bandits()

    def rest(self, days: int) -> tuple[int, Optional[Any]]:
        """Descansa hasta `days` días; se interrumpe si ocurre algo. Devuelve (días, interrupción)."""
        done = 0
        for _ in range(days):
            self.rest_day(1)
            done += 1
            if not self.living():
                return done, self._game_over("El campamento queda en silencio: nadie ha sobrevivido.")
            if self.day >= data.FORCED_WINTER_DAY and not self.forced_winter and self.mile < data.TRAIL_END:
                it = self._check_winter()
                if it:
                    return done, it
            it = self.camp_event()
            if it:
                return done, it
        return done, None

    def travel_to_site(self, site_id: str) -> list[str]:
        """Recorre las millas extra hasta el lugar elegido; devuelve notas de lo ocurrido."""
        extra = data.SITES[site_id]["extra"] if site_id in data.SITES else 0
        days = int(math.ceil(extra / 17.0))
        notes = []
        for _ in range(days):
            self.day += 1
            self.update_weather()
            self._daily_upkeep()
            for c in self._daily_health():
                notes.append(f"{c.name} murió en el último tramo ({c.cause}).")
        self.mile += extra
        self.arrived_site = site_id
        return notes

    def repair_wagon(self, idx: int) -> tuple[bool, str]:
        w = self.wagons[idx]
        if w.hp >= w.max_hp - 1:
            return False, "Esa carreta está en perfecto estado."
        cost = 1
        if self.profession == "carpintero" or self.best("build") >= 8:
            cost = 1 if self.rng.random() < 0.5 else 0
        if self.sup.parts < cost:
            return False, "Faltan repuestos."
        self.sup.parts -= cost
        w.hp = min(w.max_hp, w.hp + 90)
        return True, f"Carreta {idx + 1} reparada ({int(w.hp)}/{int(w.max_hp)})."

    def upgrade(self, idx: int, kind: str) -> tuple[bool, str]:
        w = self.wagons[idx]
        s = self.sup
        if kind == "refuerzo":
            if w.reinforced >= 2:
                return False, "Ya tiene el máximo de refuerzos."
            if s.parts < 2:
                return False, "Faltan repuestos (2)."
            s.parts -= 2
            w.reinforce()
            return True, f"Carreta {idx + 1}: planchas de refuerzo (+120 de resistencia)."
        if kind == "plataforma":
            if w.platform:
                return False, "Ya tiene plataforma."
            if s.parts < 2 or s.goods < 1:
                return False, "Faltan repuestos (2) o mercancías (1)."
            s.parts -= 2
            s.goods -= 1
            w.platform = True
            return True, f"Carreta {idx + 1}: plataforma de tiro (más alcance y puntería)."
        if kind == "farol":
            if w.lantern:
                return False, "Ya tiene farol."
            if s.goods < 2:
                return False, "Faltan mercancías (2)."
            s.goods -= 2
            w.lantern = True
            return True, f"Carreta {idx + 1}: farol para combates nocturnos."
        if kind == "cañón":
            if w.cannon:
                return False, "Ya tiene cañón."
            if self.cannon_stock < 1:
                return False, "No tienes ningún cañón en el almacén (cómpralo en Fort Laramie o Fort Hall)."
            self.cannon_stock -= 1
            w.cannon = True
            return True, f"Carreta {idx + 1}: cañón montado."
        return False, "Mejora desconocida."

    def hunt_day(self) -> Prompt:
        """Un día de cacería organizada."""
        self.day += 1
        self.update_weather()
        self._daily_upkeep()
        self._daily_health()
        hunters = sorted([c for c in self.living() if c.group in ("adulto", "joven")], key=lambda c: -c.hunt)[:2]
        if self.sup.ammo < 6 or not hunters:
            return Prompt.info("Sin medios", "No tienes munición o cazadores para salir.", "danger")
        used = min(self.sup.ammo, self.rng.randint(8, 14))
        self.sup.ammo -= used
        skill = sum(h.hunt for h in hunters) / len(hunters)
        terrain_f = dict(pradera=1.2, llanura=1.4, estepa=0.9, montaña=0.8, desierto=0.5, cañón=0.7, bosque=1.0, valle=1.3)[self.terrain()]
        gain = int(used * self.rng.uniform(14, 30) * (0.6 + skill / 8) * terrain_f)
        self.sup.food += gain
        self.stats["hunted"] += gain
        txt = f"{' y '.join(h.name for h in hunters)} regresan con {gain} lb de carne ({used} balas)."
        tid = self.current_tribe()
        if tid and self.day > self.tribes[tid].treaty_until and not self.tribes[tid].allied \
                and self.rng.random() < 0.3:
            self.tribes[tid].attitude -= 5
            txt += f" Pero los {self.tribe_name(tid)} los vieron cazar en sus tierras."
        return Prompt.info("Cacería", txt, "good")

    # ------------------------------------------------------------ combate
    def apply_battle(self, spec: BattleSpec, res: BattleResult) -> Prompt:
        """Aplica el resultado de un combate y devuelve el resumen."""
        lines = []
        tid = spec.foe
        self.director.on_battle_end(self, res)
        self.stats["raids"] += 1
        self.stats["kills"] += res.foes_killed
        native = tid in self.tribes
        outcome_title = {"victoria": "¡Victoria!", "huida": "El enemigo se retira", "paz": "Se acuerda la paz",
                         "derrota": "Derrota"}[res.outcome]
        lines.append(f"Enemigos abatidos: {res.foes_killed}/{res.foes_total}. Munición gastada: {res.ammo_used}.")
        if res.dead:
            lines.append("Caídos: " + ", ".join(res.dead) + ".")
        if res.wagons_lost:
            lines.append(f"Carretas destruidas: {res.wagons_lost} (con parte de la carga).")
        if native:
            ts = self.tribes[tid]
            ts.kills += res.foes_killed
            ts.raids += 1
            if res.outcome == "paz":
                delta = 8 - res.foes_killed * 0.6
                self.stats["parleys"] += 1
                ts.treaty_until = max(ts.treaty_until, self.day + 8)
                lines.append(f"El parlamento calma los ánimos de los {self.tribe_name(tid)}. Habrá una tregua.")
            else:
                delta = -4 - res.foes_killed * 1.0
                lines.append(f"Los {self.tribe_name(tid)} guardarán memoria de la sangre derramada ({delta:+.0f} en su trato).")
            ts.attitude = max(-100, min(100, ts.attitude + delta))
            for k, o in self.tribes.items():
                if k != tid and k in data.TRIBES and o is not ts:
                    o.attitude = max(-100, min(100, o.attitude - res.foes_killed * 0.15))
        else:
            if res.outcome in ("victoria", "huida") and res.foes_killed:
                loot_a = self.rng.randint(5, 8) * max(1, res.foes_killed // 3)
                loot_g = self.rng.randint(0, 3)
                self.sup.ammo += loot_a
                self.sup.goods += loot_g
                lines.append(f"Botín de los bandidos: +{loot_a} balas, +{loot_g} mercancías.")
        if res.outcome in ("victoria", "huida") and res.ammo_used > 10:
            back = int(res.ammo_used * 0.12)
            self.sup.ammo += back
            lines.append(f"Recoges balas y flechas aprovechables: +{back} balas.")
        if res.outcome == "victoria":
            self.morale = min(100, self.morale + 6)
        elif res.outcome == "derrota":
            self.morale = max(0, self.morale - 25)
            lost_f = self.sup.food * 0.5
            self.sup.food -= lost_f
            self.sup.goods = self.sup.goods // 2
            lines.append("Los atacantes saquean la mitad de las provisiones antes de retirarse.")
        self.normalize_posts()
        for c in self.living():
            if c.health < 50 and not c.sick and self.rng.random() < 0.1:
                c.sick = "herida infectada"
        self.log(f"Combate contra {self.tribe_name(tid) if native else 'bandidos'}: {res.outcome}.")
        tone = "good" if res.outcome in ("victoria", "paz", "huida") else "danger"
        return Prompt.info(outcome_title, "\n".join(lines), tone)

    # ------------------------------------------------------------ fin
    def pop(self) -> int:
        return len(self.living())

    def travel_score_text(self) -> str:
        return f"{self.pop()} colonos, {len(self.wagons)} carretas, día {self.day}"


# ====================================================================== Diplomacia
class Contact:
    """Una reunión diplomática con una tribu."""

    GIFT_VALUE = dict(goods=4.0, food=3.0, ammo=5.0, medicine=6.0)
    GIFT_UNITS = dict(goods=(1, 3, 6), food=(1, 3, 6), ammo=(10, 20, 40), medicine=(1, 2, 4))
    GIFT_UNIT_NAME = dict(goods="lote(s) de mercancías", food="× 50 lb de comida", ammo="balas", medicine="dosis de medicina")

    def __init__(self, game: Game, tribe: str, kind: str = "visit", opening: str = ""):
        self.game = game
        self.tribe = tribe
        self.kind = kind
        self.patience = 4 + (1 if game.has_guide() else 0) + (1 if kind == "visit" else 0) - (1 if kind == "tense" else 0)
        self.ended = False
        self.result = "neutral"  # neutral | paz | hostil
        self.history: list[str] = []
        self.opening = opening
        self.used: set[str] = set()
        self.spec_after: Optional[BattleSpec] = None
        self.shop_requested = False
        ts = game.tribes[tribe]
        ts.met = True
        if kind == "patrol" and ts.attitude < 10:
            lots = 2 + data.TRIBES[tribe]["pride"] // 2
            self.history.append(f"Su portavoz exige un tributo por cruzar sus tierras: unos {lots} lotes de mercancías.")

    @property
    def ts(self) -> TribeState:
        return self.game.tribes[self.tribe]

    @property
    def info(self) -> dict:
        return data.TRIBES[self.tribe]

    def mood(self) -> str:
        a = self.ts.attitude
        if a < -60:
            return "Furiosos"
        if a < -30:
            return "Hostiles"
        if a < -5:
            return "Recelosos"
        if a < 20:
            return "Cautelosos"
        if a < 50:
            return "Amistosos"
        return "Aliados"

    def talk_skill(self) -> float:
        g = self.game
        from . import story
        s = g.best("talk") + (3 if g.has_guide() else 0) + story.talk_bonus(g)
        return s

    def chance(self, base: float, per_skill: float = 0.04) -> float:
        a = self.ts.attitude
        p = base + per_skill * self.talk_skill() + 0.004 * a - 0.03 * self.info["pride"]
        if self.game.has_guide():
            p += 0.1
        return max(0.05, min(0.95, p))

    def _spend(self, kind: str, units: int) -> bool:
        s = self.game.sup
        if kind == "goods":
            if s.goods < units:
                return False
            s.goods -= units
        elif kind == "food":
            if s.food < 50 * units:
                return False
            s.food -= 50 * units
        elif kind == "ammo":
            if s.ammo < units:
                return False
            s.ammo -= units
        elif kind == "medicine":
            if s.medicine < units:
                return False
            s.medicine -= units
        return True

    def _tick(self):
        self.patience -= 1
        if self.patience <= 0 and not self.ended:
            self.ended = True
            if self.kind == "tense" and self.ts.attitude < 5:
                self.result = "hostil"
                self.history.append("Se les agota la paciencia. La partida de guerra da media vuelta y carga.")
            else:
                self.history.append("Se hace tarde; la delegación se despide.")

    def do(self, key: str, arg: Any = None) -> str:
        g = self.game
        ts = self.ts
        rng = g.rng
        msg = ""
        if self.ended:
            return "La reunión ha terminado."
        if key == "saludo":
            ok = rng.random() < self.chance(0.45)
            if ok:
                ts.attitude += rng.uniform(3, 6)
                msg = "Saludas con respeto, mostrando las manos vacías. Asienten con gravedad: les ha gustado el gesto."
            else:
                ts.attitude -= 2
                msg = "Tu saludo se malinterpreta. Intercambian miradas fría."
            self._tick()
        elif key == "regalo":
            kind, units = arg
            if not self._spend(kind, units):
                return "No tienes eso para regalar."
            val = self.GIFT_VALUE[kind] * units * (1.5 if self.info["wants"] == kind else 1.0)
            if kind == "ammo":
                val = self.GIFT_VALUE[kind] * units / 20 * (1.5 if self.info["wants"] == kind else 1.0)
                ts.arms += units / 20 * 0.5
            gain = val * max(0.25, 1.0 - max(0.0, ts.attitude) / 120.0)
            ts.attitude = min(100, ts.attitude + gain)
            g.stats["gifts"] += 1
            nice = "les agrada muchísimo" if self.info["wants"] == kind else "lo aceptan con cortesía"
            msg = f"Entregas {units} {self.GIFT_UNIT_NAME[kind]}; {nice}. (+{gain:.0f})"
            if kind == "ammo":
                msg += " Ahora tienen más pólvora… para bien o para mal."
            self._tick()
        elif key == "comerciar":
            if ts.attitude < -20:
                return "No están de humor para comerciar con quien no respetan."
            self.shop_requested = True
            if "trade" not in self.used:
                ts.attitude += 2
                self.used.add("trade")
            msg = "Se extienden mantas en el suelo para el trueque."
        elif key == "paso":
            if ts.attitude < -25:
                return "No quieren oír hablar de pactos mientras haya tanta desconfianza."
            lots = 3 + self.info["pride"] // 2
            if g.sup.goods < lots:
                return f"El tributo ronda los {lots} lotes de mercancías y no los tienes."
            g.sup.goods -= lots
            if rng.random() < self.chance(0.38, 0.045):
                days = 12 + int(max(0, ts.attitude) / 8)
                ts.treaty_until = g.day + days
                ts.attitude += 4
                g.stats["treaties"] += 1
                self.result = "paz"
                msg = f"Paso seguro acordado: {days} días de tregua. Pagas {lots} lotes y el jefe sella el pacto con humo de pipa."
            else:
                ts.attitude -= 3
                msg = f"Aceptan el tributo ({lots} lotes) pero no prometen nada: 'veremos qué dicen los espíritus'."
            self._tick()
        elif key == "info":
            if g.sup.goods < 1:
                return "Necesitas al menos 1 lote de mercancías para pagar la información."
            g.sup.goods -= 1
            ts.attitude += 2
            nxt = g.next_tribe()
            parts = []
            if nxt and nxt != self.tribe:
                a = g.tribes[nxt].attitude
                parts.append(f"Cuentan que más adelante los {g.tribe_name(nxt)} están " +
                             ("muy hostiles." if a < -30 else "inquietos." if a < 0 else "tranquilos." if a < 30 else "bien dispuestos."))
            parts.append(f"Calculan que la partida de guerra más cercana tardará {rng.randint(3, 12)} días.")
            if rng.random() < 0.5:
                g.sup.food += 25
                parts.append("Te indican un manantial con caza abundante (+25 lb de comida).")
            msg = " ".join(parts)
            self._tick()
        elif key == "guia":
            if ts.attitude < 10:
                return "Necesitas ganarte más su confianza antes de que alguien guíe a forasteros."
            if g.sup.goods < 8:
                return "El guía pide 8 lotes de mercancías."
            g.sup.goods -= 8
            g.guide_until = g.mile + 450
            g.guide_tribe = self.tribe
            ts.attitude += 3
            msg = "Un joven intérprete se une a la caravana por unas 450 millas. Facilita los tratos y reduce peligros."
            self._tick()
        elif key == "alianza":
            if ts.attitude < 55 or ts.treaty_until < 0:
                return "Una alianza exige confianza (trato 55+) y un pacto previo."
            if g.sup.goods < 10:
                return "El banquete de alianza cuesta 10 lotes de mercancías."
            g.sup.goods -= 10
            if rng.random() < self.chance(0.4, 0.05):
                ts.allied = True
                ts.attitude += 6
                msg = "¡Alianza sellada! Sus jinetes cabalgarán con vosotros si os atacan otros."
            else:
                ts.attitude -= 2
                msg = "Piden más tiempo para consultar con el consejo."
            self._tick()
        elif key == "fuerza":
            wagons = len(g.wagons)
            sh = len(g.shooters())
            p = 0.28 + 0.04 * g.best("shoot") + 0.015 * wagons + 0.01 * sh - 0.04 * self.info["pride"] + (0.1 if g.sup.ammo >= 60 else -0.1)
            p = max(0.05, min(0.85, p))
            if rng.random() < p:
                ts.treaty_until = max(ts.treaty_until, g.day + 6)
                ts.attitude -= 8
                msg = "Los tiradores se alinean sobre las carretas con un estruendo de cerrojos. La partida se aparta… con rencor."
            else:
                ts.attitude -= 16
                msg = "Tu exhibición los ofende. Hay gritos y flechas en los arcos."
                if self.kind in ("tense", "patrol") and rng.random() < 0.5:
                    self.result = "hostil"
                    self.ended = True
                    msg += " Ya no hay vuelta atrás."
            self._tick()
        elif key == "eli":
            e = g.member("abuelo")
            if e is None or not g.flags.get("eli_friend"):
                return "Eli no está en condiciones de hablar por vosotros."
            p = 0.5 + (0.3 if self.tribe == "lakota" else 0.0) + 0.002 * e.loyalty
            if rng.random() < p:
                ts.attitude += 25
                e.loyalty = min(100, e.loyalty + 6)
                msg = ("Eli avanza solo, con las manos abiertas, y dice un nombre: «Sombra del Roble». Hay un silencio largo. "
                       "Al rato, un hombre mayor responde. Las lanzas bajan.")
                self.result = "paz"
                ts.treaty_until = max(ts.treaty_until, g.day + 10)
                self.ended = True
            else:
                ts.attitude -= 5
                e.loyalty = max(0, e.loyalty - 2)
                msg = "Eli habla con firmeza, pero no es su gente: no conocen el nombre. Vuelve al círculo con la cabeza gacha."
            self._tick()
        elif key == "adios":
            self.ended = True
            if self.kind == "tense" and ts.attitude < 5:
                self.result = "hostil"
                msg = "Te retiras. Sin acuerdo, la partida de guerra continúa su avance."
            elif self.kind == "patrol" and ts.attitude < -20 and not self.used:
                ts.attitude -= 8
                msg = "Te marchas sin decir palabra; lo toman como un desaire."
            else:
                msg = "Os despedís con cortesía."
        # al final: si la actitud se desplomó en reunión tensa
        ts.attitude = max(-100, min(100, ts.attitude))
        if key != "adios" and self.kind == "tense" and ts.attitude >= 25 and not self.ended:
            self.ended = True
            self.result = "paz"
            ts.treaty_until = max(ts.treaty_until, g.day + 6)
            msg += " La partida de guerra baja los arcos: no habrá batalla hoy."
        if self.ended and self.kind == "tense" and self.result == "hostil":
            self.spec_after = g.make_raid(self.tribe)
            self.spec_after.tense = False
            self.spec_after.prep_time = 12.0
            self.spec_after.reason = "El parlamento ha fracasado."
        self.history.append(msg)
        return msg

    def finish(self) -> Optional[BattleSpec]:
        if self.result == "hostil":
            if self.spec_after is None:
                self.spec_after = self.game.make_raid(self.tribe)
                self.spec_after.prep_time = 12.0
            return self.spec_after
        return None


# ====================================================================== Trueque con tribus
def tribe_offers(game: Game, tid: str) -> list[dict]:
    """Ofertas de trueque ('te doy X por Y'), generadas con la semilla actual."""
    rng = random.Random((game.seed or 0) * 1000 + game.day * 7 + len(tid))
    t = data.TRIBES[tid]
    wants = t["wants"]
    att = game.tribes[tid].attitude
    rate = 1.0 + max(0, att) / 120.0
    offers = [
        dict(give=("food", int(50 * rate) + 25), take=("goods", 1), text="Carne de bisonte seca (a cambio de 1 lote de mercancías)"),
        dict(give=("oxen", 2), take=("goods", 5), text="Un par de bueyes bien alimentados (por 5 mercancías)"),
        dict(give=("goods", 2), take=("food", 50), text="Pieles y mantas (por 50 lb de comida)"),
        dict(give=("food", 120), take=("ammo", 15), text="Pemmican de bisonte (por 15 balas)"),
        dict(give=("medicine", 1), take=("goods", 3), text="Hierbas curativas (por 3 mercancías)"),
        dict(give=("ammo", 10), take=("goods", 2), text="Munición recuperada (por 2 mercancías)"),
        dict(give=("parts", 1), take=("goods", 3), text="Un eje de buena madera (por 3 mercancías)"),
    ]
    rng.shuffle(offers)
    return offers[:5]


def apply_offer(game: Game, offer: dict) -> tuple[bool, str]:
    gk, gn = offer["give"]
    tk, tn = offer["take"]
    s = game.sup
    if getattr(s, tk) < tn:
        return False, "No tienes lo que piden."
    setattr(s, tk, getattr(s, tk) - tn)
    setattr(s, gk, getattr(s, gk) + gn)
    return True, "Trato cerrado."
