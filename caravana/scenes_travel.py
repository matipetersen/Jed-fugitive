"""Escena de viaje: mapa de la ruta, paisaje con la caravana, avisos, campamento y diario."""
from __future__ import annotations

import math
import random

import pygame

from . import art, data, ui
from .model import (ArrivalSpec, BattleSpec, Contact, ContactSpec, EndSpec, ForkSpec, Game, Option, Prompt,
                    ShopSpec)
from .scene import Scene
from .ui import C, Button, text, panel, para, bar

DAY_TIME = 0.75


# ====================================================================== avisos modales
class PromptScene(Scene):
    overlay = True

    def __init__(self, app, prompt: Prompt):
        super().__init__(app)
        self.prompt = prompt
        self.btns: list[Button] = []
        self.rect = pygame.Rect(0, 0, 700, 300)
        self._layout()

    def _layout(self):
        p = self.prompt
        body_lines = ui.wrap(p.body, 19, 640)
        h_body = len(body_lines) * (ui.font(19).get_linesize() + 3)
        n = len(p.options)
        h = 78 + h_body + 20 + n * 54 + 20
        self.rect = pygame.Rect(0, 0, 700, h)
        self.rect.center = (ui.W // 2, ui.H // 2 - 10)
        self.btns = []
        y = self.rect.y + 78 + h_body + 20
        for i, opt in enumerate(p.options):
            lbl = opt.label + (f"   ·   {opt.hint}" if opt.hint else "")
            b = Button((self.rect.x + 30, y, 640, 46), lbl, (lambda o=opt: self._choose(o)), size=18,
                       key=(pygame.K_1 + i) if i < 9 else None)
            self.btns.append(b)
            y += 54

    def _choose(self, opt: Option):
        res = opt.action()
        self.app.pop()
        if res is not None:
            self.app.handle_interrupt(res)

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE) and len(self.prompt.options) == 1:
            self._choose(self.prompt.options[0])

    def draw(self, screen):
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 165))
        screen.blit(veil, (0, 0))
        col = {"info": C["gold"], "good": C["green"], "danger": C["red"]}[self.prompt.tone]
        panel(screen, self.rect, C["panel"], col, 12, width=3)
        text(screen, self.prompt.title, (self.rect.centerx, self.rect.y + 20), 32, col, bold=True, serif=True, anchor="midtop", shadow=True)
        para(screen, self.prompt.body, (self.rect.x + 30, self.rect.y + 76), 640, 19, C["text"], gap=3)
        for b in self.btns:
            b.draw(screen)


class JournalScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.g = app.game
        self.scroll = 0
        self.close = Button((ui.W // 2 - 70, 624, 140, 42), "Cerrar", self.app.pop, size=18)

    def handle(self, ev):
        if self.close.handle(ev):
            return
        if ev.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - ev.y * 2)
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.app.pop()
            elif ev.key == pygame.K_DOWN:
                self.scroll += 2
            elif ev.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 2)

    def draw(self, screen):
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 175))
        screen.blit(veil, (0, 0))
        panel(screen, (240, 60, 800, 620), C["parch"], C["edge"], 12, width=3)
        text(screen, "Diario de la caravana", (640, 78), 34, C["ink"], serif=True, bold=True, anchor="midtop")
        lines = list(reversed(self.g.journal))
        self.scroll = min(self.scroll, max(0, len(lines) - 18))
        y = 130
        for d, t in lines[self.scroll:self.scroll + 18]:
            text(screen, f"Día {d}", (270, y), 15, (120, 84, 44), bold=True)
            text(screen, t, (350, y), 16, C["ink"])
            y += 26
        text(screen, "Rueda del ratón: desplazar", (640, 604), 13, (110, 90, 60), anchor="midtop")
        self.close.draw(screen)


# ====================================================================== viaje
def _hills(surf, rect, color, base, amp, freq, offset, seed):
    pts = [(rect.x, rect.bottom)]
    for x in range(rect.x, rect.right + 8, 8):
        y = base + math.sin((x + offset) * freq + seed) * amp + math.sin((x + offset) * freq * 2.3 + seed * 2) * amp * 0.45
        pts.append((x, y))
    pts.append((rect.right, rect.bottom))
    pygame.draw.polygon(surf, color, pts)


def draw_side_wagon(surf, x, y, s, t, phase, oxen=True, hp=1.0):
    """Carreta de lado, con yunta de bueyes, mirando a la derecha. (x,y) = suelo bajo el eje trasero."""
    bob = math.sin(t * 6 + phase) * 1.2 * s
    # sombra
    pygame.draw.ellipse(surf, (40, 60, 30), (x - 70 * s, y - 4 * s, 200 * s, 9 * s))
    # caja
    body = pygame.Rect(x - 60 * s, y - 50 * s + bob, 118 * s, 24 * s)
    pygame.draw.rect(surf, (118, 82, 48), body, border_radius=3)
    pygame.draw.rect(surf, (70, 48, 28), body, 2, border_radius=3)
    for i in range(1, 5):
        pygame.draw.line(surf, (88, 60, 36), (body.x + i * body.w / 5, body.y + 2), (body.x + i * body.w / 5, body.bottom - 2), 1)
    # lona
    cover = [(x - 56 * s, y - 50 * s + bob)]
    for a in range(0, 181, 12):
        r = math.radians(a)
        cover.append((x - 2 * s - math.cos(r) * 56 * s, y - 50 * s + bob - math.sin(r) * 38 * s))
    cover.append((x + 54 * s, y - 50 * s + bob))
    col = (232, 222, 190) if hp > 0.5 else (200, 188, 156)
    pygame.draw.polygon(surf, col, cover)
    pygame.draw.polygon(surf, (150, 134, 104), cover, 2)
    for i in range(1, 6):
        xx = x - 56 * s + i * 18 * s
        top = y - 50 * s + bob - math.sin(math.acos(max(-1, min(1, (x - 2 * s - xx) / (56 * s))))) * 38 * s
        pygame.draw.line(surf, (190, 176, 140), (xx, y - 50 * s + bob), (xx, top), 1)
    # ruedas
    for wx, wr in ((x - 32 * s, 19 * s), (x + 30 * s, 15 * s)):
        pygame.draw.circle(surf, (40, 30, 22), (wx, y - wr + bob * 0.3), wr)
        pygame.draw.circle(surf, (110, 82, 50), (wx, y - wr + bob * 0.3), wr - 3 * s)
        pygame.draw.circle(surf, (40, 30, 22), (wx, y - wr + bob * 0.3), wr - 5 * s)
        for k in range(8):
            a = t * 5 + phase + k * math.pi / 4
            pygame.draw.line(surf, (110, 82, 50), (wx, y - wr + bob * 0.3),
                             (wx + math.cos(a) * (wr - 3 * s), y - wr + bob * 0.3 + math.sin(a) * (wr - 3 * s)), 2)
    # conductor
    pygame.draw.circle(surf, (222, 184, 150), (x + 46 * s, y - 62 * s + bob), 5 * s)
    pygame.draw.ellipse(surf, (70, 52, 36), (x + 39 * s, y - 70 * s + bob, 14 * s, 5 * s))
    pygame.draw.rect(surf, (90, 110, 150), (x + 41 * s, y - 57 * s + bob, 10 * s, 9 * s), border_radius=2)
    if oxen:
        pygame.draw.line(surf, (80, 58, 36), (x + 56 * s, y - 30 * s), (x + 118 * s, y - 36 * s), 3)
        for k, ox in enumerate((x + 96 * s, x + 130 * s)):
            ph = t * 6 + phase + k
            oy = y - 4 * s + math.sin(ph * 2) * 1.0
            # patas
            for lx, lp in ((-14, 0), (-8, math.pi), (8, math.pi * 0.5), (14, math.pi * 1.5)):
                sw = math.sin(ph + lp) * 4 * s
                pygame.draw.line(surf, (70, 50, 34), (ox + lx * s, oy - 22 * s), (ox + lx * s + sw, oy), max(2, int(3 * s)))
            pygame.draw.ellipse(surf, (110, 78, 52), (ox - 22 * s, oy - 40 * s, 44 * s, 22 * s))
            pygame.draw.circle(surf, (96, 66, 44), (ox + 24 * s, oy - 34 * s), 8 * s)
            pygame.draw.line(surf, (240, 236, 220), (ox + 24 * s, oy - 40 * s), (ox + 30 * s, oy - 47 * s), 2)
            pygame.draw.line(surf, (80, 58, 36), (ox - 8 * s, oy - 40 * s), (ox + 8 * s, oy - 40 * s), 3)


class TravelScene(Scene):
    def __init__(self, app, intro: bool = False):
        super().__init__(app)
        app.travel = self
        self.g: Game = app.game
        self.moving = False
        self.speed = 1
        self.acc = 0.0
        self.scroll = 0.0
        self.t = 0.0
        self.feed: list[tuple[str, tuple]] = []
        self.parts = art.Particles()
        self.rain: list = []
        self.btns: list[Button] = []
        self.hover_tip = ""
        self._build()
        self._intro = intro

    def enter(self):
        if self._intro:
            self._intro = False
            g = self.g
            self.push_feed("La caravana parte de Independence.", C["gold"])
            self.app.push(PromptScene(self.app, Prompt.info(
                "Independence, 15 de abril de 1848",
                f"{g.leader_name} y sus 13 compañeros miran el horizonte. Por delante hay 1.950 millas, ríos crecidos, "
                "pasos de montaña y pueblos que ya vieron pasar a demasiados forasteros.\n\n"
                "Ritmo, raciones y guardia se ajustan abajo. Acampa cuando lo necesites. Y pase lo que pase: "
                "llegad antes del 15 de diciembre.", "info")))

    def resume(self):
        self._build()

    # ------------------------------------------------------------ botones
    def _build(self):
        g = self.g
        x0 = 832
        w = 180
        h = 36
        gap = 6
        y0 = 548
        self.go_btn = Button((x0, y0, 2 * w + gap, 44), "", self._toggle, size=21, color=(98, 74, 40), key=pygame.K_SPACE)
        rows = [
            ("Acampar (C)", self._camp, pygame.K_c),
            ("Plan de defensa (D)", self._defense, pygame.K_d),
            ("", self._cycle_pace, pygame.K_r),
            ("", self._cycle_rations, pygame.K_t),
            ("", self._cycle_watch, pygame.K_g),
            ("Diario (J)", self._journal, pygame.K_j),
        ]
        self.btns = [self.go_btn]
        self.dyn = {}
        for i, (lbl, fn, key) in enumerate(rows):
            col, row = i % 2, i // 2
            b = Button((x0 + col * (w + gap), y0 + 50 + row * (h + gap), w, h), lbl, fn, size=15, key=key)
            self.btns.append(b)
        self.pace_btn, self.rations_btn, self.watch_btn = self.btns[3], self.btns[4], self.btns[5]
        self.speed_btn = Button((x0 + 2 * w + gap + 8, y0, 66, 44), "x1", self._cycle_speed, size=18)
        self.menu_btn = Button((x0 + 2 * w + gap + 8, y0 + 50, 66, 36), "Menú", self._menu, size=14)
        self.btns += [self.speed_btn, self.menu_btn]

    def _toggle(self):
        self.moving = not self.moving
        self.acc = DAY_TIME * 0.6

    def _camp(self):
        self.moving = False
        self.app.push(CampScene(self.app, None))

    def _defense(self):
        from .scenes_defense import DefenseScene
        self.moving = False
        self.app.push(DefenseScene(self.app))

    def _journal(self):
        self.moving = False
        self.app.push(JournalScene(self.app))

    def _cycle_pace(self):
        order = list(data.PACES)
        self.g.pace = order[(order.index(self.g.pace) + 1) % 3]

    def _cycle_rations(self):
        order = list(data.RATIONS)
        self.g.rations = order[(order.index(self.g.rations) + 1) % 3]

    def _cycle_watch(self):
        order = list(data.WATCH_LABEL)
        self.g.watch = order[(order.index(self.g.watch) + 1) % 3]

    def _cycle_speed(self):
        self.speed = {1: 2, 2: 4, 4: 1}[self.speed]

    def _menu(self):
        self.moving = False
        self.app.autosave()
        self.app.push(ConfirmQuit(self.app))

    # ------------------------------------------------------------ avisos
    def push_feed(self, s, col=None):
        self.feed.append((s, col or C["text"]))
        self.feed = self.feed[-7:]

    def consume_notices(self):
        g = self.g
        for n in g.notices:
            bad = any(w in n for w in ("muer", "enferm", "agot", "Ladrones", "Desastre", "perd", "roto", "rompe"))
            self.push_feed(n, C["orange"] if bad else C["parch"])
        g.notices.clear()

    # ------------------------------------------------------------ interrupciones
    def handle_interrupt(self, it):
        from .scenes_diplo import DiplomacyScene
        from .battle_view import BattleScene
        from .scenes_menu import EndScene
        from .scenes_settle import SiteScene
        from .scenes_trade import ShopScene
        g = self.g
        if it is None:
            return
        if isinstance(it, Prompt):
            self.app.push(PromptScene(self.app, it))
        elif isinstance(it, ContactSpec):
            self.moving = False
            c = Contact(g, it.tribe, it.kind, it.prep_text)
            self.app.push(DiplomacyScene(self.app, c))
        elif isinstance(it, BattleSpec):
            self.moving = False
            sc = BattleScene(self.app, g, it, lambda res, spec=it: self._battle_done(spec, res))
            self.app.push(sc)
        elif isinstance(it, ShopSpec):
            self.moving = False
            self.app.push(ShopScene(self.app, it))
        elif isinstance(it, ArrivalSpec):
            self.moving = False
            self.app.autosave()
            self.app.push(CampScene(self.app, it.waypoint))
        elif isinstance(it, ForkSpec):
            self.moving = False
            self.app.push(SiteScene(self.app))
        elif isinstance(it, EndSpec):
            self.moving = False
            self.app.replace(EndScene(self.app, it.title, it.body, it.victory))

    def _battle_done(self, spec, res):
        from .scenes_menu import EndScene
        g = self.g
        self.app.pop()  # BattleScene
        prompt = g.apply_battle(spec, res)
        if not g.living():
            g.over = True
            self.app.replace(EndScene(self.app, "La caravana ha caído",
                                      "El último defensor cae al pie de las carretas. El viento levanta ceniza sobre el camino a Oregón."))
            return
        self.app.autosave()
        self.app.push(PromptScene(self.app, prompt))

    # ------------------------------------------------------------ bucle
    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.MOUSEMOTION:
            self.hover_tip = ""
            for b, tip in ((self.pace_btn, "Ritmo: lento ahorra a los bueyes y a la gente; rápido cansa y enferma."),
                           (self.rations_btn, "Raciones: escasas ahorran comida pero debilitan; abundantes alimentan y suben la moral."),
                           (self.watch_btn, "Guardia: más vigilancia da más avisos antes de un ataque, a cambio de cansancio.")):
                if b.rect.collidepoint(ev.pos):
                    self.hover_tip = tip
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._menu()

    def update(self, dt):
        self.t += dt
        g = self.g
        self.pace_btn.label = f"Ritmo: {data.PACE_LABEL[g.pace]} (R)"
        self.rations_btn.label = f"Raciones: {data.RATION_LABEL[g.rations]} (T)"
        self.watch_btn.label = f"{data.WATCH_LABEL[g.watch]} (G)"
        self.go_btn.label = "Detener la marcha (Espacio)" if self.moving else "Continuar el viaje (Espacio)"
        self.speed_btn.label = f"x{self.speed}"
        if self.moving and not g.over:
            self.scroll += dt * 90 * self.speed * (0.6 if g.pace == "lento" else 1.35 if g.pace == "rapido" else 1.0)
            self.acc += dt * self.speed
            guard = 0
            while self.acc >= DAY_TIME and self.moving and guard < 8:
                guard += 1
                self.acc -= DAY_TIME
                it = g.advance_day()
                self.consume_notices()
                if it is not None:
                    self.handle_interrupt(it)
                    break
            if random.random() < 0.7:
                self.parts.add("dust", 140 + random.random() * 900, 484 + random.random() * 10, 1)
        self.parts.update(dt)
        # lluvia/nieve
        if g.weather in ("lluvia", "tormenta", "nieve") and len(self.rain) < 160:
            for _ in range(6):
                self.rain.append([random.uniform(0, ui.W), random.uniform(250, 300), random.uniform(0.7, 1.3)])
        spd = {"lluvia": 520, "tormenta": 700, "nieve": 90}.get(g.weather, 0)
        for r in self.rain:
            r[1] += spd * dt * r[2]
            r[0] += (-60 if g.weather != "nieve" else math.sin(self.t * 2 + r[0]) * 20) * dt
        self.rain = [r for r in self.rain if r[1] < 520 and g.weather in ("lluvia", "tormenta", "nieve")]

    # ------------------------------------------------------------ dibujo
    def draw(self, screen):
        g = self.g
        screen.fill(C["bg"])
        self._draw_header(screen)
        self._draw_map(screen, pygame.Rect(0, 56, ui.W, 196))
        self._draw_landscape(screen, pygame.Rect(0, 254, ui.W, 262))
        self._draw_bottom(screen)
        if self.hover_tip:
            ui.draw_tooltip(screen, self.hover_tip, pygame.mouse.get_pos())

    def _draw_header(self, screen):
        g = self.g
        panel(screen, (0, 0, ui.W, 56), (40, 30, 20), C["edge"], 0)
        text(screen, f"Día {g.day} · {g.date_text()}", (16, 8), 22, C["gold"], bold=True, serif=True)
        days_left = data.FORCED_WINTER_DAY - g.day
        col = C["green"] if days_left > 60 else C["gold"] if days_left > 25 else C["red"]
        text(screen, f"Faltan {max(0, days_left)} días para el invierno", (16, 33), 14, col)
        wp = g.next_waypoint()
        if wp:
            text(screen, f"Próximo: {wp['name']} — {g.miles_to_next():.0f} millas", (ui.W // 2, 8), 21, C["text"], anchor="midtop")
        text(screen, f"Recorrido: {int(g.mile)} / {data.TRAIL_END} millas", (ui.W // 2, 33), 14, C["dim"], anchor="midtop")
        wico = {"despejado": "sun", "lluvia": "rain", "tormenta": "storm", "calor": "sun", "nieve": "snow", "frío": "snow"}[g.weather]
        ui.icon(screen, wico, ui.W - 190, 28, 28)
        tr = g.current_tribe()
        text(screen, g.weather.capitalize(), (ui.W - 168, 8), 18, C["text"])
        terr = g.terrain()
        text(screen, f"{terr.capitalize()}" + (f" · {g.tribe_name(tr)}" if tr else ""), (ui.W - 168, 31), 14, data.TRIBES[tr]["color"] if tr else C["dim"])

    def _draw_map(self, screen, r):
        g = self.g
        pygame.draw.rect(screen, (214, 194, 150), r)
        # textura de pergamino
        rng = random.Random(4)
        for _ in range(60):
            x, y = rng.randint(r.x, r.right), rng.randint(r.y, r.bottom)
            pygame.draw.circle(screen, (206, 184, 138), (x, y), rng.randint(6, 26), 0)
        pygame.draw.rect(screen, (150, 112, 66), r, 3)
        x0, x1 = 60, ui.W - 60
        total = 2000.0
        mx = lambda m: x0 + (x1 - x0) * m / total
        line_y = r.y + 118
        # territorios
        for a, b, tid in data.TERRITORIES:
            t = data.TRIBES[tid]
            s = pygame.Surface((int(mx(min(b, total)) - mx(a)), 86), pygame.SRCALPHA)
            s.fill(tuple(t["color"]) + (70,))
            screen.blit(s, (mx(a), r.y + 28))
            text(screen, t["name"].upper(), ((mx(a) + mx(min(b, total))) / 2, r.y + 36), 16, tuple(max(0, c - 60) for c in t["color"]),
                 bold=True, anchor="midtop", serif=True)
            att = g.tribes[tid].attitude
            mood = "aliados" if g.tribes[tid].allied else "hostiles" if att < -30 else "recelosos" if att < -5 else "cautos" if att < 20 else "amistosos"
            text(screen, mood, ((mx(a) + mx(min(b, total))) / 2, r.y + 56), 13, (80, 56, 34), anchor="midtop")
        # camino
        pts = []
        for m in range(0, int(total) + 1, 20):
            pts.append((mx(m), line_y + math.sin(m * 0.012) * 9))
        pygame.draw.lines(screen, (130, 96, 56), False, pts, 3)
        done = [p for p, m in zip(pts, range(0, int(total) + 1, 20)) if m <= g.mile]
        if len(done) > 1:
            pygame.draw.lines(screen, (200, 70, 50), False, done, 4)
        # hitos
        for i, wp in enumerate(data.WAYPOINTS):
            x = mx(wp["mile"])
            y = line_y + math.sin(wp["mile"] * 0.012) * 9
            visited = wp["name"] in g.visited
            col = (200, 70, 50) if visited else (90, 66, 40)
            k = wp["kind"]
            if k == "post":
                pygame.draw.rect(screen, col, (x - 6, y - 6, 12, 12))
                pygame.draw.rect(screen, (240, 224, 180), (x - 3, y - 3, 6, 6))
            elif k == "river":
                for dy in (-4, 0, 4):
                    pygame.draw.arc(screen, (70, 120, 190), (x - 8, y + dy - 4, 16, 8), 0, math.pi, 2)
            elif k in ("mountain",):
                pygame.draw.polygon(screen, col, [(x - 9, y + 6), (x, y - 9), (x + 9, y + 6)])
            elif k == "fork":
                pygame.draw.circle(screen, (60, 130, 60), (int(x), int(y)), 9)
                pygame.draw.circle(screen, (240, 224, 180), (int(x), int(y)), 4)
            else:
                pygame.draw.polygon(screen, col, [(x - 5, y + 6), (x, y - 8), (x + 5, y + 6)])
            ly = y + 18 if i % 2 == 0 else y - 30
            text(screen, wp["name"], (x, ly), 12, (70, 46, 26) if visited else (110, 84, 56), anchor="midtop" if i % 2 == 0 else "midtop")
        # marcador
        px = mx(min(g.mile, total))
        py = line_y + math.sin(g.mile * 0.012) * 9
        pygame.draw.polygon(screen, (40, 30, 20), [(px, py - 10), (px - 7, py - 24), (px + 7, py - 24)])
        ui.icon(screen, "wagon", int(px), int(py - 32), 22)
        text(screen, "Independence", (x0 - 20, r.y + 6), 14, (80, 56, 34), bold=True)
        text(screen, "Valle del Columbia", (x1 + 20, r.y + 6), 14, (80, 56, 34), bold=True, anchor="topright")

    def _draw_landscape(self, screen, r):
        g = self.g
        wmod = {"despejado": 0, "lluvia": 40, "tormenta": 70, "calor": -10, "nieve": 30, "frío": 25}[g.weather]
        top = (max(0, 118 - wmod), max(0, 168 - wmod), max(0, 220 - wmod))
        bot = (min(255, 224 - wmod // 2), min(255, 218 - wmod // 2), min(255, 196 - wmod // 2))
        ui.vgradient(screen, r, top, bot)
        terr = g.terrain()
        base = art.TERRAIN_COLORS[terr]
        off = self.scroll
        far = tuple(int(c * 0.55 + 90 * 0.45) for c in (base[0] * 0.8, base[1] * 0.9, base[2] * 1.1))
        far = tuple(max(0, min(255, c)) for c in far)
        _hills(screen, r, (far[0] - 10, far[1] - 5, far[2] + 15), r.y + 130, 34 if terr in ("montaña", "bosque", "cañón") else 14, 0.006, off * 0.15, 1.0)
        mid = tuple(int(c * 0.8) for c in base)
        _hills(screen, r, mid, r.y + 160, 18, 0.011, off * 0.35, 3.0)
        # hitos cercanos
        wp = g.next_waypoint()
        prev = data.WAYPOINTS[max(0, g.next_wp - 1)]
        for w in (wp, prev):
            if not w:
                continue
            dx = (w["mile"] - g.mile) * 14
            x = 640 + dx
            if -200 < x < ui.W + 200:
                self._draw_landmark(screen, w, x, r.y + 190)
        # suelo
        ground = pygame.Rect(r.x, r.y + 180, r.w, r.h - 180)
        pygame.draw.rect(screen, base, ground)
        tile = art.ground_surface((640, ground.h), terr, 31)
        o = int(off) % 640
        for k in (-1, 0, 1, 2):
            screen.blit(tile, (-o + k * 640, ground.y))
        pygame.draw.line(screen, tuple(int(c * 0.7) for c in base), (0, ground.y), (ui.W, ground.y), 2)
        # camino de tierra
        road = pygame.Rect(0, r.y + 236, ui.W, 20)
        pygame.draw.rect(screen, (150, 120, 82), road)
        for xx in range(-60, ui.W + 60, 36):
            pygame.draw.line(screen, (130, 102, 68), (xx - int(off * 1.0) % 36, road.y + 6), (xx + 14 - int(off * 1.0) % 36, road.y + 6), 1)
        # caravana
        n = min(6, len(g.wagons))
        for i in range(n):
            x = 150 + (n - 1 - i) * 175
            draw_side_wagon(screen, x, r.y + 252, 0.62, self.t * (1 if self.moving else 0.0), i * 1.7, oxen=True, hp=g.wagons[i].hp / g.wagons[i].max_hp)
        self.parts.draw(screen, _ScreenCam())
        # clima
        if g.weather in ("lluvia", "tormenta"):
            for x, y, k in self.rain:
                pygame.draw.line(screen, (180, 200, 240), (x, y), (x - 5, y + 14), 1)
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((30, 40, 60, 60 if g.weather == "lluvia" else 100))
            screen.blit(veil, r.topleft)
            if g.weather == "tormenta" and int(self.t * 3) % 11 == 0:
                fl = pygame.Surface(r.size, pygame.SRCALPHA)
                fl.fill((255, 255, 255, 90))
                screen.blit(fl, r.topleft)
        elif g.weather == "nieve":
            for x, y, k in self.rain:
                pygame.draw.circle(screen, (245, 248, 255), (int(x), int(y)), 2)
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((220, 230, 250, 40))
            screen.blit(veil, r.topleft)
        elif g.weather == "calor":
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((255, 200, 90, 28))
            screen.blit(veil, r.topleft)
        pygame.draw.rect(screen, (30, 20, 12), r, 3)

    def _draw_landmark(self, screen, w, x, y):
        k = w["kind"]
        if k == "post":
            # fortín
            pygame.draw.rect(screen, (120, 86, 52), (x - 70, y - 70, 140, 70))
            pygame.draw.rect(screen, (70, 48, 28), (x - 70, y - 70, 140, 70), 3)
            for i in range(-6, 7):
                pygame.draw.line(screen, (90, 62, 36), (x + i * 10, y - 70), (x + i * 10, y), 1)
                pygame.draw.polygon(screen, (120, 86, 52), [(x + i * 10 - 4, y - 70), (x + i * 10, y - 78), (x + i * 10 + 4, y - 70)])
            pygame.draw.rect(screen, (40, 28, 20), (x - 12, y - 36, 24, 36))
            pygame.draw.line(screen, (60, 40, 24), (x + 50, y - 70), (x + 50, y - 110), 3)
            pygame.draw.polygon(screen, (200, 60, 50), [(x + 50, y - 110), (x + 78, y - 102), (x + 50, y - 94)])
            text(screen, w["name"], (x, y - 140), 17, (50, 30, 18), bold=True, anchor="midtop", serif=True)
        elif k == "river":
            pygame.draw.rect(screen, (74, 130, 196), (x - 110, y - 30, 220, 76))
            for i in range(8):
                xx = x - 100 + i * 26 + (self.t * 20) % 26
                pygame.draw.arc(screen, (180, 220, 250), (xx, y - 14 + (i % 3) * 18, 18, 8), 0, math.pi, 2)
            text(screen, w["name"], (x, y - 60), 17, (30, 50, 90), bold=True, anchor="midtop", serif=True)
        elif k == "mountain":
            pygame.draw.polygon(screen, (110, 106, 118), [(x - 160, y), (x - 40, y - 150), (x + 20, y - 80), (x + 90, y - 170), (x + 190, y)])
            pygame.draw.polygon(screen, (240, 244, 250), [(x - 40, y - 150), (x - 62, y - 118), (x - 20, y - 126)])
            pygame.draw.polygon(screen, (240, 244, 250), [(x + 90, y - 170), (x + 62, y - 120), (x + 118, y - 128)])
            text(screen, w["name"], (x, y - 200), 17, (40, 40, 56), bold=True, anchor="midtop", serif=True)
        elif k == "fork":
            pygame.draw.line(screen, (90, 62, 36), (x, y), (x, y - 90), 5)
            for i, (lbl, dy) in enumerate((("Willamette →", -86), ("← Walla Walla", -64), ("Columbia ↓", -42))):
                pygame.draw.rect(screen, (150, 112, 66), (x - 70, y + dy, 140, 18))
                text(screen, lbl, (x, y + dy + 1), 13, (40, 26, 14), anchor="midtop")
        else:
            pygame.draw.polygon(screen, (170, 142, 104), [(x - 38, y), (x - 14, y - 120), (x - 4, y - 124), (x + 10, y - 40), (x + 52, y)])
            pygame.draw.polygon(screen, (130, 104, 72), [(x - 14, y - 120), (x - 4, y - 124), (x + 10, y - 40), (x - 8, y - 40)])
            text(screen, w["name"], (x, y - 152), 17, (60, 40, 24), bold=True, anchor="midtop", serif=True)

    def _draw_bottom(self, screen):
        g = self.g
        y0 = 518
        panel(screen, (0, y0, ui.W, ui.H - y0), (44, 32, 22), C["edge"], 0)
        s = g.sup
        # recursos
        x, y = 16, y0 + 12
        need = sum(data.RATIONS[g.rations] * (0.6 if c.group == "niño" else 0.8 if c.group == "anciano" else 1.0) for c in g.living())
        days = s.food / max(0.1, need)
        items = [
            ("food", f"{int(s.food)} lb", f"≈{days:.0f} días", C["green"] if days > 25 else C["gold"] if days > 8 else C["red"]),
            ("ammo", f"{s.ammo}", "balas", C["text"] if s.ammo > 30 else C["gold"] if s.ammo > 10 else C["red"]),
            ("goods", f"{s.goods}", "mercancías", C["text"]),
            ("parts", f"{s.parts}", "repuestos", C["text"] if s.parts else C["gold"]),
            ("medicine", f"{s.medicine}", "medicinas", C["text"]),
            ("oxen", f"{s.oxen}", f"bueyes / {2 * len(g.wagons)}", C["text"] if s.oxen >= 2 * len(g.wagons) else C["red"]),
            ("money", f"${s.money:,.0f}", "dinero", C["gold"]),
            ("wagon", f"{len(g.wagons)}", "carretas", C["text"]),
        ]
        for i, (ico, val, lbl, col) in enumerate(items):
            cx = 16 + (i % 4) * 130
            cy = y0 + 14 + (i // 4) * 44
            ui.icon(screen, ico, cx + 12, cy + 14, 22)
            text(screen, val, (cx + 30, cy), 19, col, bold=True)
            text(screen, lbl, (cx + 30, cy + 21), 12, C["dim"])
        # moral y gente
        sick = sum(1 for c in g.living() if c.sick)
        text(screen, f"Colonos: {g.pop()}" + (f"  ({sick} enfermos)" if sick else ""), (16, y0 + 106), 16, C["red"] if sick else C["text"])
        ui.icon(screen, "morale", 190, y0 + 115, 18)
        bar(screen, (206, y0 + 110, 110, 10), g.morale / 100.0, C["green"] if g.morale > 55 else C["gold"] if g.morale > 28 else C["red"])
        # grupo
        gx = 16
        gy = y0 + 134
        for c in g.living()[:16]:
            art.draw_person(screen, gx + 10, gy + 14, c.group, c.cid, 1.2)
            hp = c.health / 100.0
            bar(screen, (gx, gy + 28, 20, 3), hp, C["green"] if hp > 0.5 else C["orange"] if hp > 0.25 else C["red"], border=False)
            if c.sick:
                pygame.draw.circle(screen, (110, 200, 90), (gx + 18, gy + 4), 3)
            gx += 25
        # registro
        fx = 548
        text(screen, "Bitácora", (fx, y0 + 8), 14, C["gold"], bold=True)
        lines = []
        for s_, col in self.feed[-7:]:
            for k, ln in enumerate(ui.wrap(s_, 14, 268)):
                lines.append((("" if k == 0 else "  ") + ln, col))
        yy = y0 + 28
        for ln, col in lines[-9:]:
            text(screen, ln, (fx, yy), 14, col)
            yy += 19
        for b in self.btns:
            b.draw(screen)


class _ScreenCam:
    s = 1.0

    def __call__(self, x, y):
        return (x, y)


class ConfirmQuit(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.btns = [Button((ui.W // 2 - 220, 380, 200, 46), "Volver al juego", self.app.pop, size=18),
                     Button((ui.W // 2 + 20, 380, 200, 46), "Guardar y salir", self._quit, size=18, color=(98, 74, 40))]

    def _quit(self):
        self.app.autosave()
        from .scenes_menu import TitleScene
        self.app.travel = None
        self.app.replace(TitleScene(self.app))

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.app.pop()

    def draw(self, screen):
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        screen.blit(veil, (0, 0))
        panel(screen, (ui.W // 2 - 260, 280, 520, 170), C["panel"], C["gold"], 12)
        text(screen, "¿Dejar el camino?", (ui.W // 2, 300), 28, C["gold"], serif=True, anchor="midtop")
        text(screen, "Se guardará la partida en este punto.", (ui.W // 2, 346), 17, C["dim"], anchor="midtop")
        for b in self.btns:
            b.draw(screen)


# ====================================================================== campamento
class CampScene(Scene):
    def __init__(self, app, wp):
        super().__init__(app)
        self.g = app.game
        self.wp = wp
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), self.g.terrain(), 41)
        self.btns: list[Button] = []
        self.chatted = False
        self.msg = ""
        self.t = 0.0
        self._build()

    def resume(self):
        self._build()
        if self.g.over or not self.g.living():
            return

    def _build(self):
        g = self.g
        wp = self.wp
        x, w = 700, 230
        bx = [x, x + w + 10]
        y = 150
        self.btns = []
        def add(col, row, label, fn, **kw):
            b = Button((bx[col], y + row * 56, w, 46), label, fn, size=17, **kw)
            self.btns.append(b)
            return b
        add(0, 0, "Descansar 1 día", lambda: self._rest(1))
        add(1, 0, "Descansar 3 días", lambda: self._rest(3))
        add(0, 1, "Salir de caza (1 día)", self._hunt)
        add(1, 1, "Reparar carretas", self._repair_all)
        add(0, 2, "Plan de defensa", self._defense)
        shop_here = wp is not None and wp["kind"] == "post"
        b = add(1, 2, "Comerciar" if shop_here else "Sin comercio aquí", self._trade)
        b.enabled = shop_here
        talk = add(0, 3, "Hablar con viajeros", self._talk)
        talk.enabled = wp is not None and not self.chatted
        add(1, 3, "Tratar enfermos", self._treat)
        self.pace_btn = add(0, 4, "", self._cycle_pace)
        self.rations_btn = add(1, 4, "", self._cycle_rations)
        self.watch_btn = add(0, 5, "", self._cycle_watch)
        self.go_btn = Button((bx[0], y + 6 * 56 + 14, 2 * w + 10, 56), "Levantar el campamento y seguir", self._leave, size=22, color=(98, 74, 40))
        self.btns.append(self.go_btn)

    def _cycle_pace(self):
        order = list(data.PACES)
        self.g.pace = order[(order.index(self.g.pace) + 1) % 3]

    def _cycle_rations(self):
        order = list(data.RATIONS)
        self.g.rations = order[(order.index(self.g.rations) + 1) % 3]

    def _cycle_watch(self):
        order = list(data.WATCH_LABEL)
        self.g.watch = order[(order.index(self.g.watch) + 1) % 3]

    def _after_days(self, title, body, it):
        g = self.g
        if it is None and g.living():
            self.app.push(PromptScene(self.app, Prompt.info(title, body, "good")))
        else:
            self.app.push(PromptScene(self.app, Prompt.info(title, body, "info", then=lambda it=it: it)))

    def _rest(self, n):
        g = self.g
        before = sum(c.health for c in g.living())
        sick_before = sum(1 for c in g.living() if c.sick)
        days, it = g.rest(n)
        after = sum(c.health for c in g.living())
        sick_after = sum(1 for c in g.living() if c.sick)
        body = f"Pasan {days} día(s) de descanso. Los carros se remiendan y la gente se repone"
        if sick_before > sick_after:
            body += f"; {sick_before - sick_after} enfermo(s) mejoran"
        body += ". La comida, en cambio, no se estira sola."
        if g.sup.food <= 0:
            body += " ¡La comida se ha acabado!"
        self.app.travel.consume_notices()
        self._after_days("Descanso", body, it)

    def _hunt(self):
        g = self.g
        p = g.hunt_day()
        self.app.travel.consume_notices()
        it = g.camp_event()
        if it is not None:
            p.options[0].action = (lambda it=it: it)
        self.app.push(PromptScene(self.app, p))

    def _repair_all(self):
        g = self.g
        done = 0
        for i in range(len(g.wagons)):
            while g.wagons[i].hp < g.wagons[i].max_hp - 20 and g.sup.parts > 0:
                ok, _ = g.repair_wagon(i)
                if not ok:
                    break
                done += 1
        body = f"Se hacen {done} reparaciones." if done else "No hay nada que reparar o no quedan repuestos."
        self.app.push(PromptScene(self.app, Prompt.info("Taller de campaña", body, "good" if done else "info")))

    def _defense(self):
        from .scenes_defense import DefenseScene
        self.app.push(DefenseScene(self.app))

    def _trade(self):
        from .scenes_trade import ShopScene
        wp = self.wp
        self.app.push(ShopScene(self.app, ShopSpec(wp["name"], wp.get("price", 1.0), wp.get("cannon", False))))

    def _talk(self):
        g = self.g
        self.chatted = True
        self.btns[6].enabled = False
        parts = []
        for t in ("pawnee", "cheyenne", "lakota", "shoshone", "cayuse"):
            if g.tribes[t].met or t == g.next_tribe():
                att = g.tribes[t].attitude
                parts.append(f"Los {g.tribe_name(t)} andan " + ("furiosos con los blancos." if att < -50 else "hostiles." if att < -20 else "recelosos." if att < 5 else "tranquilos." if att < 30 else "amistosos."))
        extra = ""
        r = g.rng.random()
        if r < 0.33:
            g.sup.goods += 1
            extra = " Un viajero te regala un lote de mercancías a cambio de tu compañía."
        elif r < 0.66:
            g.morale = min(100, g.morale + 6)
            extra = " La charla anima al grupo."
        txt = "Viajeros que vuelven al este y otros que van al oeste comparten noticias: " + " ".join(parts[:4]) + extra
        self.app.push(PromptScene(self.app, Prompt.info("Noticias del camino", txt)))

    def _treat(self):
        g = self.g
        sick = [c for c in g.living() if c.sick]
        if not sick:
            self.app.push(PromptScene(self.app, Prompt.info("Enfermería", "Nadie necesita tratamiento ahora.")))
            return
        used = 0
        for c in sick:
            if g.sup.medicine > 0:
                g.sup.medicine -= 1
                c.health = min(100, c.health + 30)
                if g.rng.random() < 0.6 + 0.04 * g.best("medic"):
                    c.sick = ""
                used += 1
        left = sum(1 for c in g.living() if c.sick)
        self.app.push(PromptScene(self.app, Prompt.info("Enfermería", f"Gastas {used} medicinas. Siguen enfermos: {left}." if used else "No quedan medicinas.", "good" if used else "danger")))

    def _leave(self):
        self.app.pop()
        if self.app.travel:
            self.app.travel.moving = True
            self.app.travel.acc = 0.0

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self._leave()

    def update(self, dt):
        self.t += dt
        g = self.g
        self.pace_btn.label = f"Ritmo: {data.PACE_LABEL[g.pace]}"
        self.rations_btn.label = f"Raciones: {data.RATION_LABEL[g.rations]}"
        self.watch_btn.label = data.WATCH_LABEL[g.watch]
        self.btns[6].enabled = self.wp is not None and not self.chatted

    def draw(self, screen):
        g = self.g
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((16, 11, 7, 190))
        screen.blit(veil, (0, 0))
        title = self.wp["name"] if self.wp else "Campamento en el camino"
        text(screen, title, (40, 28), 42, C["gold"], serif=True, bold=True)
        sub = self.wp["text"] if self.wp else f"{g.terrain().capitalize()}. Millas recorridas: {int(g.mile)}."
        para(screen, sub, (42, 84), 580, 17, C["dim"])
        text(screen, g.date_text(), (42, 140), 17, C["parch"])
        # colonos
        panel(screen, (30, 170, 640, ui.H - 190), C["panel"], C["edge"], 10)
        text(screen, "La compañía", (48, 182), 20, C["gold"], serif=True, bold=True)
        y = 214
        for c in g.living():
            art.draw_person(screen, 64, y + 12, c.group, c.cid, 1.3)
            text(screen, c.name, (88, y), 17, C["text"])
            text(screen, c.role_label + (f" · {c.sick}" if c.sick else ""), (88, y + 18), 12, C["red"] if c.sick else C["dim"])
            bar(screen, (320, y + 8, 130, 9), c.health / 100.0, C["green"] if c.health > 50 else C["orange"] if c.health > 25 else C["red"])
            text(screen, f"Punt. {c.shoot} · Med. {c.medic} · Lab. {c.talk}", (466, y + 6), 13, C["dim"])
            y += 36
            if y > ui.H - 60:
                break
        # estado
        panel(screen, (690, 10, 550, 128), C["panel"], C["edge"], 10)
        s = g.sup
        vals = [("food", f"{int(s.food)} lb"), ("ammo", f"{s.ammo}"), ("goods", f"{s.goods}"), ("parts", f"{s.parts}"),
                ("medicine", f"{s.medicine}"), ("oxen", f"{s.oxen}"), ("money", f"${s.money:,.0f}"), ("wagon", f"{len(g.wagons)}")]
        for i, (ico, v) in enumerate(vals):
            cx = 708 + (i % 4) * 134
            cy = 26 + (i // 4) * 40
            ui.icon(screen, ico, cx + 12, cy + 10, 22)
            text(screen, v, (cx + 30, cy), 19, C["gold"], bold=True)
        ui.icon(screen, "morale", 716, 112, 18)
        bar(screen, (736, 106, 180, 11), g.morale / 100.0, C["green"] if g.morale > 55 else C["gold"] if g.morale > 28 else C["red"])
        text(screen, "moral", (924, 104), 14, C["dim"])
        for b in self.btns:
            b.draw(screen)
