"""Graphical renderer for the map viewport.

Reads game state directly (``game_map``, ``map_biomes``, ``visible``,
``explored``, ``enemies``, ``projectiles``, ``player``) and draws:

* procedurally generated tiles per terrain/biome, cached per zoom level
* distance-based lighting inside the field of view, tinted memory for
  explored tiles, true darkness for unexplored ones
* smoothly interpolated player/enemies, lightsaber glow coloured by corruption
* particles, tracers, floating combat text and screen shake, all derived from
  state changes (HP deltas, deaths, popups) so no game logic had to change
* a HUD: HP/Force/Stress bars, mode chip, location, minimap, tomb compass
"""
from __future__ import annotations

import math
import random
import time

import pygame

from jedi_fugitive.gfx import theme
from jedi_fugitive.gfx.app import load_font

FLOOR_CH = '.'
WALL_CH = '#'


def _ease(cur, target, rate, dt):
    return cur + (target - cur) * min(1.0, rate * dt)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "drag")

    def __init__(self, x, y, vx, vy, life, color, size, drag=2.5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.drag = color, size, drag


class WorldRenderer:
    MIN_TILE, MAX_TILE = 16, 60

    def __init__(self, app, game):
        self.app = app
        self.game = game
        self.tile = None
        self.cam = None
        self.disp = {}
        self.facing = (1.0, 0.0)
        self.particles = []
        self.floaters = []
        self.tracers = []
        self.shake = 0.0
        self.hurt = 0.0
        self.t = 0.0
        self.enemy_state = {}
        self.hit_flash = {}
        self.player_hp = None
        self.map_key = None
        self.popup_ids = set()
        self.tiles = {}
        self.glows = {}
        self.fonts = {}
        self.bar_vals = {}
        self.minimap = None
        self.minimap_at = 0.0
        self.vignette = None
        self.rng = random.Random()

    # ---------------------------------------------------------------- helpers
    def font(self, size, bold=True):
        key = (size, bold)
        f = self.fonts.get(key)
        if f is None:
            f = self.fonts[key] = load_font(max(8, size), bold=bold)
        return f

    def zoom(self, direction):
        if self.tile is None:
            return
        self.tile = max(self.MIN_TILE, min(self.MAX_TILE, self.tile + (4 if direction > 0 else -4)))
        self.tiles.clear()

    def in_tomb(self):
        g = self.game
        return bool(getattr(g, 'tomb_levels', None)) and g.game_map is not getattr(g, 'surface_map', None)

    def glow(self, radius, color):
        radius = max(2, int(radius))
        key = (radius, color)
        s = self.glows.get(key)
        if s is None:
            s = pygame.Surface((radius * 2, radius * 2))
            s.fill((0, 0, 0))
            steps = 14
            for i in range(steps, 0, -1):
                r = radius * i / steps
                k = (1 - i / steps) ** 1.6
                pygame.draw.circle(s, theme.scale(color, k), (radius, radius), max(1, int(r)))
            if len(self.glows) > 300:
                self.glows.clear()
            self.glows[key] = s
        return s

    def add_glow(self, surf, cx, cy, radius, color, strength=1.0):
        g = self.glow(radius, theme.scale(color, strength))
        surf.blit(g, (int(cx - g.get_width() / 2), int(cy - g.get_height() / 2)), special_flags=pygame.BLEND_RGB_ADD)

    def burst(self, x, y, color, n=14, speed=4.0, life=0.6, size=3):
        for _ in range(n):
            a = self.rng.random() * math.tau
            v = speed * (0.3 + self.rng.random())
            self.particles.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v,
                                           life * (0.5 + self.rng.random() * 0.8), color, size))
        if len(self.particles) > 600:
            self.particles = self.particles[-600:]

    def floater(self, x, y, text, color, big=False):
        self.floaters.append({"x": x, "y": y, "text": str(text), "color": color, "t": 0.0,
                              "life": 1.25 if big else 1.0, "big": big,
                              "dx": (self.rng.random() - 0.5) * 0.4})

    def tracer(self, sx, sy, ex, ey, color, speed=26.0):
        dist = max(0.5, math.hypot(ex - sx, ey - sy))
        self.tracers.append({"sx": sx, "sy": sy, "ex": ex, "ey": ey, "t": 0.0,
                             "dur": dist / speed, "color": color, "done": False})

    # ------------------------------------------------------------ tile sprites
    def _floor_kind(self, x, y, in_tomb):
        if in_tomb:
            return 'tomb'
        biomes = getattr(self.game, 'map_biomes', None)
        try:
            if biomes and 0 <= y < len(biomes) and 0 <= x < len(biomes[0]):
                b = biomes[y][x]
                if b in theme.FLOOR:
                    return b
        except Exception:
            pass
        return 'plains'

    # item glyphs (see items/registry.py): drawn as icons, never as terrain
    ITEM_ICONS = set('$!:&+0ctfn;zvb/sE') | set('mhwepliKk')

    def _tile_kind(self, ch, in_tomb):
        if ch == FLOOR_CH:
            return 'floor'
        if ch == WALL_CH:
            return 'wall'
        if ch in self.ITEM_ICONS or (in_tomb and ch == 'Q'):
            return 'item'
        if in_tomb:
            if ch in ('>', '<'):
                return 'stairs'
            return 'token'
        return {
            'T': 'tree', 'r': 'rock', '~': 'dune', 'o': 'crater', 'x': 'wreck',
            '>': 'stairs', '<': 'stairs', 'D': 'portal', 'S': 'ship', 'C': 'comms',
            '=': 'bridge', '*': 'crystal', 'L': 'cache',
            '?': 'lore', '§': 'lore', '¶': 'lore', '†': 'lore', '‡': 'lore', '%': 'lore',
        }.get(ch, 'token')

    def _base_tile(self, ch, kind, floor, variant, in_tomb):
        T = self.tile
        s = pygame.Surface((T, T))
        rnd = random.Random(hash((ch, floor, variant)) & 0xFFFF)
        base = theme.FLOOR.get(floor, theme.FLOOR['plains'])
        # floor ------------------------------------------------------------
        s.fill(theme.scale(base, 0.94 + variant * 0.03))
        for _ in range(max(3, T // 5)):
            px, py = rnd.randrange(T), rnd.randrange(T)
            c = theme.scale(base, rnd.choice((0.8, 0.88, 1.12, 1.2)))
            pygame.draw.rect(s, c, (px, py, max(1, T // 14), max(1, T // 14)))
        if floor == 'forest':
            for _ in range(3 + variant):
                gx, gy = rnd.randrange(2, T - 2), rnd.randrange(T // 3, T - 2)
                pygame.draw.line(s, theme.scale(base, 1.45), (gx, gy), (gx + rnd.choice((-1, 1)) * T // 10, gy - T // 6), 1)
        elif floor == 'desert':
            y0 = T // 3 + variant * T // 8
            pygame.draw.arc(s, theme.scale(base, 1.18), (-T // 4, y0, T * 3 // 2, T // 2), 0.3, 2.8, 1)
        elif floor == 'river':
            # reeds on the riverbank
            for _ in range(2 + variant):
                gx, gy = rnd.randrange(3, T - 3), rnd.randrange(T // 2, T - 2)
                pygame.draw.line(s, theme.scale(base, 1.5), (gx, gy), (gx + rnd.choice((-1, 0, 1)), gy - T // 4), 1)
        elif floor == 'mountain_pass':
            pygame.draw.line(s, theme.scale(base, 0.75), (T * 0.1, T * (0.3 + variant * 0.2)), (T * 0.6, T * (0.5 + variant * 0.1)), 1)
        elif floor == 'tomb':
            pygame.draw.rect(s, theme.scale(base, 0.72), (0, 0, T, T), 1)
            if variant % 2:
                pygame.draw.line(s, theme.scale(base, 0.8), (T // 2, 0), (T // 2, T // 2))
        pygame.draw.line(s, theme.scale(base, 0.82), (0, T - 1), (T - 1, T - 1))
        pygame.draw.line(s, theme.scale(base, 0.86), (T - 1, 0), (T - 1, T - 1))

        c = T / 2
        if kind == 'wall':
            wc = theme.WALL_TOMB if in_tomb else theme.WALL
            s.fill(theme.scale(wc, 0.62))
            pygame.draw.rect(s, wc, (0, 0, T, int(T * 0.72)))
            pygame.draw.line(s, theme.scale(wc, 1.35), (0, 0), (T - 1, 0), 2)
            pygame.draw.line(s, theme.scale(wc, 0.8), (0, int(T * 0.72)), (T, int(T * 0.72)), 1)
            if in_tomb or variant % 2:
                mid = int(T * 0.36)
                pygame.draw.line(s, theme.scale(wc, 0.78), (0, mid), (T, mid))
                off = T // 2 if variant % 2 else T // 4
                pygame.draw.line(s, theme.scale(wc, 0.78), (off, 0), (off, mid))
                pygame.draw.line(s, theme.scale(wc, 0.78), ((off + T // 2) % T, mid), ((off + T // 2) % T, int(T * 0.72)))
        elif kind == 'tree':
            pygame.draw.ellipse(s, (18, 30, 22), (T * 0.18, T * 0.62, T * 0.64, T * 0.3))
            pygame.draw.rect(s, (86, 62, 44), (c - T * 0.06, T * 0.5, T * 0.12, T * 0.32))
            for (ox, oy, r) in ((-0.16, 0.05, 0.26), (0.16, 0.05, 0.26), (0, -0.14, 0.3)):
                pygame.draw.circle(s, theme.TREE_CANOPY, (c + ox * T, c + oy * T - T * 0.08), r * T)
            pygame.draw.circle(s, theme.TREE_LIGHT, (c - T * 0.08, c - T * 0.3), T * 0.12)
        elif kind == 'rock':
            pts = [(c + math.cos(a) * T * (0.28 + rnd.random() * 0.12), c + math.sin(a) * T * (0.24 + rnd.random() * 0.1) + T * 0.05)
                   for a in [i * math.tau / 7 for i in range(7)]]
            pygame.draw.polygon(s, theme.scale(theme.ROCK, 0.7), [(x, y + T * 0.05) for x, y in pts])
            pygame.draw.polygon(s, theme.ROCK, pts)
            pygame.draw.circle(s, theme.scale(theme.ROCK, 1.3), (c - T * 0.1, c - T * 0.06), T * 0.07)
        elif kind == 'dune' and floor == 'river':
            # river water
            s.fill((34, 78, 128))
            for i in range(3):
                yy = T * (0.2 + 0.28 * i) + variant * 2
                pygame.draw.arc(s, (90, 150, 210), (T * (0.05 + 0.2 * (i % 2)), yy, T * 0.5, T * 0.22), 0.3, 2.8, 1)
        elif kind == 'bridge':
            s.fill((34, 78, 128))
            for i in range(4):
                pygame.draw.rect(s, (120, 92, 60), (T * 0.08, T * (0.08 + i * 0.23), T * 0.84, T * 0.18), border_radius=2)
                pygame.draw.line(s, (80, 60, 40), (T * 0.08, T * (0.26 + i * 0.23)), (T * 0.92, T * (0.26 + i * 0.23)))
        elif kind == 'crystal':
            for (ox, oy, h_) in ((-0.15, 0.1, 0.35), (0.1, 0.05, 0.45), (0.25, 0.15, 0.28)):
                bx, by = c + ox * T, c + oy * T + T * 0.2
                pts = [(bx - T * 0.07, by), (bx, by - h_ * T), (bx + T * 0.07, by)]
                pygame.draw.polygon(s, (120, 200, 230), pts)
                pygame.draw.polygon(s, (220, 250, 255), pts, 1)
        elif kind == 'lore':
            # holocron: glowing cube
            d = T * 0.22
            top = [(c, c - d * 1.2), (c + d, c - d * 0.6), (c, c), (c - d, c - d * 0.6)]
            pygame.draw.polygon(s, (60, 30, 90), [(c - d, c - d * 0.6), (c, c), (c, c + d * 1.1), (c - d, c + d * 0.5)])
            pygame.draw.polygon(s, (90, 40, 130), [(c + d, c - d * 0.6), (c, c), (c, c + d * 1.1), (c + d, c + d * 0.5)])
            pygame.draw.polygon(s, (190, 110, 255), top)
            pygame.draw.polygon(s, (250, 220, 255), top, 1)
        elif kind == 'dune':
            for i in range(2):
                pygame.draw.arc(s, theme.scale(base, 1.3), (-T * 0.2, T * (0.25 + i * 0.3), T * 1.4, T * 0.5), 0.4, 2.7, 2)
        elif kind == 'crater':
            pygame.draw.ellipse(s, theme.scale(base, 1.25), (T * 0.12, T * 0.24, T * 0.76, T * 0.56))
            pygame.draw.ellipse(s, theme.scale(base, 0.5), (T * 0.18, T * 0.3, T * 0.64, T * 0.44))
        elif kind == 'wreck':
            for _ in range(3):
                x0, y0 = rnd.uniform(0.15, 0.7) * T, rnd.uniform(0.2, 0.7) * T
                pts = [(x0, y0), (x0 + rnd.uniform(0.15, 0.3) * T, y0 + rnd.uniform(-0.1, 0.15) * T),
                       (x0 + rnd.uniform(0.05, 0.2) * T, y0 + rnd.uniform(0.15, 0.3) * T)]
                pygame.draw.polygon(s, (120, 124, 136), pts)
                pygame.draw.polygon(s, (255, 150, 70), pts, 1)
        elif kind == 'stairs':
            col = theme.TOKEN_COLORS.get(ch, (200, 200, 200))
            for i in range(4):
                w = T * (0.7 - i * 0.12)
                pygame.draw.rect(s, theme.scale(col, 0.35 + i * 0.18), (c - w / 2, T * (0.22 + i * 0.15), w, T * 0.1), border_radius=2)
        elif kind == 'portal':
            s.fill(theme.scale(base, 0.5))
            for i, col in enumerate(((90, 20, 40), (160, 30, 60), (230, 60, 90))):
                pygame.draw.ellipse(s, col, (T * (0.1 + i * 0.1), T * (0.15 + i * 0.1), T * (0.8 - i * 0.2), T * (0.7 - i * 0.2)), 2)
            pygame.draw.ellipse(s, (10, 4, 12), (T * 0.36, T * 0.4, T * 0.28, T * 0.2))
        elif kind == 'ship':
            hull = [(T * 0.1, T * 0.7), (T * 0.5, T * 0.15), (T * 0.9, T * 0.7), (T * 0.5, T * 0.58)]
            pygame.draw.polygon(s, (170, 176, 196), hull)
            pygame.draw.polygon(s, (230, 234, 245), hull, 1)
            pygame.draw.circle(s, (86, 214, 255), (c, T * 0.45), T * 0.07)
        elif kind == 'comms':
            pygame.draw.line(s, (170, 176, 196), (c, T * 0.85), (c, T * 0.3), 2)
            pygame.draw.arc(s, (210, 216, 236), (c - T * 0.3, T * 0.08, T * 0.6, T * 0.4), math.pi, math.tau, 2)
            pygame.draw.circle(s, (110, 224, 150), (c, T * 0.3), max(2, T // 14))
        elif kind == 'item':
            col = theme.TOKEN_COLORS.get(ch, theme.POI_COLOR)
            if ch == '$':
                for i, (ox, oy) in enumerate(((-0.1, 0.08), (0.08, 0.02), (0.0, -0.08))):
                    pygame.draw.circle(s, theme.scale(col, 0.7), (c + ox * T, c + oy * T + 1), T * 0.14)
                    pygame.draw.circle(s, col, (c + ox * T, c + oy * T), T * 0.14)
            elif ch == '!':
                pygame.draw.rect(s, (220, 230, 240), (c - T * 0.05, T * 0.2, T * 0.1, T * 0.16))
                pygame.draw.circle(s, col, (c, T * 0.56), T * 0.2)
                pygame.draw.circle(s, theme.mix(col, (255, 255, 255), 0.5), (c - T * 0.07, T * 0.5), T * 0.05)
            elif ch == '&':
                d = T * 0.3
                pygame.draw.polygon(s, col, [(c, c - d), (c + d * 0.75, c), (c, c + d), (c - d * 0.75, c)])
                pygame.draw.polygon(s, (255, 240, 255), [(c, c - d), (c + d * 0.75, c), (c, c + d), (c - d * 0.75, c)], 1)
            elif ch == '+':   # medkit
                pygame.draw.rect(s, (235, 238, 245), (c - T * 0.22, c - T * 0.17, T * 0.44, T * 0.34), border_radius=3)
                pygame.draw.rect(s, (230, 60, 80), (c - T * 0.04, c - T * 0.12, T * 0.08, T * 0.24))
                pygame.draw.rect(s, (230, 60, 80), (c - T * 0.12, c - T * 0.04, T * 0.24, T * 0.08))
            elif ch == '0':   # thermal grenade
                pygame.draw.circle(s, (70, 72, 84), (c, c), T * 0.18)
                pygame.draw.circle(s, (255, 190, 70), (c, c), T * 0.06)
                pygame.draw.circle(s, (150, 152, 170), (c, c), T * 0.18, 1)
            elif ch == '/':   # lightsaber
                pygame.draw.line(s, (170, 230, 255), (c - T * 0.05, c + T * 0.05), (c + T * 0.3, c - T * 0.3), max(2, T // 12))
                pygame.draw.line(s, (120, 124, 140), (c - T * 0.28, c + T * 0.28), (c - T * 0.05, c + T * 0.05), max(3, T // 9))
            elif ch == 'v':   # vibroblade
                pygame.draw.polygon(s, (200, 206, 220), [(c - T * 0.2, c + T * 0.2), (c + T * 0.28, c - T * 0.28), (c - T * 0.12, c + T * 0.26)])
                pygame.draw.line(s, (120, 90, 60), (c - T * 0.28, c + T * 0.28), (c - T * 0.16, c + T * 0.16), max(3, T // 9))
            elif ch == 'b':   # blaster
                pygame.draw.rect(s, (90, 94, 110), (c - T * 0.26, c - T * 0.1, T * 0.44, T * 0.14), border_radius=2)
                pygame.draw.rect(s, (70, 60, 50), (c - T * 0.2, c, T * 0.12, T * 0.2), border_radius=2)
            elif ch == 's':   # shield emitter
                pygame.draw.circle(s, (110, 170, 255), (c, c), T * 0.22, 2)
                pygame.draw.circle(s, (200, 230, 255), (c, c), T * 0.08)
            elif ch == 'c':   # energy cell
                pygame.draw.rect(s, (60, 200, 170), (c - T * 0.08, c - T * 0.18, T * 0.16, T * 0.36), border_radius=3)
            elif ch in 'ftnz;':  # focus, tea, compass, paste, canteen
                colmap = {'f': (170, 140, 255), 't': (190, 140, 90), 'n': (240, 210, 120), 'z': (160, 200, 120), ';': (110, 170, 230)}
                pygame.draw.circle(s, colmap[ch], (c, c), T * 0.16)
                pygame.draw.circle(s, (250, 250, 255), (c - T * 0.05, c - T * 0.05), max(1, T // 16))
            elif ch == 'E':   # enemy drop: loot bundle
                pygame.draw.ellipse(s, (130, 100, 70), (c - T * 0.2, c - T * 0.12, T * 0.4, T * 0.3))
                pygame.draw.line(s, (255, 210, 120), (c - T * 0.12, c - T * 0.12), (c + T * 0.12, c - T * 0.12), 2)
            elif ch == 'Q':   # corrupted Jedi artifact
                d = T * 0.28
                pts = [(c, c - d), (c + d * 0.6, c), (c, c + d), (c - d * 0.6, c)]
                pygame.draw.polygon(s, (90, 200, 255), pts)
                pygame.draw.polygon(s, (160, 40, 80), pts, 2)
            elif ch in 'mhwepliKk':  # crafting material: ore chunk
                mc = (140, 220, 255) if ch == 'K' else (170, 175, 190)
                pts = [(c - T * 0.18, c + T * 0.14), (c - T * 0.1, c - T * 0.14), (c + T * 0.12, c - T * 0.16), (c + T * 0.2, c + T * 0.1)]
                pygame.draw.polygon(s, theme.scale(mc, 0.7), pts)
                pygame.draw.polygon(s, mc, pts, 1)
            else:
                pygame.draw.ellipse(s, col, (c - T * 0.22, c - T * 0.12, T * 0.44, T * 0.26))
        elif kind == 'cache':
            pygame.draw.rect(s, (70, 60, 50), (T * 0.18, T * 0.3, T * 0.64, T * 0.44), border_radius=3)
            pygame.draw.rect(s, (200, 60, 70), (T * 0.18, T * 0.3, T * 0.64, T * 0.44), 1, border_radius=3)
            pygame.draw.line(s, (200, 60, 70), (T * 0.18, T * 0.45), (T * 0.82, T * 0.45), 1)
        elif kind == 'token':
            if ch.isupper():
                col = theme.POI_COLOR
            elif ch.islower():
                col = theme.MATERIAL_COLOR
            else:
                col = theme.TOKEN_COLORS.get(ch, theme.POI_COLOR)
            badge = pygame.Rect(T * 0.14, T * 0.14, T * 0.72, T * 0.72)
            pygame.draw.rect(s, theme.mix(base, col, 0.28), badge, border_radius=max(3, T // 6))
            pygame.draw.rect(s, col, badge, 1, border_radius=max(3, T // 6))
            g = self.font(int(T * 0.52)).render(ch, True, col)
            s.blit(g, (c - g.get_width() / 2, c - g.get_height() / 2))
        return s

    def tile_sprite(self, ch, x, y, in_tomb, light):
        """light: 0..10 for lit tiles, -1 for remembered tiles."""
        floor = self._floor_kind(x, y, in_tomb)
        kind = self._tile_kind(ch, in_tomb)
        variant = ((x * 73856093) ^ (y * 19349663)) % 3 if kind in ('floor', 'wall', 'rock', 'tree', 'dune') else 0
        key = (ch, floor, variant, light)
        s = self.tiles.get(key)
        if s is None:
            base_key = (ch, floor, variant, 'base')
            base = self.tiles.get(base_key)
            if base is None:
                base = self.tiles[base_key] = self._base_tile(ch, kind, floor, variant, in_tomb)
            s = base.copy()
            if light < 0:
                s.fill((92, 96, 118), special_flags=pygame.BLEND_RGB_MULT)
                tint = pygame.Surface(s.get_size())
                tint.fill(theme.scale(theme.MEMORY_TINT, 0.35))
                s.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            elif light < 10:
                k = int(255 * (0.3 + 0.7 * light / 10))
                s.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
            if len(self.tiles) > 5000:
                self.tiles.clear()
            self.tiles[key] = s
        return s

    # --------------------------------------------------------- state tracking
    def _entity_pos(self, ent, key=None):
        key = key or id(ent)
        tx, ty = float(getattr(ent, 'x', 0)), float(getattr(ent, 'y', 0))
        cur = self.disp.get(key)
        if cur is None or abs(cur[0] - tx) + abs(cur[1] - ty) > 3.5:
            cur = [tx, ty]
            self.disp[key] = cur
        return cur, tx, ty

    def _track(self, dt):
        g = self.game
        p = g.player
        mkey = (id(g.game_map), getattr(g, 'tomb_floor', None))
        if mkey != self.map_key:
            self.map_key = mkey
            self.enemy_state.clear()
            self.disp.clear()
            self.particles.clear()
            self.tracers.clear()
            self.cam = None
            self.player_hp = getattr(p, 'hp', 0)
            self.minimap = None
        # player hp
        hp = getattr(p, 'hp', 0)
        if self.player_hp is not None and hp != self.player_hp:
            d = hp - self.player_hp
            if d < 0:
                self.shake = min(14.0, self.shake + 4 + (-d) * 1.2)
                self.hurt = 0.45
                self.floater(p.x, p.y - 0.2, f"{d}", theme.ANSI[1], big=True)
                self.burst(p.x + 0.5, p.y + 0.5, (255, 90, 110), n=10, speed=3.5)
            else:
                self.floater(p.x, p.y - 0.2, f"+{d}", theme.ANSI[2])
                self.burst(p.x + 0.5, p.y + 0.5, (110, 224, 150), n=8, speed=1.8, life=0.9, size=2)
        self.player_hp = hp
        # enemies
        seen = set()
        vis = getattr(g, 'visible', set()) or set()
        for e in list(getattr(g, 'enemies', []) or []):
            k = id(e)
            seen.add(k)
            ehp = getattr(e, 'hp', 0)
            st = self.enemy_state.get(k)
            pos = (getattr(e, 'x', 0), getattr(e, 'y', 0))
            if st is not None and ehp < st['hp'] and (pos in vis or st['vis']):
                d = st['hp'] - ehp
                self.floater(pos[0], pos[1] - 0.2, f"-{d}", (255, 236, 200))
                self.burst(pos[0] + 0.5, pos[1] + 0.5, (255, 170, 80), n=8, speed=4.5, life=0.35, size=2)
                self.hit_flash[k] = 0.14
            self.enemy_state[k] = {'hp': ehp, 'pos': pos, 'vis': pos in vis,
                                   'color': self._enemy_color(e), 'alive': ehp > 0}
            if ehp <= 0 and st is not None and st.get('alive'):
                self._death_fx(pos, self._enemy_color(e))
        for k in [k for k in self.enemy_state if k not in seen]:
            st = self.enemy_state.pop(k)
            if st.get('alive') and st.get('vis'):
                self._death_fx(st['pos'], st['color'])
            self.disp.pop(k, None)
        # popups (explosions / taunts) raised by game code
        pops = getattr(getattr(g, 'ui', None), 'popups', None) or []
        ids = set()
        for pop in pops:
            pid = id(pop)
            ids.add(pid)
            if pid in self.popup_ids or not isinstance(pop, dict):
                continue
            text = str(pop.get('text', ''))
            try:
                x, y = int(pop.get('x')), int(pop.get('y'))
            except Exception:
                continue
            if 'BOOM' in text.upper():
                self.explosion(x, y)
            elif not text.strip().lstrip('-+').isdigit():
                self.floater(x, y - 0.3, text, theme.ANSI[3])
        self.popup_ids = ids

    def explosion(self, x, y, radius=1.5):
        cx, cy = x + 0.5, y + 0.5
        self.burst(cx, cy, (255, 200, 90), n=40, speed=7.0, life=0.7, size=4)
        self.burst(cx, cy, (255, 90, 60), n=24, speed=4.0, life=0.9, size=3)
        self.burst(cx, cy, (90, 90, 100), n=16, speed=1.5, life=1.4, size=5)
        self.shake = min(18.0, self.shake + 12)
        self.floater(x, y - 0.4, "BOOM", (255, 200, 90), big=True)

    def _death_fx(self, pos, color):
        cx, cy = pos[0] + 0.5, pos[1] + 0.5
        self.burst(cx, cy, color, n=26, speed=5.0, life=0.8, size=3)
        self.burst(cx, cy, (70, 70, 84), n=10, speed=1.2, life=1.2, size=4)

    def _enemy_color(self, e):
        if getattr(e, '_is_hallucination', False):
            return theme.ENEMY_HALLUCINATION
        name = str(getattr(e, 'name', '')).lower()
        if getattr(e, 'is_boss', False) or 'sith' in name or 'inquisitor' in name:
            return theme.ENEMY_SITH
        return theme.ENEMY

    def player_colors(self):
        corr = getattr(self.game.player, 'dark_corruption', 0) or 0
        return theme.by_threshold(theme.PLAYER_BY_CORRUPTION, corr), theme.by_threshold(theme.SABER_BY_CORRUPTION, corr)

    # ------------------------------------------------------------------ render
    def render(self, screen, rect, dt):
        g = self.game
        if not getattr(g, 'game_map', None):
            return
        self.t += dt
        if self.tile is None:
            self.tile = max(22, min(44, rect.h // 19))
        T = self.tile
        self._track(dt)
        p = g.player
        in_tomb = self.in_tomb()
        map_h = len(g.game_map)
        map_w = len(g.game_map[0]) if map_h else 0

        # interpolate player and update facing
        ppos, ptx, pty = self._entity_pos(p, 'player')
        dxp, dyp = ptx - ppos[0], pty - ppos[1]
        if abs(dxp) + abs(dyp) > 0.05:
            n = math.hypot(dxp, dyp)
            self.facing = (dxp / n, dyp / n)
        ppos[0] = _ease(ppos[0], ptx, 16, dt)
        ppos[1] = _ease(ppos[1], pty, 16, dt)
        if self.cam is None:
            self.cam = [ppos[0], ppos[1]]
        self.cam[0] = _ease(self.cam[0], ppos[0], 10, dt)
        self.cam[1] = _ease(self.cam[1], ppos[1], 10, dt)

        # screen shake
        self.shake = max(0.0, self.shake - dt * 40)
        sx = sy = 0
        if self.shake > 0.3:
            sx = self.rng.uniform(-1, 1) * self.shake
            sy = self.rng.uniform(-1, 1) * self.shake

        ox = rect.centerx - (self.cam[0] + 0.5) * T
        oy = rect.centery - (self.cam[1] + 0.5) * T
        if map_w * T <= rect.w:
            ox = rect.x + (rect.w - map_w * T) / 2
        else:
            ox = min(rect.x, max(rect.right - map_w * T, ox))
        if map_h * T <= rect.h:
            oy = rect.y + (rect.h - map_h * T) / 2
        else:
            oy = min(rect.y, max(rect.bottom - map_h * T, oy))
        ox += sx
        oy += sy
        self._origin = (ox, oy)

        prev_clip = screen.get_clip()
        screen.set_clip(rect)
        screen.fill(theme.VOID, rect)

        vis = getattr(g, 'visible', set()) or set()
        explored = getattr(g, 'explored', set()) or set()
        fog = bool(getattr(g, 'fog_of_war', True))
        radius = float(getattr(p, 'los_radius', 6) or 6) + float(getattr(p, 'los_bonus', 0) or 0)
        flicker = 0.04 * math.sin(self.t * 7.3) + 0.03 * math.sin(self.t * 13.1)

        tx0 = max(0, int((rect.x - ox) // T))
        ty0 = max(0, int((rect.y - oy) // T))
        tx1 = min(map_w, int((rect.right - ox) // T) + 1)
        ty1 = min(map_h, int((rect.bottom - oy) // T) + 1)
        pcx, pcy = ppos[0], ppos[1]
        specials = []
        blit = screen.blit
        for ty in range(ty0, ty1):
            row = g.game_map[ty]
            py = oy + ty * T
            for tx in range(tx0, tx1):
                ch = row[tx]
                pos = (tx, ty)
                if pos in vis:
                    d = math.hypot(tx - pcx, ty - pcy)
                    b = 1.0 - (d / (radius + 2.0)) ** 2 * 0.6 + flicker
                    light = max(0, min(10, int(round(b * 10))))
                    if ch in ('D', '&', '>', '<', '?', '§', '¶', '†', '‡', '%'):
                        specials.append((tx, ty, ch))
                elif pos in explored or not fog:
                    light = -1
                else:
                    continue
                blit(self.tile_sprite(ch, tx, ty, in_tomb, light), (ox + tx * T, py))

        self._draw_specials(screen, specials, in_tomb)
        if not in_tomb:
            self._draw_cordon(screen, dt)
        self._draw_targeting(screen, vis)
        self._draw_enemies(screen, vis, dt)
        if not in_tomb:
            self._draw_landings(screen, dt)
        self._draw_player(screen, ppos, dt)
        self._draw_projectiles(screen, dt)
        self._draw_tracers(screen, dt)
        self._draw_particles(screen, dt)
        self._draw_lighting(screen, rect, ppos, in_tomb)
        self._draw_floaters(screen, dt)
        self._draw_compass(screen, rect, in_tomb)
        if self.hurt > 0:
            self.hurt = max(0.0, self.hurt - dt)
            self._draw_hurt(screen, rect, self.hurt / 0.45)
        screen.set_clip(prev_clip)
        self._draw_hud(screen, rect, in_tomb)
        self._draw_minimap(screen, rect, vis, explored, fog, in_tomb)

    def to_px(self, x, y):
        ox, oy = self._origin
        T = self.tile
        return ox + (x + 0.5) * T, oy + (y + 0.5) * T

    def _draw_specials(self, screen, specials, in_tomb):
        T = self.tile
        for tx, ty, ch in specials:
            cx, cy = self.to_px(tx, ty)
            if ch == 'D' and not in_tomb:
                k = 0.7 + 0.3 * math.sin(self.t * 3 + tx)
                self.add_glow(screen, cx, cy, T * 1.3, (170, 30, 60), k)
            elif ch == '&':
                k = 0.6 + 0.4 * math.sin(self.t * 4 + ty)
                self.add_glow(screen, cx, cy, T * 0.9, (120, 60, 200), k)
            elif ch in '?§¶†‡%' and not in_tomb:
                self.add_glow(screen, cx, cy, T * 0.75, (110, 50, 170), 0.5 + 0.3 * math.sin(self.t * 3 + tx * 0.7))
            elif ch in '<>':
                col = theme.TOKEN_COLORS[ch]
                self.add_glow(screen, cx, cy, T * 0.8, theme.scale(col, 0.5), 0.6 + 0.2 * math.sin(self.t * 2))

    # ------------------------------------------------------------ cordon
    def _draw_cordon(self, screen, dt):
        c = getattr(self.game, 'cordon', None)
        if c is None:
            return
        T = self.tile
        cx, cy = self.to_px(c.center[0], c.center[1])
        # smoke and embers from the wreck for the first minutes
        if self.t < 180 and self.rng.random() < 0.5:
            self.particles.append(Particle(c.center[0] + 0.5 + self.rng.uniform(-0.6, 0.6), c.center[1] + 0.5,
                                           self.rng.uniform(-0.2, 0.2), self.rng.uniform(-1.4, -0.7), 2.6,
                                           (24, 23, 28), 6, drag=0.3))
            if self.rng.random() < 0.3:
                self.particles.append(Particle(c.center[0] + 0.5, c.center[1] + 0.5, self.rng.uniform(-1, 1),
                                               self.rng.uniform(-2.5, -1), 0.6, (255, 150, 60), 2))
        if not c.active:
            return
        # the closing ring (dashed, pulsing) and the line you must cross (faint)
        pulse = 0.6 + 0.4 * math.sin(self.t * 5)
        col = theme.scale((255, 60, 80), 0.5 + 0.5 * pulse)
        r = c.radius * T
        segs = max(24, int(r / 6))
        rot = self.t * 0.25
        for i in range(0, segs, 2):
            a0 = rot + i * math.tau / segs
            a1 = rot + (i + 1) * math.tau / segs
            pygame.draw.line(screen, col, (cx + math.cos(a0) * r, cy + math.sin(a0) * r),
                             (cx + math.cos(a1) * r, cy + math.sin(a1) * r), 2)
        re = c.escape_radius * T
        segs = max(32, int(re / 5))
        for i in range(0, segs, 3):
            a = i * math.tau / segs
            pygame.draw.circle(screen, (120, 220, 160), (int(cx + math.cos(a) * re), int(cy + math.sin(a) * re)), 1)

    def _draw_landings(self, screen, dt):
        c = getattr(self.game, 'cordon', None)
        if c is None or not c.landings:
            return
        T = self.tile
        if not hasattr(self, '_landed'):
            self._landed = set()
            self._landing_t0 = self.t
        el = self.t - self._landing_t0
        for i, (lx, ly) in enumerate(c.landings):
            start = 0.3 + i * 0.35
            k = (el - start) / 2.2
            if k < 0 or k > 1.6:
                continue
            gx, gy = self.to_px(lx, ly)
            if k <= 1.0:
                h = (1 - k) ** 2 * T * 9
                shadow = pygame.Surface((int(T * 2.4), int(T * 1.0)), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, int(60 + 100 * k)), shadow.get_rect())
                screen.blit(shadow, (gx - shadow.get_width() / 2, gy - shadow.get_height() / 2))
                self._dropship(screen, gx, gy - h, T * (1.2 - 0.2 * k))
            else:
                if i not in self._landed:
                    self._landed.add(i)
                    self.burst(lx + 0.5, ly + 0.5, (120, 110, 100), n=26, speed=4.0, life=1.0, size=5)
                    self.shake = min(10.0, self.shake + 3)
                # lift off and leave
                h = (k - 1.0) ** 2 * T * 30
                self._dropship(screen, gx, gy - h, T)

    def _dropship(self, screen, x, y, s):
        body = [(x - s, y), (x - s * 0.4, y - s * 0.35), (x + s * 0.4, y - s * 0.35), (x + s, y),
                (x + s * 0.3, y + s * 0.25), (x - s * 0.3, y + s * 0.25)]
        pygame.draw.polygon(screen, (40, 40, 50), body)
        pygame.draw.polygon(screen, (100, 100, 120), body, 1)
        self.add_glow(screen, x, y + s * 0.3, s * 0.7, (255, 150, 80), 0.7)
        if int(self.t * 4) % 2:
            self.add_glow(screen, x - s * 0.9, y, s * 0.3, (255, 40, 50), 1.0)
            self.add_glow(screen, x + s * 0.9, y, s * 0.3, (255, 40, 50), 1.0)

    def _targeting(self):
        g = self.game
        if getattr(g, 'pending_gun_shot', False):
            return 'gun', int(getattr(g, 'gun_range', 5) or 5)
        if getattr(g, 'pending_grenade_throw', False):
            return 'grenade', 3
        if getattr(g, 'pending_force_ability', None) is not None:
            return 'force', None
        return None, None

    def _draw_targeting(self, screen, vis):
        mode, rng = self._targeting()
        if not mode:
            return
        g = self.game
        T = self.tile
        col = theme.RETICLE[mode]
        px, py = int(g.player.x), int(g.player.y)
        tx, ty = int(getattr(g, 'target_x', px)), int(getattr(g, 'target_y', py))
        if rng:
            shade = pygame.Surface((T, T), pygame.SRCALPHA)
            shade.fill((*col, 34))
            for yy in range(py - rng, py + rng + 1):
                for xx in range(px - rng, px + rng + 1):
                    if abs(xx - px) + abs(yy - py) <= rng and (xx, yy) in vis:
                        x0, y0 = self.to_px(xx - 0.5, yy - 0.5)
                        screen.blit(shade, (x0, y0))
        # dotted aim line
        steps = max(abs(tx - px), abs(ty - py))
        for i in range(1, steps):
            f = i / steps
            x, y = self.to_px(px + (tx - px) * f, py + (ty - py) * f)
            pygame.draw.circle(screen, col, (int(x), int(y)), max(1, T // 14))
        # animated brackets
        cx, cy = self.to_px(tx, ty)
        pulse = 1.0 + 0.12 * math.sin(self.t * 8)
        h = T * 0.5 * pulse
        L = T * 0.22
        for sxn, syn in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x0, y0 = cx + sxn * h, cy + syn * h
            pygame.draw.line(screen, col, (x0, y0), (x0 - sxn * L, y0), 2)
            pygame.draw.line(screen, col, (x0, y0), (x0, y0 - syn * L), 2)
        self.add_glow(screen, cx, cy, T * 0.8, col, 0.35)
        # label enemy under reticle
        for e in getattr(g, 'enemies', []) or []:
            if getattr(e, 'x', None) == tx and getattr(e, 'y', None) == ty and (tx, ty) in vis:
                label = f"{getattr(e, 'name', 'Enemy')}  {getattr(e, 'hp', '?')}/{getattr(e, 'max_hp', '?')}"
                self._chip(screen, label, cx, cy - h - 14, col, center=True)
                break

    def _draw_enemies(self, screen, vis, dt):
        T = self.tile
        for e in list(getattr(self.game, 'enemies', []) or []):
            try:
                if not e.is_alive():
                    continue
            except Exception:
                continue
            ex, ey = getattr(e, 'x', -1), getattr(e, 'y', -1)
            if (ex, ey) not in vis:
                continue
            cur, tx, ty = self._entity_pos(e)
            cur[0] = _ease(cur[0], tx, 14, dt)
            cur[1] = _ease(cur[1], ty, 14, dt)
            cx, cy = self.to_px(cur[0], cur[1])
            color = self._enemy_color(e)
            boss = getattr(e, 'is_boss', False)
            r = T * (0.42 if boss else 0.34)
            halluc = getattr(e, '_is_hallucination', False)
            layer = pygame.Surface((int(T * 1.4), int(T * 1.4)), pygame.SRCALPHA)
            lc = layer.get_width() / 2
            pygame.draw.ellipse(layer, (0, 0, 0, 90), (lc - r, lc + r * 0.55, r * 2, r * 0.7))
            pygame.draw.circle(layer, theme.scale(color, 0.45), (lc, lc + 1), r)
            pygame.draw.circle(layer, color, (lc, lc), r - 1)
            pygame.draw.circle(layer, theme.mix(color, (255, 255, 255), 0.35), (lc - r * 0.3, lc - r * 0.35), r * 0.3)
            fl = self.hit_flash.get(id(e), 0)
            if fl > 0:
                self.hit_flash[id(e)] = fl - dt
                pygame.draw.circle(layer, (255, 255, 255, int(220 * fl / 0.14)), (lc, lc), r)
            glyph = self.font(int(T * 0.46)).render(str(getattr(e, 'symbol', 'E'))[:1], True, (255, 245, 245))
            layer.blit(glyph, (lc - glyph.get_width() / 2, lc - glyph.get_height() / 2))
            if halluc:
                layer.set_alpha(int(110 + 60 * math.sin(self.t * 5)))
            if boss:
                pygame.draw.circle(layer, (255, 200, 90), (lc, lc), r + 3, 2)
            screen.blit(layer, (cx - lc, cy - lc))
            self.add_glow(screen, cx, cy, T * (0.9 if boss else 0.65), theme.scale(color, 0.4), 0.8)
            hp, mhp = getattr(e, 'hp', 0), max(1, getattr(e, 'max_hp', 1) or 1)
            if hp < mhp:
                w = T * 0.8
                bx, by = cx - w / 2, cy - r - 7
                pygame.draw.rect(screen, (20, 20, 28), (bx - 1, by - 1, w + 2, 5), border_radius=2)
                pygame.draw.rect(screen, theme.mix((255, 80, 90), (110, 224, 150), hp / mhp), (bx, by, max(1, w * hp / mhp), 3), border_radius=2)

    def _draw_player(self, screen, ppos, dt):
        T = self.tile
        body, saber = self.player_colors()
        cx, cy = self.to_px(ppos[0], ppos[1])
        r = T * 0.34
        pygame.draw.ellipse(screen, (0, 0, 0), (cx - r, cy + r * 0.55, r * 2, r * 0.7))
        self.add_glow(screen, cx, cy, T * 1.1, theme.scale(saber, 0.35))
        pygame.draw.circle(screen, theme.scale(body, 0.45), (cx, cy + 1), r)
        pygame.draw.circle(screen, body, (cx, cy), r - 1)
        pygame.draw.circle(screen, (245, 250, 255), (cx, cy), r - 1, 2)
        pygame.draw.circle(screen, theme.mix(body, (255, 255, 255), 0.5), (cx - r * 0.3, cy - r * 0.35), r * 0.28)
        # lightsaber: held to the side of the facing direction, with idle sway
        fx, fy = self.facing
        sway = 0.25 * math.sin(self.t * 2.2)
        ang = math.atan2(fy, fx) - 0.9 + sway
        hx, hy = cx + math.cos(ang + 0.6) * r * 0.9, cy + math.sin(ang + 0.6) * r * 0.9
        L = T * 0.78
        ex, ey = hx + math.cos(ang) * L, hy + math.sin(ang) * L
        steps = 6
        for i in range(steps + 1):
            f = i / steps
            self.add_glow(screen, hx + (ex - hx) * f, hy + (ey - hy) * f, T * 0.26, saber, 0.55)
        pygame.draw.line(screen, theme.mix(saber, (255, 255, 255), 0.7), (hx, hy), (ex, ey), max(2, T // 12))
        pygame.draw.line(screen, (60, 64, 76), (hx, hy), (hx - math.cos(ang) * T * 0.16, hy - math.sin(ang) * T * 0.16), max(3, T // 9))

    def _draw_projectiles(self, screen, dt):
        T = self.tile
        g = self.game
        for pr in list(getattr(g, 'projectiles', []) or []):
            try:
                cur, tx, ty = self._entity_pos(pr)
                cur[0] = _ease(cur[0], tx, 22, dt)
                cur[1] = _ease(cur[1], ty, 22, dt)
                cx, cy = self.to_px(cur[0], cur[1])
                owner = getattr(pr, 'owner', None)
                sym = str(getattr(pr, 'symbol', '*'))
                if sym in ('o', 'O', '0', '@') or 'grenade' in str(getattr(pr, 'kind', '')).lower():
                    col = (255, 198, 92)
                elif owner is g.player:
                    col = (90, 220, 255)
                else:
                    col = (255, 70, 80)
                dx, dy = float(getattr(pr, 'dx', 0) or 0), float(getattr(pr, 'dy', 0) or 0)
                n = math.hypot(dx, dy) or 1
                tail = (cx - dx / n * T * 0.6, cy - dy / n * T * 0.6)
                self.add_glow(screen, cx, cy, T * 0.5, col, 0.9)
                pygame.draw.line(screen, theme.mix(col, (255, 255, 255), 0.6), tail, (cx, cy), max(2, T // 10))
            except Exception:
                continue

    def _draw_tracers(self, screen, dt):
        T = self.tile
        keep = []
        for tr in self.tracers:
            tr['t'] += dt
            f = min(1.0, tr['t'] / tr['dur'])
            hx = tr['sx'] + (tr['ex'] - tr['sx']) * f
            hy = tr['sy'] + (tr['ey'] - tr['sy']) * f
            f0 = max(0.0, f - 0.35)
            tx = tr['sx'] + (tr['ex'] - tr['sx']) * f0
            ty = tr['sy'] + (tr['ey'] - tr['sy']) * f0
            a = self.to_px(tx, ty)
            b = self.to_px(hx, hy)
            col = tr['color']
            if f < 1.0:
                self.add_glow(screen, b[0], b[1], T * 0.5, col, 1.0)
                pygame.draw.line(screen, theme.mix(col, (255, 255, 255), 0.6), a, b, max(2, T // 10))
                keep.append(tr)
            elif not tr['done']:
                tr['done'] = True
                self.burst(tr['ex'] + 0.5, tr['ey'] + 0.5, col, n=10, speed=3.0, life=0.3, size=2)
        self.tracers = keep

    def _draw_particles(self, screen, dt):
        T = self.tile
        keep = []
        for pt in self.particles:
            pt.life -= dt
            if pt.life <= 0:
                continue
            pt.vx -= pt.vx * pt.drag * dt
            pt.vy -= pt.vy * pt.drag * dt
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
            k = pt.life / pt.max_life
            cx, cy = self.to_px(pt.x - 0.5, pt.y - 0.5)
            size = max(1, int(pt.size * (0.4 + 0.6 * k) * T / 28))
            self.add_glow(screen, cx, cy, size * 3, pt.color, k)
            keep.append(pt)
        self.particles = keep

    def _edge_mask(self, size, color, max_alpha, power):
        """Smooth elliptical edge gradient: small per-pixel mask upscaled with smoothscale."""
        key = ('edge', size, color, max_alpha, power)
        surf = self.glows.get(key)
        if surf is None:
            sw, sh = 96, 60
            small = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for y in range(sh):
                ny = (y + 0.5) / sh * 2 - 1
                for x in range(sw):
                    nx = (x + 0.5) / sw * 2 - 1
                    d = min(1.0, math.sqrt(nx * nx * 0.5 + ny * ny * 0.5) * 1.05)
                    small.set_at((x, y), (*color, int(max_alpha * d ** power)))
            surf = pygame.transform.smoothscale(small, size)
            self.glows[key] = surf
        return surf

    def _draw_lighting(self, screen, rect, ppos, in_tomb):
        screen.blit(self._edge_mask(rect.size, (4, 5, 10), 190 if in_tomb else 150, 2.6), rect.topleft)

    def _draw_floaters(self, screen, dt):
        keep = []
        T = self.tile
        for f in self.floaters:
            f['t'] += dt
            k = f['t'] / f['life']
            if k >= 1:
                continue
            cx, cy = self.to_px(f['x'] + f['dx'] * k, f['y'] - 0.9 * (1 - (1 - k) ** 2))
            size = int(T * (0.62 if f['big'] else 0.48))
            font = self.font(size)
            txt = font.render(f['text'], True, f['color'])
            sh = font.render(f['text'], True, (0, 0, 0))
            surf = pygame.Surface((txt.get_width() + 2, txt.get_height() + 2), pygame.SRCALPHA)
            surf.blit(sh, (2, 2))
            surf.blit(txt, (0, 0))
            surf.set_alpha(int(255 * min(1.0, (1 - k) * 2.2)))
            pop = 1.0 + 0.35 * max(0.0, 1 - k * 6) if f['big'] else 1.0
            if pop != 1.0:
                surf = pygame.transform.smoothscale(surf, (int(surf.get_width() * pop), int(surf.get_height() * pop)))
            screen.blit(surf, (cx - surf.get_width() / 2, cy - surf.get_height() / 2))
            keep.append(f)
        self.floaters = keep

    def _draw_hurt(self, screen, rect, k):
        m = self._edge_mask(rect.size, (230, 20, 45), 200, 2.0)
        m.set_alpha(int(255 * max(0.0, min(1.0, k))))
        screen.blit(m, rect.topleft)
        m.set_alpha(None)

    def _draw_compass(self, screen, rect, in_tomb):
        if in_tomb:
            return
        g = self.game
        tombs = getattr(g, 'tomb_entrances', None) or ()
        if not tombs:
            return
        px, py = g.player.x, g.player.y
        best = min(tombs, key=lambda t: (t[0] - px) ** 2 + (t[1] - py) ** 2)
        cx, cy = self.to_px(best[0], best[1])
        if rect.collidepoint(cx, cy):
            return
        pcx, pcy = self.to_px(self.disp.get('player', [px, py])[0], self.disp.get('player', [px, py])[1])
        ang = math.atan2(cy - pcy, cx - pcx)
        # intersect ray with inset viewport edge
        inset = rect.inflate(-90, -110)
        dx, dy = math.cos(ang), math.sin(ang)
        tmax = min((inset.right - pcx) / dx if dx > 0 else (inset.left - pcx) / dx if dx < 0 else 1e9,
                   (inset.bottom - pcy) / dy if dy > 0 else (inset.top - pcy) / dy if dy < 0 else 1e9)
        ax, ay = pcx + dx * tmax, pcy + dy * tmax
        s = 12 + 2 * math.sin(self.t * 4)
        pts = [(ax + dx * s, ay + dy * s),
               (ax + math.cos(ang + 2.5) * s, ay + math.sin(ang + 2.5) * s),
               (ax + math.cos(ang - 2.5) * s, ay + math.sin(ang - 2.5) * s)]
        self.add_glow(screen, ax, ay, 26, (170, 30, 60), 0.8)
        pygame.draw.polygon(screen, (255, 90, 110), pts)
        dist = int(math.hypot(best[0] - px, best[1] - py))
        lbl = self.font(max(10, self.app.font_size - 3)).render(f"TOMB {dist}m", True, (255, 170, 180))
        screen.blit(lbl, (ax - dx * 34 - lbl.get_width() / 2, ay - dy * 34 - lbl.get_height() / 2))

    # ---------------------------------------------------------------- HUD
    def _chip(self, screen, text, x, y, color, center=False, font=None):
        font = font or self.app.ui_font_small
        t = font.render(text, True, color)
        w, h = t.get_width() + 16, t.get_height() + 6
        if center:
            x -= w / 2
        chip = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(chip, (12, 14, 24, 200), chip.get_rect(), border_radius=h // 2)
        pygame.draw.rect(chip, (*theme.scale(color, 0.6), 255), chip.get_rect(), 1, border_radius=h // 2)
        chip.blit(t, (8, 3))
        screen.blit(chip, (x, y))
        return w, h

    def _bar_surface(self, w, h, colors):
        key = ('bar', w, h, colors)
        surf = self.glows.get(key)
        if surf is None:
            grad = pygame.Surface((w, h))
            for i in range(w):
                grad.fill(theme.mix(colors[0], colors[1], i / max(1, w - 1)), (i, 0, 1, h))
            pygame.draw.line(grad, theme.mix(colors[0], (255, 255, 255), 0.45), (h // 2, 1), (w - h // 2, 1))
            surf = grad.convert_alpha() if pygame.display.get_surface() else grad
            self.glows[key] = surf
        return surf

    def _bar(self, screen, x, y, w, h, key, value, maximum, colors, label):
        maximum = max(1e-6, float(maximum))
        target = max(0.0, min(1.0, float(value) / maximum))
        cur = self.bar_vals.get(key, target)
        lag = self.bar_vals.get(key + '_lag', target)
        cur = _ease(cur, target, 14, self.app.frame_dt)
        lag = _ease(lag, target, 2.5, self.app.frame_dt) if lag > target else target
        self.bar_vals[key], self.bar_vals[key + '_lag'] = cur, lag
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 12, 20, 215), bg.get_rect(), border_radius=h // 2)
        iw, ih = w - 4, h - 4
        if lag > cur:
            pygame.draw.rect(bg, (255, 235, 200, 110), (2, 2, max(ih, int(iw * lag)), ih), border_radius=ih // 2)
        fw = int(iw * cur)
        if fw > 0:
            fill = self._bar_surface(iw, ih, colors).subsurface((0, 0, max(1, fw), ih)).copy()
            mask = pygame.Surface(fill.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=ih // 2)
            fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            bg.blit(fill, (2, 2))
        pygame.draw.rect(bg, (*theme.scale(colors[0], 0.75), 255), bg.get_rect(), 1, border_radius=h // 2)
        f = self.app.ui_font_small
        sh = f.render(label, True, (0, 0, 0))
        t = f.render(label, True, (250, 252, 255))
        ty = (h - t.get_height()) // 2
        bg.blit(sh, (11, ty + 1))
        bg.blit(t, (10, ty))
        screen.blit(bg, (x, y))

    def _draw_hud(self, screen, rect, in_tomb):
        g = self.game
        p = g.player
        x, y = rect.x + 12, rect.y + 10
        w = min(260, rect.w // 3)
        h = max(16, self.app.ui_font_small.get_linesize() + 4)
        hp, mhp = getattr(p, 'hp', 0), getattr(p, 'max_hp', 1)
        self._bar(screen, x, y, w, h, 'hp', hp, mhp, theme.BAR_HP, f"HP  {hp}/{mhp}")
        y += h + 6
        fe = getattr(p, 'force_energy', None)
        mfe = getattr(p, 'max_force_energy', 100) or 100
        if fe is not None:
            self._bar(screen, x, y, w, h, 'force', fe, mfe, theme.BAR_FORCE, f"FORCE  {int(fe)}/{int(mfe)}")
            y += h + 6
        if getattr(p, '_stress_system_active', False):
            st, mst = getattr(p, 'stress', 0), getattr(p, 'max_stress', 100) or 100
            self._bar(screen, x, y, w, h, 'stress', st, mst, theme.BAR_STRESS, f"STRESS  {int(st)}/{int(mst)}")
            y += h + 6
        ps = getattr(g, 'pursuit_system', None)
        if ps is not None:
            from jedi_fugitive.game.pursuit import tier_name
            heat = int(ps.detection_level)
            self._bar(screen, x, y, w, h, 'heat', heat, 100, ((150, 110, 255), (255, 60, 90)), f"HEAT  {tier_name(heat)}")
            y += h + 6
        corr = int(getattr(p, 'dark_corruption', 0) or 0)
        body, saber = self.player_colors()
        cw, _ = self._chip(screen, f"LV {getattr(p, 'level', 1)}", x, y, (240, 244, 255))
        self._chip(screen, f"CORRUPTION {corr}%", x + cw + 6, y, saber)

        # top-right: mode + location
        rt = getattr(g, 'realtime', False)
        mode = "● REAL-TIME" if rt else "❚❚ TURN-BASED"
        mcol = (110, 224, 150) if rt else (170, 180, 210)
        f = self.app.ui_font_small
        label = f"{mode}   F2"
        wlab = f.size(label)[0] + 16
        self._chip(screen, label, rect.right - wlab - 12, rect.y + 10, mcol)
        if in_tomb:
            loc = f"SITH TOMB · LEVEL {int(getattr(g, 'tomb_floor', 0) or 0) + 1}"
            lcol = (255, 110, 130)
        else:
            biome = str(getattr(g, 'current_biome', '') or getattr(g, 'current_location', 'Surface'))
            loc = biome.upper()
            lcol = (220, 200, 150)
        wl = f.size(loc)[0] + 16
        self._chip(screen, loc, rect.right - wl - 12, rect.y + 16 + h, lcol)
        # objective banner for the opening escape
        c = getattr(g, 'cordon', None)
        if c is not None and not in_tomb:
            import math as _m
            d = _m.hypot(p.x - c.center[0], p.y - c.center[1])
            if c.active:
                text = f"⚠ ESCAPE THE CORDON · ring {c.radius:.0f}m · you {d:.0f}/{c.escape_radius:.0f}m"
                col = (255, 120, 130) if int(self.t * 2) % 2 else (255, 190, 190)
                fb = self.app.ui_font
                w = fb.size(text)[0] + 16
                self._chip(screen, text, rect.centerx - w / 2, rect.bottom - fb.get_linesize() - 22, col, font=fb)
            else:
                if not hasattr(self, '_cordon_end_t'):
                    self._cordon_end_t = self.t
                if self.t - self._cordon_end_t < 5:
                    fb = self.app.ui_font
                    text = "CORDON BROKEN. The hunt goes on."
                    w = fb.size(text)[0] + 16
                    self._chip(screen, text, rect.centerx - w / 2, rect.bottom - fb.get_linesize() - 22, (140, 240, 170), font=fb)
        if getattr(self.app, 'show_fps', False):
            self._chip(screen, f"{self.app.fps:4.0f} fps", rect.right - 90, rect.bottom - 30, (150, 160, 190))

    def _draw_minimap(self, screen, rect, vis, explored, fog, in_tomb):
        g = self.game
        mh = len(g.game_map)
        mw = len(g.game_map[0]) if mh else 0
        if not mw:
            return
        scale = 2
        span_w = max(20, min(80, rect.w // 4 // scale))
        span_h = max(14, min(50, rect.h // 4 // scale))
        span_w, span_h = min(span_w, mw), min(span_h, mh)
        px, py = int(g.player.x), int(g.player.y)
        x0 = max(0, min(mw - span_w, px - span_w // 2))
        y0 = max(0, min(mh - span_h, py - span_h // 2))
        now = time.perf_counter()
        key = (x0, y0, span_w, span_h, id(g.game_map))
        if self.minimap is None or now - self.minimap_at > 0.3 or getattr(self, '_mm_key', None) != key:
            self.minimap_at = now
            self._mm_key = key
            mm = pygame.Surface((span_w * scale, span_h * scale), pygame.SRCALPHA)
            mm.fill((0, 0, 0, 0))
            for y in range(y0, y0 + span_h):
                row = g.game_map[y]
                for x in range(x0, x0 + span_w):
                    if fog and (x, y) not in explored:
                        continue
                    ch = row[x]
                    if ch == WALL_CH:
                        col = (96, 108, 150, 230)
                    elif ch == 'T':
                        col = (50, 110, 70, 220)
                    elif ch == '~' and not in_tomb:
                        col = (50, 100, 170, 230)
                    elif ch == 'D' and not in_tomb:
                        col = (255, 70, 90, 255)
                    elif ch in '<>':
                        col = (255, 198, 92, 255)
                    elif ch in 'SC' and not in_tomb:
                        col = (86, 214, 255, 255)
                    elif (x, y) in vis:
                        col = (110, 112, 128, 220)
                    else:
                        col = (62, 64, 80, 190)
                    mm.fill(col, ((x - x0) * scale, (y - y0) * scale, scale, scale))
            self.minimap = mm
        mm = self.minimap
        bx = rect.right - mm.get_width() - 14
        by = rect.bottom - mm.get_height() - 14
        frame = pygame.Surface((mm.get_width() + 12, mm.get_height() + 12), pygame.SRCALPHA)
        pygame.draw.rect(frame, (8, 10, 18, 190), frame.get_rect(), border_radius=8)
        pygame.draw.rect(frame, (*theme.PANEL_BORDER, 255), frame.get_rect(), 1, border_radius=8)
        screen.blit(frame, (bx - 6, by - 6))
        screen.blit(mm, (bx, by))
        for e in getattr(g, 'enemies', []) or []:
            ex, ey = getattr(e, 'x', -1), getattr(e, 'y', -1)
            if (ex, ey) in vis and x0 <= ex < x0 + span_w and y0 <= ey < y0 + span_h:
                screen.fill((255, 80, 90), (bx + (ex - x0) * scale, by + (ey - y0) * scale, scale + 1, scale + 1))
        _, saber = self.player_colors()
        pcx, pcy = bx + (px - x0) * scale + 1, by + (py - y0) * scale + 1
        pygame.draw.circle(screen, saber, (pcx, pcy), 3)
        if int(self.t * 2) % 2:
            pygame.draw.circle(screen, (255, 255, 255), (pcx, pcy), 6, 1)
