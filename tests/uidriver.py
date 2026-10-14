"""Conductor de interfaz: juega 'La Caravana' sólo con eventos de ratón/teclado (sin ventana real)."""
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from caravana.app import App
from caravana.battle_view import BattleScene
from caravana.scenes_defense import DefenseScene
from caravana.scenes_diplo import DiplomacyScene
from caravana.scenes_cutscene import CutsceneScene
from caravana.scenes_menu import EndScene, HowToScene, SetupScene, TitleScene
from caravana.scenes_origin import OriginScene, RecruitScene
from caravana.scenes_settle import ChronicleScene, SettlementScene, SiteScene
from caravana.scenes_trade import ShopScene
from caravana.scenes_travel import CampScene, ConfirmQuit, JournalScene, PromptScene, TravelScene


def click(app, pos, button=1):
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)
    app.step(1 / 30, [ev])


def click_button(app, btn):
    btn.hover = True
    click(app, btn.rect.center)


def key(app, k):
    app.step(1 / 30, [pygame.event.Event(pygame.KEYDOWN, key=k, unicode="", mod=0)])


def find(buttons, text):
    for b in buttons:
        if text.lower() in b.label.lower() and b.enabled:
            return b
    return None


class Driver:
    def __init__(self, seed=1, profession="comerciante", diplomacy=True, verbose=False, shot_dir=None):
        self.shot_dir = shot_dir
        self.shots = {}
        self.app = App(headless=True)
        self.rng = random.Random(seed)
        self.seed = seed
        self.prof = profession
        self.diplomacy = diplomacy
        self.verbose = verbose
        self.steps = 0
        self.seen = {}
        self.log = []

    def note(self, s):
        self.seen[s] = self.seen.get(s, 0) + 1

    def run(self, max_steps=6000):
        app = self.app
        app.replace(TitleScene(app))
        while self.steps < max_steps and app.running:
            self.steps += 1
            top = app.top
            name = type(top).__name__
            self.note(name)
            if self.shot_dir:
                n = self.shots.get(name, 0)
                if n < 2 and self.seen[name] in (1, 6):
                    self.shots[name] = n + 1
                    self.app.step(1 / 30, [])
                    pygame.image.save(self.app.screen, f"{self.shot_dir}/ui_{name}_{n}.png")
            fn = getattr(self, "do_" + name, None)
            if fn is None:
                app.step(1 / 30, [])
                continue
            r = fn(top)
            if r == "end":
                break
        return self

    # ---------------------------------------------------------------- escenas
    def do_TitleScene(self, sc):
        click_button(self.app, find(sc.menu_buttons, "Nueva"))

    def do_SetupScene(self, sc):
        sc.prof = self.prof
        sc.name = "Tester"
        random.seed(self.seed)
        click_button(self.app, sc.go)

    def do_OriginScene(self, sc):
        sc.motive = ["tierra", "deudas", "fe", "oro"][self.seed % 4]
        sc.purpose = ["granja", "comercio", "comunidad", "fortaleza"][self.seed % 4]
        click_button(self.app, sc.go)

    def do_RecruitScene(self, sc):
        for i, b in enumerate(sc.btns):
            if b.enabled and self.rng.random() < 0.7:
                click_button(self.app, b)
                if self.app.top is not sc:
                    return
        click_button(self.app, sc.done)

    def do_CutsceneScene(self, sc):
        click(self.app, (640, 300))
        click(self.app, (640, 300))

    def do_HowToScene(self, sc):
        self.app.pop()

    def do_ShopScene(self, sc):
        g = self.app.game
        if sc.initial:
            for item, n in (("food", 36), ("ammo", 7), ("goods", 16), ("parts", 3), ("medicine", 2)):
                for _ in range(n):
                    g.buy(item, 1.0)
            click_button(self.app, sc.done_btn)
        else:
            if sc.spec.barter_tribe:
                for b in sc.buttons:
                    if b.enabled and self.rng.random() < 0.5:
                        click_button(self.app, b)
            else:
                spec = sc.spec
                for k in ("food", "ammo", "medicine", "parts"):
                    for _ in range(4):
                        g.buy(k, spec.mult)
            click_button(self.app, sc.done_btn)

    def do_TravelScene(self, sc):
        g = self.app.game
        sc.moving = True
        sc.speed = 4
        sc.update(1.0) if False else None
        for _ in range(30):
            self.app.step(1 / 20, [])
            if self.app.top is not sc:
                return
        # mantenimiento
        for i, w in enumerate(g.wagons):
            if w.hp < w.max_hp * 0.6 and g.sup.parts > 0:
                g.repair_wagon(i)
        if g.sup.food < 250 and g.sup.ammo > 30:
            sc.moving = False
            click_button(self.app, find(sc.btns, "Acampar"))

    def do_PromptScene(self, sc):
        opts = sc.prompt.options
        if sc.prompt.title.startswith("¡") and len(opts) == 3 and self.diplomacy:
            click_button(self.app, sc.btns[1])
        elif "profundidad" in sc.prompt.title:
            click_button(self.app, sc.btns[2 if self.app.game.sup.money > 250 else 1])
        else:
            click_button(self.app, sc.btns[0])

    def do_CampScene(self, sc):
        g = self.app.game
        if g.sup.food < 250 and g.sup.ammo > 30 and not getattr(sc, "_hunted", 0) > 2:
            sc._hunted = getattr(sc, "_hunted", 0) + 1
            click_button(self.app, find(sc.btns, "caza"))
            return
        if sc.wp is not None and sc.wp["kind"] == "post" and not getattr(sc, "_shopped", False):
            sc._shopped = True
            click_button(self.app, find(sc.btns, "Comerciar"))
            return
        if not getattr(sc, "_visited", False):
            sc._visited = True
            click_button(self.app, find(sc.btns, "Reparar"))
            return
        if any(c.health < 55 for c in g.living()) and g.sup.food > 100 and getattr(sc, "_rests", 0) < 3:
            sc._rests = getattr(sc, "_rests", 0) + 1
            click_button(self.app, find(sc.btns, "Descansar 3"))
            return
        click_button(self.app, sc.go_btn)

    def do_DefenseScene(self, sc):
        click_button(self.app, sc.auto)
        click_button(self.app, sc.close)

    def do_DiplomacyScene(self, sc):
        c = sc.c
        g = self.app.game
        if c.ended:
            click_button(self.app, find(sc.btns, "Terminar"))
            return
        if sc.gift_open:
            if g.sup.goods >= 2:
                click_button(self.app, sc.btns[0])
            else:
                click_button(self.app, find(sc.btns, "Volver"))
            return
        a = c.ts.attitude
        if "saludo" not in c.used:
            c.used.add("saludo")
            click_button(self.app, find(sc.btns, "Saludar"))
        elif a < 25 and g.sup.goods >= 3 and getattr(sc, "_gifts", 0) < 2:
            sc._gifts = getattr(sc, "_gifts", 0) + 1
            click_button(self.app, find(sc.btns, "regalo"))
        elif g.day > c.ts.treaty_until and g.sup.goods >= 6 and a > -25 and "paso" not in c.used:
            c.used.add("paso")
            click_button(self.app, find(sc.btns, "paso seguro"))
        elif "trade" not in c.used and a > 0 and getattr(sc, "_traded", 0) == 0:
            sc._traded = 1
            click_button(self.app, find(sc.btns, "Comerciar"))
        else:
            click_button(self.app, find(sc.btns, "Despedirse"))

    def do_BattleScene(self, sc):
        b = sc.battle
        if b.done:
            for _ in range(60):
                self.app.step(1 / 20, [])
            click(self.app, (700, 300))
            return
        if b.phase == "prep":
            key(self.app, pygame.K_a)
            key(self.app, pygame.K_RETURN)
        for i in range(40):
            if self.app.top is not sc:
                return
            if i % 12 == 0:
                key(self.app, pygame.K_a)
            self.app.step(1 / 10, [])
            if b.done:
                return

    def do_SiteScene(self, sc):
        k, r = sc.cards[min(1, len(sc.cards) - 1)]
        click_button(self.app, sc.btns[min(1, len(sc.btns) - 1)])

    def do_SettlementScene(self, sc):
        for _ in range(3):
            for b in sc.btns:
                if b.enabled:
                    click_button(self.app, b)
        click_button(self.app, sc.go)

    def do_ChronicleScene(self, sc):
        for _ in range(3):
            click_button(self.app, sc.skip) if sc.phase == "story" else None
        self.note("CHRONICLE_RESULT")
        self.app.step(1 / 30, [])
        return "end"

    def do_EndScene(self, sc):
        self.note("ENDSCENE")
        self.end_title = sc.title
        return "end"

    def do_JournalScene(self, sc):
        self.app.pop()

    def do_ConfirmQuit(self, sc):
        self.app.pop()
