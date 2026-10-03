"""Game configuration chosen on the new-game screen (or the command line)."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from outbreak import content


@dataclass(frozen=True)
class Difficulty:
    name: str
    zombies: float       # population multiplier
    loot: float          # loot multiplier
    damage: float        # damage taken multiplier
    timer: float         # infection timer / deadline multiplier
    noise: float         # how quickly noise builds heat


DIFFICULTIES = {
    "easy": Difficulty("easy", 0.7, 1.3, 0.75, 1.3, 0.8),
    "normal": Difficulty("normal", 1.0, 1.0, 1.0, 1.0, 1.0),
    "hard": Difficulty("hard", 1.3, 0.8, 1.25, 0.8, 1.25),
}


@dataclass
class GameConfig:
    era: str = "modern"
    zombies: str = "classic"
    scenario: str = "cure"
    origin: str = "medic"
    opening: str = "random"      # a key of content.OPENINGS, or "random" (picked from your origin)
    difficulty: str = "normal"
    seed: Optional[int] = None
    needs: bool = False          # hunger
    permadeath: bool = True      # delete the save when you die
    map_w: int = 120
    map_h: int = 76

    def validate(self) -> "GameConfig":
        content.get_era(self.era)
        content.get_preset(self.zombies)
        content.get_scenario(self.scenario)
        content.get_origin(self.origin)
        if self.opening != "random":
            content.get_opening(self.opening)
        if self.difficulty not in DIFFICULTIES:
            raise KeyError(f"unknown difficulty {self.difficulty!r}; choose one of: {', '.join(DIFFICULTIES)}")
        if not (100 <= self.map_w <= 400 and 64 <= self.map_h <= 300):
            raise ValueError("map size out of range (minimum 100x64: smaller maps cannot hold every building type)")
        return self

    @property
    def diff(self) -> Difficulty:
        return DIFFICULTIES[self.difficulty]

    def to_dict(self) -> dict:
        return asdict(self)
