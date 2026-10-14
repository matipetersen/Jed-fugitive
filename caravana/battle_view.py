"""Escena de combate: vista cenital 360° del círculo de carretas y panel de mando."""
from __future__ import annotations

import math
import random
from typing import Callable, Optional

import pygame

from . import art, data, sfx, ui
from .battle import Battle, FIELD_RADIUS
from .model import BattleSpec, Game
from .scene import Scene
from .ui import C, Button, text, panel, bar

LEFT_W = 262
S = 1.0


class Camera:
    def __init__(self, cx, cy, s):
        self.cx, self.cy, self.s = cx, cy, s
        self.shake = 0.0

    def __call__(self, x, y):
        ox = random.uniform(-1, 1) * self.shake
        oy = random.uniform(-1, 1) * self.shake
        return (self.cx + x * self.s + ox, self.cy + y * self.s + oy)

    def inv(self, sx, sy):
        return ((sx - self.cx) / self.s, (sy - self.cy) / self.s)


class BattleScene(Scene):
    def __init__(self, app, game: Game, spec: BattleSpec, on_done: Callable):
        super().__init__(app)
        self.game = game
        self.spec = spec
        self.on_done = on_done
        self.battle = Battle(game, spec)
        self.cam = Camera(LEFT_W + (ui.W - LEFT_W) // 2, ui.H // 2 + 8, S)
        self.field = pygame.Rect(LEFT_W, 0, ui.W - LEFT_W, ui.H)
        self.speed = 1
        self.paused = False
        self.selected = None
        self.parts = art.Particles()
        self.tracers: list = []
        self.bodies: list = []
        self.t = 0.0
        self.hover_tip = ""
        self.tribe_col = data.TRIBES[spec.foe]["color"] if spec.foe in data.TRIBES else (96, 80, 70)
        self.ground = self._make_ground()
        self.parley_open = False
        self.end_timer = 0.0
        self.finished = False
        rng = random.Random(game.day * 3 + 1)
        R = self.battle.R
        self.tents = [(-0.42 * R, -0.28 * R, 1.0), (0.36 * R, -0.34 * R, 0.95), (-0.34 * R, 0.30 * R, 0.9), (0.4 * R, 0.28 * R, 0.85)][
            : 2 + min(2, len(game.living()) // 5)]
        self.crates = [(rng.uniform(-0.5, 0.5) * R, rng.uniform(-0.5, 0.5) * R) for _ in range(5)]
        self.crates = [(x, y) for x, y in self.crates if math.hypot(x, y) > 30]
        self.oxen = [(rng.uniform(-0.5, 0.5) * R * 0.9, rng.uniform(-0.5, 0.5) * R * 0.9, rng.uniform(0, 6.28)) for _ in range(min(7, 3 + game.sup.oxen // 4))]
        self.oxen = [o for o in self.oxen if math.hypot(o[0], o[1]) > 36]
        self.buttons: list[Button] = []
        self.roster_scroll = 0
        self._rdown = None
        self._rdrag = False
        self._build_buttons()
        self.update(0.0)

    # ------------------------------------------------------------ preparación
    def _make_ground(self):
        g = art.ground_surface((self.field.w + 40, ui.H + 40), self.game.terrain(), seed=self.game.day % 5)
        g = g.copy()
        # círculo de tierra pisada
        c = (self.cam.cx - self.field.x + 20, self.cam.cy + 20)
        R = self.battle.R * S
        dirt = pygame.Surface(g.get_size(), pygame.SRCALPHA)
        for i in range(8):
            pygame.draw.circle(dirt, (120, 96, 62, 22), c, int(R + 80 - i * 10 + 40))
        pygame.draw.circle(dirt, (122, 98, 64, 90), c, int(R + 8))
        g.blit(dirt, (0, 0))
        return g

    def _build_buttons(self):
        self._touch = ui.TOUCH
        x = 10
        w = LEFT_W - 20
        th = 38 if ui.TOUCH else 30
        gp = th + 4
        y = ui.H - 238 if not ui.TOUCH else ui.H - 252
        h2 = w // 2 - 2
        self.buttons = [
            Button((x, y, h2, th), "Auto (A)", self._auto, size=15, key=pygame.K_a),
            Button((x + w // 2 + 2, y, h2, th), "Quitar puesto", self._unassign_sel, size=15),
            Button((x, y + gp, w, th), "", self._cycle_policy, size=15, key=pygame.K_f),
            Button((x, y + 2 * gp, h2, th), "Parlamento (P)", self._toggle_parley, size=15, key=pygame.K_p),
            Button((x + w // 2 + 2, y + 2 * gp, h2, th), "Fundir (M)", self._melt, size=15, key=pygame.K_m),
            Button((x, y + 3 * gp, w, th), "", self._start, size=15, key=pygame.K_RETURN),
            Button((x, y + 4 * gp, w // 3 - 2, th - 2), "Pausa", self._pause, size=14, key=pygame.K_SPACE),
            Button((x + w // 3 + 1, y + 4 * gp, w // 3 - 2, th - 2), "x1", lambda: self._set_speed(1), size=14, key=pygame.K_1),
            Button((x + 2 * w // 3 + 2, y + 4 * gp, w // 3 - 2, th - 2), "x2", lambda: self._set_speed(2), size=14, key=pygame.K_2),
        ]
        self.unassign_btn = self.buttons[1]
        self.policy_btn = self.buttons[2]
        self.parley_btn = self.buttons[3]
        self.melt_btn = self.buttons[4]
        self.start_btn = self.buttons[5]
        self.roster_bottom = y - 6

    def _unassign_sel(self):
        if self.selected is not None:
            self.battle.unassign(self.selected)
            self.selected = None

    def _auto(self):
        self.battle.auto_assign()

    def _cycle_policy(self):
        order = ["libre", "contenido", "alto"]
        self.battle.policy = order[(order.index(self.battle.policy) + 1) % 3]

    def _toggle_parley(self):
        if self.battle.parley_available:
            self.parley_open = not self.parley_open

    def _melt(self):
        self.battle.melt()

    def _start(self):
        self.battle.start_fight()

    def _pause(self):
        self.paused = not self.paused

    def _set_speed(self, n):
        self.speed = n
        self.paused = False

    # ------------------------------------------------------------ entrada
    def handle(self, ev):
        b = self.battle
        if b.done:
            if ev.type == pygame.MOUSEBUTTONDOWN or (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE)):
                if self.end_timer > 0.8:
                    self._finish()
            return
        if self.parley_open:
            for btn in self._parley_buttons():
                if btn.handle(ev):
                    return
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_p):
                self.parley_open = False
            return
        for btn in self.buttons:
            if btn.handle(ev):
                return
        if ev.type == pygame.MOUSEMOTION:
            self._hover(ev.pos)
            if self._rdown is not None and ev.buttons[0]:
                dy = ev.pos[1] - self._rdown[0][1]
                if abs(dy) > 8 or self._rdrag:
                    self._rdrag = True
                    self.roster_scroll -= ev.rel[1]
        elif ev.type == pygame.MOUSEWHEEL:
            if self._roster_area().collidepoint(pygame.mouse.get_pos()):
                self.roster_scroll -= ev.y * 30
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                self._hover(ev.pos)
                if self._roster_area().collidepoint(ev.pos):
                    self._rdown = (ev.pos, None)
                    self._rdrag = False
                else:
                    self._click(ev.pos)
            elif ev.button == 3:
                self._rclick(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self._rdown is not None and not self._rdrag:
                self._click(ev.pos)
            self._rdown = None
            self._rdrag = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.selected = None
            elif ev.key == pygame.K_3:
                self._set_speed(3)

    def _roster_geom(self):
        n = max(1, len(self.battle.colonists))
        top = 60
        avail = self.roster_bottom - top
        rh = max(26 if ui.TOUCH else 21, min(31 if not ui.TOUCH else 34, avail // n))
        return top, avail, rh

    def _roster_rows(self):
        rows = []
        top, avail, rh = self._roster_geom()
        total = rh * len(self.battle.colonists)
        self.roster_scroll = max(0, min(self.roster_scroll, max(0, total - avail)))
        y = top - self.roster_scroll
        for bc in self.battle.colonists:
            rows.append((bc, pygame.Rect(8, y, LEFT_W - 16, rh - 2)))
            y += rh
        return rows

    def _roster_area(self):
        top, avail, rh = self._roster_geom()
        return pygame.Rect(0, top, LEFT_W, avail)

    def _slot_positions(self):
        out = []
        for w in self.battle.wagons:
            if w.destroyed:
                continue
            for slot in ("tirador", "ayuda"):
                px, py = self.battle.post_pos(w.idx, slot)
                out.append((w.idx, slot, self.cam(px, py)))
        return out

    def _click(self, pos):
        b = self.battle
        for bc, r in self._roster_rows():
            if r.collidepoint(pos):
                if bc.ref.health <= 0 or not bc.alive:
                    return
                self.selected = None if self.selected is bc else bc
                return
        if not self.field.collidepoint(pos):
            return
        # plazas
        for widx, slot, (sx, sy) in self._slot_positions():
            if math.hypot(pos[0] - sx, pos[1] - sy) < (28 if ui.TOUCH else 15):
                occupant = b.game.post_of(widx, slot)
                if self.selected is not None:
                    if slot == "tirador" and not self.selected.ref.can_shoot:
                        b.say("Sólo adultos y jóvenes sanos pueden disparar; ponlos de ayudantes.", (255, 170, 120))
                        return
                    b.assign(self.selected, widx, slot)
                    self.selected = None
                elif occupant is not None:
                    for bc in b.colonists:
                        if bc.ref is occupant:
                            self.selected = bc
                return
        # enemigos
        wx, wy = self.cam.inv(*pos)
        best = None
        bd = 44 if ui.TOUCH else 26
        for f in b.alive_foes():
            if not b.is_visible(f):
                continue
            d = math.hypot(f.x - wx, f.y - wy) * S
            if d < bd:
                best, bd = f, d
        if best is not None:
            b.set_focus(None if b.focus is best else best)
            return
        # carretas destruidas -> barricada
        for w in b.wagons:
            if w.destroyed and w.barricade <= 0 and math.hypot(w.x - wx, w.y - wy) * S < (56 if ui.TOUCH else 40):
                b.order_barricade(w.idx)
                return
        self.selected = None

    def _rclick(self, pos):
        for bc, r in self._roster_rows():
            if r.collidepoint(pos):
                self.battle.unassign(bc)
                return
        for widx, slot, (sx, sy) in self._slot_positions():
            if math.hypot(pos[0] - sx, pos[1] - sy) < (28 if ui.TOUCH else 15):
                occ = self.battle.game.post_of(widx, slot)
                if occ:
                    occ.post = None
                return
        self.selected = None
        self.battle.set_focus(None)

    def _hover(self, pos):
        b = self.battle
        self.hover_tip = ""
        for bc, r in self._roster_rows():
            if r.collidepoint(pos):
                c = bc.ref
                self.hover_tip = (f"{c.name} — {c.role_label}. Puntería {c.shoot}, Medicina {c.medic}, "
                                  f"Construcción {c.build}. Salud {int(c.health)}." + (f" Enfermedad: {c.sick}." if c.sick else ""))
                return
        wx, wy = self.cam.inv(*pos)
        for w in b.wagons:
            if math.hypot(w.x - wx, w.y - wy) * S < 36:
                r = w.ref
                if w.destroyed:
                    self.hover_tip = f"Carreta {w.idx + 1} destruida." + (" Haz clic para levantar una barricada (1 repuesto)." if w.barricade <= 0 else " Barricada en pie.")
                else:
                    ex = [x for x, ok in (("cañón", r.cannon), ("plataforma", r.platform), ("farol", r.lantern)) if ok]
                    self.hover_tip = (f"Carreta {w.idx + 1}: {int(r.hp)}/{int(r.max_hp)} PV, refuerzos {r.reinforced}"
                                      + (f", {', '.join(ex)}" if ex else "") + (" ¡ARDE!" if w.burning > 0 else ""))
                return
        for f in b.alive_foes():
            if b.is_visible(f) and math.hypot(f.x - wx, f.y - wy) * S < 16:
                self.hover_tip = f"{data.FOES[f.kind]['name']} — {int(f.hp)}/{int(f.max_hp)} PV (clic para marcar objetivo)"
                return

    # ------------------------------------------------------------ actualización
    def update(self, dt):
        self.t += dt
        b = self.battle
        self.cam.shake = max(0.0, self.cam.shake - dt * 14)
        if not self.paused and not b.done:
            steps = self.speed
            for _ in range(steps):
                b.update(dt)
        self._consume_fx()
        self.parts.update(dt * (0 if self.paused else 1))
        self.tracers = [(x1, y1, x2, y2, ttl - dt, ok) for x1, y1, x2, y2, ttl, ok in self.tracers if ttl - dt > 0]
        for body in self.bodies:
            body[4] += dt
        self.bodies = [x for x in self.bodies if x[4] < 22][-70:]
        if b.done:
            if self.end_timer == 0.0:
                sfx.play("win" if b.result.outcome in ("victoria", "huida", "paz") else "lose", 0.7)
            self.end_timer += dt
        if self._touch != ui.TOUCH:
            self._build_buttons()
        self.unassign_btn.enabled = self.selected is not None and self.selected.ref.post is not None
        # texto de botones
        pol = {"libre": "Fuego libre (F)", "contenido": "Fuego contenido (F)", "alto": "Alto el fuego (F)"}[b.policy]
        self.policy_btn.label = pol
        self.start_btn.label = "¡Empezar ya! (Enter)" if b.phase == "prep" else "Combate en curso"
        self.start_btn.enabled = b.phase == "prep"
        self.melt_btn.enabled = self.game.sup.goods >= 5
        self.parley_btn.enabled = b.parley_available and b.phase == "fight"
        # fuego visual
        if not self.paused:
            for w in b.wagons:
                if w.burning > 0 and random.random() < 0.6:
                    self.parts.add("fire", w.x, w.y, 1)
                    if random.random() < 0.3:
                        self.parts.add("smoke", w.x, w.y, 1)

    def _consume_fx(self):
        b = self.battle
        for ev in b.fx:
            k = ev[0]
            if k == "shot":
                _, px, py, tx, ty, ok = ev
                sfx.play("shot", 0.45, 0.05)
                self.tracers.append((px, py, tx, ty, 0.1, ok))
                self.parts.add("smoke", px, py, 2)
                self.parts.add("spark", px, py, 2)
            elif k == "hit":
                sfx.play("hit", 0.5, 0.04)
                self.parts.add("spark", ev[1], ev[2], 4, color=(255, 120, 90))
            elif k == "death":
                sfx.play("death", 0.35, 0.08)
                self.parts.add("dust", ev[1], ev[2], 5)
                self.parts.add("ring", ev[1], ev[2], 1, color=(255, 230, 190))
                self.bodies.append([ev[1], ev[2], "foe", ev[3], 0.0])
            elif k == "wave":
                sfx.play("horn", 0.8, 1.0)
            elif k == "bow":
                sfx.play("bow", 0.3, 0.12)
            elif k == "death_col":
                sfx.play("lose", 0.5)
                self.parts.add("ring", ev[1], ev[2], 1, color=(255, 120, 120))
            elif k == "hurt":
                sfx.play("hurt", 0.5, 0.1)
                self.parts.add("spark", ev[1], ev[2], 5, color=(255, 80, 80))
            elif k == "rifle":
                _, x, y, tx, ty = ev
                sfx.play("rifle", 0.5, 0.1)
                self.tracers.append((x, y, tx, ty, 0.1, False))
                self.parts.add("smoke", x, y, 2)
            elif k == "chop":
                sfx.play("chop", 0.35, 0.1)
                self.parts.add("spark", ev[1], ev[2], 2, color=(190, 140, 80))
            elif k == "thunk":
                sfx.play("thunk", 0.3, 0.1)
                self.parts.add("dust", ev[1], ev[2], 1)
            elif k == "boom":
                sfx.play("boom", 0.8, 0.2)
                self.parts.add("fire", ev[1], ev[2], 14)
                self.parts.add("smoke", ev[1], ev[2], 14)
                self.parts.add("dust", ev[1], ev[2], 10)
                self.cam.shake = 7
            elif k == "cannon":
                _, px, py, tx, ty = ev
                sfx.play("cannon", 0.9, 0.2)
                self.parts.add("smoke", px, py, 10)
                self.parts.add("spark", px, py, 8)
                self.parts.add("fire", tx, ty, 8)
                self.parts.add("smoke", tx, ty, 8)
                self.parts.add("dust", tx, ty, 8)
                self.parts.add("ring", tx, ty, 1, color=(255, 200, 120))
                self.tracers.append((px, py, tx, ty, 0.25, True))
                self.cam.shake = 5
        b.fx.clear()

    # ------------------------------------------------------------ dibujo
    def draw(self, screen):
        b = self.battle
        cam = self.cam
        screen.fill(C["bg"])
        screen.blit(self.ground, (self.field.x - 20, -20))
        clip = screen.get_clip()
        screen.set_clip(self.field)
        self._draw_camp(screen)
        self._draw_bodies(screen)
        self._draw_wagons(screen)
        self._draw_slots(screen)
        self._draw_colonists(screen)
        self._draw_foes(screen)
        self._draw_allies(screen)
        self._draw_arrows(screen)
        for x1, y1, x2, y2, ttl, ok in self.tracers:
            a, c2 = cam(x1, y1), cam(x2, y2)
            pygame.draw.line(screen, (255, 240, 170) if ok else (200, 200, 200), a, c2, 1)
        self.parts.draw(screen, cam)
        if b.night:
            self._draw_night(screen)
        self._draw_warnings(screen)
        self._draw_focus(screen)
        screen.set_clip(clip)
        self._draw_hud(screen)
        if self.parley_open:
            self._draw_parley(screen)
        if b.done:
            self._draw_result(screen)
        if self.hover_tip and not b.done:
            ui.draw_tooltip(screen, self.hover_tip, pygame.mouse.get_pos())

    def _draw_camp(self, screen):
        cam = self.cam
        b = self.battle
        for x, y, s in self.tents:
            sx, sy = cam(x, y)
            art.draw_tent(screen, sx, sy, s * 1.0)
        for x, y in self.crates:
            sx, sy = cam(x, y)
            pygame.draw.rect(screen, (124, 90, 54), (sx - 6, sy - 5, 12, 10))
            pygame.draw.rect(screen, (70, 48, 28), (sx - 6, sy - 5, 12, 10), 1)
            pygame.draw.line(screen, (70, 48, 28), (sx - 6, sy - 5), (sx + 6, sy + 5), 1)
        for x, y, a in self.oxen:
            sx, sy = cam(x, y)
            art.draw_ox(screen, sx, sy, 0.9, a + math.sin(self.t * 0.3 + x) * 0.1)
        # enfermería
        sx, sy = cam(0, 52)
        pygame.draw.rect(screen, (235, 232, 222), (sx - 22, sy - 12, 44, 24), border_radius=3)
        pygame.draw.rect(screen, (150, 140, 120), (sx - 22, sy - 12, 44, 24), 1, border_radius=3)
        pygame.draw.rect(screen, (200, 50, 50), (sx - 2, sy - 8, 4, 16))
        pygame.draw.rect(screen, (200, 50, 50), (sx - 8, sy - 2, 16, 4))
        fx, fy = cam(0, 0)
        art.draw_fire(screen, fx, fy, self.t, 1.0)
        if random.random() < 0.4 and not self.paused:
            self.parts.add("ember", 0, 0, 1)
            if random.random() < 0.3:
                self.parts.add("smoke", 0, 0, 1)

    def _draw_bodies(self, screen):
        cam = self.cam
        for x, y, kind, info, t in self.bodies:
            sx, sy = cam(x, y)
            a = max(0, 1 - t / 22)
            s = pygame.Surface((26, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (60, 36, 30, int(150 * a)), (0, 0, 26, 14))
            screen.blit(s, (sx - 13, sy - 7))

    def _draw_wagons(self, screen):
        b = self.battle
        cam = self.cam
        for w in b.wagons:
            r = w.ref
            frac = max(0.0, r.hp / max(1.0, r.max_hp))
            surf = art.wagon_surface(frac, r.reinforced, r.platform, r.cannon, r.lantern, w.destroyed, w.angle + math.pi / 2)
            sx, sy = cam(w.x, w.y)
            scaled = surf if abs(S - 1.0) < 1e-6 else pygame.transform.smoothscale(
                surf, (max(2, int(surf.get_width() * S)), max(2, int(surf.get_height() * S))))
            if w.flash > 0 and not w.destroyed:
                scaled = scaled.copy()
                scaled.fill((90, 40, 30), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(scaled, scaled.get_rect(center=(int(sx), int(sy))))
            if w.destroyed and w.barricade > 0:
                for i in range(-2, 3):
                    ox = i * 10
                    a = w.angle + math.pi / 2
                    px, py = sx + math.cos(a) * ox * S * 1.4, sy + math.sin(a) * ox * S * 1.4
                    pygame.draw.line(screen, (120, 84, 50), (px - 5, py - 8), (px + 5, py + 8), 3)
                    pygame.draw.line(screen, (120, 84, 50), (px + 5, py - 8), (px - 5, py + 8), 3)
                bar(screen, (sx - 18, sy + 14, 36, 4), w.barricade / 90.0, (200, 160, 90))
            if w.destroyed and w.build_progress > 0 and w.barricade <= 0:
                bar(screen, (sx - 18, sy + 14, 36, 4), w.build_progress, (130, 200, 120))
            if not w.destroyed and frac < 0.999:
                ox, oy = math.cos(w.angle) * 34 * S, math.sin(w.angle) * 34 * S
                bar(screen, (sx + ox - 18, sy + oy - 3, 36, 5), frac, C["green"] if frac > 0.5 else C["orange"] if frac > 0.25 else C["red"])
            if not w.destroyed:
                text(screen, w.idx + 1, (sx - math.cos(w.angle) * 33 * S, sy - math.sin(w.angle) * 33 * S), 13, (255, 245, 220), anchor="center", bold=True, shadow=True)

    def _draw_slots(self, screen):
        b = self.battle
        show_all = b.phase == "prep" or self.selected is not None
        for widx, slot, (sx, sy) in self._slot_positions():
            occ = b.game.post_of(widx, slot)
            col = (110, 160, 220) if slot == "tirador" else (120, 184, 100)
            if occ is None and not show_all:
                continue
            if occ is None or show_all:
                pygame.draw.circle(screen, col, (int(sx), int(sy)), 12, 2)
                if occ is None:
                    text(screen, "T" if slot == "tirador" else "A", (sx, sy), 12, col, anchor="center", bold=True)
            if self.selected is not None and self.selected.ref is occ:
                pygame.draw.circle(screen, C["gold"], (int(sx), int(sy)), 15, 3)

    def _draw_colonists(self, screen):
        b = self.battle
        cam = self.cam
        for bc in sorted(b.colonists, key=lambda c: c.y):
            c = bc.ref
            sx, sy = cam(bc.x, bc.y)
            if not c.alive:
                art.draw_person(screen, sx, sy, c.group, c.cid, S * 1.5, dead=True)
                continue
            aim = None
            if bc.aim and bc.flash > 0:
                aim = math.atan2(bc.aim[1] - bc.y, bc.aim[0] - bc.x)
            elif bc.task == "post":
                aim = math.atan2(bc.y, bc.x)
            art.draw_person(screen, sx, sy, c.group, c.cid, S * 1.6, aim=aim, hurt=bc.flash > 0.2 and False,
                            wounded=c.health < 30)
            if bc.flash > 0 and bc.task != "post":
                pygame.draw.circle(screen, (255, 80, 80), (int(sx), int(sy)), 10, 1)
            if self.selected is bc:
                pygame.draw.circle(screen, C["gold"], (int(sx), int(sy)), 13, 2)
            if c.health < 100 and c.alive and c.health > 0:
                bar(screen, (sx - 8, sy - 14, 16, 3), c.health / 100.0, C["green"] if c.health > 50 else C["orange"] if c.health > 25 else C["red"], border=False)
            if bc.task in ("repair", "extinguish", "heal", "build"):
                text(screen, {"repair": "reparando", "extinguish": "apagando", "heal": "curando", "build": "construyendo"}[bc.task], (sx, sy + 12), 11, C["dim"], anchor="midtop")

    def _draw_foes(self, screen):
        b = self.battle
        cam = self.cam
        for f in sorted(b.foes, key=lambda f: f.y):
            if not f.alive or f.fled:
                continue
            sx, sy = cam(f.x, f.y)
            if not self.field.inflate(60, 60).collidepoint(sx, sy):
                continue
            if b.night and not b.is_visible(f):
                if math.hypot(f.x, f.y) < 520:
                    pygame.draw.circle(screen, (150, 40, 40), (int(sx), int(sy)), 2)
                continue
            art.draw_foe(screen, f, sx, sy, S * 1.75, self.tribe_col, flash=f.flash > 0)
            if f.mounted and f.state != "stand" and random.random() < 0.18 and not self.paused:
                self.parts.add("dust", f.x, f.y, 1)
            if f.hp < f.max_hp:
                bar(screen, (sx - 9, sy - 16, 18, 3), f.hp / f.max_hp, C["red"], border=False)
            if f.state == "flee":
                text(screen, "huye", (sx, sy - 22), 11, C["dim"], anchor="midbottom")

    def _draw_allies(self, screen):
        b = self.battle
        for al in b.allies:
            if not al.alive:
                continue
            sx, sy = self.cam(al.x, al.y)
            class _F:
                kind = "jinete"
                face = al.face
            art.draw_foe(screen, _F, sx, sy, S * 1.75, (90, 190, 120))

    def _draw_arrows(self, screen):
        b = self.battle
        for a in b.arrows:
            sx, sy = self.cam(a.x, a.y)
            dx, dy = a.tx - a.x, a.ty - a.y
            d = max(1.0, math.hypot(dx, dy))
            ex, ey = sx - dx / d * 12, sy - dy / d * 12
            col = (255, 160, 50) if a.fire else (230, 220, 190)
            pygame.draw.line(screen, col, (ex, ey), (sx, sy), 2)
            if a.fire and random.random() < 0.5:
                self.parts.add("fire", a.x, a.y, 1)

    def _draw_focus(self, screen):
        f = self.battle.focus
        if f is not None and f.alive and not f.fled:
            sx, sy = self.cam(f.x, f.y)
            r = 16 + 2 * math.sin(self.t * 8)
            pygame.draw.circle(screen, C["red"], (int(sx), int(sy)), int(r), 2)
            for a in range(0, 360, 90):
                x1, y1 = sx + math.cos(math.radians(a)) * (r - 4), sy + math.sin(math.radians(a)) * (r - 4)
                x2, y2 = sx + math.cos(math.radians(a)) * (r + 5), sy + math.sin(math.radians(a)) * (r + 5)
                pygame.draw.line(screen, C["red"], (x1, y1), (x2, y2), 2)

    def _draw_night(self, screen):
        b = self.battle
        cam = self.cam
        if getattr(self, "_dark", None) is None:
            self._dark = pygame.Surface(self.field.size, pygame.SRCALPHA)
        dark = self._dark
        dark.fill((6, 10, 30, 214))
        ox, oy = self.field.x, self.field.y

        def light(x, y, radius, strength=255):
            r = max(8, int(radius * S))
            img = art.radial_light(r, strength)
            sx, sy = cam(x, y)
            dark.blit(img, (sx - ox - r, sy - oy - r), special_flags=pygame.BLEND_RGBA_MIN)

        flick = 1 + 0.03 * math.sin(self.t * 9)
        light(0, 0, (b.R + 190) * flick)
        for w in b.wagons:
            if w.ref.lantern and not w.destroyed:
                light(w.x, w.y, 300 * flick)
            if w.burning > 0:
                light(w.x, w.y, 170 * flick)
        for f in b.foes:
            if f.alive and f.revealed > 0 and not f.fled:
                light(f.x, f.y, 70)
        screen.blit(dark, self.field.topleft)

    def _draw_warnings(self, screen):
        b = self.battle
        rect = self.field.inflate(-70, -70)
        cx, cy = self.cam(0, 0)
        for ang, secs, comp in b.warnings():
            dx, dy = math.cos(ang), math.sin(ang)
            # intersección del rayo con el rectángulo
            tx = ((rect.right - cx) / dx) if dx > 0 else ((rect.left - cx) / dx) if dx < 0 else 1e9
            ty = ((rect.bottom - cy) / dy) if dy > 0 else ((rect.top - cy) / dy) if dy < 0 else 1e9
            t = min(tx, ty)
            px, py = cx + dx * t, cy + dy * t
            pulse = 0.6 + 0.4 * math.sin(self.t * 7)
            col = (255, int(80 + 100 * pulse), 60)
            tip = (px + dx * 14, py + dy * 14)
            base1 = (px - dx * 6 - dy * 12, py - dy * 6 + dx * 12)
            base2 = (px - dx * 6 + dy * 12, py - dy * 6 - dx * 12)
            pygame.draw.polygon(screen, col, [tip, base1, base2])
            n = sum(comp.values())
            lbl = f"{n} · {max(0, secs):.0f}s"
            text(screen, lbl, (px - dx * 30, py - dy * 30), 14, col, anchor="center", bold=True, shadow=True)

    def _draw_hud(self, screen):
        b = self.battle
        g = self.game
        # panel izquierdo
        panel(screen, (0, 0, LEFT_W, ui.H), (40, 30, 22), C["edge"], 0)
        text(screen, "DEFENSA DEL CÍRCULO", (LEFT_W // 2, 14), 17, C["gold"], bold=True, anchor="midtop", serif=True)
        text(screen, "toca un colono → toca una plaza T/A", (LEFT_W // 2, 38), 12, C["dim"], anchor="midtop")
        clip_old = screen.get_clip()
        screen.set_clip(self._roster_area())
        for bc, r in self._roster_rows():
            c = bc.ref
            sel = self.selected is bc
            pygame.draw.rect(screen, (92, 70, 46) if sel else (58, 44, 30), r, border_radius=5)
            if sel:
                pygame.draw.rect(screen, C["gold"], r, 2, border_radius=5)
            if not c.alive:
                text(screen, "† " + c.name, (r.x + 8, r.y + 3), 14, (130, 100, 90))
                continue
            art.draw_person(screen, r.x + 13, r.y + r.h // 2, c.group, c.cid, 0.9)
            text(screen, c.name[:16], (r.x + 28, r.y + max(1, (r.h - 17) // 2 - 2)), 14, C["text"])
            hp = c.health / 100.0
            bar(screen, (r.x + 28, r.bottom - 5, 96, 3), hp, C["green"] if hp > 0.5 else C["orange"] if hp > 0.25 else C["red"], border=False)
            lbl = "—"
            col = C["dim"]
            if c.post:
                lbl = f"C{c.post[0] + 1} " + ("tirador" if c.post[1] == "tirador" else "ayuda")
                col = (140, 190, 240) if c.post[1] == "tirador" else (150, 210, 130)
            elif bc.task in ("repair", "extinguish", "heal", "build", "melee"):
                lbl = {"repair": "repara", "extinguish": "apaga", "heal": "cura", "build": "construye", "melee": "lucha"}[bc.task]
            elif bc.task == "wounded":
                lbl = "herido"
                col = C["red"]
            text(screen, lbl, (r.right - 6, r.centery), 12, col, anchor="midright")
        screen.set_clip(clip_old)
        for btn in self.buttons:
            btn.draw(screen)
        # barra superior
        top = pygame.Rect(LEFT_W, 0, ui.W - LEFT_W, 40)
        panel(screen, top, (30, 22, 16), C["edge"], 0, alpha=200, width=1)
        left = len(b.alive_foes()) + sum(sum(c.values()) for _, _, c in b.pending)
        ui.icon(screen, "ammo", LEFT_W + 20, 20, 20)
        text(screen, f"{g.sup.ammo}", (LEFT_W + 36, 10), 20, C["gold"] if g.sup.ammo > 15 else C["red"], bold=True)
        text(screen, f"Enemigos: {left}", (LEFT_W + 110, 11), 18, C["text"])
        text(screen, f"Abatidos: {b.killed}", (LEFT_W + 230, 11), 18, C["green"])
        text(screen, f"Bajas: {len(b.dead_names)}", (LEFT_W + 345, 11), 18, C["red"] if b.dead_names else C["dim"])
        st = "PREPARACIÓN" if b.phase == "prep" else f"{int(b.fight_time) // 60}:{int(b.fight_time) % 60:02d}"
        if b.phase == "prep":
            text(screen, f"PREPARACIÓN  {max(0, b.prep):.0f}s", (ui.W - 14, 11), 18, C["gold"], bold=True, anchor="topright")
        else:
            text(screen, st, (ui.W - 14, 11), 18, C["text"], bold=True, anchor="topright")
        if self.paused:
            text(screen, "PAUSA", (self.field.centerx, 70), 34, C["gold"], bold=True, anchor="center", shadow=True)
        pol = {"libre": "Libre", "contenido": "Contenido", "alto": "Alto"}[b.policy]
        text(screen, f"Fuego: {pol}", (LEFT_W + 450, 11), 16, C["dim"])
        if b.phase == "prep":
            panel(screen, (self.field.centerx - 280, 48, 560, 52), (30, 22, 16), C["gold"], 6, alpha=215, width=1)
            text(screen, "Cierra el círculo: pon a tus mejores tiradores (T) en las carretas por donde vendrá el ataque.",
                 (self.field.centerx, 54), 14, C["text"], anchor="midtop")
            text(screen, "Las flechas rojas del borde indican por dónde llegará cada oleada.", (self.field.centerx, 74), 14, C["gold"], anchor="midtop")
        # registro de mensajes
        y = ui.H - 24
        for t0, msg, col in list(b.msgs)[::-1][:6]:
            age = b.time - t0
            a = 255 if age < 8 else max(0, int(255 - (age - 8) * 60))
            if a <= 0:
                continue
            img = ui.font(15).render(msg, True, col)
            img.set_alpha(a)
            bg = pygame.Surface((img.get_width() + 12, img.get_height() + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, int(a * 0.5)))
            screen.blit(bg, (LEFT_W + 8, y - 1))
            screen.blit(img, (LEFT_W + 14, y))
            y -= 20

    def _parley_buttons(self):
        cx = self.field.centerx
        b = self.battle
        out = []
        labels = [(0, "Parlamentar con las manos vacías"), (1, "Ofrecer un regalo (3 mercancías)"), (2, "Ofrecer un gran regalo (8 mercancías)")]
        for i, (gift, lbl) in enumerate(labels):
            p = int(b.parley_chance(gift) * 100)
            enabled = self.game.sup.goods >= (0, 3, 8)[gift] and b.parley_cd <= 0 and b.fight_time >= 10
            out.append(Button((cx - 230, 250 + i * 54, 460, 44), f"{lbl} — {p}%", (lambda g=gift: self._do_parley(g)), enabled, size=17))
        out.append(Button((cx - 100, 250 + 3 * 54 + 6, 200, 36), "Volver al combate", lambda: setattr(self, "parley_open", False), size=16))
        return out

    def _do_parley(self, gift):
        ok, msg = self.battle.parley(gift)
        self.battle.say(msg, (170, 255, 170) if ok else (255, 150, 120))
        self.parley_open = False

    def _draw_parley(self, screen):
        cx = self.field.centerx
        veil = pygame.Surface(self.field.size, pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        screen.blit(veil, self.field.topleft)
        panel(screen, (cx - 270, 190, 540, 330), C["panel"], C["gold"], 10)
        text(screen, "Parlamento a mitad de la batalla", (cx, 204), 24, C["gold"], serif=True, anchor="midtop")
        ts = self.game.tribes.get(self.spec.foe)
        text(screen, "Bandera blanca e intérprete. El éxito depende de su trato hacia ti, tu labia y el regalo.",
             (cx, 234), 13, C["dim"], anchor="midtop")
        for btn in self._parley_buttons():
            btn.draw(screen)
        text(screen, "(espera 10 s de combate; si fracasan, no podrás intentarlo de nuevo durante 28 s)", (cx, 495), 12, C["dim"], anchor="midtop")

    def _draw_result(self, screen):
        b = self.battle
        res = b.result
        veil = pygame.Surface((ui.W, ui.H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 120))
        screen.blit(veil, (0, 0))
        cx = self.field.centerx
        panel(screen, (cx - 250, 220, 500, 230), C["panel"], C["gold"], 12)
        title = {"victoria": "¡VICTORIA!", "huida": "EL ENEMIGO SE RETIRA", "paz": "SE HA PACTADO LA PAZ", "derrota": "DERROTA"}[res.outcome]
        text(screen, title, (cx, 238), 38, C["gold"] if res.outcome != "derrota" else C["red"], bold=True, serif=True, anchor="midtop", shadow=True)
        text(screen, f"Enemigos abatidos: {res.foes_killed}/{res.foes_total}", (cx, 298), 20, C["text"], anchor="midtop")
        text(screen, f"Colonos caídos: {len(res.dead)}   ·   Carretas perdidas: {res.wagons_lost}", (cx, 326), 20, C["text"], anchor="midtop")
        text(screen, f"Munición gastada: {res.ammo_used}", (cx, 354), 20, C["text"], anchor="midtop")
        if self.end_timer > 0.8:
            text(screen, "Haz clic para continuar", (cx, 410), 17, C["dim"], anchor="midtop")

    def _finish(self):
        if self.finished:
            return
        self.finished = True
        self.on_done(self.battle.result)
