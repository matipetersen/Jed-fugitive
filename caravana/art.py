"""Dibujo procedural: terreno, carretas, personas, partículas y luces (todo sin archivos externos)."""
from __future__ import annotations

import math
import random

import pygame

TERRAIN_COLORS = {
    "pradera": (96, 138, 68), "llanura": (140, 146, 78), "estepa": (156, 144, 94), "montaña": (108, 116, 94),
    "desierto": (190, 164, 116), "cañón": (168, 118, 82), "bosque": (56, 94, 58), "valle": (84, 140, 74),
}
SHIRTS = [(150, 70, 60), (70, 100, 150), (90, 130, 80), (150, 120, 60), (120, 80, 130), (60, 120, 120),
          (160, 90, 110), (110, 110, 110)]
SKIN = (222, 184, 150)

_ground_cache: dict = {}
_wagon_cache: dict = {}
_rot_cache: dict = {}
_light_cache: dict = {}


# ---------------------------------------------------------------- terreno
def ground_surface(size: tuple, terrain: str = "pradera", seed: int = 7) -> pygame.Surface:
    key = (size, terrain, seed)
    if key in _ground_cache:
        return _ground_cache[key]
    rng = random.Random(seed)
    base = TERRAIN_COLORS.get(terrain, TERRAIN_COLORS["pradera"])
    surf = pygame.Surface(size)
    surf.fill(base)
    w, h = size
    # manchas grandes
    for _ in range(int(w * h / 9000)):
        r = rng.randint(30, 110)
        d = rng.randint(-14, 14)
        col = tuple(max(0, min(255, c + d)) for c in base)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col + (22,), (r, r), r)
        surf.blit(s, (rng.randint(-r, w), rng.randint(-r, h)))
    # matas de hierba
    for _ in range(int(w * h / 700)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        d = rng.randint(-34, 22)
        col = tuple(max(0, min(255, c + d)) for c in base)
        ln = rng.randint(3, 7)
        pygame.draw.line(surf, col, (x, y), (x + rng.randint(-2, 2), y - ln), 1)
        if rng.random() < 0.5:
            pygame.draw.line(surf, col, (x + 2, y), (x + 3 + rng.randint(-1, 2), y - ln + 1), 1)
    # piedras y flores
    for _ in range(int(w * h / 14000)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        g = rng.randint(110, 150)
        pygame.draw.ellipse(surf, (g, g - 4, g - 10), (x, y, rng.randint(4, 9), rng.randint(3, 6)))
    if terrain in ("pradera", "valle", "llanura"):
        for _ in range(int(w * h / 22000)):
            x, y = rng.randint(0, w), rng.randint(0, h)
            col = rng.choice([(240, 220, 90), (230, 230, 240), (210, 120, 170)])
            surf.set_at((x, y), col)
            surf.set_at((x + 1, y), col)
    _ground_cache[key] = surf
    return surf


# ---------------------------------------------------------------- carreta
def wagon_base(level: int, reinforced: int, platform: bool, cannon: bool, lantern: bool, destroyed: bool) -> pygame.Surface:
    key = (level, reinforced, platform, cannon, lantern, destroyed)
    if key in _wagon_cache:
        return _wagon_cache[key]
    W, H = 100, 54
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2
    rng = random.Random(5)
    if destroyed:
        for _ in range(16):
            x, y = rng.randint(14, W - 26), rng.randint(10, H - 14)
            ang = rng.uniform(0, math.pi)
            ln = rng.randint(10, 26)
            col = rng.choice([(70, 48, 30), (92, 62, 38), (40, 30, 24)])
            pygame.draw.line(s, col, (x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln), rng.randint(2, 4))
        pygame.draw.ellipse(s, (30, 26, 24, 160), (cx - 24, cy - 10, 48, 20))
        pygame.draw.circle(s, (60, 50, 44), (cx - 28, cy + 10), 8, 2)
        _wagon_cache[key] = s
        return s
    # ruedas
    for dx in (-27, 27):
        for dy in (-1, 1):
            r = pygame.Rect(0, 0, 14, 7)
            r.center = (cx + dx, cy + dy * (H // 2 - 5))
            pygame.draw.rect(s, (34, 26, 20), r, border_radius=2)
            pygame.draw.line(s, (86, 66, 44), (r.left + 2, r.centery), (r.right - 2, r.centery), 1)
    # caja
    body = pygame.Rect(6, 7, W - 12, H - 14)
    pygame.draw.rect(s, (118, 82, 48), body, border_radius=5)
    pygame.draw.rect(s, (74, 50, 30), body, 2, border_radius=5)
    if reinforced:
        for i in range(reinforced):
            plate = pygame.Rect(10 + i * 4, 9 + i * 2, W - 20 - i * 8, H - 18 - i * 4)
            pygame.draw.rect(s, (120, 124, 130), plate, 2, border_radius=4)
        for x in range(14, W - 12, 18):
            pygame.draw.circle(s, (150, 154, 160), (x, 10), 2)
            pygame.draw.circle(s, (150, 154, 160), (x, H - 11), 2)
    # lona
    cover = pygame.Rect(12, 11, W - 24, H - 22)
    canvas = (232, 222, 190)
    pygame.draw.rect(s, canvas, cover, border_radius=14)
    for x in range(cover.left + 8, cover.right - 4, 11):
        pygame.draw.line(s, (206, 194, 160), (x, cover.top + 3), (x, cover.bottom - 3), 1)
    pygame.draw.rect(s, (176, 160, 126), cover, 2, border_radius=14)
    # daño
    if level >= 1:
        for _ in range(3 * level):
            x, y = rng.randint(cover.left + 6, cover.right - 6), rng.randint(cover.top + 4, cover.bottom - 4)
            pygame.draw.circle(s, (70, 56, 40), (x, y), rng.randint(2, 4))
            pygame.draw.line(s, (60, 48, 34), (x, y), (x + rng.randint(-8, 8), y + rng.randint(-5, 5)), 1)
    if level >= 2:
        pygame.draw.polygon(s, (60, 50, 40, 220), [(cx - 6, cover.top + 2), (cx + 12, cover.top + 8), (cx + 2, cover.top + 16)])
        pygame.draw.line(s, (40, 30, 24), (cx - 22, cover.bottom - 3), (cx - 10, cover.top + 8), 2)
    if level >= 3:
        pygame.draw.ellipse(s, (36, 30, 26, 200), (cx + 4, cy - 2, 26, 14))
    if platform:
        pl = pygame.Rect(0, 0, 36, 14)
        pl.center = (cx, cy)
        pygame.draw.rect(s, (150, 112, 66), pl, border_radius=2)
        pygame.draw.rect(s, (80, 56, 32), pl, 2, border_radius=2)
        for x in range(pl.left + 4, pl.right, 6):
            pygame.draw.line(s, (100, 72, 42), (x, pl.top + 2), (x, pl.bottom - 2), 1)
    if cannon:
        pygame.draw.circle(s, (46, 44, 48), (cx - 6, cy), 8)
        pygame.draw.rect(s, (62, 62, 68), (cx - 6, cy - 4, 30, 8), border_radius=3)
        pygame.draw.circle(s, (30, 30, 34), (cx + 24, cy), 5)
    if lantern:
        pygame.draw.circle(s, (255, 214, 110), (W - 14, 12), 4)
        pygame.draw.circle(s, (120, 80, 30), (W - 14, 12), 4, 1)
    _wagon_cache[key] = s
    return s


def wagon_surface(hp_frac: float, reinforced: int, platform: bool, cannon: bool, lantern: bool,
                  destroyed: bool, tangent_angle: float) -> pygame.Surface:
    level = 0 if hp_frac > 0.75 else 1 if hp_frac > 0.5 else 2 if hp_frac > 0.25 else 3
    base = wagon_base(level, reinforced, platform, cannon, lantern, destroyed)
    deg = round(-math.degrees(tangent_angle) / 4) * 4
    key = (id(base), deg)
    r = _rot_cache.get(key)
    if r is None:
        r = pygame.transform.rotate(base, deg)
        _rot_cache[key] = r
    return r


# ---------------------------------------------------------------- personas
def draw_person(surf, x, y, group: str, cid: int, scale: float = 1.0, aim: float | None = None,
                hurt: bool = False, dead: bool = False, label_col=None, wounded: bool = False):
    sz = {"adulto": 7.5, "joven": 6.8, "niño": 5.0, "anciano": 7.0}.get(group, 7.0) * scale
    if dead:
        pygame.draw.ellipse(surf, (60, 40, 36), (x - sz, y - sz * 0.5, sz * 2, sz))
        return
    shirt = SHIRTS[cid % len(SHIRTS)]
    if hurt:
        shirt = (230, 90, 80)
    # sombra
    pygame.draw.ellipse(surf, (0, 0, 0, 60) if surf.get_flags() & pygame.SRCALPHA else (50, 70, 40),
                        (x - sz, y + sz * 0.3, sz * 2, sz * 0.9))
    if aim is not None:
        ex, ey = x + math.cos(aim) * (sz + 8 * scale), y + math.sin(aim) * (sz + 8 * scale)
        pygame.draw.line(surf, (60, 46, 34), (x, y), (ex, ey), max(1, int(2 * scale)))
        pygame.draw.line(surf, (190, 190, 200), (ex, ey), (x + math.cos(aim) * (sz + 11 * scale), y + math.sin(aim) * (sz + 11 * scale)), 1)
    pygame.draw.circle(surf, shirt, (int(x), int(y)), int(sz))
    pygame.draw.circle(surf, (40, 30, 24), (int(x), int(y)), int(sz), 1)
    hx, hy = x, y - sz * 0.25
    pygame.draw.circle(surf, SKIN, (int(hx), int(hy)), max(2, int(sz * 0.55)))
    if group == "adulto":
        pygame.draw.ellipse(surf, (70, 52, 36), (hx - sz * 0.8, hy - sz * 0.75, sz * 1.6, sz * 0.7))
    elif group == "anciano":
        pygame.draw.circle(surf, (225, 225, 225), (int(hx), int(hy - sz * 0.35)), max(1, int(sz * 0.4)))
    elif group == "joven":
        pygame.draw.arc(surf, (110, 76, 40), (hx - sz * 0.6, hy - sz * 0.7, sz * 1.2, sz * 1.0), 0, math.pi, 2)
    else:
        pygame.draw.circle(surf, (200, 150, 70), (int(hx), int(hy - sz * 0.35)), max(1, int(sz * 0.45)))
    if wounded:
        pygame.draw.line(surf, (220, 40, 40), (x - 3, y - sz - 5), (x + 3, y - sz - 5), 2)
        pygame.draw.line(surf, (220, 40, 40), (x, y - sz - 8), (x, y - sz - 2), 2)


def draw_foe(surf, f, x, y, scale, tribe_col, flash=False, ghost=False):
    k = f.kind
    s = scale
    col = (240, 240, 240) if flash else tribe_col
    face = f.face
    if ghost:
        pygame.draw.circle(surf, (160, 40, 40), (int(x), int(y)), max(2, int(3 * s)))
        return
    if k in ("jinete", "jefe"):
        L = 14 * s * (1.25 if k == "jefe" else 1.0)
        c, sn = math.cos(face), math.sin(face)
        # caballo
        horse = (110, 74, 44) if k == "jinete" else (30, 24, 22)
        pts = [(x + c * L - sn * 0, y + sn * L)]
        pygame.draw.ellipse(surf, (0, 0, 0, 50) if surf.get_flags() & pygame.SRCALPHA else (50, 70, 40),
                            (x - L * 0.9, y + 4 * s, L * 1.8, 6 * s))
        body = pygame.Surface((int(L * 2.6), int(L * 1.3)), pygame.SRCALPHA)
        bw, bh = body.get_size()
        pygame.draw.ellipse(body, horse, (int(bw * 0.12), int(bh * 0.2), int(bw * 0.72), int(bh * 0.6)))
        pygame.draw.ellipse(body, horse, (int(bw * 0.72), int(bh * 0.28), int(bw * 0.24), int(bh * 0.34)))
        pygame.draw.line(body, (50, 36, 26), (int(bw * 0.12), int(bh * 0.5)), (int(bw * 0.02), int(bh * 0.7)), 2)
        rb = pygame.transform.rotate(body, -math.degrees(face))
        surf.blit(rb, rb.get_rect(center=(int(x), int(y))))
        pygame.draw.circle(surf, col, (int(x), int(y - 2 * s)), max(3, int(4.5 * s)))
        pygame.draw.circle(surf, (205, 160, 120), (int(x), int(y - 5 * s)), max(2, int(3 * s)))
        if k == "jefe":
            for i in range(-3, 4):
                pygame.draw.line(surf, (240, 240, 230), (x, y - 6 * s), (x + i * 4 * s, y - 15 * s), 2)
                pygame.draw.circle(surf, (200, 40, 40), (int(x + i * 4 * s), int(y - 15 * s)), 2)
        else:
            pygame.draw.line(surf, (240, 240, 230), (x + 1, y - 6 * s), (x + 3 * s, y - 11 * s), 2)
        bx, by = x + math.cos(face + 1.2) * 8 * s, y + math.sin(face + 1.2) * 8 * s
        pygame.draw.line(surf, (92, 66, 40), (x, y), (bx, by), 1)
    else:
        r = 6.2 * s
        pygame.draw.ellipse(surf, (0, 0, 0, 50) if surf.get_flags() & pygame.SRCALPHA else (50, 70, 40),
                            (x - r, y + r * 0.3, r * 2, r))
        pygame.draw.circle(surf, col, (int(x), int(y)), int(r))
        pygame.draw.circle(surf, (50, 30, 24), (int(x), int(y)), int(r), 1)
        pygame.draw.circle(surf, (205, 160, 120), (int(x), int(y - r * 0.3)), max(2, int(r * 0.55)))
        pygame.draw.line(surf, (30, 30, 36), (x - r * 0.4, y - r * 0.2), (x + r * 0.4, y - r * 0.2), 1)
        if k == "guerrero":
            pygame.draw.line(surf, (110, 80, 50), (x + 3 * s, y + 6 * s), (x + 9 * s, y - 12 * s), 2)
            pygame.draw.polygon(surf, (200, 200, 205), [(x + 9 * s, y - 12 * s), (x + 11 * s, y - 16 * s), (x + 7 * s, y - 15 * s)])
            pygame.draw.line(surf, (230, 220, 200), (x, y - r), (x - 1, y - r - 5 * s), 2)
        elif k == "fuego":
            pygame.draw.arc(surf, (110, 80, 50), (x - 4 * s, y - 10 * s, 12 * s, 20 * s), -1.2, 1.2, 2)
            pygame.draw.circle(surf, (255, 140, 40), (int(x + 8 * s), int(y)), max(2, int(3 * s)))
            pygame.draw.circle(surf, (255, 220, 100), (int(x + 8 * s), int(y)), max(1, int(1.5 * s)))
        elif k == "bandido":
            pygame.draw.ellipse(surf, (50, 40, 36), (x - r, y - r * 1.1, r * 2, r * 0.8))
            pygame.draw.line(surf, (60, 50, 44), (x - 2 * s, y + 3 * s), (x + 12 * s, y - 3 * s), 2)


def draw_tent(surf, x, y, s=1.0, col=(214, 200, 168)):
    r = 15 * s
    pygame.draw.circle(surf, (0, 0, 0, 40) if surf.get_flags() & pygame.SRCALPHA else (60, 80, 50), (int(x + 3), int(y + 4)), int(r))
    pts = [(x, y - r * 0.9), (x + r, y + r * 0.7), (x - r, y + r * 0.7)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, (150, 134, 104), pts, 2)
    pygame.draw.line(surf, (150, 134, 104), (x, y - r * 0.9), (x, y + r * 0.7), 1)
    pygame.draw.polygon(surf, (70, 56, 40), [(x, y + r * 0.7), (x - 4 * s, y + r * 0.7), (x, y - 1 * s)])


def draw_ox(surf, x, y, s=1.0, angle=0.0):
    c, sn = math.cos(angle), math.sin(angle)
    pygame.draw.ellipse(surf, (96, 70, 48), (x - 11 * s, y - 6 * s, 22 * s, 12 * s))
    pygame.draw.circle(surf, (80, 58, 40), (int(x + c * 11 * s), int(y + sn * 11 * s)), int(5 * s))
    pygame.draw.line(surf, (235, 230, 215), (x + c * 13 * s, y + sn * 13 * s - 3), (x + c * 17 * s, y + sn * 17 * s - 6), 2)


def draw_fire(surf, x, y, t, s=1.0):
    flick = 1 + 0.15 * math.sin(t * 13) + 0.1 * math.sin(t * 7.3)
    for i in range(7):
        a = i * math.tau / 7
        pygame.draw.line(surf, (66, 44, 28), (x + math.cos(a) * 3 * s, y + math.sin(a) * 3 * s),
                         (x + math.cos(a) * 11 * s, y + math.sin(a) * 11 * s), max(1, int(3 * s)))
    for r, col in ((9, (230, 90, 30)), (6.5, (250, 160, 40)), (3.8, (255, 230, 120))):
        pygame.draw.circle(surf, col, (int(x), int(y)), max(1, int(r * s * flick)))


# ---------------------------------------------------------------- luz y partículas
def radial_light(radius: int, strength: int = 255) -> pygame.Surface:
    """Máscara de luz: alfa 255 en el borde (oscuridad total) y 0 en el centro (luz total)."""
    key = (radius, strength)
    if key in _light_cache:
        return _light_cache[key]
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    s.fill((255, 255, 255, 255))
    steps = max(12, min(48, radius // 3))
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        a = int(255 - strength * (1 - (i / steps)) ** 1.4)
        pygame.draw.circle(s, (255, 255, 255, a), (radius, radius), r)
    _light_cache[key] = s
    return s


class Particles:
    def __init__(self):
        self.items: list[list] = []  # [kind, x, y, vx, vy, life, max, size, color]

    def add(self, kind, x, y, n=1, **kw):
        rng = random
        for _ in range(n):
            if kind == "smoke":
                self.items.append([kind, x, y, rng.uniform(-8, 8), rng.uniform(-14, -4), 0, rng.uniform(0.8, 1.6), rng.uniform(4, 8), (210, 210, 210)])
            elif kind == "spark":
                a = rng.uniform(0, math.tau)
                v = rng.uniform(40, 120)
                self.items.append([kind, x, y, math.cos(a) * v, math.sin(a) * v, 0, rng.uniform(0.2, 0.5), 2, kw.get("color", (255, 220, 120))])
            elif kind == "dust":
                self.items.append([kind, x, y, rng.uniform(-18, 18), rng.uniform(-18, 18), 0, rng.uniform(0.5, 1.1), rng.uniform(4, 9), (190, 170, 130)])
            elif kind == "fire":
                self.items.append([kind, x + rng.uniform(-8, 8), y + rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-40, -18), 0, rng.uniform(0.4, 0.9), rng.uniform(3, 6), (255, 150, 40)])
            elif kind == "ember":
                self.items.append([kind, x, y, rng.uniform(-20, 20), rng.uniform(-60, -20), 0, rng.uniform(0.6, 1.4), 2, (255, 190, 90)])
            elif kind == "ring":
                self.items.append([kind, x, y, 0, 0, 0, 0.5, 6, kw.get("color", (255, 255, 255))])

    def update(self, dt):
        for p in self.items:
            p[5] += dt
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            if p[0] in ("smoke", "dust"):
                p[7] += dt * 8
            if p[0] == "ring":
                p[7] += dt * 120
        self.items = [p for p in self.items if p[5] < p[6]][-900:]

    def draw(self, surf, cam):
        if not self.items:
            return
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for kind, x, y, vx, vy, t, mx, size, col in self.items:
            sx, sy = cam(x, y)
            k = 1 - t / mx
            if kind in ("smoke", "dust"):
                pygame.draw.circle(layer, col + (int(120 * k * (0.7 if kind == "dust" else 1)),), (int(sx), int(sy)), int(size * cam.s))
            elif kind == "ring":
                pygame.draw.circle(layer, col + (int(220 * k),), (int(sx), int(sy)), int(size * cam.s), 2)
            else:
                pygame.draw.circle(layer, col + (int(255 * k),), (int(sx), int(sy)), max(1, int(size * cam.s * (0.5 + k))))
        surf.blit(layer, (0, 0))


# ---------------------------------------------------------------- retratos para cutscenes
PORTRAIT_STYLES = {
    # hair color, style, hat, beard, shirt
    "esposa": ((96, 64, 42), "bun", "bonnet", None, (96, 120, 150)),
    "hijo": ((120, 80, 46), "messy", "cap", None, (150, 90, 60)),
    "hija": ((140, 96, 54), "braids", "ribbon", None, (190, 120, 130)),
    "abuelo": ((226, 226, 226), "white", "hat", "full", (96, 96, 104)),
    "tomas": ((40, 32, 28), "short", "hat", "full", (110, 80, 60)),
    "ruth": ((120, 90, 60), "bun", "bonnet", None, (70, 70, 90)),
    "ada": ((200, 160, 90), "braids", "ribbon", None, (170, 190, 140)),
    "silas": ((70, 56, 44), "short", "hat", "stubble", (80, 90, 70)),
    "mary": ((90, 60, 40), "braids", "hat", None, (120, 110, 70)),
    "josiah": ((70, 50, 36), "short", "none", "stubble", (130, 100, 70)),
    "hannah": ((110, 76, 50), "bun", "none", None, (120, 140, 120)),
    "lucas": ((150, 110, 60), "messy", "none", None, (140, 140, 160)),
    "emma": ((170, 120, 70), "braids", "none", None, (160, 120, 150)),
    "medico": ((60, 50, 44), "short", "none", "stubble", (60, 64, 76)),
    "cazadora": ((80, 56, 40), "braids", "hat", None, (110, 96, 60)),
    "herrero": ((60, 40, 30), "bald", "none", "full", (88, 70, 60)),
    "predicador": ((190, 190, 190), "white", "none", None, (30, 30, 36)),
    "mercenario": ((40, 36, 34), "short", "hat", "stubble", (60, 50, 50)),
    "traductora": ((50, 36, 30), "braids", "none", None, (150, 90, 70)),
    "gemelos": ((110, 76, 44), "messy", "cap", None, (130, 110, 100)),
    "partera": ((70, 50, 40), "bun", "bonnet", None, (110, 80, 90)),
    "carretero": ((100, 70, 40), "short", "hat", "stubble", (120, 100, 70)),
    "viuda": ((60, 50, 44), "bun", "bonnet", None, (40, 40, 48)),
}
SKINS = [(224, 186, 152), (206, 160, 124), (186, 138, 104), (232, 196, 164)]


def _style_for(role: str, cid: int = 0, group: str = "adulto"):
    base = role.split("_")[0]
    if base in PORTRAIT_STYLES:
        return PORTRAIT_STYLES[base]
    hair = [(60, 44, 34), (120, 84, 50), (170, 130, 76), (40, 34, 30)][cid % 4]
    return (hair, ["short", "bun", "messy", "braids"][cid % 4], ["hat", "none", "cap", "bonnet"][cid % 4],
            "stubble" if cid % 3 == 0 and group == "adulto" else None, SHIRTS[cid % len(SHIRTS)])


def draw_portrait(surf, cx, base_y, height, role: str, group="adulto", cid=0, mood="neutral",
                  speaking=False, t=0.0, dim=False, back=False):
    """Busto procedural. `back=True` dibuja una silueta de espaldas (para el protagonista, sin rostro)."""
    scale = height / 360.0
    if group == "niño":
        scale *= 0.74
    elif group == "anciano":
        scale *= 0.94
    W, H = int(380 * scale), int(400 * scale)
    pic = pygame.Surface((W, H), pygame.SRCALPHA)
    mx = W // 2
    by = H - 2
    hair, hstyle, hat, beard, shirt = _style_for(role, cid, group)
    skin = SKINS[(cid + len(role)) % len(SKINS)]
    k = scale

    def E(x, y, w, h, col, width=0):
        pygame.draw.ellipse(pic, col, (mx + x * k - w * k / 2, by + y * k - h * k / 2, w * k, h * k), max(0, int(width * k)))

    def R(x, y, w, h, col, rad=0):
        pygame.draw.rect(pic, col, (mx + x * k, by + y * k, w * k, h * k), border_radius=int(rad * k))

    def L(x1, y1, x2, y2, col, w=2):
        pygame.draw.line(pic, col, (mx + x1 * k, by + y1 * k), (mx + x2 * k, by + y2 * k), max(1, int(w * k)))

    # cuerpo
    E(0, 10, 300, 190, tuple(max(0, c - 28) for c in shirt))
    E(0, 6, 290, 175, shirt)
    # cuello y cabeza
    head_y = -205
    if back:
        E(0, head_y, 120, 130, (50, 40, 36))
        E(0, head_y - 52, 150, 38, (34, 26, 22))   # ala del sombrero
        E(0, head_y - 70, 90, 60, (40, 32, 28))
        E(0, 6, 290, 175, (36, 40, 52))
        out = pic
    else:
        R(-24, head_y + 52, 48, 60, tuple(max(0, c - 22) for c in skin))
        # pelo (detrás)
        if hstyle in ("white", "messy"):
            E(0, head_y - 4, 128, 140, hair)
        if hstyle == "braids":
            for sx in (-1, 1):
                L(sx * 46, head_y + 20, sx * 52, head_y + 100, hair, 12)
                E(sx * 52, head_y + 104, 14, 14, (200, 90, 90))
        if hstyle == "bun":
            E(0, head_y - 66, 52, 44, hair)
        E(0, head_y, 106, 126, skin)
        E(-52, head_y + 6, 16, 28, skin)
        E(52, head_y + 6, 16, 28, skin)
        # flequillo
        if hstyle in ("short", "bun", "braids"):
            E(0, head_y - 40, 106, 50, hair)
        elif hstyle in ("messy", "white"):
            E(-20, head_y - 46, 54, 36, hair)
            E(24, head_y - 44, 50, 34, hair)
        if beard == "full":
            pygame.draw.ellipse(pic, hair, (mx - 46 * k, by + (head_y + 14) * k, 92 * k, 82 * k))
            E(0, head_y + 20, 70, 36, skin)
        elif beard == "stubble":
            col_s = tuple(int(skin[i] * 0.62 + hair[i] * 0.38) for i in range(3))
            pic.set_clip(pygame.Rect(0, int(by + (head_y + 14) * k), W, int(80 * k)))
            E(0, head_y, 106, 126, col_s)
            pic.set_clip(None)
        # sombrero / gorro
        if hat == "hat":
            E(0, head_y - 50, 170, 28, (66, 46, 32))
            E(0, head_y - 72, 90, 56, (80, 58, 40))
            R(-45, head_y - 66, 90, 10, (40, 28, 20))
        elif hat == "cap":
            E(0, head_y - 52, 112, 56, (90, 100, 120))
            E(30, head_y - 38, 60, 14, (70, 80, 96))
        elif hat == "bonnet":
            E(0, head_y - 22, 130, 118, (236, 228, 208), 0)
            E(0, head_y + 2, 100, 112, skin)
            E(0, head_y - 40, 104, 44, hair if hstyle != "white" else (230, 230, 230))
        elif hat == "ribbon":
            E(0, head_y - 62, 22, 18, (200, 90, 100))
        # ojos y cejas
        blink = (int(t * 1.7 + cid) % 5 == 0) and (t * 1.7 % 1 < 0.12)
        ey = head_y - 4
        for sx in (-1, 1):
            if blink:
                L(sx * 24 - 9, ey, sx * 24 + 9, ey, (40, 28, 24), 3)
            else:
                E(sx * 24, ey, 20, 14, (250, 248, 240))
                E(sx * 24 + (3 if mood != "miedo" else 0), ey + (1 if mood == "triste" else 0), 9, 9, (50, 38, 30))
            by0 = ey - 18
            ex = sx * 24
            brow = (50, 34, 26)
            if mood == "enojado":
                p1, p2 = ((ex - 12, by0 - 3), (ex + 12, by0 + 5)) if sx < 0 else ((ex - 12, by0 + 5), (ex + 12, by0 - 3))
            elif mood == "triste":
                p1, p2 = ((ex - 12, by0 + 4), (ex + 12, by0 - 4)) if sx < 0 else ((ex - 12, by0 - 4), (ex + 12, by0 + 4))
            elif mood == "miedo":
                p1, p2 = (ex - 12, by0 - 6), (ex + 12, by0 - 6)
            elif mood in ("alegre", "risa"):
                p1, p2 = ((ex - 12, by0 + 1), (ex + 12, by0 - 3)) if sx > 0 else ((ex - 12, by0 - 3), (ex + 12, by0 + 1))
            else:
                p1, p2 = (ex - 12, by0), (ex + 12, by0)
            L(p1[0], p1[1], p2[0], p2[1], brow, 4 if mood == "enojado" else 3)
        L(-2, ey + 6, 4, ey + 30, tuple(max(0, c - 40) for c in skin), 3)
        # boca
        my = head_y + 40
        opening = speaking and (int(t * 9) % 3 != 0)
        if mood in ("alegre", "risa"):
            pygame.draw.arc(pic, (110, 50, 44), (mx - 20 * k, by + (my - 12) * k, 40 * k, 26 * k), math.pi, 2 * math.pi, max(1, int(3 * k)))
            if mood == "risa" or opening:
                E(0, my + 4, 22, 12, (90, 30, 30))
        elif mood == "triste":
            pygame.draw.arc(pic, (110, 50, 44), (mx - 16 * k, by + (my - 2) * k, 32 * k, 20 * k), 0, math.pi, max(1, int(3 * k)))
        elif mood == "miedo":
            E(0, my + 4, 18, 22, (90, 30, 30))
        elif mood == "enojado":
            L(-16, my + 2, 16, my - 2, (110, 50, 44), 4)
        else:
            if opening:
                E(0, my + 2, 22, 12, (90, 30, 30))
            else:
                L(-14, my + 2, 14, my + 2, (110, 50, 44), 3)
        # cicatriz del mercenario / Silas
        if role.split("_")[0] in ("silas", "mercenario"):
            L(24, head_y - 20, 38, head_y + 18, (170, 90, 80), 3)
        if role.split("_")[0] == "medico":
            for sx in (-1, 1):
                E(sx * 24, ey, 30, 24, (0, 0, 0, 0), 3)
            L(-9, ey, 9, ey, (60, 50, 40), 2)
        if role.split("_")[0] == "predicador":
            R(-18, head_y + 62, 36, 14, (240, 240, 240), 3)
        out = pic
    if dim:
        shade = pygame.Surface(out.get_size(), pygame.SRCALPHA)
        shade.fill((120, 120, 140, 255))
        out = out.copy()
        out.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    bob = int(math.sin(t * 2.2 + cid) * 2 * k + (3 * k if speaking and not dim else 0) * (0.5 + 0.5 * math.sin(t * 8)))
    surf.blit(out, out.get_rect(midbottom=(int(cx), int(base_y + bob))))
