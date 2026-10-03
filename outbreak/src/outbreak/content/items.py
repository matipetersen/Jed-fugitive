"""Item definitions shared by every era.

Eras add their own weapons/armour and may *rename* the generic items below
(a "medkit" is a herbal poultice in 1348), so gameplay code only ever refers to
ids, never to names.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, Tuple

STYLES = ("unarmed", "blunt", "blade", "polearm", "bow", "firearm", "energy")
RANGED_STYLES = ("bow", "firearm", "energy")
KINDS = ("weapon", "armor", "light", "food", "med", "material", "tool", "throw", "ammo", "component")


@dataclass
class ItemDef:
    id: str
    name: str
    kind: str
    desc: str = ""
    value: int = 1
    stackable: bool = False
    tags: Tuple[str, ...] = ()
    rarity: int = 1                      # 1 common .. 4 very rare (lowers loot weight)
    poi: Tuple[str, ...] = ()            # POI kinds that favour this item
    # weapons
    style: str = ""
    dmg: Tuple[int, int] = (0, 0)
    reach: int = 1
    noise: int = 0
    durability: int = 0
    ammo: str = ""
    accuracy: int = 0
    head: float = 0.0                    # extra headshot chance
    # armour
    defense: int = 0
    bite_guard: float = 0.0              # fraction of bites it turns away
    stealth: int = 0                     # extra noise while worn
    # lights
    light: int = 0
    # consumables and tools: effect keys are interpreted by engine.items
    effect: Dict[str, object] = field(default_factory=dict)

    @property
    def is_ranged(self) -> bool:
        return self.style in RANGED_STYLES

    @property
    def uses_durability(self) -> bool:
        return self.durability > 0


def _i(id, name, kind, desc="", **kw) -> ItemDef:
    return ItemDef(id, name, kind, desc, **kw)


# Generic items every era has (names are overridden per era).
BASE_ITEMS: Tuple[ItemDef, ...] = (
    _i("bandage", "Bandage", "med", "Stops bleeding and closes small wounds.", value=4, stackable=True,
       tags=("medical",), effect={"heal": 6, "stop_bleed": True}, poi=("medical", "market")),
    _i("splint", "Splint", "med", "Sets a broken limb so you can walk properly.", value=5, stackable=True,
       tags=("medical",), effect={"splint": True}, poi=("medical",)),
    _i("medkit", "Medkit", "med", "Treats serious wounds.", value=15, stackable=True, rarity=2,
       tags=("medical",), effect={"heal": 32, "stop_bleed": True}, poi=("medical", "military")),
    _i("suppressant", "Suppressant", "med", "Slows an infection. It does not cure it.", value=32, stackable=True,
       rarity=3, tags=("medical",), effect={"suppress": 300}, poi=("medical", "lab")),
    _i("painkiller", "Painkillers", "med", "Dulls pain and steadies your nerves.", value=6, stackable=True,
       tags=("medical",), effect={"heal": 4, "panic": -22}, poi=("medical", "market")),
    _i("filter", "Spore filter", "med", "Keeps spores and gas out of your lungs for a while.", value=9,
       stackable=True, rarity=2, effect={"filter": 160}, poi=("lab", "military", "industry")),
    _i("food", "Rations", "food", "Something to eat.", value=3, stackable=True, effect={"food": 40},
       poi=("market", "military")),
    _i("scrap", "Scrap metal", "material", "Bent metal. Good for repairs.", value=1, stackable=True,
       poi=("industry", "transit")),
    _i("cloth", "Cloth", "material", "Rags and fabric.", value=1, stackable=True, poi=("market", "faith")),
    _i("wood", "Planks", "material", "Boards and splintered timber.", value=1, stackable=True,
       poi=("industry", "faith")),
    _i("chem", "Chemicals", "material", "Volatile compounds.", value=3, stackable=True, rarity=2,
       poi=("lab", "industry", "medical")),
    _i("parts", "Parts", "material", "Mechanisms and wiring.", value=3, stackable=True, rarity=2,
       poi=("lab", "military", "industry")),
    _i("fuel", "Fuel", "material", "Something that burns. Also tops up a lamp.", value=4, stackable=True, rarity=2,
       effect={"refuel": 140}, poi=("industry", "military", "transit")),
    _i("molotov", "Fire bomb", "throw", "Thrown, it burns everything around the impact.", value=10,
       stackable=True, effect={"fire": True, "damage": (9, 15), "radius": 1}),
    _i("noisemaker", "Noisemaker", "throw", "Thrown, it draws the dead to wherever it lands.", value=6,
       stackable=True, effect={"noise": 20}),
    _i("repair_kit", "Repair kit", "tool", "Restores a weapon's durability.", value=8, stackable=True,
       effect={"repair": 25}, poi=("industry", "military", "market")),
    _i("barricade_kit", "Barricade kit", "tool", "Reinforces the door next to you.", value=7, stackable=True,
       effect={"barricade": 40}, poi=("industry", "market")),
    _i("spike_trap", "Spike trap", "tool", "Set where you stand. The first of the dead to step on it takes a savage wound.",
       value=6, stackable=True, effect={"trap": 26}, poi=("industry", "market")),
)

BASE_BY_ID: Dict[str, ItemDef] = {i.id: i for i in BASE_ITEMS}


def renamed(item: ItemDef, name: str, desc: str = "") -> ItemDef:
    return replace(item, name=name, desc=desc or item.desc)


def index(items: Iterable[ItemDef]) -> Dict[str, ItemDef]:
    out: Dict[str, ItemDef] = {}
    for it in items:
        if it.id in out:
            raise ValueError(f"duplicate item id {it.id!r}")
        out[it.id] = it
    return out
