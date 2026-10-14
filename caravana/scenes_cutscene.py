"""Escena de cutscene: fondo, personajes en escena, diálogo con máquina de escribir y barras de cine."""
from __future__ import annotations

import math

import pygame

from . import art, ui
from .cutscene_art import Backdrop
from .model import CutsceneSpec
from .scene import Scene
from .ui import C, Button, text, panel, wrap

CHARS_PER_SEC = 46.0
BAR_TOP, BAR_BOT = 62, 150


_VIG = None


def _vignette() -> pygame.Surface:
    """Viñeta elíptica suave (se calcula una vez a baja resolución y se amplía)."""
    global _VIG
    if _VIG is None:
        sw, sh = 64, 36
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                d = math.hypot((x - sw / 2) / (sw / 2), (y - sh / 2) / (sh / 2))
                a = max(0.0, min(1.0, (d - 0.55) / 0.75))
                small.set_at((x, y), (0, 0, 0, int(150 * a * a)))
        _VIG = pygame.transform.smoothscale(small, (ui.W, ui.H))
    return _VIG


class CutsceneScene(Scene):
    def __init__(self, app, spec: CutsceneSpec):
        super().__init__(app)
        self.g = app.game
        self.spec = spec
        self.i = 0
        self.t = 0.0
        self.t_line = 0.0
        self.t_bg = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.backs: dict[str, Backdrop] = {}
        self.finished = False
        self.skip = Button((ui.W - 190, 12, 170, 40), "Saltar", self.finish, size=17)
        self._enter_beat()

    # ------------------------------------------------------------ control
    @property
    def beat(self):
        return self.spec.beats[self.i]

    def _enter_beat(self):
        self.t_line = 0.0
        b = self.beat
        if b.fx == "shake":
            self.shake = 14.0
        if b.fx == "flash":
            self.flash = 1.0
        prev = self.spec.beats[self.i - 1].bg if self.i > 0 else None
        if prev != b.bg:
            self.t_bg = 0.0

    def line_done(self) -> bool:
        return self.t_line * CHARS_PER_SEC >= len(self.beat.text)

    def advance(self):
        if self.finished:
            return
        if not self.line_done():
            self.t_line = 999.0
            return
        if self.i + 1 >= len(self.spec.beats):
            self.finish()
            return
        self.i += 1
        self._enter_beat()

    def finish(self):
        if self.finished:
            return
        self.finished = True
        self.app.pop()
        res = self.spec.then() if self.spec.then else None
        if res is not None:
            self.app.handle_interrupt(res)

    def handle(self, ev):
        if self.skip.handle(ev):
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
            self.advance()
        elif ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT):
                self.advance()
            elif ev.key == pygame.K_ESCAPE:
                self.finish()

    def update(self, dt):
        self.t += dt
        self.t_line += dt
        self.t_bg += dt
        self.shake = max(0.0, self.shake - dt * 30)
        self.flash = max(0.0, self.flash - dt * 1.6)

    # ------------------------------------------------------------ dibujo
    def _name(self, who: str) -> str:
        if who == "tu":
            return "Tú"
        if not who:
            return ""
        c = self.g.by_role(who)
        return c.name.split()[0] if c else who

    def draw(self, screen):
        b = self.beat
        g = self.g
        if b.bg not in self.backs:
            self.backs[b.bg] = Backdrop(b.bg)
        ox = int(math.sin(self.t * 60) * self.shake)
        oy = int(math.cos(self.t * 47) * self.shake * 0.6)
        stage = pygame.Surface((ui.W, ui.H))
        self.backs[b.bg].draw(stage, self.t, self.i / max(1, len(self.spec.beats) - 1))
        # personajes
        n = len(b.cast)
        base_y = ui.H - BAR_BOT + 40
        xs = []
        if n:
            span = 800 if n > 1 else 0
            x0 = ui.W // 2 - span // 2 + (60 if n < 3 else 0)
            xs = [x0 + (span * k / max(1, n - 1) if n > 1 else 0) for k in range(n)]
        for role, x in zip(b.cast, xs):
            c = g.by_role(role)
            if c is None:
                continue
            speaking = role == b.speaker and not self.line_done()
            dim = bool(b.speaker) and role != b.speaker
            art.draw_portrait(stage, x, base_y, 470, role, c.group, c.cid, b.mood if role == b.speaker else "neutral",
                              speaking=speaking, t=self.t, dim=dim)
        if b.speaker == "tu":
            art.draw_portrait(stage, 170, base_y + 30, 430, "lider", "adulto", 0, "neutral", t=self.t, back=True)
        # viñeta
        stage.blit(_vignette(), (0, 0))
        if self.t_bg < 0.5:
            fade = pygame.Surface((ui.W, ui.H))
            fade.fill((0, 0, 0))
            fade.set_alpha(int(255 * (1 - self.t_bg / 0.5)))
            stage.blit(fade, (0, 0))
        screen.fill((0, 0, 0))
        screen.blit(stage, (ox, oy))
        if self.flash > 0:
            fl = pygame.Surface((ui.W, ui.H))
            fl.fill((255, 255, 255))
            fl.set_alpha(int(220 * self.flash))
            screen.blit(fl, (0, 0))
        # barras de cine
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, ui.W, BAR_TOP))
        pygame.draw.rect(screen, (0, 0, 0), (0, ui.H - BAR_BOT, ui.W, BAR_BOT))
        text(screen, self.spec.title, (28, 16), 28, C["gold"], serif=True, bold=True)
        self.skip.draw(screen)
        # diálogo
        box = pygame.Rect(46, ui.H - BAR_BOT + 12, ui.W - 92, BAR_BOT - 26)
        panel(screen, box, (28, 20, 14), C["gold"], 10, alpha=235)
        name = self._name(b.speaker)
        tx = box.x + 22
        if name:
            tag = pygame.Rect(box.x + 18, box.y - 16, ui.font(22, bold=True).size(name)[0] + 30, 32)
            panel(screen, tag, (92, 64, 36), C["gold"], 8)
            text(screen, name, tag.center, 22, C["gold"], bold=True, anchor="center")
        shown = b.text[: int(self.t_line * CHARS_PER_SEC)]
        italic = b.speaker == ""
        col = (214, 202, 170) if italic else C["text"]
        yy = box.y + 22
        for ln in wrap(shown if shown else " ", 23, box.w - 60):
            screen.blit(ui.font(23).render(ln, True, col), (tx, yy))
            yy += 30
        if self.line_done():
            pulse = 0.5 + 0.5 * math.sin(self.t * 6)
            pygame.draw.polygon(screen, (int(220 * pulse + 30), int(180 * pulse + 30), 70),
                                [(box.right - 36, box.bottom - 30), (box.right - 20, box.bottom - 22), (box.right - 36, box.bottom - 14)])
        # progreso
        n_b = len(self.spec.beats)
        for k in range(n_b):
            pygame.draw.circle(screen, C["gold"] if k <= self.i else (80, 66, 46), (ui.W // 2 - (n_b - 1) * 7 + k * 14, 40), 3)
