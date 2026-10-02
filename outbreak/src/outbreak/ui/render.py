"""Turn game state into a drawable view.  No curses here: the result is plain
data (rows of coloured cells), so it is easy to test and to print headlessly."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from outbreak.engine import tiles as T
from outbreak.engine.game import Game
from outbreak.engine.model import Human, Zombie
from outbreak.util import Pos, cheb, compass

Cell = Tuple[str, str, bool]          # glyph, colour name, bold
Line = Tuple[str, str]                # text, colour name

POI_LETTER = {"medical": "M", "market": "$", "guard": "P", "lab": "L", "transit": "U", "military": "A",
              "faith": "C", "industry": "F", "refuge": "R", "pad": "E", "house": "h"}
ZOMBIE_COLOR = {"walker": "red", "crawler": "red", "brute": "magenta", "bloater": "green", "screamer": "yellow",
                "leaper": "red", "clicker": "cyan", "stalker": "magenta", "alpha": "magenta"}
TAG_COLOR = {"info": "white", "good": "green", "bad": "red", "warn": "yellow", "combat": "grey",
             "lore": "cyan", "loud": "yellow"}
BLANK: Cell = (" ", "grey", False)


@dataclass
class View:
    map_rows: List[List[Cell]]
    side: List[Line]
    log: List[Line]
    origin: Pos = (0, 0)              # world coordinates of the top-left map cell

    def map_text(self) -> str:
        return "\n".join("".join(c[0] for c in row) for row in self.map_rows)

    def to_text(self) -> str:
        return self.map_text() + "\n" + "\n".join(t for t, _ in self.side) + "\n" + "\n".join(t for t, _ in self.log)


def bar(value: float, maximum: float, width: int = 10) -> str:
    maximum = max(1.0, maximum)
    filled = int(round(width * max(0.0, min(1.0, value / maximum))))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# ------------------------------------------------------------------ map
def _glyph(game: Game, x: int, y: int, visible: bool) -> Cell:
    lv = game.level
    t = lv.tile(x, y)
    info = T.TILES[t]
    ch, color, bold = info.glyph, info.color, False
    portal = lv.portals.get((x, y))
    if portal is not None and t == T.PORTAL:
        if portal.target == "world":
            ch, color, bold = "^", "yellow", True
        else:
            poi = game.pois.get(portal.target.rsplit(":", 1)[0])
            ch, color, bold = (POI_LETTER.get(poi.kind, "H") if poi else "H"), "white", True
    if t == T.LOCKED:
        ch, color, bold = "+", "red", True
    if not visible:
        return (ch, "grey", False)
    hz = lv.hazards.get((x, y))
    if hz is not None:
        return ("^" if hz.kind == "fire" else "~", "red" if hz.kind == "fire" else "green", True)
    if (x, y) in lv.corpses and t in (T.FLOOR, T.GRASS, T.ROAD, T.BRUSH, T.SHALLOW):
        ch, color = "x", "grey"
    if (x, y) in lv.docs:
        ch, color, bold = "?", "cyan", True
    if (x, y) in lv.items:
        ch, color, bold = "!", "yellow", True
    return (ch, color, bold)


def _actor_cell(a) -> Cell:
    if a.is_player:
        return ("@", "white", True)
    if isinstance(a, Zombie):
        return (a.glyph, ZOMBIE_COLOR.get(a.special, "red"), "boss" in a.flags)
    if isinstance(a, Human):
        return (a.glyph, "yellow" if a.hostile else "cyan", True)
    return ("?", "white", False)


def build_map(game: Game, w: int, h: int, cursor: Optional[Pos] = None) -> Tuple[List[List[Cell]], Pos]:
    lv, p = game.level, game.player
    ox = max(0, min(lv.w - w, p.x - w // 2)) if lv.w > w else -((w - lv.w) // 2)
    oy = max(0, min(lv.h - h, p.y - h // 2)) if lv.h > h else -((h - lv.h) // 2)
    rows: List[List[Cell]] = []
    for sy in range(h):
        y = oy + sy
        row: List[Cell] = []
        for sx in range(w):
            x = ox + sx
            if not lv.in_bounds(x, y):
                row.append(BLANK)
                continue
            vis = (x, y) in game.visible
            if not vis and not lv.seen[y][x]:
                row.append(BLANK)
                continue
            row.append(_glyph(game, x, y, vis))
        rows.append(row)
    # known buildings you cannot currently see
    if lv.kind == "overworld":
        for poi in game.pois.values():
            if poi.kind == "breach" or not (poi.revealed or poi.visited):
                continue
            sx, sy = poi.x - ox, poi.y - oy
            if 0 <= sx < w and 0 <= sy < h and rows[sy][sx][0] == " ":
                rows[sy][sx] = (POI_LETTER.get(poi.kind, "H"), "magenta", True)
            elif 0 <= sx < w and 0 <= sy < h and poi.pos not in game.visible:
                rows[sy][sx] = (POI_LETTER.get(poi.kind, "H"), "magenta", True)
    for a in lv.actors:
        if a.pos in game.visible:
            sx, sy = a.x - ox, a.y - oy
            if 0 <= sx < w and 0 <= sy < h:
                rows[sy][sx] = _actor_cell(a)
    sx, sy = p.x - ox, p.y - oy
    if 0 <= sx < w and 0 <= sy < h:
        rows[sy][sx] = ("@", "white", True)
    if cursor is not None:
        cx, cy = cursor[0] - ox, cursor[1] - oy
        if 0 <= cx < w and 0 <= cy < h:
            ch, color, _ = rows[cy][cx]
            rows[cy][cx] = ("X" if ch == " " else ch, "yellow", True)
    return rows, (ox, oy)


# ------------------------------------------------------------------ sidebar
def _hours(turns: int) -> str:
    return f"{turns / 10:.0f}h" if turns >= 20 else f"{turns} turns"


def build_side(game: Game) -> List[Line]:
    p, c, era = game.player, game.clock, game.era
    lv = game.level
    out: List[Line] = []
    out.append((f"{game.era.origin_names[game.cfg.origin]}  Lv{p.level}", "white"))
    out.append((f"{c.stamp()}  {c.phase}", "cyan" if c.is_night else "yellow"))
    out.append((lv.name[:28], "grey"))
    out.append(("", "grey"))
    hp_color = "green" if p.hp > p.max_hp * 0.5 else "yellow" if p.hp > p.max_hp * 0.25 else "red"
    out.append((f"HP    {bar(p.hp, p.max_hp)} {p.hp}", hp_color))
    out.append((f"Stam  {bar(p.stamina, p.max_stamina)}", "white"))
    pc = "green" if p.panic < 40 else "yellow" if p.panic < 75 else "red"
    out.append((f"Panic {bar(p.panic, p.max_panic)}", pc))
    hc = "green" if p.humanity >= 60 else "yellow" if p.humanity >= 25 else "red"
    out.append((f"Human {bar(p.humanity, 100)} {p.humanity}", hc))
    out.append((f"Noise {bar(game.heat, 100)}", "red" if game.heat > 60 else "yellow" if game.heat > 30 else "grey"))
    if game.cfg.needs:
        out.append((f"Hungr {bar(p.hunger, 100)}", "red" if p.hunger > 75 else "grey"))
    if p.infected:
        extra = f"  cut it off! {p.bite_window}" if p.bite_window > 0 and p.bite_limb in ("arm", "leg") else ""
        out.append((f"INFECTED {_hours(p.infection_timer)} left{extra}", "red"))
    flags = []
    if p.bleeding:
        flags.append("bleeding")
    if p.fracture:
        flags.append("broken leg")
    if p.lost:
        flags.append("no " + "/".join(p.lost))
    if p.disguise_turns:
        flags.append("disguised")
    if p.filter_turns:
        flags.append("filtered")
    if p.sneaking:
        flags.append("sneaking")
    if p.sprinting:
        flags.append("running")
    if flags:
        out.append((", ".join(flags), "yellow"))
    out.append(("", "grey"))
    out.append((_equip_line(game, p.weapon, "Hand"), "white"))
    if p.armor:
        out.append((_equip_line(game, p.armor, "Wear"), "white"))
    if p.light:
        state = "on" if p.light_on else "off"
        out.append((f"Light {game.item_def(p.light.id).name} ({p.light.dur}) {state}", "white"))
    out.append((f"{era.coin.title()}: {p.coins}   XP {p.xp}", "grey"))
    if p.perk_points:
        out.append((f"{p.perk_points} perk point(s)! (p)", "green"))
    out.append(("", "grey"))
    for text, done in game.objectives()[:5]:
        out.append((("[x] " if done else "[ ] ") + text, "green" if done else "white"))
    if game.final:
        out.append((f"HOLD OUT: {game.final.turns_left} turns", "red"))
    hostiles = sorted(game.visible_hostiles(), key=lambda a: cheb(a.pos, p.pos))
    if hostiles:
        out.append(("", "grey"))
        out.append(("In view:", "grey"))
        for a in hostiles[:4]:
            out.append((f" {a.glyph} {a.name} {cheb(a.pos, p.pos)}", ZOMBIE_COLOR.get(getattr(a, 'special', ''), "yellow")))
    return out


def _equip_line(game: Game, item, label: str) -> str:
    if item is None:
        return f"{label}: fists" if label == "Hand" else f"{label}: none"
    d = game.item_def(item.id)
    extra = f" ({item.dur}/{d.durability})" if d.durability and item.dur is not None else ""
    if d.ammo:
        extra += f" [{game.player.count(d.ammo)} {game.item_def(d.ammo).name.lower()}]"
    return f"{label}: {d.name}{extra}"


def build_log(game: Game, lines: int, width: int) -> List[Line]:
    out: List[Line] = []
    for turn, text, tag in game.log[-lines * 2:]:
        color = TAG_COLOR.get(tag, "white")
        while len(text) > width:
            cut = text.rfind(" ", 0, width)
            cut = cut if cut > 10 else width
            out.append((text[:cut], color))
            text = "  " + text[cut:].lstrip()
        out.append((text, color))
    return out[-lines:]


def build_view(game: Game, map_w: int, map_h: int, log_lines: int = 6, log_w: int = 100,
               cursor: Optional[Pos] = None) -> View:
    rows, origin = build_map(game, map_w, map_h, cursor)
    return View(rows, build_side(game), build_log(game, log_lines, log_w), origin)


def places(game: Game) -> List[Tuple[str, str]]:
    """Known buildings with direction and distance, for the 'places' screen."""
    p = game.player
    out = []
    for poi in sorted(game.pois.values(), key=lambda q: cheb(q.pos, p.pos)):
        if poi.kind == "breach" or not (poi.revealed or poi.visited):
            continue
        d = cheb(poi.pos, p.pos)
        mark = "visited" if poi.visited else "known"
        out.append((f"{POI_LETTER.get(poi.kind, 'H')}  {poi.name:<28} {compass(poi.x - p.x, poi.y - p.y):<11} {d:>3} tiles  {mark}",
                    "magenta" if poi.id == game.final_site_id else "white"))
    return out
