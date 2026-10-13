"""Escena de diplomacia con las tribus."""
from __future__ import annotations

import math

import pygame

from . import art, data, ui
from .model import Contact
from .scene import Scene
from .ui import C, Button, text, panel, para, bar


class DiplomacyScene(Scene):
    def __init__(self, app, contact: Contact):
        super().__init__(app)
        self.c = contact
        self.g = app.game
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), self.g.terrain(), 61)
        self.gift_open = False
        self.btns: list[Button] = []
        self.t = 0.0
        self.log: list[tuple[str, str]] = []  # (quien, texto)
        if contact.opening:
            self.log.append(("narr", contact.opening))
        for h in contact.history:
            self.log.append(("narr", h))
        self._shown = len(contact.history)
        self.hover_tip = ""
        self._build()

    # ------------------------------------------------------------ botones
    def _build(self):
        c = self.c
        g = self.g
        self.btns = []
        x, w = 880, 360
        ts = c.ts
        if c.ended:
            self.btns.append(Button((x, 560, w, 54), "Terminar el encuentro", self._finish, size=21, color=(98, 74, 40)))
            return
        if self.gift_open:
            y = 150
            for kind, name in (("goods", "Mercancías"), ("food", "Comida (×50 lb)"), ("ammo", "Munición"), ("medicine", "Medicinas")):
                units = c.GIFT_UNITS[kind]
                star = " ★" if c.info["wants"] == kind else ""
                for j, u in enumerate(units):
                    lbl = f"{u}" if kind != "food" else f"{u * 50} lb"
                    self.btns.append(Button((x + 120 + j * 82, y, 76, 40), lbl, (lambda k=kind, u=u: self._gift(k, u)), size=17))
                y += 56
            self.btns.append(Button((x, 560, w, 46), "Volver", lambda: self._set_gift(False), size=18))
            return
        defs = [
            ("Saludar con respeto", "saludo", "Gratis. Quizá te cause buena impresión."),
            ("Hacer un regalo…", None, "Regalar mercancías, comida, munición o medicinas."),
            ("Comerciar (trueque)", "comerciar", "Bueyes, medicinas, comida… no cuesta paciencia."),
            ("Negociar paso seguro", "paso", f"Tributo ≈ {3 + c.info['pride'] // 2} mercancías. Tregua de unos 12+ días."),
            ("Pedir información", "info", "1 mercancía. Noticias y a veces un buen sitio de caza."),
            ("Contratar guía e intérprete", "guia", "8 mercancías. Requiere trato 10+. Dura ~450 millas."),
            ("Proponer alianza", "alianza", "10 mercancías. Requiere trato 55+ y un pacto previo."),
            ("Mostrar fuerza", "fuerza", "Arriesgado: intimidar puede evitar o provocar una guerra."),
            ("Despedirse", "adios", "Termina la reunión."),
        ]
        y = 110
        for lbl, key, hint in defs:
            if key is None:
                fn = lambda: self._set_gift(True)
            else:
                fn = (lambda k=key: self._do(k))
            b = Button((x, y, w, 46), lbl, fn, size=18)
            b.hint = hint
            self.btns.append(b)
            y += 52

    def _set_gift(self, v):
        self.gift_open = v
        self._build()

    def _gift(self, kind, units):
        self._do("regalo", (kind, units))
        self.gift_open = False
        self._build()

    def _do(self, key, arg=None):
        c = self.c
        msg = c.do(key, arg)
        before = self._shown
        # el último mensaje de historia ya se ha añadido en c.history salvo errores
        if len(c.history) > before:
            for h in c.history[before:]:
                self.log.append(("narr", h))
            self._shown = len(c.history)
        else:
            self.log.append(("warn", msg))
        if c.shop_requested:
            c.shop_requested = False
            from .scenes_trade import ShopScene
            self.app.push(ShopScene(self.app, __import__("caravana.model", fromlist=["ShopSpec"]).ShopSpec(
                "Trueque", 1.0, barter_tribe=c.tribe)))
        self._build()

    def _finish(self):
        spec = self.c.finish()
        self.app.pop()
        t = self.app.travel
        if t:
            if self.c.result == "paz":
                t.push_feed(f"Paz con los {self.c.info['name']}.", C["green"])
            if spec is not None:
                t.handle_interrupt(spec)

    def resume(self):
        self._build()

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.MOUSEMOTION:
            self.hover_tip = ""
            for b in self.btns:
                if b.rect.collidepoint(ev.pos) and b.hint:
                    self.hover_tip = b.hint

    def update(self, dt):
        self.t += dt

    # ------------------------------------------------------------ dibujo
    def draw(self, screen):
        c = self.c
        g = self.g
        info = c.info
        tcol = info["color"]
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((14, 10, 6, 195))
        screen.blit(veil, (0, 0))
        # tarjeta de la tribu
        panel(screen, (30, 30, 330, ui.H - 60), C["panel"], tcol, 12, width=3)
        banner = pygame.Rect(46, 46, 298, 120)
        pygame.draw.rect(screen, tcol, banner, border_radius=8)
        pygame.draw.rect(screen, (20, 14, 10), banner, 3, border_radius=8)
        # tipi y jefe
        bx, by = banner.centerx, banner.centery + 6
        pygame.draw.polygon(screen, (236, 224, 190), [(bx, by - 46), (bx + 50, by + 40), (bx - 50, by + 40)])
        pygame.draw.polygon(screen, (60, 44, 30), [(bx, by + 40), (bx - 12, by + 40), (bx, by - 2)])
        for k in range(-2, 3):
            pygame.draw.line(screen, (120, 90, 56), (bx + k * 6, by - 48), (bx + k * 14, by - 70), 2)
        pygame.draw.circle(screen, (170, 90, 60), (bx - 5, by - 14), 6)
        text(screen, info["name"].upper(), (banner.centerx, 176), 30, C["gold"], serif=True, bold=True, anchor="midtop")
        para(screen, info["lore"], (50, 216), 290, 14, C["dim"], max_lines=4)
        # humor
        mood = c.mood()
        att = c.ts.attitude
        text(screen, f"Trato: {mood}", (50, 300), 22, C["text"], bold=True)
        r = pygame.Rect(50, 336, 290, 14)
        for i in range(r.w):
            k = i / r.w
            col = (int(210 - 90 * k), int(70 + 110 * k), 60) if k < 0.5 else (int(120 - 40 * (k - 0.5) * 2), int(180), int(70 + 60 * (k - 0.5) * 2))
            pygame.draw.line(screen, col, (r.x + i, r.y), (r.x + i, r.bottom))
        pygame.draw.rect(screen, (0, 0, 0), r, 1)
        px = r.x + (att + 100) / 200 * r.w
        pygame.draw.polygon(screen, C["white"], [(px, r.bottom + 2), (px - 6, r.bottom + 12), (px + 6, r.bottom + 12)])
        text(screen, f"{att:+.0f}", (px, r.bottom + 14), 14, C["white"], anchor="midtop")
        # estados
        y = 396
        chips = []
        if g.day <= c.ts.treaty_until:
            chips.append((f"Tregua hasta el día {c.ts.treaty_until}" if c.ts.treaty_until < 9999 else "Paz permanente", C["green"]))
        if c.ts.allied:
            chips.append(("Alianza sellada", C["green"]))
        if g.has_guide():
            chips.append(("Guía/intérprete contigo", C["blue"]))
        if c.ts.arms > 2:
            chips.append(("Bien armados (con tu pólvora)", C["orange"]))
        for s, col in chips:
            text(screen, "• " + s, (50, y), 15, col)
            y += 22
        # paciencia
        text(screen, "Paciencia", (50, ui.H - 160), 16, C["dim"])
        for i in range(max(c.patience, 0)):
            pygame.draw.circle(screen, C["gold"], (150 + i * 24, ui.H - 151), 8)
        for i in range(max(c.patience, 0), 6):
            pygame.draw.circle(screen, (70, 54, 38), (150 + i * 24, ui.H - 151), 8, 2)
        # recursos
        s = g.sup
        ui.icon(screen, "goods", 62, ui.H - 108, 20)
        text(screen, f"{s.goods}", (80, ui.H - 118), 17, C["gold"])
        ui.icon(screen, "food", 132, ui.H - 108, 20)
        text(screen, f"{int(s.food)}", (150, ui.H - 118), 17, C["gold"])
        ui.icon(screen, "ammo", 232, ui.H - 108, 20)
        text(screen, f"{s.ammo}", (250, ui.H - 118), 17, C["gold"])
        ui.icon(screen, "medicine", 302, ui.H - 108, 20)
        text(screen, f"{s.medicine}", (320, ui.H - 118), 17, C["gold"])
        text(screen, f"Tu labia: {c.talk_skill():.0f}", (50, ui.H - 76), 15, C["dim"])
        # diálogo
        panel(screen, (380, 30, 480, ui.H - 60), (226, 208, 164), C["edge"], 12, width=3)
        text(screen, {"visit": "Una visita", "patrol": "Una patrulla os sale al paso", "tense": "Parlamento a vida o muerte"}[c.kind],
             (620, 44), 24, C["ink"], serif=True, bold=True, anchor="midtop")
        # mensajes (de abajo arriba)
        y = ui.H - 60
        for who, msg in list(self.log)[::-1]:
            lines = ui.wrap(msg, 16, 430)
            h = len(lines) * (ui.font(16).get_linesize() + 1) + 10
            y -= h + 6
            if y < 90:
                break
            col = (80, 40, 30) if who == "warn" else C["ink"]
            bg = (214, 192, 140) if who == "narr" else (236, 214, 190)
            pygame.draw.rect(screen, bg, (396, y, 448, h), border_radius=6)
            yy = y + 5
            for ln in lines:
                screen.blit(ui.font(16).render(ln, True, col), (404, yy))
                yy += ui.font(16).get_linesize() + 1
        # acciones
        panel(screen, (870, 30, 380, ui.H - 60), C["panel"], C["edge"], 12)
        text(screen, "¿Qué haces?" if not self.gift_open else "Elige el regalo", (1060, 46), 22, C["gold"], serif=True, bold=True, anchor="midtop")
        if c.ended:
            text(screen, {"paz": "Hay paz.", "hostil": "¡La guerra es inevitable!", "neutral": "El encuentro ha terminado."}[c.result],
                 (1060, 480), 24, C["green"] if c.result == "paz" else C["red"] if c.result == "hostil" else C["parch"], anchor="midtop", serif=True)
        if self.gift_open:
            y = 150
            for kind, name in (("goods", "Mercancías"), ("food", "Comida"), ("ammo", "Munición"), ("medicine", "Medicinas")):
                star = "★ " if info["wants"] == kind else ""
                text(screen, star + name, (890, y + 10), 16, C["gold"] if star else C["text"])
                y += 56
            text(screen, "★ = lo que más valoran", (890, 380), 14, C["dim"])
        for b in self.btns:
            b.draw(screen)
        if self.hover_tip:
            ui.draw_tooltip(screen, self.hover_tip, pygame.mouse.get_pos())
