"""Origen de la expedición (motivo y propósito) y primera etapa: reclutar seguidores."""
from __future__ import annotations

import pygame

from . import art, data, origin, ui
from .scene import Scene
from .ui import C, Button, text, panel, para, bar


class OriginScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.g = app.game
        self.motive = "tierra"
        self.purpose = "granja"
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "pradera", 17)
        self.go = Button((ui.W - 400, ui.H - 70, 360, 52), "Reclutar seguidores →", self._go, size=21, color=(98, 74, 40))

    def _go(self):
        origin.apply_origin(self.g, self.motive, self.purpose)
        self.app.replace(RecruitScene(self.app))

    def _rects(self, row: int):
        n = 4
        w, gap = 295, 20
        x0 = (ui.W - (n * w + (n - 1) * gap)) // 2
        y = 118 if row == 0 else 388
        h = 205 if row == 0 else 175
        return [pygame.Rect(x0 + i * (w + gap), y, w, h) for i in range(n)]

    def handle(self, ev):
        if self.go.handle(ev):
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for key, r in zip(origin.MOTIVES, self._rects(0)):
                if r.collidepoint(ev.pos):
                    self.motive = key
            for key, r in zip(origin.PURPOSES, self._rects(1)):
                if r.collidepoint(ev.pos):
                    self.purpose = key

    def _cards(self, screen, items: dict, rects, selected: str, perk_col):
        for (key, d), r in zip(items.items(), rects):
            sel = key == selected
            panel(screen, r, (84, 62, 38) if sel else C["panel"], C["gold"] if sel else C["edge"], 10, width=3 if sel else 2)
            text(screen, d["name"], (r.x + 14, r.y + 10), 21, C["gold"] if sel else C["text"], serif=True, bold=True)
            y = para(screen, d["text"], (r.x + 14, r.y + 44), r.w - 28, 14, C["text"] if sel else C["dim"], max_lines=5, gap=2)
            para(screen, d["perks"], (r.x + 14, r.bottom - 52), r.w - 28, 13, perk_col, max_lines=3, gap=1)

    def draw(self, screen):
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((14, 10, 6, 196))
        screen.blit(veil, (0, 0))
        text(screen, "Vuestra historia", (40, 20), 40, C["gold"], serif=True, bold=True)
        text(screen, "¿Por qué dejáis todo atrás?", (44, 82), 21, C["parch"], serif=True)
        self._cards(screen, origin.MOTIVES, self._rects(0), self.motive, C["green"])
        text(screen, "¿Qué pretendéis al llegar?", (44, 352), 21, C["parch"], serif=True)
        self._cards(screen, origin.PURPOSES, self._rects(1), self.purpose, C["blue"])
        text(screen, "El motivo cambia cómo parte la caravana; el propósito decide qué cuenta como éxito al fundar.", (44, ui.H - 62), 14, C["dim"])
        text(screen, f"Compañía: {self.g.leader_name} y su familia.", (44, ui.H - 40), 14, C["dim"])
        self.go.draw(screen)


class RecruitScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.g = app.game
        self.r = origin.Recruitment(self.g)
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "pradera", 18)
        self.t = 0.0
        self.msg = "Independence al amanecer. Varios viajeros sin carreta esperan en la plaza."
        self.msg_col = C["parch"]
        self.btns: list[Button] = []
        self.done = Button((ui.W - 360, ui.H - 62, 330, 48), "Ir a la tienda →", self._done, size=20, color=(98, 74, 40))
        self._build()

    def _done(self):
        from .scenes_trade import ShopScene
        from .model import ShopSpec
        self.app.replace(ShopScene(self.app, ShopSpec("Independence, Misuri", 1.0), initial=True))

    def _cards(self):
        out = []
        w, h, gap = 400, 238, 16
        x0 = (ui.W - (3 * w + 2 * gap)) // 2
        for i in range(len(self.r.cands)):
            col, row = i % 3, i // 3
            out.append(pygame.Rect(x0 + col * (w + gap), 92 + row * (h + gap), w, h))
        return out

    def _build(self):
        self.btns = []
        r = self.r
        for i, rect in enumerate(self._cards()):
            c = r.cands[i]
            tpl = c["tpl"]
            free = c["state"] == "libre"
            ok, _ = r.can_act(i)
            p = int(r.persuade_chance(i) * 100)
            self.btns.append(Button((rect.x + 130, rect.bottom - 48, 120, 38), f"Persuadir {p}%", (lambda i=i: self._act(i, False)),
                                    enabled=free and ok and r.approaches > 0, size=14))
            label = f"Contratar ${tpl['fee']}" if tpl["fee"] > 0 else "Se une gratis"
            self.btns.append(Button((rect.x + 258, rect.bottom - 48, 130, 38), label, (lambda i=i: self._act(i, True)),
                                    enabled=free and ok and (tpl["fee"] <= self.g.sup.money), size=14))

    def _act(self, i, hire):
        ok, msg = (self.r.hire(i) if hire else self.r.persuade(i))
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])
        self._build()

    def handle(self, ev):
        if self.done.handle(ev):
            return
        for b in self.btns:
            if b.handle(ev):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        g = self.g
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((14, 10, 6, 192))
        screen.blit(veil, (0, 0))
        text(screen, "Reclutar seguidores", (40, 16), 38, C["gold"], serif=True, bold=True)
        r = self.r
        ui.icon(screen, "money", ui.W - 340, 36, 26)
        text(screen, f"${g.sup.money:,.0f}", (ui.W - 318, 22), 26, C["gold"], bold=True)
        text(screen, f"Compañía {len(g.living())}/{origin.MAX_PARTY}", (ui.W - 220, 16), 18, C["text"])
        text(screen, f"Conversaciones: {r.approaches}", (ui.W - 220, 42), 16, C["gold"] if r.approaches else C["red"])
        for i, rect in enumerate(self._cards()):
            c = r.cands[i]
            tpl = c["tpl"]
            st = c["state"]
            panel(screen, rect, (60, 66, 40) if st == "unido" else (62, 34, 30) if st == "rechazo" else C["panel"],
                  C["green"] if st == "unido" else C["red"] if st == "rechazo" else C["edge"], 10)
            # retrato
            sub = pygame.Surface((120, 200), pygame.SRCALPHA)
            art.draw_portrait(sub, 60, 196, 230, tpl["id"], tpl["groups"][0], i + 3, "alegre" if st == "unido" else "triste" if st == "rechazo" else "neutral",
                              t=self.t + i, dim=(st == "rechazo"))
            screen.blit(sub, (rect.x + 6, rect.y + 10))
            names = " y ".join(tpl["names"]) if len(tpl["names"]) == 2 and tpl["id"] == "gemelos" else tpl["names"][0]
            text(screen, names, (rect.x + 130, rect.y + 10), 19, C["gold"], serif=True, bold=True)
            if len(tpl["names"]) > 1 and tpl["id"] != "gemelos":
                text(screen, "y su hijo/a", (rect.x + 130, rect.y + 32), 12, C["dim"])
            text(screen, f"{data.ROLE_NAMES.get(tpl['id'], '')} · {tpl['trait']}", (rect.x + 130, rect.y + 32 + (12 if len(tpl['names']) > 1 and tpl['id'] != 'gemelos' else 0)), 13, C["parch"])
            para(screen, tpl["pitch"], (rect.x + 130, rect.y + 62), rect.w - 142, 13, C["text"], max_lines=4, gap=1)
            sk = tpl["skills"]
            yy = rect.y + 142
            for j, (lb, key) in enumerate((("Punt.", "shoot"), ("Med.", "medic"), ("Const.", "build"), ("Labia", "talk"), ("Caza", "hunt"))):
                x = rect.x + 130 + (j % 3) * 88
                y = yy + (j // 3) * 22
                text(screen, lb, (x, y), 11, C["dim"])
                bar(screen, (x + 32, y + 3, 48, 7), sk[key] / 10.0, C["green"] if sk[key] >= 7 else C["gold"] if sk[key] >= 4 else C["red"], border=False)
            if st != "libre":
                text(screen, "SE UNE" if st == "unido" else "RECHAZÓ", (rect.right - 14, rect.y + 10), 15, C["green"] if st == "unido" else C["red"], bold=True, anchor="topright")
            tags = {"land": "tierra", "faith": "fe", "gold": "fortuna", "escape": "huida"}
            lk = ", ".join(tags[t] for t in sorted(tpl["likes"]))
            text(screen, f"Le mueve: {lk}", (rect.x + 14, rect.bottom - 22), 11, C["dim"])
        for b in self.btns:
            b.draw(screen)
        para(screen, self.msg, (40, ui.H - 62), ui.W - 440, 16, self.msg_col, max_lines=2)
        self.done.draw(screen)
