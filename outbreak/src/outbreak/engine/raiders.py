"""Raiders are not mobs: they lie in wait, lay snares round their camps, and fight as a squad (see ai._raider_hunt).

This module holds what is not a per-turn decision: building a camp's defences, springing an ambush, spotting and
disarming snares, and the morale that breaks when their friends die.
"""
from __future__ import annotations

from outbreak.engine import tiles as T
from outbreak.engine.fov import has_los
from outbreak.engine.model import Hazard, Human
from outbreak.util import DIRS8, cheb

SNARE_POWER = 8
SPRING_RANGE = 3                       # you walk this close to someone lying in wait and it springs (2 if you creep)


def is_raider(a) -> bool:
    return isinstance(a, Human) and a.role == "raider" and a.hostile and a.hp > 0


def alert_near(game, pos, radius: int) -> None:
    """A clatter, a shout: every raider within earshot knows where you are."""
    p = game.player
    for a in game.level.actors:
        if is_raider(a) and cheb(a.pos, pos) <= radius:
            a.hidden = False
            a.state, a.target = "hunt", p.pos


def spring(game, h: Human, text: str = "") -> None:
    """Someone lying in wait jumps out, and so does the rest of its squad."""
    squad = [a for a in game.level.actors if is_raider(a) and a.hidden and (a is h or (h.squad and a.squad == h.squad))]
    p = game.player
    for a in squad:
        a.hidden = False
        a.state, a.target = "hunt", p.pos
    if squad:
        game.msg(text or "Raiders burst out of cover!", "bad", key=True)


def notice_snares(game) -> None:
    """Walking, you may spot a snare next to you (more likely if you creep).  Spotted ones show, and can be disarmed."""
    p, lv = game.player, game.level
    reach = 2 if p.sneaking else 1
    chance = 0.7 if p.sneaking else 0.35
    for pos, hz in lv.hazards.items():
        if hz.kind == "snare" and hz.hidden and cheb(pos, p.pos) <= reach and game.rng.random() < chance:
            hz.hidden = False
            game.msg("You spot a snare in the ground ahead.", "good")
            return


def shaken(game, dead) -> None:
    """Friends dying shakes the rest of the squad."""
    for a in game.level.actors:
        if is_raider(a) and a is not dead and (cheb(a.pos, dead.pos) <= 8 or (dead.squad and a.squad == dead.squad)):
            a.morale = max(0, a.morale - 25)


def spring_check(game, h: Human, humans, d: int) -> bool:
    """For a raider lying in wait: spring, be spotted by a creeping player, or stay put.  True if it stays hidden."""
    p = game.player
    reach = 2 if p.sneaking else SPRING_RANGE
    if d <= reach and has_los(game.level, h.pos, p.pos):
        spring(game, h)
        return False
    if any(is_raider(o) and o.squad == h.squad and o.state == "hunt" and cheb(o.pos, h.pos) <= 12 for o in humans):
        spring(game, h, "Raiders break cover!")
        return False
    if p.sneaking and d <= 3 and game.rng.random() < 0.25:
        h.hidden = False                                      # you saw it first: it has not seen you
        game.msg("You spot a raider crouched in cover.", "good")
        return False
    return True


def setup_camp(game, lv, camp, raiders) -> None:
    """A camp is not a clearing: half its raiders lie in wait round it, and the approaches are snared."""
    rng = game.rng
    squad = game.next_uid()
    for i, r in enumerate(raiders):
        r.squad = squad
        r.flank = 1 if i % 2 == 0 else -1
    for r in raiders[1::2]:
        for _ in range(30):
            x, y = camp[0] + rng.randint(-9, 9), camp[1] + rng.randint(-9, 9)
            if 4 <= cheb((x, y), camp) <= 9 and lv.free(x, y) and lv.tile(x, y) in (T.GRASS, T.BRUSH, T.ROAD):
                lv.move_actor(r, x, y)
                r.hidden, r.state = True, "idle"
                break
    placed = 0
    for _ in range(60):
        if placed >= 5:
            break
        x, y = camp[0] + rng.randint(-9, 9), camp[1] + rng.randint(-9, 9)
        if 4 <= cheb((x, y), camp) <= 9 and lv.free(x, y) and lv.tile(x, y) in (T.GRASS, T.ROAD, T.BRUSH) \
                and (x, y) not in lv.hazards:
            lv.hazards[(x, y)] = Hazard("snare", 10 ** 9, SNARE_POWER, hidden=True)
            placed += 1
