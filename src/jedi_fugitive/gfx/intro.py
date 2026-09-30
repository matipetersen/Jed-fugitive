"""Opening cinematic: the chase in orbit, the burning descent, the crash, the dropships.

Everything is drawn procedurally with pygame primitives (no image assets).
It plays while the world is generated in the background and can be skipped
with any key. Timeline (seconds):

  0.0 - 4.8   orbit: your shuttle flees, Sith fighters strafe it, the hull is hit
  4.8 - 8.6   descent: a planet fills the view, the shuttle burns through the atmosphere
  8.6 - 11.0  impact: horizon at dusk, a streak, the flash, shockwave and debris
 11.0 - 14.5  aftermath: smoke rising, dropships with red running lights descend
"""
import math
import random

import pygame

from jedi_fugitive.gfx import theme

DURATION = 14.5

CAPTIONS = [
    (0.3, 4.6, "OUTER RIM. The purge left few Jedi alive. You are one of them."),
    (2.4, 4.6, "Sith fighters found your trail."),
    (5.0, 8.4, "Hull breach. Engines failing. The planet below is a Sith world."),
    (8.8, 10.9, "Impact."),
    (11.2, 14.4, "You live. But they saw you fall, and their dropships are already coming."),
]


class _P:
    __slots__ = ("x", "y", "vx", "vy", "life", "max", "col", "size", "grav")

    def __init__(self, x, y, vx, vy, life, col, size, grav=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max = life
        self.col, self.size, self.grav = col, size, grav


class Intro:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.done = False
        self.rng = random.Random(11)
        W, H = app.screen.get_size()
        self.stars = [(self.rng.random() * W, self.rng.random() * H, self.rng.choice((0.3, 0.6, 1.0))) for _ in range(260)]
        self.parts = []
        self.bolts = []
        self.next_bolt = 1.0
        self.hits = 0
        self.shake = 0.0
        self.flash = 0.0
        self.impact_done = False
        self._glows = {}
        self.font_caption = app.ui_font
        self.font_title = app.ui_font_big

    # ------------------------------------------------------------ helpers
    def skip(self):
        self.done = True

    def _emit(self, x, y, n, col, speed, life, size, spread=math.tau, base_ang=0.0, grav=0.0):
        for _ in range(n):
            a = base_ang + (self.rng.random() - 0.5) * spread
            v = speed * (0.3 + self.rng.random())
            self.parts.append(_P(x, y, math.cos(a) * v, math.sin(a) * v, life * (0.5 + self.rng.random()), col, size, grav))
        if len(self.parts) > 1500:
            self.parts = self.parts[-1500:]

    def _glow(self, surf, x, y, r, col, k=1.0):
        r = max(2, int(r))
        kq = max(1, min(8, int(round(k * 8))))
        key = (r, col, kq)
        g = self._glows.get(key)
        if g is None:
            g = pygame.Surface((r * 2, r * 2))
            g.fill((0, 0, 0))
            kk = kq / 8.0
            for i in range(10, 0, -1):
                pygame.draw.circle(g, theme.scale(col, kk * (1 - i / 10) ** 1.5), (r, r), max(1, int(r * i / 10)))
            if len(self._glows) > 2500:
                self._glows.clear()
            self._glows[key] = g
        surf.blit(g, (x - r, y - r), special_flags=pygame.BLEND_RGB_ADD)

    def _shuttle(self, surf, x, y, ang, scale, burning=0.0):
        pts = [(1.0, 0), (-0.7, -0.45), (-0.45, 0), (-0.7, 0.45)]
        ca, sa = math.cos(ang), math.sin(ang)
        poly = [(x + (px * ca - py * sa) * scale, y + (px * sa + py * ca) * scale) for px, py in pts]
        body = theme.mix((225, 230, 242), (255, 140, 60), burning)
        pygame.draw.polygon(surf, body, poly)
        pygame.draw.polygon(surf, (120, 130, 150), poly, 2)
        ex, ey = x - ca * 0.5 * scale, y - sa * 0.5 * scale
        self._glow(surf, ex, ey, scale * 0.6, (80, 170, 255) if burning < 0.5 else (255, 120, 40), 1.0)

    def _fighter(self, surf, x, y, s):
        pygame.draw.line(surf, (70, 72, 84), (x, y - s), (x, y + s), max(2, int(s * 0.25)))
        pygame.draw.circle(surf, (110, 112, 126), (int(x), int(y)), int(s * 0.35))
        pygame.draw.circle(surf, (255, 60, 70), (int(x + s * 0.2), int(y)), max(2, int(s * 0.1)))

    def _dropship(self, surf, x, y, s, blink):
        body = [(x - s, y), (x - s * 0.4, y - s * 0.35), (x + s * 0.4, y - s * 0.35), (x + s, y), (x + s * 0.3, y + s * 0.25), (x - s * 0.3, y + s * 0.25)]
        pygame.draw.polygon(surf, (36, 36, 44), body)
        pygame.draw.polygon(surf, (80, 80, 96), body, 1)
        if blink:
            self._glow(surf, x - s * 0.9, y, s * 0.35, (255, 40, 50), 1.0)
            self._glow(surf, x + s * 0.9, y, s * 0.35, (255, 40, 50), 1.0)
        self._glow(surf, x, y + s * 0.35, s * 0.6, (255, 150, 80), 0.6)

    def _caption(self, surf, W, H):
        for (t0, t1, text) in CAPTIONS:
            if t0 <= self.t <= t1:
                k = min(1.0, (self.t - t0) / 0.5, (t1 - self.t) / 0.5)
                n = int(len(text) * min(1.0, (self.t - t0) / max(0.4, len(text) * 0.03)))
                img = self.font_caption.render(text[:n], True, (235, 238, 250))
                img.set_alpha(int(255 * max(0.0, k)))
                bar = pygame.Surface((img.get_width() + 40, img.get_height() + 18), pygame.SRCALPHA)
                bar.fill((0, 0, 0, int(150 * max(0.0, k))))
                surf.blit(bar, ((W - bar.get_width()) // 2, H - 90))
                surf.blit(img, ((W - img.get_width()) // 2, H - 81))
                break
        hint = self.app.ui_font_small.render("any key to skip", True, (120, 126, 150))
        surf.blit(hint, (W - hint.get_width() - 16, H - 28))

    def _update_parts(self, surf, dt, ox, oy):
        keep = []
        for p in self.parts:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            k = p.life / p.max
            r = max(1, p.size * (0.5 + 0.5 * k))
            self._glow(surf, p.x + ox, p.y + oy, r * 2.2, p.col, k)
            keep.append(p)
        self.parts = keep

    # ----------------------------------------------------------- scenes
    def draw(self, dt):
        """Advance and draw one frame. Returns True while the cinematic runs."""
        if self.done:
            return False
        self.t += dt
        if self.t >= DURATION:
            self.done = True
            return False
        screen = self.app.screen
        W, H = screen.get_size()
        canvas = pygame.Surface((W, H))
        self.shake = max(0.0, self.shake - dt * 30)
        ox = self.rng.uniform(-1, 1) * self.shake
        oy = self.rng.uniform(-1, 1) * self.shake
        t = self.t
        if t < 4.8:
            self._orbit(canvas, W, H, t, dt)
        elif t < 8.6:
            self._descent(canvas, W, H, t - 4.8, dt)
        elif t < 11.0:
            self._impact(canvas, W, H, t - 8.6, dt)
        else:
            self._aftermath(canvas, W, H, t - 11.0, dt)
        self._update_parts(canvas, dt, 0, 0)
        screen.fill((0, 0, 0))
        screen.blit(canvas, (ox, oy))
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt * 2.0)
            f = pygame.Surface((W, H))
            f.fill((255, 250, 235))
            f.set_alpha(int(255 * min(1.0, self.flash)))
            screen.blit(f, (0, 0))
        # letterbox
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, W, int(H * 0.08)))
        pygame.draw.rect(screen, (0, 0, 0), (0, H - int(H * 0.08), W, int(H * 0.08)))
        fade = min(1.0, t / 0.8, (DURATION - t) / 0.8)
        if fade < 1:
            f = pygame.Surface((W, H))
            f.fill((0, 0, 0))
            f.set_alpha(int(255 * (1 - fade)))
            screen.blit(f, (0, 0))
        self._caption(screen, W, H)
        return True

    def _stars(self, c, W, H, speed):
        for i, (x, y, z) in enumerate(self.stars):
            x = (x - speed * z * self.t * 60) % W
            v = int(90 + 160 * z)
            c.fill((v, v, min(255, v + 25)), (x, y, 2 if z > 0.9 else 1, 1))

    def _orbit(self, c, W, H, t, dt):
        c.fill((4, 5, 12))
        self._stars(c, W, H, 3.0)
        sx, sy = W * 0.62 + math.sin(t * 1.3) * 30, H * 0.45 + math.sin(t * 2.1) * 24
        fighters = [(W * 0.2 + math.sin(t * 1.7 + i) * 40 + i * 60, H * (0.3 + 0.18 * i) + math.cos(t * 1.4 + i) * 30) for i in range(3)]
        self.next_bolt -= dt
        if self.next_bolt <= 0 and t > 0.8:
            self.next_bolt = 0.22
            fx, fy = self.rng.choice(fighters)
            self.bolts.append([fx, fy, sx, sy, 0.0])
        keep = []
        for b in self.bolts:
            b[4] += dt * 2.2
            if b[4] >= 1.0:
                if self.rng.random() < 0.45:
                    self.hits += 1
                    self.shake = min(10, self.shake + 5)
                    self._emit(sx, sy, 16, (255, 170, 80), 180, 0.5, 3)
                continue
            x = b[0] + (b[2] - b[0]) * b[4]
            y = b[1] + (b[3] - b[1]) * b[4]
            ang = math.atan2(b[3] - b[1], b[2] - b[0])
            pygame.draw.line(c, (255, 90, 90), (x, y), (x - math.cos(ang) * 26, y - math.sin(ang) * 26), 3)
            keep.append(b)
        self.bolts = keep
        if self.hits:
            self._emit(sx - 30, sy, 2, (110, 110, 120), 40, 1.2, 5, spread=0.8, base_ang=math.pi)
        self._shuttle(c, sx, sy, 0.0, 34)
        for fx, fy in fighters:
            self._fighter(c, fx, fy, 22)

    def _descent(self, c, W, H, t, dt):
        c.fill((5, 6, 14))
        self._stars(c, W, H, 0.8)
        k = t / 3.8
        # a shaded sphere rising from the bottom of the frame
        R = int(W * 0.75 * (1 + 0.5 * k))
        px, py = W // 2, int(H * 0.95 + R * 0.72 - k * H * 0.25)
        for i in range(14, 0, -1):
            pygame.draw.circle(c, theme.scale((255, 120, 70), 0.07 * (1 - i / 14)), (px, py), R + i * 7)
        steps = 18
        for i in range(steps):
            f = i / steps
            col = theme.mix((40, 26, 30), (150, 104, 80), f)
            rr = int(R * (1 - f * 0.55))
            cx = px - int(R * 0.25 * f)
            cy = py - int(R * 0.35 * f)
            pygame.draw.circle(c, col, (cx, cy), rr)
        ang = 0.55 + k * 0.5 + math.sin(t * 9) * 0.05 * k
        sx = W * (0.35 + k * 0.25)
        sy = H * (0.18 + k * 0.45)
        self._emit(sx, sy, 6, (255, 150, 60), 120, 0.7, 4, spread=0.6, base_ang=ang + math.pi)
        self._emit(sx, sy, 2, (90, 90, 100), 60, 1.4, 7, spread=0.8, base_ang=ang + math.pi)
        self._glow(c, sx, sy, 60 + 30 * k, (255, 110, 40), 0.8)
        self._shuttle(c, sx, sy, ang, 30 - 10 * k, burning=min(1.0, k * 1.5))
        self.shake = max(self.shake, 2 + 6 * k)

    def _impact(self, c, W, H, t, dt):
        horizon = int(H * 0.68)
        for y in range(H):
            if y < horizon:
                col = theme.mix((22, 16, 40), (190, 90, 60), y / horizon)
            else:
                col = theme.mix((40, 28, 26), (18, 12, 14), (y - horizon) / max(1, H - horizon))
            pygame.draw.line(c, col, (0, y), (W, y))
        rnd = random.Random(3)
        pts = [(0, horizon)]
        for i in range(12):
            pts.append((W * (i + 0.5) / 12, horizon - rnd.randint(20, 90)))
        pts += [(W, horizon), (W, horizon + 2), (0, horizon + 2)]
        pygame.draw.polygon(c, (30, 20, 30), pts)
        ix, iy = W * 0.58, horizon + 6
        if t < 0.9:
            k = t / 0.9
            sx, sy = W * 0.1 + (ix - W * 0.1) * k, H * 0.12 + (iy - H * 0.12) * k
            self._emit(sx, sy, 8, (255, 160, 70), 90, 0.5, 4)
            pygame.draw.line(c, (255, 200, 140), (sx, sy), (sx - 120 * (1 - k * 0.3), sy - 80), 4)
            self._glow(c, sx, sy, 50, (255, 130, 50), 1.0)
        elif not self.impact_done:
            self.impact_done = True
            self.flash = 0.9
            self.shake = 22
            self._emit(ix, iy, 140, (255, 170, 80), 420, 1.2, 4, spread=math.pi, base_ang=-math.pi / 2, grav=380)
            self._emit(ix, iy, 60, (120, 110, 110), 160, 2.4, 9, spread=math.pi, base_ang=-math.pi / 2)
        if self.impact_done:
            k = min(1.0, (t - 0.9) / 1.2)
            pygame.draw.ellipse(c, (255, 220, 170), (ix - 600 * k, iy - 40 * k, 1200 * k, 80 * k), 2)
            self._glow(c, ix, iy, 140 * (1 - k * 0.5), (255, 140, 60), 1 - k * 0.6)
            self._emit(ix, iy - 10, 1, (40, 38, 44), 50, 2.5, 12, spread=0.7, base_ang=-math.pi / 2)

    def _aftermath(self, c, W, H, t, dt):
        horizon = int(H * 0.68)
        for y in range(0, H, 2):
            if y < horizon:
                col = theme.mix((14, 10, 28), (120, 60, 50), y / horizon)
            else:
                col = (16, 11, 13)
            pygame.draw.rect(c, col, (0, y, W, 2))
        ix, iy = W * 0.58, horizon + 6
        self._glow(c, ix, iy, 70 + 8 * math.sin(t * 7), (255, 110, 40), 0.9)
        if self.rng.random() < 0.6:
            self._emit(ix, iy - 8, 1, (34, 32, 38), 40, 3.0, 12, spread=0.5, base_ang=-math.pi / 2)
        self._emit(ix, iy, 1, (200, 110, 50), 60, 0.5, 3, spread=1.2, base_ang=-math.pi / 2)
        # the ring of dropships closing in
        for i in range(5):
            a = i / 5.0
            x0 = W * (0.05 + 0.9 * a)
            y0 = -60 + (H * 0.42 + 40 * math.sin(i)) * min(1.0, t / (2.6 + 0.3 * i))
            s = 26 + 8 * (i % 2)
            self._dropship(c, x0, y0, s, blink=int(t * 3 + i) % 2 == 0)
            # searchlights sweeping the ground
            beam = pygame.Surface((W, H), pygame.SRCALPHA)
            tx = ix + math.sin(t * 1.3 + i * 1.7) * 220
            pygame.draw.polygon(beam, (255, 240, 200, 26), [(x0 - 6, y0 + 8), (x0 + 6, y0 + 8), (tx + 40, horizon + 30), (tx - 40, horizon + 30)])
            c.blit(beam, (0, 0))
