"""Tienda de fuertes, comerciantes y trueque con las tribus."""
from __future__ import annotations

import pygame

from . import art, data, sfx, ui
from .model import ShopSpec, apply_offer, tribe_offers
from .scene import Scene
from .ui import C, Button, text, panel, para

ROW_H = 60


class ShopScene(Scene):
    def __init__(self, app, spec: ShopSpec, initial: bool = False):
        super().__init__(app)
        self.spec = spec
        self.initial = initial
        self.g = app.game
        self.msg = ""
        self.msg_col = C["dim"]
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "pradera" if initial else self.g.terrain(), 21)
        self.used: set[int] = set()
        self.bulk = False
        self.offers = tribe_offers(self.g, spec.barter_tribe) if spec.barter_tribe else []
        self.items = [k for k in ("food", "ammo", "goods", "parts", "medicine", "oxen", "wagon", "cannon")
                      if not (k == "cannon" and not spec.cannon) and not (k == "wagon" and not spec.wagons)]
        self.buttons: list[Button] = []
        self.bulk_btn = Button((620, 30, 220, 40), "", self._toggle_bulk, size=16)
        self.done_btn = Button((ui.W - 330, ui.H - 74, 270, 50), "¡Partir hacia Oregón!" if initial else "Terminar", self._done,
                               size=21, color=(98, 74, 40))
        self._build()

    def _mult(self):
        return self.spec.mult

    def _qty(self):
        return 5 if (self.bulk or pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1

    def _toggle_bulk(self):
        self.bulk = not self.bulk

    def _build(self):
        self.buttons = []
        if self.spec.barter_tribe:
            for i, off in enumerate(self.offers):
                y = 130 + i * 84
                self.buttons.append(Button((700, y + 12, 140, 46), "Aceptar", (lambda i=i: self._accept(i)),
                                           enabled=i not in self.used and self._can_offer(self.offers[i]), size=18))
            return
        for i, k in enumerate(self.items):
            y = 120 + i * ROW_H
            self.buttons.append(Button((620, y + 8, 100, 40), "Comprar", (lambda k=k: self._buy(k)), size=17))
            self.buttons.append(Button((730, y + 8, 100, 40), "Vender", (lambda k=k: self._sell(k)), size=17))

    def _can_offer(self, off):
        tk, tn = off["take"]
        return getattr(self.g.sup, tk) >= tn

    def _accept(self, i):
        ok, msg = apply_offer(self.g, self.offers[i])
        if ok:
            self.used.add(i)
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])
        self._build()

    def _buy(self, k):
        ok, msg = self.g.buy(k, self._mult(), self._qty())
        if ok:
            sfx.play("coin", 0.6, 0.05)
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])

    def _sell(self, k):
        ok, msg = self.g.sell(k, self._mult(), self._qty())
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])

    def _done(self):
        if self.initial:
            from .scenes_travel import TravelScene
            self.app.replace(TravelScene(self.app, intro=True))
        else:
            self.app.pop()

    def handle(self, ev):
        if self.done_btn.handle(ev):
            return
        if not self.spec.barter_tribe and self.bulk_btn.handle(ev):
            return
        for b in self.buttons:
            if b.handle(ev):
                return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE and not self.initial:
            self.app.pop()

    def draw(self, screen):
        g = self.g
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((16, 11, 7, 205))
        screen.blit(veil, (0, 0))
        if self.spec.barter_tribe:
            t = data.TRIBES[self.spec.barter_tribe]
            text(screen, f"Trueque con los {t['name']}", (50, 36), 38, C["gold"], serif=True, bold=True)
            wants = {"food": "comida", "goods": "mercancías", "ammo": "munición", "medicine": "medicinas"}[t["wants"]]
            text(screen, f"Valoran sobre todo: {wants}. Cada trato se puede aceptar una vez.", (52, 86), 17, C["dim"])
            for i, off in enumerate(self.offers):
                y = 130 + i * 84
                panel(screen, (50, y, 800, 74), C["panel"], C["edge"], 8)
                para(screen, off["text"], (70, y + 14), 600, 19, C["text"])
                gk, gn = off["give"]
                tk, tn = off["take"]
                text(screen, f"Recibes {gn} · Entregas {tn}", (70, y + 46), 14, C["dim"])
                if i in self.used:
                    text(screen, "Hecho", (780, y + 26), 18, C["green"], anchor="topright")
            for b in self.buttons:
                b.draw(screen)
        else:
            text(screen, self.spec.name, (50, 30), 38, C["gold"], serif=True, bold=True)
            text(screen, "Precios con recargo por la distancia" if self.spec.mult > 1.05 else "Los precios más baratos de todo el camino",
                 (52, 80), 16, C["dim"])
            self.bulk_btn.label = "Cantidad: ×5" if self.bulk else "Cantidad: ×1"
            self.bulk_btn.selected = self.bulk
            self.bulk_btn.draw(screen)
            for i, k in enumerate(self.items):
                y = 120 + i * ROW_H
                name, unit, base, per = data.ITEMS[k]
                panel(screen, (50, y, 790, ROW_H - 6), C["panel"], C["edge"], 8)
                ico = {"food": "food", "ammo": "ammo", "goods": "goods", "parts": "parts", "medicine": "medicine",
                       "oxen": "oxen", "wagon": "wagon", "cannon": "cannon"}[k]
                ui.icon(screen, ico, 82, y + 24, 28)
                text(screen, name, (110, y + 6), 22, C["text"], bold=True)
                text(screen, f"{unit} · ${g.price(k, self._mult()):.0f} (vende a ${g.price(k, self._mult(), True):.0f})", (110, y + 32), 14, C["dim"])
                have = self._have_text(k)
                text(screen, have, (440, y + 16), 17, C["gold"])
            for b in self.buttons:
                b.draw(screen)
        self._draw_side(screen)
        self.done_btn.draw(screen)
        if self.msg:
            text(screen, self.msg, (50, ui.H - 60), 18, self.msg_col)

    def _have_text(self, k):
        g = self.g
        s = g.sup
        if k == "food":
            return f"Tienes {int(s.food)} lb"
        if k == "ammo":
            return f"Tienes {s.ammo} balas"
        if k == "goods":
            return f"Tienes {s.goods}"
        if k == "parts":
            return f"Tienes {s.parts}"
        if k == "medicine":
            return f"Tienes {s.medicine}"
        if k == "oxen":
            return f"Tienes {s.oxen} bueyes"
        if k == "wagon":
            return f"Tienes {len(g.wagons)} carretas"
        return f"En almacén: {g.cannon_stock}"

    def _daily_need(self):
        g = self.g
        return sum(data.RATIONS[g.rations] * (0.6 if c.group == "niño" else 0.8 if c.group == "anciano" else 1.0) for c in g.living())

    def _draw_side(self, screen):
        g = self.g
        s = g.sup
        x = 880
        panel(screen, (x, 30, 360, ui.H - 130), C["panel"], C["gold"], 10)
        ui.icon(screen, "money", x + 30, 62, 30)
        text(screen, f"${s.money:,.0f}", (x + 56, 44), 32, C["gold"], bold=True)
        y = 100
        rows = [
            ("food", "Comida", f"{int(s.food)} lb"), ("ammo", "Munición", f"{s.ammo}"), ("goods", "Mercancías", f"{s.goods}"),
            ("parts", "Repuestos", f"{s.parts}"), ("medicine", "Medicinas", f"{s.medicine}"),
            ("oxen", "Bueyes", f"{s.oxen}"), ("wagon", "Carretas", f"{len(g.wagons)}"),
        ]
        for ico, name, val in rows:
            ui.icon(screen, ico, x + 28, y + 11, 20)
            text(screen, name, (x + 54, y), 17, C["text"])
            text(screen, val, (x + 330, y), 17, C["gold"], anchor="topright")
            y += 27
        y += 10
        pygame.draw.line(screen, C["edge"], (x + 14, y), (x + 346, y))
        y += 10
        days = s.food / max(0.1, self._daily_need())
        adv = []
        adv.append((f"Comida para unos {days:.0f} días a raciones normales. El viaje dura 110–160.",
                    C["green"] if days > 90 else C["gold"] if days > 45 else C["red"]))
        need_ox = 2 * len(g.wagons)
        adv.append((f"Bueyes: {s.oxen}/{need_ox}. Con menos, las carretas se frenan.", C["green"] if s.oxen >= need_ox else C["red"]))
        adv.append((f"Munición: un combate grande gasta 50–100 balas.", C["green"] if s.ammo >= 100 else C["gold"] if s.ammo >= 40 else C["red"]))
        if s.goods < 12:
            adv.append(("Mercancías: son tus regalos y tributos. Sin ellas, la diplomacia es imposible.", C["gold"] if s.goods >= 6 else C["red"]))
        if g.mile > 1200 or self.initial is False and g.mile > 1000:
            adv.append(("Guarda repuestos, mercancías y comida: el asentamiento los necesita para construir.", C["parch"]))
        for t, col in adv:
            y = para(screen, t, (x + 16, y), 330, 15, col, gap=2) + 6
