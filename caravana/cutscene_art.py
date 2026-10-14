"""Fondos procedurales para las cutscenes."""
from __future__ import annotations

import math
import random

import pygame

from . import art

SW, SH = 1280, 720
BW = 1400  # ancho del fondo estático: permite un travelling lento


def _grad(s, rect, top, bot):
    r = pygame.Rect(rect)
    for i in range(r.h):
        k = i / max(1, r.h - 1)
        pygame.draw.line(s, tuple(int(top[j] + (bot[j] - top[j]) * k) for j in range(3)), (r.x, r.y + i), (r.right - 1, r.y + i))


def _hills(s, base, amp, freq, col, seed=0, y0=0):
    pts = [(0, SH)]
    for x in range(0, BW + 8, 8):
        y = base + math.sin(x * freq + seed) * amp + math.sin(x * freq * 2.3 + seed * 2) * amp * 0.4
        pts.append((x, y))
    pts.append((BW, SH))
    pygame.draw.polygon(s, col, pts)


def _stars(s, n, seed, h):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(0, BW), rng.randint(0, h)
        b = rng.randint(150, 255)
        s.set_at((x, y), (b, b, b))
        if rng.random() < 0.15:
            pygame.draw.circle(s, (b, b, b - 20), (x, y), 1)


def _pine(s, x, y, h, col=(26, 56, 40)):
    w = h * 0.45
    for i in range(4):
        yy = y - h + i * h * 0.22
        ww = w * (0.35 + i * 0.22)
        pygame.draw.polygon(s, col, [(x, yy), (x - ww, yy + h * 0.32), (x + ww, yy + h * 0.32)])
    pygame.draw.rect(s, (50, 36, 26), (x - 3, y - 4, 6, 10))


def _wagon_sil(s, x, y, sc, col=(24, 20, 20)):
    pygame.draw.rect(s, col, (x - 40 * sc, y - 30 * sc, 80 * sc, 22 * sc), border_radius=3)
    pts = [(x - 38 * sc, y - 30 * sc)]
    for a in range(0, 181, 15):
        r = math.radians(a)
        pts.append((x - math.cos(r) * 38 * sc, y - 30 * sc - math.sin(r) * 30 * sc))
    pygame.draw.polygon(s, col, pts)
    pygame.draw.circle(s, col, (x - 20 * sc, y - 6 * sc), 13 * sc)
    pygame.draw.circle(s, col, (x + 20 * sc, y - 6 * sc), 11 * sc)


def _build(key: str) -> pygame.Surface:
    s = pygame.Surface((BW, SH))
    rng = random.Random(sum(map(ord, key)))
    if key == "alba":
        _grad(s, (0, 0, BW, SH), (38, 34, 84), (250, 170, 104))
        pygame.draw.circle(s, (255, 226, 150), (780, 430), 70)
        _hills(s, 470, 14, 0.004, (86, 60, 80), 1)
        # pueblo
        for i in range(14):
            x = 120 + i * 46
            h = rng.randint(34, 80)
            pygame.draw.rect(s, (50, 34, 46), (x, 520 - h, 36, h))
            pygame.draw.polygon(s, (60, 40, 50), [(x - 4, 520 - h), (x + 18, 520 - h - 20), (x + 40, 520 - h)])
        pygame.draw.rect(s, (46, 30, 42), (330, 360, 24, 160))
        pygame.draw.polygon(s, (46, 30, 42), [(324, 360), (342, 320), (360, 360)])
        _hills(s, 540, 8, 0.006, (44, 54, 52), 3)
        pygame.draw.rect(s, (34, 44, 42), (0, 560, BW, SH))
        pygame.draw.rect(s, (96, 74, 56), (0, 640, BW, 40))
        for i in range(7):
            _wagon_sil(s, 700 + i * 90, 650, 1.0)
    elif key == "noche":
        _grad(s, (0, 0, BW, SH), (6, 8, 26), (22, 26, 56))
        _stars(s, 260, 3, 380)
        pygame.draw.circle(s, (230, 232, 215), (1040, 140), 32)
        pygame.draw.circle(s, (6, 8, 26), (1054, 130), 28)
        _hills(s, 470, 22, 0.005, (14, 20, 28), 2)
        pygame.draw.rect(s, (14, 22, 22), (0, 520, BW, SH))
        for i, x in enumerate((140, 330, 560, 880, 1110, 1290)):
            _wagon_sil(s, x, 560 + (i % 2) * 14, 1.3 if i % 2 else 1.1, (10, 12, 14))
        for x in (460, 1000):
            pygame.draw.polygon(s, (12, 14, 18), [(x, 470), (x - 54, 560), (x + 54, 560)])
    elif key == "dia":
        _grad(s, (0, 0, BW, SH), (96, 150, 220), (200, 220, 236))
        for i in range(6):
            x, y = rng.randint(0, BW), rng.randint(40, 200)
            for j in range(4):
                pygame.draw.ellipse(s, (246, 248, 252), (x + j * 34, y + (j % 2) * 8, 100, 36))
        _hills(s, 430, 26, 0.004, (92, 130, 100), 5)
        _hills(s, 480, 18, 0.007, (110, 150, 92), 9)
        pygame.draw.rect(s, (110, 150, 84), (0, 520, BW, SH))
        pygame.draw.rect(s, (160, 128, 90), (0, 620, BW, 36))
    elif key == "rio":
        _grad(s, (0, 0, BW, SH), (110, 160, 224), (208, 224, 236))
        _hills(s, 410, 20, 0.004, (96, 128, 96), 4)
        pygame.draw.rect(s, (96, 140, 90), (0, 440, BW, SH))
        pygame.draw.polygon(s, (66, 120, 186), [(0, 520), (BW, 500), (BW, 600), (0, 640)])
        for i in range(60):
            x, y = rng.randint(0, BW), rng.randint(530, 620)
            pygame.draw.line(s, (180, 214, 244), (x, y), (x + rng.randint(14, 40), y), 1)
        for x in (90, 1210, 1330):
            pygame.draw.line(s, (70, 50, 36), (x, 520), (x + 6, 380), 8)
            for k in range(7):
                pygame.draw.line(s, (60, 110, 60), (x + 6, 390), (x + 6 + rng.randint(-110, 110), 500), 3)
    elif key == "roca":
        _grad(s, (0, 0, BW, SH), (216, 154, 100), (250, 214, 160))
        _hills(s, 470, 14, 0.004, (150, 126, 90), 3)
        pygame.draw.rect(s, (156, 134, 92), (0, 520, BW, SH))
        pygame.draw.polygon(s, (170, 140, 104), [(780, 540), (840, 160), (860, 150), (890, 300), (960, 540)])
        pygame.draw.polygon(s, (130, 104, 76), [(840, 160), (860, 150), (890, 300), (846, 300)])
        for i in range(24):
            x = rng.randint(0, BW)
            pygame.draw.circle(s, (130, 112, 80), (x, rng.randint(540, 700)), rng.randint(3, 8))
    elif key == "montana":
        _grad(s, (0, 0, BW, SH), (84, 120, 184), (216, 226, 240))
        pygame.draw.polygon(s, (126, 132, 152), [(0, 520), (260, 220), (460, 400), (700, 170), (980, 420), (1220, 240), (BW, 520)])
        for px, py in ((260, 220), (700, 170), (1220, 240)):
            pygame.draw.polygon(s, (244, 246, 252), [(px, py), (px - 60, py + 90), (px + 60, py + 90)])
        pygame.draw.rect(s, (60, 80, 70), (0, 520, BW, SH))
        for i in range(30):
            _pine(s, rng.randint(0, BW), rng.randint(560, 700), rng.randint(70, 140))
    elif key == "bosque":
        _grad(s, (0, 0, BW, SH), (24, 44, 40), (14, 30, 28))
        for i in range(60):
            _pine(s, rng.randint(0, BW), rng.randint(500, 700), rng.randint(180, 340), (14 + rng.randint(0, 14), 40 + rng.randint(0, 20), 34 + rng.randint(0, 14)))
        pygame.draw.rect(s, (30, 44, 30), (0, 640, BW, 80))
    elif key == "tienda":
        _grad(s, (0, 0, BW, SH), (62, 44, 30), (36, 24, 18))
        for i in range(0, BW, 70):
            pygame.draw.line(s, (50, 36, 26), (i, 0), (i - 90, SH), 3)
        pygame.draw.polygon(s, (92, 70, 50), [(0, 560), (BW, 560), (BW, SH), (0, SH)])
        pygame.draw.rect(s, (190, 170, 130), (180, 520, 480, 90), border_radius=22)
        pygame.draw.rect(s, (120, 100, 80), (180, 520, 480, 90), 4, border_radius=22)
        pygame.draw.rect(s, (80, 40, 40), (200, 510, 440, 40), border_radius=18)
    elif key == "fuerte":
        _grad(s, (0, 0, BW, SH), (110, 160, 224), (216, 226, 236))
        _hills(s, 420, 16, 0.004, (96, 130, 96), 6)
        pygame.draw.rect(s, (110, 146, 90), (0, 500, BW, SH))
        pygame.draw.rect(s, (112, 80, 48), (320, 280, 700, 240))
        for i in range(0, 700, 28):
            pygame.draw.line(s, (84, 58, 34), (320 + i, 280), (320 + i, 520), 2)
            pygame.draw.polygon(s, (112, 80, 48), [(318 + i, 280), (334 + i, 252), (350 + i, 280)])
        pygame.draw.rect(s, (36, 26, 20), (630, 380, 80, 140), border_radius=40)
        pygame.draw.line(s, (60, 40, 24), (940, 280), (940, 140), 5)
        pygame.draw.polygon(s, (200, 60, 50), [(940, 140), (1000, 156), (940, 174)])
    elif key == "bifurcacion":
        _grad(s, (0, 0, BW, SH), (130, 170, 224), (236, 232, 210))
        _hills(s, 430, 20, 0.004, (96, 130, 100), 7)
        _hills(s, 470, 14, 0.008, (70, 110, 80), 2)
        pygame.draw.rect(s, (96, 140, 90), (0, 520, BW, SH))
        pygame.draw.polygon(s, (66, 120, 186), [(900, 470), (BW, 440), (BW, 520), (1040, 540)])
        pygame.draw.line(s, (90, 62, 36), (560, 640), (560, 330), 10)
        for i, (lbl, dy, dx) in enumerate((("Willamette", 0, 1), ("Walla Walla", 56, -1), ("Columbia", 112, 1))):
            pts = [(560, 340 + dy), (560 + dx * 150, 340 + dy), (560 + dx * 172, 360 + dy), (560 + dx * 150, 380 + dy), (560, 380 + dy)]
            pygame.draw.polygon(s, (150, 112, 66), pts)
            pygame.draw.polygon(s, (70, 46, 26), pts, 2)
        pygame.draw.rect(s, (160, 128, 90), (0, 650, BW, 40))
    else:
        _grad(s, (0, 0, BW, SH), (30, 30, 40), (10, 10, 16))
    return s


class Backdrop:
    _cache: dict = {}

    def __init__(self, key: str):
        self.key = key
        if key not in Backdrop._cache:
            Backdrop._cache[key] = _build(key)
        self.surf = Backdrop._cache[key]
        self.motes = [[random.uniform(0, SW), random.uniform(0, SH), random.uniform(0.3, 1.0)] for _ in range(40)]

    def draw(self, screen, t: float, progress: float = 0.0):
        pan = int(-progress * 60 - math.sin(t * 0.2) * 6)
        screen.blit(self.surf, (max(-(BW - SW), min(0, pan)), 0))
        k = self.key
        if k in ("noche", "tienda"):
            self._fire(screen, t, (640, 600) if k == "noche" else (730, 330))
        if k == "alba":
            glow = pygame.Surface((SW, SH), pygame.SRCALPHA)
            for r, a in ((260, 26), (180, 36), (110, 46)):
                pygame.draw.circle(glow, (255, 210, 130, a), (780 + pan, 430), r)
            screen.blit(glow, (0, 0))
        if k == "rio":
            for i in range(14):
                x = (i * 117 + t * 30) % SW
                pygame.draw.line(screen, (200, 226, 250), (x, 540 + (i % 5) * 18), (x + 26, 540 + (i % 5) * 18), 2)
        if k in ("bosque", "montana"):
            for m in self.motes:
                m[0] = (m[0] + m[2] * 6 * 0.016 * 30) % SW
                m[1] = (m[1] + math.sin(t + m[0]) * 0.3) % SH
                pygame.draw.circle(screen, (200, 220, 190), (int(m[0]), int(m[1])), 1)
        if k == "montana":
            veil = pygame.Surface((SW, SH), pygame.SRCALPHA)
            veil.fill((220, 230, 250, 20 + int(14 * math.sin(t))))
            screen.blit(veil, (0, 0))

    @staticmethod
    def _fire(screen, t, pos):
        x, y = pos
        flick = 1 + 0.07 * math.sin(t * 13) + 0.05 * math.sin(t * 7.3)
        glow = pygame.Surface((SW, SH), pygame.SRCALPHA)
        for r, a in ((380, 22), (270, 28), (180, 36), (100, 52)):
            pygame.draw.circle(glow, (255, 150, 60, a), (x, y), int(r * flick))
        screen.blit(glow, (0, 0))
        art.draw_fire(screen, x, y, t, 3.2)
