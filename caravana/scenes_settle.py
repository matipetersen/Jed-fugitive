"""Final del camino: elegir sitio, construir el asentamiento y vivir el primer año."""
from __future__ import annotations

import math

import pygame

from . import art, data, ui
from .scene import Scene
from .scenes_travel import PromptScene
from .model import Prompt
from .settlement import MAKESHIFT, Chronicle, Settlement
from .ui import C, Button, text, panel, para, bar


def _mood(att: float) -> str:
    return "hostiles" if att < -30 else "recelosos" if att < -5 else "cautos" if att < 20 else "amistosos" if att < 50 else "aliados"


PREFS = {"esposa": "willamette", "hannah": "willamette", "hija": "willamette", "abuelo": "walla", "ruth": "walla",
         "hijo": "columbia", "tomas": "columbia", "silas": "columbia", "mary": "columbia"}


class SiteScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.g = app.game
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "valle", 71)
        self.cards = []
        if self.g.forced_winter:
            self.keys = ["improvisado"]
        else:
            self.keys = list(data.SITES.keys())
        self.btns = []
        n = len(self.keys)
        w = 380
        total = n * w + (n - 1) * 30
        x0 = (ui.W - total) // 2
        for i, k in enumerate(self.keys):
            rect = pygame.Rect(x0 + i * (w + 30), 150, w, 480)
            self.cards.append((k, rect))
            self.btns.append(Button((rect.x + 40, rect.bottom - 62, w - 80, 46), "Fundar aquí", (lambda k=k: self._choose(k)), size=19, color=(98, 74, 40)))

    def _choose(self, key):
        from .scenes_menu import EndScene
        g = self.g
        for role, pref in PREFS.items():
            c = g.member(role)
            if c is not None and key != "improvisado":
                c.loyalty = max(0, min(100, c.loyalty + (4 if pref == key else -1)))
        notes = g.travel_to_site(key) if key != "improvisado" else []
        if not g.living():
            self.app.replace(EndScene(self.app, "El último tramo fue el definitivo",
                                      "Los últimos supervivientes no resisten el tramo final."))
            return
        st = Settlement(g, key)
        sc = SettlementScene(self.app, st)
        self.app.replace(sc)
        if notes:
            self.app.push(PromptScene(self.app, Prompt.info("El último tramo", "\n".join(notes), "danger")))

    def handle(self, ev):
        for b in self.btns:
            if b.handle(ev):
                return

    def draw(self, screen):
        g = self.g
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((12, 9, 6, 185))
        screen.blit(veil, (0, 0))
        if g.forced_winter:
            text(screen, "El invierno os ha detenido", (ui.W // 2, 40), 44, C["red"], serif=True, bold=True, anchor="midtop", shadow=True)
            text(screen, "No hay más camino: fundaréis donde estáis.", (ui.W // 2, 98), 20, C["parch"], anchor="midtop")
        else:
            text(screen, "Bifurcación del Columbia", (ui.W // 2, 40), 44, C["gold"], serif=True, bold=True, anchor="midtop", shadow=True)
            text(screen, "¿Dónde fundaréis vuestro hogar?", (ui.W // 2, 98), 22, C["parch"], anchor="midtop")
            text(screen, f"Quedan {max(0, data.FORCED_WINTER_DAY - g.day)} días para el invierno · {g.pop()} colonos · comida {int(g.sup.food)} lb",
                 (ui.W // 2, 124), 16, C["dim"], anchor="midtop")
        for k, r in self.cards:
            site = MAKESHIFT if k == "improvisado" else data.SITES[k]
            panel(screen, r, C["panel"], C["gold"], 12, width=3)
            text(screen, site["name"], (r.centerx, r.y + 14), 26, C["gold"], serif=True, bold=True, anchor="midtop")
            # miniatura
            pic = pygame.Rect(r.x + 20, r.y + 56, r.w - 40, 90)
            pygame.draw.rect(screen, (96, 150, 90) if k != "columbia" else (110, 130, 120), pic, border_radius=8)
            if k == "willamette":
                for i in range(6):
                    pygame.draw.polygon(screen, (40, 90, 56), [(pic.x + 30 + i * 52, pic.bottom - 6), (pic.x + 44 + i * 52, pic.y + 16), (pic.x + 58 + i * 52, pic.bottom - 6)])
            elif k == "walla":
                pygame.draw.rect(screen, (170, 150, 100), (pic.x, pic.y + 50, pic.w, 40))
                pygame.draw.polygon(screen, (130, 120, 100), [(pic.x, pic.y + 50), (pic.x + 90, pic.y + 14), (pic.x + 180, pic.y + 50)])
            elif k == "columbia":
                pygame.draw.rect(screen, (70, 120, 180), (pic.x, pic.y + 54, pic.w, 36))
                pygame.draw.polygon(screen, (110, 100, 90), [(pic.x, pic.y + 54), (pic.x + 60, pic.y + 8), (pic.x + 160, pic.y + 54)])
            else:
                pygame.draw.polygon(screen, (230, 236, 244), [(pic.x, pic.bottom), (pic.x + 100, pic.y + 20), (pic.x + 200, pic.bottom)])
            para(screen, site["text"], (r.x + 20, r.y + 158), r.w - 40, 15, C["text"], max_lines=5)
            y = r.y + 262
            for lbl, key in (("Fertilidad", "fertility"), ("Defensa", "defense"), ("Agua", "water"), ("Comercio", "trade")):
                text(screen, lbl, (r.x + 22, y), 15, C["dim"])
                v = site[key]
                bar(screen, (r.x + 130, y + 3, 200, 10), v / 10.0, C["green"] if v >= 7 else C["gold"] if v >= 5 else C["red"])
                y += 24
            nb = site["neighbor"] or g.current_tribe() or "cayuse"
            t = data.TRIBES[nb]
            att = g.tribes[nb].attitude
            text(screen, f"Vecinos: {t['name']} ({_mood(att)})", (r.x + 22, y + 6), 16, t["color"], bold=True)
            if k != "improvisado":
                fans = [g.member(r).name.split()[0] for r, p in PREFS.items() if p == k and g.member(r)]
                if fans:
                    para(screen, "Lo prefieren: " + ", ".join(fans[:5]), (r.x + 22, r.y + 430), r.w - 120, 13, C["parch"], max_lines=1)
                days = int(math.ceil(site["extra"] / 17.0))
                text(screen, f"+{site['extra']} millas · ~{days} días" if site["extra"] else "Sin viaje adicional", (r.x + 22, y + 32), 15, C["dim"])
        for b in self.btns:
            b.draw(screen)


class SettlementScene(Scene):
    def __init__(self, app, st: Settlement):
        super().__init__(app)
        self.g = app.game
        self.st = st
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "valle", 81)
        self.msg = ""
        self.msg_col = C["dim"]
        self.btns = []
        self.go = Button((ui.W - 400, ui.H - 70, 360, 52), "Sobrevivir el primer año →", self._go, size=21, color=(98, 74, 40))
        self.t = 0.0
        self._build()

    def resume(self):
        self._build()

    def _build(self):
        self.btns = []
        for i, k in enumerate(data.BUILDINGS):
            y = 120 + i * 62
            ok, why = self.st.can_build(k)
            label = "Hecho" if k in self.st.built else "Construir"
            b = Button((640, y + 6, 120, 42), label, (lambda k=k: self._build_it(k)), enabled=ok, size=16)
            self.btns.append(b)

    def _build_it(self, k):
        ok, msg = self.st.build(k)
        self.msg, self.msg_col = msg, (C["green"] if ok else C["red"])
        self._build()

    def _go(self):
        from .scenes_menu import EndScene
        seed = self.g.rng.randrange(10 ** 6)
        ch = self.st.simulate(seed)
        self.app.clear_save()
        self.app.replace(ChronicleScene(self.app, self.st, ch))

    def handle(self, ev):
        if self.go.handle(ev):
            return
        for b in self.btns:
            if b.handle(ev):
                return
        if ev.type == pygame.MOUSEMOTION:
            self.tip = ""

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        g = self.g
        st = self.st
        site = st.site
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((12, 9, 6, 180))
        screen.blit(veil, (0, 0))
        text(screen, f"{site['name']}", (40, 24), 38, C["gold"], serif=True, bold=True)
        text(screen, "Gastad lo que traéis: lo que no se construya hoy, no os protegerá en invierno.", (42, 74), 16, C["dim"])
        for i, (k, b) in enumerate(data.BUILDINGS.items()):
            y = 120 + i * 62
            built = k in st.built
            panel(screen, (30, y, 740, 56), (58, 62, 40) if built else C["panel"], C["green"] if built else C["edge"], 8)
            text(screen, b["name"], (46, y + 6), 19, C["text"], bold=True)
            text(screen, b["desc"], (46, y + 31), 13, C["dim"])
            x = 520
            for res, n in b["cost"].items():
                have = getattr(g.sup, res)
                ico = {"parts": "parts", "goods": "goods", "ammo": "ammo", "food": "food"}[res]
                ui.icon(screen, ico, x - 70 + 12, y + 28, 18)
                text(screen, f"{n}", (x - 70 + 28, y + 17), 16, C["green"] if have >= n else C["red"], bold=True)
                x += 52 if len(b["cost"]) > 1 else 0
                if len(b["cost"]) > 1:
                    pass
        for bt in self.btns:
            bt.draw(screen)
        # estado
        panel(screen, (800, 110, 440, 400), C["panel"], C["edge"], 10)
        s = g.sup
        text(screen, "Almacén", (820, 122), 22, C["gold"], serif=True, bold=True)
        rows = [("food", "Comida", f"{int(s.food)} lb"), ("ammo", "Munición", f"{s.ammo}"), ("goods", "Mercancías", f"{s.goods}"),
                ("parts", "Repuestos", f"{s.parts}"), ("medicine", "Medicinas", f"{s.medicine}"), ("money", "Dinero", f"${s.money:,.0f}")]
        y = 158
        for ico, nm, v in rows:
            ui.icon(screen, ico, 836, y + 10, 20)
            text(screen, nm, (860, y), 17, C["text"])
            text(screen, v, (1220, y), 17, C["gold"], anchor="topright")
            y += 27
        y += 10
        text(screen, f"Colonos: {g.pop()}", (820, y), 17, C["text"])
        y += 28
        nb = site["neighbor"] or "cayuse"
        t = data.TRIBES[nb]
        att = g.tribes[nb].attitude
        text(screen, f"Vecinos: {t['name']} — {_mood(att)} ({att:+.0f})", (820, y), 17, t["color"], bold=True)
        y += 34
        for lbl, key in (("Fertilidad", "fertility"), ("Defensa", "defense"), ("Agua", "water"), ("Comercio", "trade")):
            text(screen, lbl, (820, y), 14, C["dim"])
            bar(screen, (920, y + 3, 200, 9), min(10, site[key]) / 10.0, C["green"])
            y += 21
        need = len(g.living()) * 36 * 4
        y += 8
        para(screen, f"Un invierno largo exige ~{need} lb de comida. Sin cabañas morirá gente por el frío; sin pozo, por fiebres; "
                     f"sin tratado, quizá por incursiones.", (820, y), 400, 14, C["parch"])
        if self.msg:
            text(screen, self.msg, (40, ui.H - 60), 18, self.msg_col)
        self.go.draw(screen)


class ChronicleScene(Scene):
    def __init__(self, app, st: Settlement, ch: Chronicle):
        super().__init__(app)
        self.g = app.game
        self.st = st
        self.ch = ch
        self.t = 0.0
        self.shown = 1
        self.phase = "story"
        self.bg = art.ground_surface((ui.W + 40, ui.H + 40), "valle", 91)
        self.btns = [Button((ui.W // 2 - 270, ui.H - 76, 250, 50), "Volver al menú", self._menu, size=20),
                     Button((ui.W // 2 + 20, ui.H - 76, 250, 50), "Nueva partida", self._new, size=20, color=(98, 74, 40))]
        self.skip = Button((ui.W - 250, ui.H - 60, 220, 44), "Ver el resultado →", self._skip, size=17)
        self.saved = False

    def _menu(self):
        from .scenes_menu import TitleScene
        self.app.travel = None
        self.app.replace(TitleScene(self.app))

    def _new(self):
        from .scenes_menu import TitleScene, SetupScene
        self.app.travel = None
        self.app.replace(TitleScene(self.app))
        self.app.push(SetupScene(self.app))

    def _skip(self):
        if self.phase == "story":
            self.shown = len(self.ch.lines)
            self.phase = "result"
            self._save()

    def _save(self):
        if not self.saved:
            self.saved = True
            self.app.add_score(self.g.leader_name, self.ch.score, self.ch.rank)

    def handle(self, ev):
        if self.phase == "result":
            for b in self.btns:
                if b.handle(ev):
                    return
        else:
            if self.skip.handle(ev):
                return
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.shown = min(len(self.ch.lines), self.shown + 1)

    def update(self, dt):
        self.t += dt
        if self.phase == "story":
            n = int(self.t / 1.3)
            self.shown = max(self.shown, min(len(self.ch.lines), n))
            if self.shown >= len(self.ch.lines) and self.t > len(self.ch.lines) * 1.3 + 1.5:
                self.phase = "result"
                self._save()

    def draw(self, screen):
        g = self.g
        ch = self.ch
        screen.blit(self.bg, (-20, -20))
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((12, 9, 6, 200))
        screen.blit(veil, (0, 0))
        if self.phase == "story":
            text(screen, "Crónica del primer año", (ui.W // 2, 30), 42, C["gold"], serif=True, bold=True, anchor="midtop")
            panel(screen, (180, 100, ui.W - 360, ui.H - 190), (226, 208, 164), C["edge"], 12, width=3)
            y = 124
            for ln in ch.lines[:self.shown]:
                y = para(screen, ln, (210, y), ui.W - 420, 18, C["ink"], gap=3) + 8
                if y > ui.H - 120:
                    break
            self.skip.draw(screen)
            return
        title_col = C["gold"] if ch.survivors else C["red"]
        text(screen, ch.rank.upper(), (ui.W // 2, 24), 50, title_col, serif=True, bold=True, anchor="midtop", shadow=True)
        text(screen, f"{ch.survivors} de {len(g.colonists)} colonos pasaron el primer año en {self.st.site['name']}", (ui.W // 2, 90), 21, C["parch"], anchor="midtop")
        # puntuación
        panel(screen, (60, 130, 560, 440), C["panel"], C["edge"], 10)
        text(screen, "Puntuación", (80, 142), 24, C["gold"], serif=True, bold=True)
        y = 182
        for lbl, v in ch.breakdown:
            text(screen, lbl, (84, y), 18, C["text"])
            text(screen, f"{v:+d}" if v < 0 else f"{v}", (590, y), 18, C["gold"], anchor="topright")
            y += 30
        pygame.draw.line(screen, C["edge"], (84, y + 4), (590, y + 4), 2)
        text(screen, "TOTAL", (84, y + 14), 26, C["gold"], bold=True)
        text(screen, f"{ch.score}", (590, y + 14), 26, C["gold"], bold=True, anchor="topright")
        # supervivientes
        panel(screen, (650, 130, 570, 440), C["panel"], C["edge"], 10)
        text(screen, "La compañía", (670, 142), 24, C["gold"], serif=True, bold=True)
        y = 182
        for c in g.colonists:
            alive = c.alive
            col = C["text"] if alive else (140, 110, 100)
            art.draw_person(screen, 690, y + 11, c.group, c.cid, 1.1, dead=not alive)
            text(screen, c.name + ("  (líder)" if c.is_leader else ""), (710, y), 16, col)
            text(screen, "vive" if alive else f"† {c.cause}", (1200, y), 15, C["green"] if alive else C["dim"], anchor="topright")
            y += 24
            if y > 550:
                break
        st = self.st
        text(screen, f"Edificios: {len(st.built)} · Días de viaje: {g.day} · Millas: {int(g.mile)}", (ui.W // 2, 590), 16, C["dim"], anchor="midtop")
        for b in self.btns:
            b.draw(screen)
