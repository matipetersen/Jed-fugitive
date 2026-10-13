"""Efectos de sonido sintetizados (sin archivos). Si no hay audio, todo es silencio."""
from __future__ import annotations

import array
import math
import random

import pygame

RATE = 22050
_sounds: dict = {}
_ready = False
_last: dict = {}
volume = 0.55


def _to_sound(samples):
    out = array.array("h")
    for s in samples:
        s = max(-1.0, min(1.0, s))
        out.append(int(s * 32000))
    return pygame.mixer.Sound(buffer=out.tobytes())


def _noise(dur, decay, low=0.0, vol=0.8):
    n = int(RATE * dur)
    prev = 0.0
    res = []
    rnd = random.Random(7)
    for i in range(n):
        t = i / RATE
        x = rnd.uniform(-1, 1)
        prev += (x - prev) * (1 - low)
        res.append(prev * math.exp(-t * decay) * vol)
    return res


def _tone(freq, dur, decay=6.0, vol=0.6, sweep=0.0, wave="sin"):
    n = int(RATE * dur)
    res = []
    ph = 0.0
    for i in range(n):
        t = i / RATE
        f = freq + sweep * t
        ph += 2 * math.pi * f / RATE
        v = math.sin(ph) if wave == "sin" else (1.0 if math.sin(ph) > 0 else -1.0) * 0.5
        res.append(v * math.exp(-t * decay) * vol)
    return res


def _mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def _seq(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def init() -> bool:
    global _ready
    if _ready:
        return True
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
        pygame.mixer.set_num_channels(16)
        _sounds["shot"] = _to_sound(_mix(_noise(0.28, 16, 0.45, 0.9), _tone(80, 0.2, 18, 0.7, -120)))
        _sounds["rifle"] = _to_sound(_mix(_noise(0.35, 12, 0.6, 0.7), _tone(60, 0.3, 14, 0.5, -60)))
        _sounds["cannon"] = _to_sound(_mix(_noise(0.7, 6, 0.8, 1.0), _tone(50, 0.6, 7, 0.9, -30)))
        _sounds["hit"] = _to_sound(_noise(0.07, 40, 0.3, 0.6))
        _sounds["thunk"] = _to_sound(_mix(_noise(0.07, 50, 0.7, 0.5), _tone(140, 0.08, 40, 0.5)))
        _sounds["chop"] = _to_sound(_mix(_noise(0.06, 60, 0.5, 0.5), _tone(220, 0.06, 50, 0.4)))
        _sounds["death"] = _to_sound(_tone(300, 0.35, 6, 0.4, -600))
        _sounds["hurt"] = _to_sound(_tone(220, 0.18, 12, 0.45, -200, "sq"))
        _sounds["boom"] = _to_sound(_mix(_noise(0.9, 5, 0.85, 1.0), _tone(45, 0.8, 5, 0.9)))
        _sounds["click"] = _to_sound(_tone(660, 0.06, 40, 0.35))
        _sounds["bow"] = _to_sound(_noise(0.12, 22, 0.1, 0.25))
        _sounds["horn"] = _to_sound(_seq(_tone(196, 0.35, 3, 0.5, 0, "sq"), _tone(262, 0.55, 2.5, 0.5, 0, "sq")))
        _sounds["win"] = _to_sound(_seq(_tone(392, 0.16, 5, 0.5), _tone(523, 0.16, 5, 0.5), _tone(659, 0.5, 3, 0.5)))
        _sounds["lose"] = _to_sound(_seq(_tone(330, 0.25, 4, 0.5), _tone(262, 0.25, 4, 0.5), _tone(196, 0.6, 3, 0.5)))
        _sounds["coin"] = _to_sound(_seq(_tone(988, 0.07, 20, 0.4), _tone(1319, 0.2, 10, 0.4)))
        _ready = True
    except Exception:
        _ready = False
    return _ready


def play(name: str, vol: float = 1.0, min_gap: float = 0.0):
    if not _ready:
        return
    snd = _sounds.get(name)
    if snd is None:
        return
    if min_gap:
        now = pygame.time.get_ticks() / 1000.0
        if now - _last.get(name, -9) < min_gap:
            return
        _last[name] = now
    try:
        snd.set_volume(max(0.0, min(1.0, vol * volume)))
        snd.play()
    except Exception:
        pass
