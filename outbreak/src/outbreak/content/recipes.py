"""Crafting recipes.  Higher-tier ones need fluency in the era's cipher: you
can only build what you can read the manual for."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Recipe:
    id: str
    out: str                              # item id; "@ammo" means the era's main ammunition
    qty: int
    inputs: Tuple[Tuple[str, int], ...]
    fluency: float = 0.0
    needs: str = ""                       # "" | "firearms" | "electricity"
    turns: int = 3


RECIPES: Tuple[Recipe, ...] = (
    Recipe("bandage", "bandage", 2, (("cloth", 2),)),
    Recipe("splint", "splint", 1, (("wood", 1), ("cloth", 1))),
    Recipe("molotov", "molotov", 1, (("fuel", 1), ("cloth", 1))),
    Recipe("noisemaker", "noisemaker", 1, (("parts", 1), ("scrap", 1))),
    Recipe("barricade", "barricade_kit", 1, (("wood", 2), ("scrap", 1))),
    Recipe("spike_trap", "spike_trap", 1, (("wood", 1), ("scrap", 2))),
    Recipe("repair", "repair_kit", 1, (("scrap", 2), ("parts", 1)), fluency=0.08),
    Recipe("filter", "filter", 1, (("cloth", 1), ("chem", 1)), fluency=0.10),
    Recipe("medkit", "medkit", 1, (("bandage", 2), ("chem", 1)), fluency=0.15),
    Recipe("suppressant", "suppressant", 1, (("chem", 2), ("cloth", 1)), fluency=0.25, turns=5),
    Recipe("ammo", "@ammo", 4, (("scrap", 1), ("chem", 1)), fluency=0.12),
)


def by_id() -> Dict[str, Recipe]:
    return {r.id: r for r in RECIPES}
