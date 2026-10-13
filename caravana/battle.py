"""Motor de combate en tiempo real: defensa 360° del círculo de carretas (sin pygame)."""
from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from . import data
from .model import BattleResult, BattleSpec, Colonist, Game

WAGON_L = 92.0
WAGON_GAP = 14.0
FIELD_RADIUS = 640.0      # radio de aparición de enemigos
GIVE_UP_TIME = 260.0      # tiempo máximo de combate antes de que el enemigo se retire
RIFLE_RANGE = 380.0
PLATFORM_RANGE = 55.0
WALK_SPEED = 95.0


def ang_diff(a: float, b: float) -> float:
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return d


@dataclass
class BWagon:
    ref: object
    idx: int
    angle: float
    x: float
    y: float
    burning: float = 0.0
    burn_time: float = 0.0
    barricade: float = 0.0       # hp de la barricada que cubre el hueco
    build_progress: float = 0.0
    destroyed: bool = False
    cooldown: float = 0.0        # para el cañón/tirador
    flash: float = 0.0

    @property
    def blocked(self) -> bool:
        return (not self.destroyed) or self.barricade > 0

    @property
    def hp(self) -> float:
        return self.ref.hp


class Foe:
    _next = 0

    def __init__(self, kind: str, x: float, y: float, rng: random.Random):
        d = data.FOES[kind]
        self.id = Foe._next
        Foe._next += 1
        self.kind = kind
        self.x, self.y = x, y
        self.hp = float(d["hp"])
        self.max_hp = float(d["hp"])
        self.speed = d["speed"] * rng.uniform(0.9, 1.1)
        self.state = "approach"
        self.cool = rng.uniform(1.0, 4.0)
        self.shots = rng.randint(3, 6)
        self.orbit_r = 0.0
        self.orbit_dir = rng.choice([-1, 1])
        self.stand_r = 0.0
        self.timer = 0.0
        self.attack_cool = rng.uniform(0, 1)
        self.target_wagon: Optional[int] = None
        self.alive = True
        self.fled = False
        self.flash = 0.0
        self.face = 0.0
        self.revealed = 0.0

    @property
    def mounted(self) -> bool:
        return self.kind in ("jinete", "jefe")

    @property
    def ranged(self) -> bool:
        return self.kind in ("jinete", "fuego", "bandido", "jefe")


class Ally:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y
        self.hp = 55.0
        self.alive = True
        self.cool = 0.0
        self.life = 75.0
        self.face = 0.0


class BColonist:
    def __init__(self, ref: Colonist, x: float, y: float):
        self.ref = ref
        self.x, self.y = x, y
        self.tx, self.ty = x, y
        self.task = "idle"
        self.cool = 0.0
        self.wander = 0.0
        self.flash = 0.0
        self.work_target: Optional[int] = None
        self.aim: Optional[tuple] = None

    @property
    def alive(self) -> bool:
        return self.ref.alive


@dataclass
class Arrow:
    x: float
    y: float
    tx: float
    ty: float
    fire: bool
    dmg: float
    target_wagon: int
    target_colonist: Optional[int]
    speed: float = 460.0
    mine: bool = False


class Battle:
    def __init__(self, game: Game, spec: BattleSpec, seed: Optional[int] = None):
        self.game = game
        self.spec = spec
        self.rng = random.Random(seed if seed is not None else game.rng.random())
        self.time = 0.0
        self.fight_time = 0.0
        self.prep = spec.prep_time
        self.phase = "prep" if spec.prep_time > 0 else "fight"
        self.done = False
        self.result: Optional[BattleResult] = None
        self.policy = "libre"
        self.focus: Optional[Foe] = None
        self.foes: list[Foe] = []
        self.allies: list[Ally] = []
        self.arrows: list[Arrow] = []
        self.msgs: deque = deque(maxlen=8)
        self.fx: list = []
        self.night = spec.night
        self.parley_cd = 0.0
        self.parley_available = spec.foe in data.TRIBES
        self.ammo_start = game.sup.ammo
        self.total_foes = sum(sum(c.values()) for _, _, c in spec.waves)
        self.killed = 0
        self.fled_count = 0
        self.dead_names: list[str] = []
        self.ruined: list[int] = []
        self.chief_dead = False
        self.retreating = False
        self.peace = False
        self.melt_used = 0
        self.check_cd = 0.0
        self.pending = sorted([(t, a, dict(c)) for t, a, c in spec.waves], key=lambda w: w[0])
        self.ally_pending = spec.allies > 0

        game.normalize_posts()
        n = max(1, len(game.wagons))
        self.n = n
        self.R = max(118.0, n * (WAGON_L + WAGON_GAP) / (2 * math.pi))
        self.R_out = self.R + 30
        self.wagons: list[BWagon] = []
        for i, w in enumerate(game.wagons):
            a = -math.pi / 2 + 2 * math.pi * i / n
            self.wagons.append(BWagon(w, i, a, math.cos(a) * self.R, math.sin(a) * self.R))
        self.colonists: list[BColonist] = []
        for c in game.living():
            ang = self.rng.uniform(0, 2 * math.pi)
            r = self.rng.uniform(25, max(30, self.R - 55))
            self.colonists.append(BColonist(c, math.cos(ang) * r, math.sin(ang) * r))
        for bc in self.colonists:
            self._assign_idle_target(bc)
        self.say(f"¡Cerrad el círculo! {len(self.colonists)} colonos, {n} carretas." if spec.prep_time > 0
                 else "¡Al combate!")
        if spec.reason:
            self.say(spec.reason, (255, 190, 120))
        if self.night:
            self.say("Es de noche: sólo se ve lo que ilumina el fuego y los faroles.", (160, 190, 255))

    # ----------------------------------------------------------- utilidades
    def say(self, text: str, color=(235, 225, 195)):
        self.msgs.append((self.time, text, color))

    def emit(self, *ev):
        self.fx.append(ev)
        if len(self.fx) > 400:
            del self.fx[:100]

    def sector(self, ang: float) -> int:
        step = 2 * math.pi / self.n
        k = round((ang + math.pi / 2) / step)
        return k % self.n

    def post_pos(self, widx: int, slot: str) -> tuple:
        w = self.wagons[widx]
        r = self.R - 30
        off = -0.17 if slot == "tirador" else 0.17
        a = w.angle + off * 90 / max(60.0, self.R) * 1.15
        return math.cos(a) * r, math.sin(a) * r

    def is_lit(self, x: float, y: float) -> bool:
        if not self.night:
            return True
        r = math.hypot(x, y)
        if r < self.R + 190:
            return True
        for w in self.wagons:
            if w.ref.lantern and not w.destroyed and math.hypot(x - w.x, y - w.y) < 300:
                return True
        for w in self.wagons:
            if w.burning > 0 and math.hypot(x - w.x, y - w.y) < 150:
                return True
        return False

    def is_visible(self, f: "Foe") -> bool:
        return (not self.night) or f.revealed > 0 or self.is_lit(f.x, f.y)

    def alive_foes(self) -> list[Foe]:
        return [f for f in self.foes if f.alive and not f.fled]

    def living_defenders(self) -> list[BColonist]:
        return [c for c in self.colonists if c.alive]

    # ----------------------------------------------------------- órdenes del jugador
    def start_fight(self):
        if self.phase == "prep":
            self.phase = "fight"
            self.prep = 0
            self.say("¡Aquí vienen!", (255, 150, 120))

    def assign(self, bc: BColonist, widx: int, slot: str) -> bool:
        if widx >= len(self.wagons) or self.wagons[widx].destroyed:
            return False
        ok = self.game.assign(bc.ref, widx, slot)
        return ok

    def unassign(self, bc: BColonist):
        bc.ref.post = None

    def threat_map(self) -> dict:
        out = {}
        foes = self.alive_foes()
        for w in self.wagons:
            if w.destroyed:
                continue
            s = 0.0
            for f in foes:
                d = math.hypot(f.x - w.x, f.y - w.y)
                if d < RIFLE_RANGE + 80:
                    s += 1.0 / (1.0 + d / 140.0) ** 2 * (1.6 if f.state in ("attack", "inside") else 1.0)
            out[w.idx] = s
        return out

    def auto_assign(self):
        """Reparte tiradores y ayudantes según la amenaza actual."""
        self.game.auto_assign(self.threat_map())

    def set_focus(self, foe: Optional[Foe]):
        self.focus = foe if foe and foe.alive else None

    def order_barricade(self, widx: int) -> bool:
        w = self.wagons[widx]
        if not w.destroyed or w.barricade > 0 or w.build_progress > 0.0001:
            return False
        if self.game.sup.parts < 1:
            self.say("No quedan repuestos para una barricada.", (255, 140, 120))
            return False
        self.game.sup.parts -= 1
        w.build_progress = 0.001
        self.say(f"Se levanta una barricada en el hueco {widx + 1}.")
        return True

    def melt(self) -> bool:
        s = self.game.sup
        if s.goods < 5:
            self.say("Necesitas 5 mercancías para fundir en balas.", (255, 140, 120))
            return False
        s.goods -= 5
        s.ammo += 12
        self.melt_used += 1
        self.say("Se funden peltre y cucharas: +12 balas.", (255, 220, 140))
        return True

    def parley_chance(self, gift: int = 0) -> float:
        g = self.game
        ts = g.tribes[self.spec.foe]
        loss = self.killed / max(1, self.total_foes)
        our_loss = len(self.dead_names) / max(1, len(g.colonists))
        p = 0.12 + 0.004 * ts.attitude + 0.03 * g.best("talk") + 0.12 * gift + 0.25 * loss + 0.1 * our_loss
        if g.has_guide():
            p += 0.1
        return max(0.05, min(0.85, p))

    def parley(self, gift: int = 0) -> tuple[bool, str]:
        if not self.parley_available:
            return False, "Estos hombres no quieren hablar."
        if self.phase == "prep":
            return False, "Aún no ha empezado el combate."
        if self.parley_cd > 0:
            return False, "Aún no pueden oírte; espera unos segundos."
        if self.fight_time < 10:
            return False, "Hay que dejar que se oiga primero el estruendo."
        g = self.game
        cost = (0, 3, 8)[gift]
        if g.sup.goods < cost:
            return False, "No tienes mercancías para el regalo."
        g.sup.goods -= cost
        p = self.parley_chance(gift)
        self.parley_cd = 28.0
        if self.rng.random() < p:
            self.peace = True
            self.say("¡Un jefe alza la lanza! Los atacantes aceptan hablar.", (170, 255, 170))
            for f in self.alive_foes():
                f.state = "flee"
            return True, "El parlamento tiene éxito."
        self.say("Rechazan el parlamento con gritos de guerra.", (255, 130, 110))
        for f in self.alive_foes():
            f.speed *= 1.05
        return False, "Rechazan hablar."

    # ----------------------------------------------------------- bucle principal
    def update(self, dt: float):
        if self.done:
            return
        self.time += dt
        self.parley_cd = max(0.0, self.parley_cd - dt)
        if self.phase == "prep":
            self.prep -= dt
            if self.prep <= 0:
                self.start_fight()
        else:
            self.fight_time += dt
            self._spawn_waves()
        self._update_colonists(dt)
        self._update_wagons(dt)
        if self.phase == "fight":
            self._update_foes(dt)
            self._update_allies(dt)
            self._update_arrows(dt)
            self._shoot(dt)
            self._morale_check(dt)
            self._check_end()
        for bc in self.colonists:
            bc.flash = max(0.0, bc.flash - dt)
        for f in self.foes:
            f.flash = max(0.0, f.flash - dt)
            f.revealed = max(0.0, f.revealed - dt)

    # ----------------------------------------------------------- oleadas
    def warnings(self) -> list:
        """Avisos de oleadas inminentes: (ángulo, segundos, composición)."""
        if self.phase == "prep":
            return [(a, t + max(0.0, self.prep), c) for t, a, c in self.pending[:3]]
        return [(a, t - self.fight_time, c) for t, a, c in self.pending if t - self.fight_time < 9]

    def _spawn_waves(self):
        while self.pending and self.pending[0][0] <= self.fight_time:
            t, ang, comp = self.pending.pop(0)
            names = []
            for kind, cnt in comp.items():
                names.append(f"{cnt} {data.FOES[kind]['name'].lower()}{'s' if cnt > 1 else ''}")
                for _ in range(cnt):
                    a = ang + self.rng.uniform(-0.35, 0.35)
                    r = FIELD_RADIUS + self.rng.uniform(0, 90)
                    f = Foe(kind, math.cos(a) * r, math.sin(a) * r, self.rng)
                    if kind == "jinete" or kind == "jefe":
                        f.orbit_r = self.R_out + self.rng.uniform(120, 200) + (90 if kind == "jefe" else 0)
                    if kind == "fuego":
                        f.stand_r = self.R_out + self.rng.uniform(95, 150)
                    if kind == "bandido":
                        f.stand_r = self.R_out + self.rng.uniform(150, 230)
                    self.foes.append(f)
            dir_txt = self._dir_text(ang)
            self.say(f"¡Oleada por el {dir_txt}!: " + ", ".join(names), (255, 170, 120))
            self.emit("wave", ang)
        if self.ally_pending and self.fight_time > 6:
            self.ally_pending = False
            for i in range(self.spec.allies):
                a = self.rng.uniform(0, 2 * math.pi)
                self.allies.append(Ally(math.cos(a) * (self.R + 260), math.sin(a) * (self.R + 260)))
            self.say("¡Jinetes aliados cabalgan en vuestra ayuda!", (170, 255, 170))

    @staticmethod
    def _dir_text(ang: float) -> str:
        # ángulo en pantalla: y hacia abajo
        deg = (math.degrees(ang) + 360) % 360
        names = ["este", "sureste", "sur", "suroeste", "oeste", "noroeste", "norte", "noreste"]
        return names[int(((deg + 22.5) % 360) // 45)]

    # ----------------------------------------------------------- colonos
    def _assign_idle_target(self, bc: BColonist):
        ang = self.rng.uniform(0, 2 * math.pi)
        r = self.rng.uniform(32, max(36, self.R - 62))
        bc.tx, bc.ty = math.cos(ang) * r, math.sin(ang) * r
        bc.wander = self.rng.uniform(3, 7)

    def _move(self, o, tx, ty, speed, dt) -> bool:
        dx, dy = tx - o.x, ty - o.y
        d = math.hypot(dx, dy)
        if d < 2.0:
            return True
        step = min(d, speed * dt)
        o.x += dx / d * step
        o.y += dy / d * step
        if hasattr(o, "face"):
            o.face = math.atan2(dy, dx)
        return d - step < 2.0

    def _update_colonists(self, dt: float):
        g = self.game
        heal_busy: set = set()
        wounded = [bc for bc in self.colonists if bc.alive and bc.ref.health < 60]
        # sanar: se asigna el mejor sanador libre al más herido
        for bc in self.colonists:
            if not bc.alive:
                continue
            c = bc.ref
            if c.health < 30:
                bc.task = "wounded"
                bc.tx, bc.ty = -14 + (c.cid % 5) * 8, 42 + (c.cid % 3) * 9
                self._move(bc, bc.tx, bc.ty, WALK_SPEED * 0.4, dt)
                continue
            post = c.post
            if post and post[0] < len(self.wagons) and not self.wagons[post[0]].destroyed:
                bc.task = "post"
                px, py = self.post_pos(post[0], post[1])
                self._move(bc, px, py, WALK_SPEED, dt)
                continue
            if post and (post[0] >= len(self.wagons) or self.wagons[post[0]].destroyed):
                c.post = None
            # libre: apagar, curar, reparar, construir
            job = self._pick_job(bc, wounded, heal_busy)
            if job:
                kind, tgt = job
                bc.task = kind
                bc.work_target = tgt
                if kind == "extinguish":
                    w = self.wagons[tgt]
                    self._move(bc, w.x * 0.78, w.y * 0.78, WALK_SPEED, dt)
                    if math.hypot(bc.x - w.x * 0.78, bc.y - w.y * 0.78) < 14:
                        w.burning -= dt * 0.35
                        if w.burning <= 0:
                            w.burning = 0.0
                            w.burn_time = 0
                elif kind == "build":
                    w = self.wagons[tgt]
                    self._move(bc, w.x * 0.8, w.y * 0.8, WALK_SPEED, dt)
                    if math.hypot(bc.x - w.x * 0.8, bc.y - w.y * 0.8) < 18:
                        rate = (0.6 + c.build / 10) / (7.0 if g.profession != "carpintero" else 4.0)
                        w.build_progress += rate * dt
                        if w.build_progress >= 1.0:
                            w.build_progress = 0.0
                            w.barricade = 90.0
                            self.say(f"Barricada terminada en el hueco {tgt + 1}.", (200, 230, 160))
                elif kind == "heal":
                    tbc = tgt
                    self._move(bc, tbc.x + 8, tbc.y + 6, WALK_SPEED, dt)
                    if math.hypot(bc.x - tbc.x, bc.y - tbc.y) < 18:
                        rate = 2.2 * (0.5 + c.medic / 5.0)
                        tbc.ref.health = min(100.0, tbc.ref.health + rate * dt)
                elif kind == "repair":
                    w = self.wagons[tgt]
                    self._move(bc, w.x * 0.8, w.y * 0.8, WALK_SPEED, dt)
                    if math.hypot(bc.x - w.x * 0.8, bc.y - w.y * 0.8) < 18:
                        rate = 3.5 * (0.5 + c.build / 8.0)
                        cap = w.ref.max_hp * 0.85
                        if w.ref.hp < cap:
                            w.ref.hp = min(cap, w.ref.hp + rate * dt)
                continue
            foe_near = None
            if c.group in ("adulto", "joven") and c.health > 30:
                for f in self.foes:
                    if f.alive and not f.fled and f.state == "inside" and math.hypot(f.x - bc.x, f.y - bc.y) < 60:
                        foe_near = f
                        break
            if foe_near is not None:
                bc.task = "melee"
                self._move(bc, foe_near.x, foe_near.y, WALK_SPEED, dt)
                if math.hypot(foe_near.x - bc.x, foe_near.y - bc.y) < 18:
                    self._damage_foe(foe_near, (6 + c.shoot) * dt * 1.6, c)
                continue
            bc.task = "idle"
            bc.wander -= dt
            if bc.wander <= 0:
                self._assign_idle_target(bc)
            self._move(bc, bc.tx, bc.ty, WALK_SPEED * 0.45, dt)
        # ayudantes y tiradores apagan fuego de su propia carreta
        for bc in self.colonists:
            if bc.alive and bc.task == "post" and bc.ref.post and bc.ref.post[1] == "ayuda":
                w = self.wagons[bc.ref.post[0]]
                if w.burning > 0:
                    w.burning -= dt * 0.28
                    if w.burning <= 0:
                        w.burning = 0.0
                        w.burn_time = 0

    def _pick_job(self, bc: BColonist, wounded, heal_busy):
        c = bc.ref
        if c.group == "niño" and c.health < 100:
            pass
        # fuego primero
        burning = [w for w in self.wagons if w.burning > 0 and not w.destroyed]
        if burning:
            w = min(burning, key=lambda w: math.hypot(w.x - bc.x, w.y - bc.y))
            return ("extinguish", w.idx)
        # barricadas pendientes
        for w in self.wagons:
            if w.destroyed and w.barricade <= 0 and w.build_progress > 0 and c.group != "niño":
                return ("build", w.idx)
        if wounded and c.medic >= 3 and c.group != "niño":
            cand = [x for x in wounded if x is not bc and x.alive and x.ref.health < 70]
            if cand:
                tgt = min(cand, key=lambda x: x.ref.health)
                return ("heal", tgt)
        if c.group in ("adulto", "joven", "anciano"):
            hurt = [w for w in self.wagons if not w.destroyed and w.ref.hp < w.ref.max_hp * 0.8]
            if hurt:
                w = min(hurt, key=lambda w: w.ref.hp / w.ref.max_hp)
                return ("repair", w.idx)
        return None

    # ----------------------------------------------------------- carretas, fuego, cañones
    def _update_wagons(self, dt: float):
        for w in self.wagons:
            w.flash = max(0.0, w.flash - dt)
            if w.destroyed:
                continue
            if w.burning > 0:
                w.burn_time += dt
                w.ref.hp -= 6.0 * w.burning * dt
                if w.burn_time > 18:
                    w.burning = 0
                    w.burn_time = 0
                elif self.rng.random() < 0.03 * dt * 10 * 0.2:
                    nb = self.wagons[(w.idx + self.rng.choice([-1, 1])) % self.n]
                    if not nb.destroyed and nb.burning <= 0 and self.rng.random() < 0.5:
                        nb.burning = 0.7
                        nb.burn_time = 0
                        self.say(f"¡El fuego se extiende a la carreta {nb.idx + 1}!", (255, 150, 90))
            if w.ref.hp <= 0:
                self._destroy_wagon(w)

    def _destroy_wagon(self, w: BWagon):
        w.destroyed = True
        w.ref.hp = 0
        w.burning = 0
        self.ruined.append(w.idx)
        self.say(f"¡La carreta {w.idx + 1} ha caído! Hay un hueco en el círculo.", (255, 120, 100))
        self.emit("boom", w.x, w.y)
        for c in self.game.colonists:
            if c.post and c.post[0] == w.idx:
                c.post = None

    # ----------------------------------------------------------- disparo
    def _shooter_stats(self, bc: BColonist, w: BWagon):
        c = bc.ref
        skill = c.shoot
        cd = 8.0 * (1.3 - 0.06 * skill)
        helper = self.game.post_of(w.idx, "ayuda")
        if helper is not None and helper.health > 25:
            cd *= 0.68
        if c.health < 50:
            cd *= 1.25
        return skill, cd

    def hit_chance(self, bc: BColonist, w: BWagon, f: Foe) -> float:
        c = bc.ref
        d = math.hypot(f.x - w.x, f.y - w.y)
        rng_ = RIFLE_RANGE + (PLATFORM_RANGE if w.ref.platform else 0)
        base = 0.24 + 0.04 * c.shoot
        distf = 1.0 if d <= 120 else max(0.35, 1.0 - (d - 120) / (rng_ - 120) * 0.65)
        hf = 0.7 if c.health < 50 else 1.0
        mf = 0.8 + 0.4 * (self.game.morale / 100.0)
        nf = 1.0
        if self.night and not w.ref.lantern:
            nf = 0.75
        pf = 1.15 if w.ref.platform else 1.0
        mv = 0.8 if f.mounted and f.state in ("orbit", "approach", "retreat") else 1.0
        return max(0.05, min(0.95, base * distf * hf * mf * nf * pf * mv))

    def _targets_for(self, w: BWagon) -> list[Foe]:
        rng_ = RIFLE_RANGE + (PLATFORM_RANGE if w.ref.platform else 0)
        out = []
        for f in self.foes:
            if not f.alive or f.fled or f.state == "flee":
                continue
            d = math.hypot(f.x - w.x, f.y - w.y)
            if d > rng_:
                continue
            if not self.is_visible(f):
                continue
            out.append(f)
        return out

    def _shoot(self, dt: float):
        g = self.game
        for w in self.wagons:
            if w.destroyed:
                continue
            bc = None
            for b in self.colonists:
                if b.alive and b.ref.post == (w.idx, "tirador") and b.task == "post":
                    bc = b
                    break
            if bc is None:
                continue
            bc.cool = max(0.0, bc.cool - dt)
            if bc.cool > 0 or self.policy == "alto":
                continue
            if bc.ref.health < 15:
                continue
            if g.sup.ammo <= 0:
                continue
            if bc and math.hypot(bc.x - self.post_pos(w.idx, "tirador")[0], bc.y - self.post_pos(w.idx, "tirador")[1]) > 6:
                continue
            if w.ref.cannon:
                self._fire_cannon(bc, w)
                continue
            targets = self._targets_for(w)
            if self.policy == "contenido":
                targets = [f for f in targets if math.hypot(f.x - w.x, f.y - w.y) < 210]
            if not targets:
                continue
            tgt = None
            if self.focus is not None and self.focus in targets:
                tgt = self.focus
            else:
                tgt = min(targets, key=lambda f: math.hypot(f.x - w.x, f.y - w.y) - (30 if f.kind in ("fuego", "bandido") else 0)
                          - (90 if f.state in ("inside", "attack") else 0))
            skill, cd = self._shooter_stats(bc, w)
            bc.cool = cd * self.rng.uniform(0.9, 1.15)
            g.sup.ammo -= 1
            ok = self.rng.random() < self.hit_chance(bc, w, tgt)
            px, py = self.post_pos(w.idx, "tirador")
            self.emit("shot", px, py, tgt.x, tgt.y, ok)
            bc.flash = 0.15
            bc.aim = (tgt.x, tgt.y)
            if ok:
                dmg = self.rng.uniform(30, 55) + 2 * (skill - 5)
                self._damage_foe(tgt, dmg, bc.ref)
        if g.sup.ammo <= 0 and not getattr(self, "_warned_ammo", False) and self.fight_time > 0:
            self._warned_ammo = True
            self.say("¡SIN MUNICIÓN! Funde utensilios (F) o intenta parlamentar (P).", (255, 120, 100))

    def _fire_cannon(self, bc: BColonist, w: BWagon):
        g = self.game
        rng_ = 440.0
        best = None
        bestn = 0
        for f in self._targets_for(w):
            if math.hypot(f.x - w.x, f.y - w.y) > rng_ or math.hypot(f.x - w.x, f.y - w.y) < 70:
                continue
            n = sum(1 for o in self.foes if o.alive and not o.fled and math.hypot(o.x - f.x, o.y - f.y) < 58)
            if n > bestn:
                best, bestn = f, n
        if best is None or g.sup.ammo < 3:
            return
        helper = g.post_of(w.idx, "ayuda")
        bc.cool = (9.0 if helper is None else 6.4) * self.rng.uniform(0.95, 1.1)
        g.sup.ammo -= 3
        px, py = self.post_pos(w.idx, "tirador")
        self.emit("cannon", px, py, best.x, best.y)
        for o in list(self.foes):
            if not o.alive or o.fled:
                continue
            d = math.hypot(o.x - best.x, o.y - best.y)
            if d < 62:
                self._damage_foe(o, 85 * (1 - d / 140), bc.ref)

    def _damage_foe(self, f: Foe, dmg: float, by: Optional[Colonist]):
        f.hp -= dmg
        f.flash = 0.2
        self.emit("hit", f.x, f.y)
        if f.hp <= 0 and f.alive:
            f.alive = False
            self.killed += 1
            if by is not None:
                by.kills += 1
            self.emit("death", f.x, f.y, f.kind)
            if f.kind == "jefe":
                self.chief_dead = True
                self.say("¡El jefe de guerra ha caído! Sus hombres titubean.", (190, 255, 160))
                for o in self.alive_foes():
                    if self.rng.random() < 0.6:
                        o.state = "flee"

    # ----------------------------------------------------------- enemigos
    def _nearest_open_sector(self, ang: float) -> Optional[BWagon]:
        best = None
        bd = 9.0
        for w in self.wagons:
            if w.destroyed and w.barricade <= 0:
                d = abs(ang_diff(w.angle, ang))
                if d < bd:
                    best, bd = w, d
        return best if bd < 1.6 else None

    def _update_foes(self, dt: float):
        boss = [f for f in self.foes if f.alive and f.kind == "jefe"]
        for f in self.foes:
            if not f.alive or f.fled:
                continue
            speed = f.speed
            for b in boss:
                if b is not f and math.hypot(b.x - f.x, b.y - f.y) < 200:
                    speed *= 1.15
                    break
            r = math.hypot(f.x, f.y)
            ang = math.atan2(f.y, f.x)
            if f.state == "flee":
                f.x += f.x / max(r, 1) * speed * 1.2 * dt
                f.y += f.y / max(r, 1) * speed * 1.2 * dt
                f.face = ang
                if r > FIELD_RADIUS + 40:
                    f.fled = True
                    self.fled_count += 1
                continue
            if f.kind in ("jinete", "jefe"):
                self._ai_rider(f, r, ang, speed, dt)
            elif f.kind == "fuego":
                self._ai_stander(f, r, ang, speed, dt, fire=True)
            elif f.kind == "bandido":
                self._ai_stander(f, r, ang, speed, dt, fire=False)
            else:
                self._ai_melee(f, r, ang, speed, dt)

    def _ai_rider(self, f: Foe, r, ang, speed, dt):
        if f.state == "approach":
            tr = f.orbit_r
            if r > tr + 8:
                self._move(f, f.x - f.x / r * 200, f.y - f.y / r * 200, speed, dt)
            else:
                f.state = "orbit"
        elif f.state == "orbit":
            w = (speed * 0.55) / max(f.orbit_r, 1) * f.orbit_dir
            na = ang + w * dt
            rr = r + (f.orbit_r - r) * min(1.0, dt * 2)
            f.x, f.y = math.cos(na) * rr, math.sin(na) * rr
            f.face = na + (math.pi / 2) * f.orbit_dir
            f.cool -= dt
            if f.cool <= 0 and f.shots > 0:
                f.cool = self.rng.uniform(1.8, 3.0) if f.kind == "jinete" else self.rng.uniform(3.0, 4.2)
                f.shots -= 1
                self._enemy_arrow(f, fire=False)
                if f.shots <= 0:
                    f.state = "retreat"
                    f.timer = self.rng.uniform(5, 9)
        elif f.state == "retreat":
            f.timer -= dt
            self._move(f, f.x * 2, f.y * 2, speed, dt)
            if f.timer <= 0:
                f.state = "approach"
                f.shots = self.rng.randint(3, 6)
                f.orbit_dir = self.rng.choice([-1, 1])
                f.orbit_r = max(self.R_out + 100, f.orbit_r + self.rng.uniform(-30, 30))

    def _ai_stander(self, f: Foe, r, ang, speed, dt, fire: bool):
        if f.state == "approach":
            if r > f.stand_r + 5:
                self._move(f, 0, 0, speed, dt)
            else:
                f.state = "stand"
                f.cool = self.rng.uniform(0.5, 2.5)
        else:
            f.face = ang + math.pi
            f.cool -= dt
            if f.cool <= 0:
                if fire:
                    f.cool = self.rng.uniform(3.8, 5.5)
                    self._enemy_arrow(f, fire=True)
                else:
                    f.cool = self.rng.uniform(3.4, 5.0)
                    self._enemy_rifle(f)

    def _ai_melee(self, f: Foe, r, ang, speed, dt):
        # ¿hueco abierto cerca? ir hacia él
        gap = self._nearest_open_sector(ang)
        if r > self.R_out + 4:
            if gap is not None:
                gx, gy = math.cos(gap.angle) * (self.R_out + 8), math.sin(gap.angle) * (self.R_out + 8)
                if r > self.R_out + 60 or abs(ang_diff(gap.angle, ang)) > 0.08:
                    self._move(f, gx * 1.0 + (f.x - gx) * 0.0, gy, speed, dt)
                    return
            sec = self.wagons[self.sector(ang)]
            if sec.blocked:
                tx, ty = math.cos(ang) * (self.R_out + 2), math.sin(ang) * (self.R_out + 2)
                self._move(f, tx, ty, speed, dt)
                if math.hypot(f.x, f.y) <= self.R_out + 6:
                    f.state = "attack"
                    f.target_wagon = sec.idx
            else:
                self._move(f, 0, 0, speed, dt)
            return
        if f.state == "attack" or r <= self.R_out + 6:
            sec = self.wagons[self.sector(ang)]
            if sec.blocked:
                f.state = "attack"
                f.target_wagon = sec.idx
                f.attack_cool -= dt
                if f.attack_cool <= 0:
                    f.attack_cool = 1.0
                    self._melee_wagon(f, sec)
                return
            f.state = "inside"
        # interior: ir a por el colonista más cercano
        foes_in = [bc for bc in self.colonists if bc.alive]
        if not foes_in:
            return
        tgt = min(foes_in, key=lambda b: math.hypot(b.x - f.x, b.y - f.y))
        d = math.hypot(tgt.x - f.x, tgt.y - f.y)
        if d > 14:
            self._move(f, tgt.x, tgt.y, speed, dt)
        else:
            f.attack_cool -= dt
            if f.attack_cool <= 0:
                f.attack_cool = 0.9
                self._hurt_colonist(tgt, self.rng.uniform(9, 16), f)
        # saqueo
        if math.hypot(f.x, f.y) < 40:
            f.timer += dt
            if f.timer > 3.0:
                f.timer = 0
                s = self.game.sup
                s.food = max(0, s.food - 12)
                s.goods = max(0, s.goods - (1 if self.rng.random() < 0.4 else 0))

    def _melee_wagon(self, f: Foe, sec: BWagon):
        dmg = 8.0 * (1.5 if f.kind == "jefe" else 1.0)
        reinforce = 1.0 - 0.08 * sec.ref.reinforced
        if sec.destroyed and sec.barricade > 0:
            sec.barricade -= dmg
            if sec.barricade <= 0:
                sec.barricade = 0
                self.say(f"¡La barricada del hueco {sec.idx + 1} cede!", (255, 140, 100))
            self.emit("chop", f.x, f.y)
            return
        sec.ref.hp -= dmg * reinforce
        sec.flash = 0.2
        self.emit("chop", f.x, f.y)
        # abordaje
        if self.rng.random() < 0.3:
            tir = self.game.post_of(sec.idx, "tirador")
            if tir is not None:
                for bc in self.colonists:
                    if bc.ref is tir and bc.alive:
                        self._hurt_colonist(bc, self.rng.uniform(7, 13), f)
        if sec.ref.hp <= 0 and not sec.destroyed:
            self._destroy_wagon(sec)

    def _enemy_arrow(self, f: Foe, fire: bool):
        ang = math.atan2(f.y, f.x)
        cands = [w for w in self.wagons if not w.destroyed and abs(ang_diff(w.angle, ang)) < 1.0]
        if not cands:
            cands = [w for w in self.wagons if not w.destroyed]
        if not cands:
            return
        w = self.rng.choice(cands)
        tc = None
        hit_col = self.rng.random() < (0.30 + (0.08 if w.ref.platform else 0) - 0.04 * w.ref.reinforced) and not fire
        if hit_col:
            for k, bc in enumerate(self.colonists):
                if bc.alive and bc.ref.post and bc.ref.post[0] == w.idx:
                    tc = k
                    break
        tx, ty = (self.colonists[tc].x, self.colonists[tc].y) if tc is not None else (w.x * 0.98, w.y * 0.98)
        tx += self.rng.uniform(-9, 9)
        ty += self.rng.uniform(-9, 9)
        dmg = self.rng.uniform(12, 20)
        self.arrows.append(Arrow(f.x, f.y, tx, ty, fire, dmg, w.idx, tc))
        f.flash = 0.1
        f.revealed = 3.0
        self.emit("bow", f.x, f.y, fire)

    def _enemy_rifle(self, f: Foe):
        ang = math.atan2(f.y, f.x)
        cands = [w for w in self.wagons if not w.destroyed and abs(ang_diff(w.angle, ang)) < 0.9]
        if not cands:
            return
        w = self.rng.choice(cands)
        self.emit("rifle", f.x, f.y, w.x, w.y)
        f.revealed = 3.0
        tir = [bc for bc in self.colonists if bc.alive and bc.ref.post and bc.ref.post[0] == w.idx]
        if tir and self.rng.random() < 0.28 - 0.03 * w.ref.reinforced + (0.06 if w.ref.platform else 0):
            self._hurt_colonist(self.rng.choice(tir), self.rng.uniform(20, 32), f)
        else:
            w.ref.hp -= 9
            w.flash = 0.15
            if w.ref.hp <= 0 and not w.destroyed:
                self._destroy_wagon(w)

    def _hurt_colonist(self, bc: BColonist, dmg: float, src=None):
        c = bc.ref
        if not c.alive:
            return
        c.health -= dmg * (0.8 if c.group == "adulto" else 1.0) * (1.25 if c.group in ("niño", "anciano") else 1.0)
        bc.flash = 0.35
        self.emit("hurt", bc.x, bc.y)
        if c.health <= 0:
            c.alive = False
            c.cause = "muerto en combate"
            c.post = None
            self.dead_names.append(c.name)
            self.game.stats["lost"] += 1
            self.game.morale = max(0.0, self.game.morale - 6)
            self.say(f"¡{c.name} ha muerto!", (255, 110, 100))
            self.emit("death_col", bc.x, bc.y)

    def _update_arrows(self, dt: float):
        for a in list(self.arrows):
            dx, dy = a.tx - a.x, a.ty - a.y
            d = math.hypot(dx, dy)
            step = a.speed * dt
            if d <= step:
                self.arrows.remove(a)
                self._arrow_hit(a)
            else:
                a.x += dx / d * step
                a.y += dy / d * step

    def _arrow_hit(self, a: Arrow):
        w = self.wagons[a.target_wagon]
        if a.target_colonist is not None:
            bc = self.colonists[a.target_colonist]
            if bc.alive and math.hypot(bc.x - a.tx, bc.y - a.ty) < 26:
                self._hurt_colonist(bc, a.dmg)
                return
        if w.destroyed:
            return
        w.ref.hp -= 6.0 * (1 - 0.08 * w.ref.reinforced)
        w.flash = 0.15
        self.emit("thunk", a.tx, a.ty)
        if a.fire and self.rng.random() < 0.75 and w.burning <= 0:
            w.burning = 1.0
            w.burn_time = 0
            self.say(f"¡Flecha incendiaria! La carreta {w.idx + 1} arde.", (255, 150, 80))
        if w.ref.hp <= 0 and not w.destroyed:
            self._destroy_wagon(w)

    def _update_allies(self, dt: float):
        for al in self.allies:
            if not al.alive:
                continue
            al.life -= dt
            al.cool -= dt
            if al.life <= 0:
                al.alive = False
                continue
            foes = self.alive_foes()
            if not foes:
                self._move(al, math.cos(al.life) * (self.R + 220), math.sin(al.life) * (self.R + 220), 160, dt)
                continue
            tgt = min(foes, key=lambda f: math.hypot(f.x - al.x, f.y - al.y))
            d = math.hypot(tgt.x - al.x, tgt.y - al.y)
            if d > 22:
                self._move(al, tgt.x, tgt.y, 190, dt)
            elif al.cool <= 0:
                al.cool = 1.1
                self._damage_foe(tgt, self.rng.uniform(28, 45), None)
                if self.rng.random() < 0.12:
                    al.hp -= 25
                    if al.hp <= 0:
                        al.alive = False

    # ----------------------------------------------------------- moral enemiga y final
    def _morale_check(self, dt: float):
        self.check_cd -= dt
        if self.check_cd > 0 or self.retreating or self.peace:
            return
        self.check_cd = 0.5
        total = max(1, self.total_foes)
        casualties = (self.killed + self.fled_count) / total
        thresh = 0.55 if self.spec.foe != "bandidos" else 0.45
        if any(f.alive and f.kind == "jefe" for f in self.foes):
            thresh += 0.15
        if self.spec.foe in data.TRIBES and self.game.tribes[self.spec.foe].arms > 6:
            thresh += 0.05
        if casualties >= thresh and not self.pending:
            self.retreating = True
            self.say("¡El enemigo rompe filas y se retira!", (190, 255, 160))
            for f in self.alive_foes():
                f.state = "flee"
        if self.fight_time > GIVE_UP_TIME and not self.retreating:
            self.retreating = True
            self.say("Cae la tarde; el enemigo se cansa y se retira.", (190, 255, 160))
            for f in self.alive_foes():
                f.state = "flee"

    def _check_end(self):
        living = [bc for bc in self.colonists if bc.alive]
        can_fight = [bc for bc in living if bc.ref.can_shoot]
        if not living:
            self._finish("derrota")
            return
        if all(w.destroyed for w in self.wagons) or (not can_fight and self.alive_foes() and
                                                      any(math.hypot(f.x, f.y) < self.R for f in self.alive_foes())):
            self._finish("derrota")
            return
        if not self.pending and not self.alive_foes():
            if self.peace:
                self._finish("paz")
            elif self.retreating or self.fled_count:
                self._finish("victoria" if self.killed >= self.total_foes * 0.6 else "huida")
            else:
                self._finish("victoria")

    def _finish(self, outcome: str):
        if self.done:
            return
        self.done = True
        g = self.game
        res = BattleResult(outcome=outcome, foes_killed=self.killed, foes_total=self.total_foes,
                           dead=list(self.dead_names), ammo_used=max(0, self.ammo_start - g.sup.ammo + self.melt_used * 12),
                           time=self.fight_time)
        # carretas destruidas se pierden con parte de la carga
        lost = [w for w in self.wagons if w.destroyed]
        res.wagons_lost = len(lost)
        if lost:
            frac = len(lost) / max(1, len(self.wagons))
            g.sup.food = max(0, g.sup.food * (1 - frac * 0.8))
            g.sup.goods = int(g.sup.goods * (1 - frac * 0.7))
            g.sup.ammo = int(g.sup.ammo * (1 - frac * 0.5))
            g.wagons = [w.ref for w in self.wagons if not w.destroyed]
            if not g.wagons:
                from .model import Wagon
                g.wagons = [Wagon(hp=40.0)]  # los supervivientes salvan una carreta maltrecha
            # los barricadas ya no existen tras el combate
        for c in g.colonists:
            if c.alive and c.health < 8:
                c.health = 8
        for bc in self.colonists:
            bc.ref.post = bc.ref.post if bc.ref.alive else None
        g.normalize_posts()
        self.result = res
        self.say({"victoria": "¡Victoria!", "huida": "El enemigo se ha retirado.", "paz": "Se ha acordado la paz.",
                  "derrota": "Todo está perdido…"}[outcome])


def run_headless(game: Game, spec: BattleSpec, seed: int = 0, dt: float = 0.1, max_time: float = 600.0,
                 policy: str = "libre", smart: bool = True) -> BattleResult:
    """Ejecuta un combate completo sin interfaz (para pruebas y simulaciones)."""
    b = Battle(game, spec, seed)
    b.policy = policy
    b.start_fight()
    t = 0.0
    nxt = 0.0
    while not b.done and t < max_time:
        if smart and t >= nxt:
            b.auto_assign()
            nxt = t + 6.0
            if b.game.sup.parts > 0:
                for w in b.wagons:
                    if w.destroyed and w.barricade <= 0 and w.build_progress <= 0:
                        b.order_barricade(w.idx)
        b.update(dt)
        t += dt
    if not b.done:
        b._finish("huida")
    return b.result
