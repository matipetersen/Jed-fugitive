"""Utilidades de interfaz: fuentes, paneles, botones, barras e iconos."""
from __future__ import annotations

import math
from typing import Callable, Optional

import pygame

from . import sfx

W, H = 1280, 720
TOUCH = False  # modo táctil: objetivos de toque más grandes, sin depender de hover/clic derecho/teclado

C = dict(
    bg=(26, 20, 15), panel=(52, 38, 26), panel2=(70, 52, 36), edge=(120, 90, 54), gold=(238, 192, 96),
    text=(240, 228, 200), dim=(170, 154, 124), red=(214, 80, 62), green=(120, 184, 100), blue=(110, 160, 220),
    parch=(226, 208, 164), parch_dark=(170, 144, 100), ink=(54, 38, 24), black=(0, 0, 0), white=(255, 255, 255),
    orange=(238, 140, 60),
)

_fonts: dict = {}


def font(size: int, bold: bool = False, serif: bool = False) -> pygame.font.Font:
    key = (size, bold, serif)
    f = _fonts.get(key)
    if f is None:
        names = "georgia,dejavuserif,timesnewroman,liberationserif,freeserif" if serif else \
            "segoeui,helveticaneue,arial,dejavusans,liberationsans,freesans"
        try:
            path = pygame.font.match_font(names, bold=bold)
            f = pygame.font.Font(path, size) if path else pygame.font.Font(None, int(size * 1.15))
        except Exception:
            f = pygame.font.Font(None, int(size * 1.15))
        _fonts[key] = f
    return f


def text(surf, s, pos, size=18, color=None, bold=False, serif=False, anchor="topleft", shadow=False, alpha=None):
    color = color or C["text"]
    f = font(size, bold, serif)
    img = f.render(str(s), True, color)
    if alpha is not None:
        img.set_alpha(alpha)
    r = img.get_rect()
    setattr(r, anchor, pos)
    if shadow:
        sh = f.render(str(s), True, (0, 0, 0))
        sh.set_alpha(150)
        surf.blit(sh, (r.x + 1, r.y + 2))
    surf.blit(img, r)
    return r


def wrap(s: str, size: int, width: int, bold=False, serif=False) -> list:
    f = font(size, bold, serif)
    lines = []
    for para in str(s).split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.size(t)[0] <= width:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def para(surf, s, pos, width, size=18, color=None, bold=False, serif=False, gap=3, max_lines=None) -> int:
    color = color or C["text"]
    lines = wrap(s, size, width, bold, serif)
    if max_lines:
        lines = lines[:max_lines]
    y = pos[1]
    f = font(size, bold, serif)
    for ln in lines:
        surf.blit(f.render(ln, True, color), (pos[0], y))
        y += f.get_linesize() + gap
    return y


def panel(surf, rect, fill=None, edge=None, radius=8, alpha=None, width=2):
    rect = pygame.Rect(rect)
    fill = fill or C["panel"]
    edge = edge or C["edge"]
    if alpha is not None:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, tuple(fill) + (alpha,), s.get_rect(), border_radius=radius)
        pygame.draw.rect(s, tuple(edge) + (min(255, alpha + 40),), s.get_rect(), width, border_radius=radius)
        surf.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surf, fill, rect, border_radius=radius)
        pygame.draw.rect(surf, edge, rect, width, border_radius=radius)


def bar(surf, rect, frac, color, back=(30, 22, 16), border=True):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=3)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        pygame.draw.rect(surf, color, (rect.x, rect.y, max(2, int(rect.w * frac)), rect.h), border_radius=3)
    if border:
        pygame.draw.rect(surf, (0, 0, 0), rect, 1, border_radius=3)


class Button:
    def __init__(self, rect, label, on_click: Callable[[], None], enabled=True, hint="", size=18,
                 color=None, key=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.enabled = enabled
        self.hint = hint
        self.size = size
        self.color = color
        self.key = key
        self.hover = False
        self.selected = False

    def handle(self, ev) -> bool:
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            if self.enabled:
                sfx.play("click", 0.6, 0.03)
                self.on_click()
            return True
        elif ev.type == pygame.KEYDOWN and self.key is not None and ev.key == self.key and self.enabled:
            sfx.play("click", 0.6, 0.03)
            self.on_click()
            return True
        return False

    def draw(self, surf):
        base = self.color or C["panel2"]
        if not self.enabled:
            fill, edge, tc = (44, 36, 28), (80, 66, 46), (110, 98, 80)
        else:
            fill = tuple(min(255, c + 22) for c in base) if self.hover else base
            edge = C["gold"] if (self.hover or self.selected) else C["edge"]
            tc = C["text"]
        pygame.draw.rect(surf, fill, self.rect, border_radius=7)
        pygame.draw.rect(surf, edge, self.rect, 2, border_radius=7)
        if self.selected:
            pygame.draw.rect(surf, C["gold"], self.rect.inflate(-6, -6), 1, border_radius=5)
        f = font(self.size)
        lines = wrap(self.label, self.size, self.rect.w - 14)
        total = len(lines) * f.get_linesize()
        y = self.rect.centery - total // 2
        for ln in lines[:3]:
            img = f.render(ln, True, tc)
            surf.blit(img, (self.rect.centerx - img.get_width() // 2, y))
            y += f.get_linesize()


class Tooltip:
    text: str = ""
    pos = (0, 0)


def draw_tooltip(surf, s, pos):
    if not s:
        return
    lines = wrap(s, 15, 260)
    w = max(font(15).size(l)[0] for l in lines) + 14
    h = len(lines) * (font(15).get_linesize() + 1) + 10
    x = min(pos[0] + 14, W - w - 6)
    y = min(pos[1] + 18, H - h - 6)
    panel(surf, (x, y, w, h), (30, 22, 16), C["gold"], 5, alpha=235, width=1)
    yy = y + 5
    for ln in lines:
        surf.blit(font(15).render(ln, True, C["text"]), (x + 7, yy))
        yy += font(15).get_linesize() + 1


# ---------------------------------------------------------------- iconos
def icon(surf, kind: str, x: int, y: int, size: int = 20):
    r = size // 2
    if kind == "food":
        pygame.draw.circle(surf, (190, 120, 70), (x, y), r)
        pygame.draw.circle(surf, (230, 170, 110), (x - r // 3, y - r // 3), r // 3)
        pygame.draw.circle(surf, (110, 60, 36), (x, y), r, 2)
    elif kind == "ammo":
        pygame.draw.rect(surf, (200, 160, 70), (x - r // 2, y - r, r, r * 2), border_radius=2)
        pygame.draw.polygon(surf, (150, 110, 60), [(x - r // 2, y - r), (x + r // 2, y - r), (x, y - r - r // 2)])
        pygame.draw.rect(surf, (80, 60, 30), (x - r // 2, y - r, r, r * 2), 1, border_radius=2)
    elif kind == "goods":
        pygame.draw.rect(surf, (150, 110, 70), (x - r, y - r // 2, r * 2, r + r // 2), border_radius=2)
        pygame.draw.line(surf, (230, 200, 120), (x - r, y), (x + r, y), 2)
        pygame.draw.line(surf, (230, 200, 120), (x, y - r // 2), (x, y + r), 2)
    elif kind == "parts":
        pygame.draw.circle(surf, (150, 150, 160), (x, y), r, 3)
        pygame.draw.circle(surf, (150, 150, 160), (x, y), r // 3)
        for a in range(0, 360, 60):
            pygame.draw.line(surf, (150, 150, 160), (x, y), (x + math.cos(math.radians(a)) * r, y + math.sin(math.radians(a)) * r), 1)
    elif kind == "medicine":
        pygame.draw.rect(surf, (235, 235, 235), (x - r, y - r, r * 2, r * 2), border_radius=3)
        pygame.draw.rect(surf, (210, 50, 50), (x - r // 4, y - r + 3, r // 2, r * 2 - 6))
        pygame.draw.rect(surf, (210, 50, 50), (x - r + 3, y - r // 4, r * 2 - 6, r // 2))
    elif kind == "oxen":
        pygame.draw.ellipse(surf, (110, 80, 54), (x - r, y - r // 2, r * 2, r))
        pygame.draw.circle(surf, (90, 64, 42), (x + r, y), r // 2)
        pygame.draw.line(surf, (240, 236, 220), (x + r, y - r // 3), (x + r + 4, y - r // 2 - 4), 2)
        pygame.draw.line(surf, (240, 236, 220), (x + r, y - r // 3), (x + r - 3, y - r // 2 - 4), 2)
    elif kind == "money":
        pygame.draw.circle(surf, (240, 200, 80), (x, y), r)
        pygame.draw.circle(surf, (170, 130, 40), (x, y), r, 2)
        text(surf, "$", (x, y), max(12, size - 6), (110, 80, 20), bold=True, anchor="center")
    elif kind == "morale":
        pygame.draw.circle(surf, (240, 200, 90), (x, y), r)
        pygame.draw.circle(surf, (90, 60, 20), (x - r // 3, y - r // 4), 2)
        pygame.draw.circle(surf, (90, 60, 20), (x + r // 3, y - r // 4), 2)
        pygame.draw.arc(surf, (90, 60, 20), (x - r // 2, y - r // 4, r, r), math.pi * 1.1, math.pi * 1.9, 2)
    elif kind == "wagon":
        pygame.draw.rect(surf, (230, 220, 190), (x - r, y - r // 2, r * 2, r), border_radius=r // 2)
        pygame.draw.circle(surf, (50, 36, 26), (x - r // 2, y + r // 2), r // 3)
        pygame.draw.circle(surf, (50, 36, 26), (x + r // 2, y + r // 2), r // 3)
    elif kind == "person":
        pygame.draw.circle(surf, (222, 184, 150), (x, y - r // 2), r // 2)
        pygame.draw.ellipse(surf, (110, 140, 190), (x - r // 2, y, r, r))
    elif kind == "cannon":
        pygame.draw.rect(surf, (80, 80, 90), (x - r, y - r // 3, r * 2, r // 1.5), border_radius=3)
        pygame.draw.circle(surf, (50, 50, 56), (x - r // 2, y + r // 3), r // 2)
    elif kind == "sun":
        pygame.draw.circle(surf, (250, 210, 80), (x, y), r // 2 + 1)
        for a in range(0, 360, 45):
            pygame.draw.line(surf, (250, 210, 80), (x + math.cos(math.radians(a)) * (r // 2 + 3), y + math.sin(math.radians(a)) * (r // 2 + 3)),
                             (x + math.cos(math.radians(a)) * r, y + math.sin(math.radians(a)) * r), 2)
    elif kind == "rain":
        pygame.draw.ellipse(surf, (170, 180, 195), (x - r, y - r, r * 2, r))
        for dx in (-r // 2, 0, r // 2):
            pygame.draw.line(surf, (110, 160, 230), (x + dx, y + 1), (x + dx - 2, y + r - 1), 2)
    elif kind == "snow":
        for a in range(0, 180, 60):
            pygame.draw.line(surf, (220, 235, 255), (x + math.cos(math.radians(a)) * r, y + math.sin(math.radians(a)) * r),
                             (x - math.cos(math.radians(a)) * r, y - math.sin(math.radians(a)) * r), 2)
    elif kind == "storm":
        pygame.draw.ellipse(surf, (110, 114, 130), (x - r, y - r, r * 2, r))
        pygame.draw.polygon(surf, (250, 230, 90), [(x, y - 2), (x - 4, y + 4), (x, y + 3), (x - 2, y + r), (x + 5, y + 1), (x + 1, y + 2)])
    else:
        pygame.draw.circle(surf, C["dim"], (x, y), r, 2)


def vgradient(surf, rect, top, bottom):
    rect = pygame.Rect(rect)
    h = max(1, rect.h)
    for i in range(h):
        k = i / h
        col = tuple(int(top[j] + (bottom[j] - top[j]) * k) for j in range(3))
        pygame.draw.line(surf, col, (rect.x, rect.y + i), (rect.right - 1, rect.y + i))
