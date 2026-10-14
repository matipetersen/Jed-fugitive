"""Plan de defensa: reparte colonos por las carretas y mejora el círculo entre ataques."""
from __future__ import annotations

import math

import pygame

from . import art, data, ui
from .battle import WAGON_GAP, WAGON_L
from .scene import Scene
from .ui import C, Button, text, panel, para, bar

CX, CY = 600, 372
S = 0.95


class DefenseScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.g = app.game
        self.sel_col = None
        self.sel_wagon = 0
        self.msg = ""
        self.msg_col = C["dim"]
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), self.g.terrain(), 51)
        self.close = Button((ui.W - 300, ui.H - 60, 270, 46), "Listo", self.app.pop, size=20, color=(98, 74, 40))
        self.auto = Button((30, ui.H - 60, 200, 46), "Auto-asignar", self._auto, size=18)
        self.unassign = Button((240, ui.H - 60, 200, 46), "Quitar puesto", self._unassign_sel, size=18)
        self.up_btns: list[Button] = []
        self.t = 0.0
        self._geom()
        self._build_up()

    def resume(self):
        self._geom()
        self._build_up()

    def _geom(self):
        g = self.g
        g.normalize_posts()
        self.n = len(g.wagons)
        self.R = max(118.0, self.n * (WAGON_L + WAGON_GAP) / (2 * math.pi))
        self.wag = []
        for i in range(self.n):
            a = -math.pi / 2 + math.tau * i / self.n
            self.wag.append((i, a, CX + math.cos(a) * self.R * S, CY + math.sin(a) * self.R * S))
        self.sel_wagon = min(self.sel_wagon, max(0, self.n - 1))

    def _auto(self):
        self.g.auto_assign()
        self.msg, self.msg_col = "Tiradores y ayudantes reasignados.", C["green"]

    def _unassign_sel(self):
        if self.sel_col is not None:
            self.sel_col.post = None
            self.sel_col = None

    def _slot_pos(self, i, slot):
        a = self.wag[i][1]
        r = (self.R - 30) * S
        off = (-0.17 if slot == "tirador" else 0.17) * 90 / max(60.0, self.R) * 1.15
        return CX + math.cos(a + off) * r, CY + math.sin(a + off) * r

    def _build_up(self):
        g = self.g
        self.up_btns = []
        if not g.wagons:
            return
        i = self.sel_wagon
        w = g.wagons[i]
        x, y, wd = 920, 330, 330
        defs = [
            (f"Reparar (+90 PV) · 1 repuesto", lambda: self._act(g.repair_wagon(i)), w.hp < w.max_hp - 1),
            (f"Reforzar con planchas · 2 repuestos ({w.reinforced}/2)", lambda: self._act(g.upgrade(i, "refuerzo")), w.reinforced < 2),
            ("Plataforma de tiro · 2 repuestos + 1 mercancía", lambda: self._act(g.upgrade(i, "plataforma")), not w.platform),
            ("Farol de combate · 2 mercancías", lambda: self._act(g.upgrade(i, "farol")), not w.lantern),
            (f"Montar cañón (en almacén: {g.cannon_stock})", lambda: self._act(g.upgrade(i, "cañón")), not w.cannon and g.cannon_stock > 0),
        ]
        for k, (lbl, fn, en) in enumerate(defs):
            b = Button((x, y + k * 50, wd, 44), lbl, fn, enabled=en, size=15)
            self.up_btns.append(b)

    def _act(self, res):
        ok, msg = res
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])
        self._build_up()

    # ------------------------------------------------------------ entrada
    def _rows(self):
        out = []
        cols = [c for c in self.g.living()]
        rh = max(24, min(36, (ui.H - 250) // max(1, len(cols))))
        y = 92
        for c in cols:
            out.append((c, pygame.Rect(24, y, 300, rh - 3)))
            y += rh
        return out

    def handle(self, ev):
        for b in [self.close, self.auto, self.unassign] + self.up_btns:
            if b.handle(ev):
                return
        g = self.g
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for c, r in self._rows():
                if r.collidepoint(ev.pos):
                    self.sel_col = None if self.sel_col is c else c
                    return
            for i in range(self.n):
                for slot in ("tirador", "ayuda"):
                    sx, sy = self._slot_pos(i, slot)
                    if math.hypot(ev.pos[0] - sx, ev.pos[1] - sy) < (28 if ui.TOUCH else 15):
                        if self.sel_col is not None:
                            if slot == "tirador" and not self.sel_col.can_shoot:
                                self.msg, self.msg_col = "Sólo adultos y jóvenes sanos pueden disparar: ponlos de ayudantes.", C["red"]
                            else:
                                g.assign(self.sel_col, i, slot)
                                self.sel_col = None
                                self.msg, self.msg_col = "", C["dim"]
                        else:
                            occ = g.post_of(i, slot)
                            if occ:
                                self.sel_col = occ
                        self.sel_wagon = i
                        self._build_up()
                        return
            for i, a, x, y in self.wag:
                if math.hypot(ev.pos[0] - x, ev.pos[1] - y) < 40:
                    self.sel_wagon = i
                    self._build_up()
                    return
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
            for c, r in self._rows():
                if r.collidepoint(ev.pos):
                    c.post = None
                    return
            for i in range(self.n):
                for slot in ("tirador", "ayuda"):
                    sx, sy = self._slot_pos(i, slot)
                    if math.hypot(ev.pos[0] - sx, ev.pos[1] - sy) < 15:
                        occ = g.post_of(i, slot)
                        if occ:
                            occ.post = None
                        return
            self.sel_col = None
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.app.pop()

    def update(self, dt):
        self.t += dt

    # ------------------------------------------------------------ dibujo
    def draw(self, screen):
        g = self.g
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((16, 11, 7, 150))
        screen.blit(veil, (0, 0))
        text(screen, "Plan de defensa", (30, 22), 38, C["gold"], serif=True, bold=True)
        text(screen, "Toca un colono y luego una plaza (T = tirador, A = ayudante). «Quitar puesto» o clic derecho para soltar.", (32, 66), 14, C["dim"])
        # círculo
        pygame.draw.circle(screen, (110, 88, 58), (CX, CY), int(self.R * S + 46), 0)
        pygame.draw.circle(screen, (126, 102, 66), (CX, CY), int(self.R * S + 46), 3)
        for tx, ty in ((-0.4, -0.25), (0.35, -0.3), (-0.3, 0.3)):
            art.draw_tent(screen, CX + tx * self.R * S, CY + ty * self.R * S, 0.9)
        art.draw_fire(screen, CX, CY, self.t, 1.0)
        for i, a, x, y in self.wag:
            w = g.wagons[i]
            surf = art.wagon_surface(max(0.0, w.hp / w.max_hp), w.reinforced, w.platform, w.cannon, w.lantern, False, a + math.pi / 2)
            sc = pygame.transform.smoothscale(surf, (int(surf.get_width() * S), int(surf.get_height() * S)))
            screen.blit(sc, sc.get_rect(center=(int(x), int(y))))
            if i == self.sel_wagon:
                pygame.draw.circle(screen, C["gold"], (int(x), int(y)), 50, 2)
            frac = w.hp / w.max_hp
            ox, oy = math.cos(a) * 52 * S, math.sin(a) * 52 * S
            bar(screen, (x + ox - 18, y + oy - 3, 36, 5), frac, C["green"] if frac > 0.5 else C["orange"] if frac > 0.25 else C["red"])
            text(screen, i + 1, (x + math.cos(a) * 66 * S, y + math.sin(a) * 66 * S), 16, C["gold"], bold=True, anchor="center", shadow=True)
        for i in range(self.n):
            for slot in ("tirador", "ayuda"):
                sx, sy = self._slot_pos(i, slot)
                occ = g.post_of(i, slot)
                col = (110, 160, 220) if slot == "tirador" else (120, 184, 100)
                pygame.draw.circle(screen, (30, 22, 16), (int(sx), int(sy)), 13)
                pygame.draw.circle(screen, col, (int(sx), int(sy)), 13, 2)
                if occ is None:
                    text(screen, "T" if slot == "tirador" else "A", (sx, sy), 13, col, anchor="center", bold=True)
                else:
                    art.draw_person(screen, sx, sy, occ.group, occ.cid, 1.4)
                    if self.sel_col is occ:
                        pygame.draw.circle(screen, C["gold"], (int(sx), int(sy)), 17, 3)
        # roster
        panel(screen, (14, 84, 322, ui.H - 160), C["panel"], C["edge"], 8)
        for c, r in self._rows():
            sel = self.sel_col is c
            pygame.draw.rect(screen, (92, 70, 46) if sel else (58, 44, 30), r, border_radius=5)
            if sel:
                pygame.draw.rect(screen, C["gold"], r, 2, border_radius=5)
            art.draw_person(screen, r.x + 14, r.centery, c.group, c.cid, 1.0)
            text(screen, c.name[:17], (r.x + 30, r.y + 1), 14, C["text"] if not c.sick else (200, 230, 150))
            bar(screen, (r.x + 30, r.bottom - 6, 100, 3), c.health / 100.0, C["green"] if c.health > 50 else C["orange"], border=False)
            lbl = "—"
            col = C["dim"]
            if c.post:
                lbl = f"C{c.post[0] + 1} " + ("tirador" if c.post[1] == "tirador" else "ayuda")
                col = (140, 190, 240) if c.post[1] == "tirador" else (150, 210, 130)
            text(screen, lbl, (r.right - 8, r.centery), 12, col, anchor="midright")
            if c.can_shoot:
                text(screen, f"P{c.shoot}", (r.x + 150, r.y + 3), 12, C["gold"])
        # panel de carreta
        panel(screen, (900, 70, 360, ui.H - 150), C["panel"], C["edge"], 10)
        if g.wagons:
            w = g.wagons[self.sel_wagon]
            text(screen, f"Carreta {self.sel_wagon + 1}", (920, 84), 26, C["gold"], serif=True, bold=True)
            bar(screen, (920, 124, 320, 12), w.hp / w.max_hp, C["green"] if w.hp / w.max_hp > 0.5 else C["red"])
            text(screen, f"{int(w.hp)} / {int(w.max_hp)} PV", (920, 142), 15, C["text"])
            ex = [n for n, ok in (("cañón", w.cannon), ("plataforma", w.platform), ("farol", w.lantern)) if ok]
            text(screen, f"Refuerzos: {w.reinforced}" + (" · " + ", ".join(ex) if ex else ""), (920, 164), 14, C["dim"])
            t_ = g.post_of(self.sel_wagon, "tirador")
            a_ = g.post_of(self.sel_wagon, "ayuda")
            text(screen, f"Tirador: {t_.name if t_ else '—'}", (920, 190), 15, (140, 190, 240))
            text(screen, f"Ayudante: {a_.name if a_ else '—'}", (920, 212), 15, (150, 210, 130))
            para(screen, "El ayudante recarga y apaga fuegos; con él el tirador dispara un 32 % más rápido.", (920, 238), 320, 13, C["dim"])
            s = g.sup
            text(screen, f"Repuestos: {s.parts} · Mercancías: {s.goods}", (920, 296), 15, C["gold"])
        for b in self.up_btns:
            b.draw(screen)
        sh = len(g.shooters())
        text(screen, f"Tiradores disponibles: {sh} · Plazas de tirador: {self.n} · Munición: {g.sup.ammo}", (30, ui.H - 100), 15, C["parch"])
        if self.msg:
            text(screen, self.msg, (460, ui.H - 52), 16, self.msg_col)
        self.unassign.enabled = self.sel_col is not None and self.sel_col.post is not None
        self.close.draw(screen)
        self.auto.draw(screen)
        self.unassign.draw(screen)
