"""Plain data model: items, actors, levels.  No game rules live here."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from outbreak.engine import tiles as T
from outbreak.util import Pos


@dataclass
class Item:
    id: str
    qty: int = 1
    dur: Optional[int] = None        # remaining durability / fuel / charge
    key: bool = False                # quest item: takes no pack space and is never lost to a full pack


@dataclass
class Container:
    loot: List[Item] = field(default_factory=list)
    docs: List[str] = field(default_factory=list)     # document ids inside
    coins: int = 0
    opened: bool = False
    note: str = ""                   # "vault" marks the container holding a quest component


@dataclass
class Portal:
    target: str                      # level id
    pos: Pos                         # arrival position; (-1, -1) = use the target's named arrival
    label: str = ""
    arrive: str = "entry"            # entry | from_above | from_below


@dataclass
class Hazard:
    kind: str                        # fire | spore
    ttl: int


@dataclass
class POI:
    id: str
    kind: str                        # one of eras.POI_KINDS, or camp/refuge/pad/breach/house
    name: str
    x: int
    y: int
    box: Tuple[int, int, int, int] = (0, 0, 0, 0)    # footprint on the overworld: x, y, w, h
    floors: int = 1
    danger: float = 1.0
    revealed: bool = False
    visited: bool = False
    component: str = ""              # requirement item id hidden in the vault
    docs: List[str] = field(default_factory=list)     # document ids placed inside
    code_known: bool = False         # the vault code has been deciphered
    done: bool = False

    @property
    def pos(self) -> Pos:
        return (self.x, self.y)

    @property
    def level_id(self) -> str:
        return f"{self.id}:0"


@dataclass(eq=False)
class Actor:
    is_player = False                # class attribute, not a dataclass field
    uid: int
    name: str
    glyph: str
    x: int
    y: int
    hp: int
    max_hp: int
    level_id: str = "world"

    @property
    def pos(self) -> Pos:
        return (self.x, self.y)

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass(eq=False)
class Zombie(Actor):
    special: str = "walker"
    dmg: Tuple[int, int] = (3, 6)
    acc: int = 55
    speed: float = 1.0
    sight: float = 6.0
    hearing: float = 1.0
    xp: int = 5
    flags: Tuple[str, ...] = ()
    energy: float = 0.0
    state: str = "idle"              # idle | investigate | hunt | dormant
    target: Optional[Pos] = None
    stimulus_turn: int = 0
    birth_day: int = 1
    cooldown: int = 0
    horde: int = 0                   # horde id (0 = none)
    carries: List[Item] = field(default_factory=list)
    fresh_human: bool = False        # was a person: reanimated corpse


@dataclass(eq=False)
class Human(Actor):
    role: str = "survivor"           # raider | trader | healer | scholar | survivor
    faction: str = ""
    hostile: bool = False
    dmg: Tuple[int, int] = (3, 7)
    acc: int = 55
    reach: int = 1
    energy: float = 0.0
    state: str = "idle"
    target: Optional[Pos] = None
    loot: List[Item] = field(default_factory=list)
    talked: bool = False


class Level:
    """A rectangular map with everything standing on it."""

    def __init__(self, level_id: str, name: str, w: int, h: int, kind: str = "interior", fill: int = T.WALL):
        self.id = level_id
        self.name = name
        self.w, self.h = w, h
        self.kind = kind                         # overworld | interior | haven
        self.tiles: List[bytearray] = [bytearray([fill]) * w for _ in range(h)]
        self.seen: List[bytearray] = [bytearray(w) for _ in range(h)]
        self.actors: List[Actor] = []
        self.occ: Dict[Pos, Actor] = {}
        self.items: Dict[Pos, List[Item]] = {}
        self.containers: Dict[Pos, Container] = {}
        self.portals: Dict[Pos, Portal] = {}
        self.corpses: Dict[Pos, Tuple[int, bool]] = {}      # pos -> (turn of death, was human)
        self.hazards: Dict[Pos, Hazard] = {}
        self.door_hp: Dict[Pos, int] = {}
        self.docs: Dict[Pos, List[str]] = {}                # document ids lying on the floor
        self.entry: Pos = (1, 1)
        self.arrivals: Dict[str, Pos] = {}
        self.vault_lock: Optional[Pos] = None     # the locked door guarding the vault, if any
        self.bench: Optional[Pos] = None          # the synthesis bench / beacon console in a haven
        self.dark = kind != "overworld"
        self.safe = False
        self.poi_id = ""

    # ----------------------------------------------------------------- terrain
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def tile(self, x: int, y: int) -> int:
        return self.tiles[y][x] if 0 <= x < self.w and 0 <= y < self.h else T.WALL

    def set_tile(self, x: int, y: int, t: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.tiles[y][x] = t

    def walkable(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h and T.WALK[self.tiles[y][x]]

    def opaque(self, x: int, y: int) -> bool:
        return not (0 <= x < self.w and 0 <= y < self.h) or T.OPAQUE[self.tiles[y][x]]

    def free(self, x: int, y: int) -> bool:
        """Walkable and nobody standing there."""
        return self.walkable(x, y) and (x, y) not in self.occ

    # ----------------------------------------------------------------- actors
    def add_actor(self, a: Actor) -> None:
        a.level_id = self.id
        self.actors.append(a)
        self.occ[a.pos] = a

    def remove_actor(self, a: Actor) -> None:
        if a in self.actors:
            self.actors.remove(a)
        if self.occ.get(a.pos) is a:
            del self.occ[a.pos]

    def move_actor(self, a: Actor, x: int, y: int) -> None:
        if self.occ.get(a.pos) is a:
            del self.occ[a.pos]
        a.x, a.y = x, y
        self.occ[a.pos] = a

    def actor_at(self, x: int, y: int) -> Optional[Actor]:
        return self.occ.get((x, y))

    # ----------------------------------------------------------------- items
    def drop(self, pos: Pos, item: Item) -> None:
        stack = self.items.setdefault(pos, [])
        proto = next((i for i in stack if i.id == item.id and i.dur == item.dur), None)
        if proto is not None and item.dur is None:
            proto.qty += item.qty
        else:
            stack.append(item)

    def free_spot_near(self, x: int, y: int, radius: int = 4, avoid: Optional[Set[Pos]] = None) -> Optional[Pos]:
        for r in range(0, radius + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    p = (x + dx, y + dy)
                    if self.free(*p) and (not avoid or p not in avoid) and self.tile(*p) not in (
                            T.PORTAL, T.STAIRS_UP, T.STAIRS_DOWN):
                        return p
        return None
