"""Small, dependency-free helpers shared by the engine."""
from __future__ import annotations

import math
import random
from typing import Iterable, Iterator, Sequence, Tuple, TypeVar

T = TypeVar("T")
Pos = Tuple[int, int]

DIRS4: Tuple[Pos, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))
DIRS8: Tuple[Pos, ...] = DIRS4 + ((1, -1), (1, 1), (-1, 1), (-1, -1))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def cheb(a: Pos, b: Pos) -> int:
    """Chebyshev distance: the number of 8-way steps between two tiles."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def dist(a: Pos, b: Pos) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def sign(v) -> int:
    return (v > 0) - (v < 0)


def line(a: Pos, b: Pos) -> Iterator[Pos]:
    """Bresenham line from ``a`` (excluded) to ``b`` (included)."""
    x0, y0 = a
    x1, y1 = b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while (x0, y0) != (x1, y1):
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
        yield x0, y0


def weighted_choice(rng: random.Random, pairs: Sequence[Tuple[T, float]]) -> T:
    """Pick a value from ``(value, weight)`` pairs; weights may be floats."""
    total = sum(w for _, w in pairs if w > 0)
    if total <= 0:
        raise ValueError("weighted_choice needs at least one positive weight")
    roll = rng.random() * total
    for value, weight in pairs:
        if weight <= 0:
            continue
        roll -= weight
        if roll <= 0:
            return value
    return pairs[-1][0]


def chance(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def compass(dx: float, dy: float) -> str:
    """Eight-way compass word for a vector (y grows southwards)."""
    if dx == 0 and dy == 0:
        return "here"
    ang = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
    names = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")
    return names[int((ang + 22.5) // 45) % 8]


def pluralize(n: int, one: str, many: str = "") -> str:
    return one if n == 1 else (many or one + "s")


def first(iterable: Iterable[T], default=None):
    for v in iterable:
        return v
    return default
