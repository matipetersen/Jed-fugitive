"""Escenas de menú: título, instrucciones, creación de personaje y fin de partida."""
from __future__ import annotations

import math
import random

import pygame

from . import art, data, ui
from .model import Game, ShopSpec
from .scene import Scene
from .ui import C, Button, text, panel, para


class _Fake:
    def __init__(self, kind, face):
        self.kind = kind
        self.face = face


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.parts = art.Particles()
        self.ground = art.ground_surface((ui.W + 40, ui.H + 40), "pradera", 3)
        self.cx, self.cy = 880, 372
        n = 9
        self.R = 200
        self.wagons = []
        for i in range(n):
            a = -math.pi / 2 + math.tau * i / n
            surf = art.wagon_surface(1.0 if i % 3 else 0.6, 1 if i % 4 == 0 else 0, i == 2, False, i % 2 == 0, False, a + math.pi / 2)
            surf = pygame.transform.smoothscale(surf, (int(surf.get_width() * 1.35), int(surf.get_height() * 1.35)))
            self.wagons.append((self.cx + math.cos(a) * self.R, self.cy + math.sin(a) * self.R, surf))
        self.riders = [[random.uniform(0, math.tau), random.uniform(330, 440), random.choice([-1, 1]) * random.uniform(0.07, 0.14)] for _ in range(7)]
        self.stars = [(random.randint(0, ui.W), random.randint(0, ui.H), random.random()) for _ in range(80)]
        self.menu_buttons: list[Button] = []
        self._build()

    def _build(self):
        x, y, w = 70, 330, 300
        self.menu_buttons = [Button((x, y, w, 46), "Nueva partida", self._new, size=22)]
        yy = y + 56
        if self.app.save_exists():
            self.menu_buttons.append(Button((x, yy, w, 46), "Continuar viaje", self._continue, size=22))
            yy += 56
        self.menu_buttons.append(Button((x, yy, w, 46), "Cómo se juega", self._how, size=22))
        yy += 56
        self.menu_buttons.append(Button((x, yy, w, 46), "Salir", self._quit, size=22))

    def resume(self):
        self._build()

    def _new(self):
        self.app.push(SetupScene(self.app))

    def _continue(self):
        g = self.app.load_save()
        if g is None:
            return
        from .scenes_travel import TravelScene
        self.app.game = g
        self.app.replace(TravelScene(self.app))

    def _how(self):
        self.app.push(HowToScene(self.app))

    def _quit(self):
        self.app.running = False

    def handle(self, ev):
        for b in self.menu_buttons:
            if b.handle(ev):
                return

    def update(self, dt):
        self.t += dt
        if random.random() < 0.5:
            self.parts.add("ember", 0, 0, 1)
        self.parts.update(dt)
        for r in self.riders:
            r[0] += r[2] * dt

    def draw(self, screen):
        screen.blit(self.ground, (-20, -20))
        cam = lambda x, y: (self.cx + x, self.cy + y)
        cam.s = 1.0
        for x, y, surf in self.wagons:
            screen.blit(surf, surf.get_rect(center=(int(x), int(y))))
        for tx, ty in ((-60, -50), (70, -30), (-30, 70), (60, 60)):
            art.draw_tent(screen, self.cx + tx, self.cy + ty, 1.6)
        art.draw_fire(screen, self.cx, self.cy, self.t, 2.0)
        for a, r, w in self.riders:
            x, y = self.cx + math.cos(a) * r, self.cy + math.sin(a) * r
            art.draw_foe(screen, _Fake("jinete", a + (math.pi / 2) * (1 if w > 0 else -1)), x, y, 1.9, (70, 50, 60))
        self.parts.draw(screen, cam)
        # noche
        dark = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        dark.fill((5, 8, 26, 205))
        flick = 1 + 0.03 * math.sin(self.t * 9)
        r = int(520 * flick)
        dark.blit(art.radial_light(r, 255), (self.cx - r, self.cy - r), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(dark, (0, 0))
        # panel de título
        veil = pygame.Surface((520, ui.H), pygame.SRCALPHA)
        for i in range(520):
            pygame.draw.line(veil, (10, 7, 5, int(230 * (1 - i / 520) ** 0.8)), (i, 0), (i, ui.H))
        screen.blit(veil, (0, 0))
        text(screen, "LA CARAVANA", (64, 90), 62, C["gold"], bold=True, serif=True, shadow=True)
        text(screen, "Hacia el Oeste · 1848", (68, 160), 26, C["parch"], serif=True, shadow=True)
        para(screen, "2.000 millas. Carretas en círculo. Comerciar, parlamentar… y resistir cuando todo lo demás falla.",
             (68, 205), 330, 17, C["dim"])
        for b in self.menu_buttons:
            b.draw(screen)
        scores = self.app.scores()
        if scores:
            text(screen, "Mejores crónicas", (70, 600), 15, C["gold"], bold=True)
            for i, s in enumerate(scores[:3]):
                text(screen, f"{i + 1}. {s['name']} — {s['score']} ({s['rank']})", (70, 622 + i * 20), 14, C["dim"])


class HowToScene(Scene):
    overlay = True
    PAGES = [
        ("El viaje", "Guías a un grupo de colonos 1.950 millas desde Independence hasta el Columbia, con carretas, bueyes y provisiones. "
                     "Cada día se avanza, se come y se enferma. Controla el ritmo, las raciones y la guardia nocturna. "
                     "Compra y vende en los fuertes, caza y descansa en el campamento. Si el invierno os alcanza (15 de diciembre), "
                     "tendréis que fundar el asentamiento donde estéis."),
        ("Diplomacia y comercio", "Cada territorio tiene su pueblo: Pawnee, Cheyenne, Lakota, Shoshone, Cayuse. Su trato hacia ti (-100 a 100) decide si "
                                  "te dejan pasar o te atacan. Saluda con respeto, haz regalos (lo que más valoran vale más), pacta un paso "
                                  "seguro, contrata un guía, o intercambia por bueyes, medicinas y comida. Dar munición gana amistad, pero los arma. "
                                  "Cada muerte que causes se recuerda."),
        ("Defensa 360°", "Cuando falla la diplomacia, se cierra el círculo. Eres el estratega: asigna tiradores (T) y ayudantes (A) a cada carreta "
                         "(clic en un colono y luego en la plaza), marca objetivos con clic en un enemigo, controla el fuego (libre, contenido, alto) "
                         "para ahorrar balas, levanta barricadas en los huecos, y si hace falta, parlamenta en plena batalla. "
                         "Las flechas rojas del borde avisan por dónde llega cada oleada. De noche, los faroles son vida."),
        ("Teclas del combate", "Espacio: pausa · 1/2/3: velocidad · Enter: empezar ya · A: auto-asignar por amenaza · F: política de fuego · "
                               "P: parlamento · M: fundir utensilios en balas (5 mercancías = 12 balas) · clic derecho: quitar puesto · "
                               "clic en carreta destruida: barricada."),
        ("El asentamiento", "Al final eliges dónde fundar: Willamette (fértil, lejos), Walla Walla (cerca, vecinos Cayuse) o los riscos del Columbia "
                            "(defendible, comercio). Con lo que traigas construyes cabañas, campos, empalizada, y un tratado con tus vecinos. "
                            "Luego sobrevivís el primer año: la crónica decide vuestra suerte."),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.btns = []
        self._build()

    def _build(self):
        self.btns = [
            Button((420, 560, 120, 40), "Anterior", lambda: self._go(-1), size=18),
            Button((740, 560, 120, 40), "Siguiente", lambda: self._go(1), size=18),
            Button((570, 560, 140, 40), "Cerrar", self.app.pop, size=18),
        ]

    def _go(self, d):
        self.page = max(0, min(len(self.PAGES) - 1, self.page + d))

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.app.pop()

    def draw(self, screen):
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        screen.blit(veil, (0, 0))
        panel(screen, (300, 110, 680, 500), C["panel"], C["gold"], 12)
        title, body = self.PAGES[self.page]
        text(screen, title, (640, 130), 34, C["gold"], serif=True, anchor="midtop", bold=True)
        para(screen, body, (340, 190), 600, 19, C["text"], gap=5)
        text(screen, f"{self.page + 1}/{len(self.PAGES)}", (640, 536), 15, C["dim"], anchor="midtop")
        for b in self.btns:
            b.draw(screen)


class SetupScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.name = "Jed"
        self.focus = False
        self.prof = "granjero"
        self.diff = "normal"
        self.t = 0.0
        self.cards = []
        self.go = Button((ui.W - 360, ui.H - 76, 300, 50), "Comprar provisiones →", self._go, size=21, color=(98, 74, 40))
        self.back = Button((60, ui.H - 76, 160, 50), "Volver", self.app.pop, size=19)
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "pradera", 11)

    def _go(self):
        seed = random.randrange(1, 10 ** 6)
        g = Game.new(self.name.strip() or "Jed", self.prof, seed, self.diff)
        self.app.game = g
        from .scenes_trade import ShopScene
        self.app.replace(ShopScene(self.app, ShopSpec("Independence, Misuri", 1.0), initial=True))

    def handle(self, ev):
        if self.go.handle(ev) or self.back.handle(ev):
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.focus = pygame.Rect(230, 120, 380, 44).collidepoint(ev.pos)
            for i, key in enumerate(data.PROFESSIONS):
                if self._card_rect(i).collidepoint(ev.pos):
                    self.prof = key
            for i, key in enumerate(data.DIFFICULTY):
                if pygame.Rect(690 + i * 180, 120, 170, 44).collidepoint(ev.pos):
                    self.diff = key
        elif ev.type == pygame.KEYDOWN and self.focus:
            if ev.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif ev.key in (pygame.K_RETURN, pygame.K_TAB):
                self.focus = False
            elif ev.unicode and ev.unicode.isprintable() and len(self.name) < 16:
                self.name += ev.unicode

    def update(self, dt):
        self.t += dt

    def _card_rect(self, i):
        return pygame.Rect(60 + (i % 3) * 400, 250 + (i // 3) * 190, 380, 170)

    def draw(self, screen):
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((14, 10, 6, 190))
        screen.blit(veil, (0, 0))
        text(screen, "El líder de la caravana", (60, 40), 40, C["gold"], serif=True, bold=True)
        r = pygame.Rect(230, 120, 380, 44)
        text(screen, "Tu nombre:", (60, 132), 20, C["text"])
        pygame.draw.rect(screen, (30, 22, 16), r, border_radius=6)
        pygame.draw.rect(screen, C["gold"] if self.focus else C["edge"], r, 2, border_radius=6)
        caret = "|" if self.focus and int(self.t * 2) % 2 == 0 else ""
        text(screen, self.name + caret, (r.x + 12, r.y + 9), 24, C["text"])
        text(screen, "Dificultad:", (660, 100), 15, C["dim"])
        for i, (key, dd) in enumerate(data.DIFFICULTY.items()):
            rr = pygame.Rect(690 + i * 180, 120, 170, 44)
            sel = key == self.diff
            panel(screen, rr, (80, 58, 36) if sel else C["panel"], C["gold"] if sel else C["edge"], 8, width=3 if sel else 2)
            text(screen, dd["name"], rr.center, 19, C["gold"] if sel else C["text"], anchor="center", bold=sel)
        text(screen, data.DIFFICULTY[self.diff]["desc"], (690, 170), 14, C["dim"])
        text(screen, "Elige tu oficio:", (60, 200), 22, C["parch"], serif=True)
        for i, (key, p) in enumerate(data.PROFESSIONS.items()):
            rc = self._card_rect(i)
            sel = key == self.prof
            panel(screen, rc, (80, 58, 36) if sel else C["panel"], C["gold"] if sel else C["edge"], 10, width=3 if sel else 2)
            text(screen, p["name"], (rc.x + 16, rc.y + 12), 26, C["gold"] if sel else C["text"], serif=True, bold=True)
            text(screen, f"${p['money']}", (rc.right - 16, rc.y + 16), 22, C["gold"], anchor="topright")
            para(screen, p["desc"], (rc.x + 16, rc.y + 52), rc.w - 32, 16, C["text"] if sel else C["dim"], max_lines=3)
            sk = p["skills"]
            labels = [("Puntería", sk["shoot"]), ("Medicina", sk["medic"]), ("Construir", sk["build"]), ("Labia", sk["talk"]), ("Caza", sk["hunt"])]
            for j, (lb, v) in enumerate(labels):
                x = rc.x + 16 + j * 70
                text(screen, lb, (x, rc.y + 112), 11, C["dim"])
                ui.bar(screen, (x, rc.y + 130, 62, 7), v / 10.0, C["green"] if v >= 7 else C["gold"] if v >= 4 else C["red"], border=False)
        rc = self._card_rect(5)
        panel(screen, rc, (36, 28, 20), C["edge"], 10)
        text(screen, "Tu compañía", (rc.x + 16, rc.y + 12), 22, C["parch"], serif=True, bold=True)
        para(screen, "Dos familias y cuatro peones: 14 almas, siete carretas y catorce bueyes. Los niños y ancianos no disparan, "
                     "pero recargan, curan y apagan fuegos. Cada colono tiene sus propias habilidades.", (rc.x + 16, rc.y + 48), rc.w - 32, 15, C["dim"])
        self.go.draw(screen)
        self.back.draw(screen)


class EndScene(Scene):
    def __init__(self, app, title: str, body: str, victory: bool = False):
        super().__init__(app)
        self.title = title
        self.body = body
        self.victory = victory
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "estepa", 5)
        self.btns = [Button((ui.W // 2 - 270, ui.H - 90, 250, 50), "Volver al menú", self._menu, size=20),
                     Button((ui.W // 2 + 20, ui.H - 90, 250, 50), "Nueva partida", self._new, size=20, color=(98, 74, 40))]
        self.app.clear_save()

    def _menu(self):
        self.app.travel = None
        self.app.replace(TitleScene(self.app))

    def _new(self):
        self.app.travel = None
        self.app.replace(TitleScene(self.app))
        self.app.push(SetupScene(self.app))

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return

    def draw(self, screen):
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((8, 6, 5, 200))
        screen.blit(veil, (0, 0))
        text(screen, self.title, (ui.W // 2, 50), 52, C["red"], serif=True, bold=True, anchor="midtop", shadow=True)
        y = para(screen, self.body, (ui.W // 2 - 360, 130), 720, 20, C["text"], gap=5)
        g = self.app.game
        if g:
            y += 14
            text(screen, f"{g.date_text()} · {int(g.mile)} millas recorridas · {g.day} días", (ui.W // 2, y), 18, C["parch"], anchor="midtop")
            y += 40
            dead = g.dead()
            text(screen, "Quienes no llegaron", (ui.W // 2, y), 22, C["gold"], serif=True, anchor="midtop")
            y += 36
            for i, c in enumerate(dead[:16]):
                col = i % 2
                row = i // 2
                text(screen, f"† {c.name} — {c.cause}", (ui.W // 2 - 340 + col * 360, y + row * 24), 17, C["dim"])
        for b in self.btns:
            b.draw(screen)
