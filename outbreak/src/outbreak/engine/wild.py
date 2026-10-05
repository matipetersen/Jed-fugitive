"""The wild: game to hunt and plants to gather, so food is something you can go and find.

Rabbits, deer and boar graze on open ground.  They notice you from a few tiles (fewer if you are creeping), bolt, and run
a little slower than you do, so a chase can end.  A creeping hunter can stab an unaware one for triple damage.  A boar
turns and gores whatever hurt it.  Kills drop raw meat; eaten raw it can make you ill, with a plank it can be cooked
(the ``cook`` recipe).  Foraging takes a few turns on grass or brush and a patch stays picked for a while.
"""
from __future__ import annotations

from typing import Optional, Tuple

from outbreak.engine import tiles as T
from outbreak.engine.fov import has_los
from outbreak.engine.model import Animal, Item
from outbreak.util import DIRS8, cheb

# species: hp, glyph, (meat min, meat max), notice radius, dmg when cornered, spawn weight
SPECIES = {
    "rabbit": (4, "r", (1, 1), 5, (0, 0), 50),
    "deer": (14, "d", (2, 3), 7, (0, 0), 35),
    "boar": (20, "b", (2, 3), 4, (3, 7), 15),
}
NAMES = {"rabbit": "Rabbit", "deer": "Deer", "boar": "Boar"}
GRAZING = (T.GRASS, T.BRUSH)
FORAGE_TURNS = 5
PATCH_TURNS = 800
FORAGE_CHANCE = {T.BRUSH: 0.8, T.GRASS: 0.5}
SNEAK_BLOW = 3.0


def make_animal(game, x: int, y: int, species: str) -> Animal:
    hp, glyph, _meat, _r, _d, _w = SPECIES[species]
    return Animal(uid=game.next_uid(), name=NAMES[species], glyph=glyph, x=x, y=y, hp=hp, max_hp=hp, species=species)


def populate(game) -> None:
    """Scatter game over the open ground, away from where you start."""
    lv, rng, start = game.world.level, game.rng, game.world.start
    spots = [(x, y) for y in range(3, lv.h - 3) for x in range(3, lv.w - 3)
             if lv.tiles[y][x] in GRAZING and cheb((x, y), start) >= 14]
    if not spots:
        return
    kinds = list(SPECIES)
    weights = [SPECIES[k][5] for k in kinds]
    for _ in range(max(6, (lv.w * lv.h) // 400)):
        x, y = rng.choice(spots)
        if lv.free(x, y):
            lv.add_actor(make_animal(game, x, y, rng.choices(kinds, weights)[0]))


# ------------------------------------------------------------------ behaviour
def _step_away(game, a: Animal) -> Optional[Tuple[int, int]]:
    lv, p = game.level, game.player
    best, best_d = None, cheb(a.pos, p.pos)
    for dx, dy in DIRS8:
        n = (a.x + dx, a.y + dy)
        if lv.free(*n) and lv.tile(*n) in GRAZING + (T.ROAD,) and cheb(n, p.pos) > best_d:
            best, best_d = n, cheb(n, p.pos)
    return best


def tick(game, a: Animal) -> None:
    p, lv, t = game.player, game.level, game.clock.turn
    if lv.kind != "overworld":
        return
    d = cheb(a.pos, p.pos)
    radius = SPECIES[a.species][3]
    if p.sneaking:
        radius = max(2, radius - 3)
    # a creeping player is only noticed now and then, which is what makes a stalk possible
    if not a.alert and d <= radius and has_los(lv, a.pos, p.pos) and (not p.sneaking or game.rng.random() < 0.4):
        a.alert = True
        a.state = "charge" if (a.species == "boar" and d <= 3) else "flee"
    if a.alert and d > radius + 6:
        a.alert, a.state = False, "graze"                               # it calms down once you are well away
    if a.state == "flee":
        if t % 3:                                                       # it is quick, but not as quick as you
            nxt = _step_away(game, a)
            if nxt:
                lv.move_actor(a, *nxt)
        return
    if a.state == "charge":
        if d == 1:
            lo, hi = SPECIES[a.species][4]
            if game.rng.random() < 0.7:
                dmg = game.rng.randint(lo, hi)
                game.msg(f"The {a.name.lower()} gores you for {dmg}.", "combat")
                _hurt(game, dmg)
        elif d <= 8:
            from outbreak.engine.pathing import greedy_step
            nxt = greedy_step(lv, a.pos, p.pos, game.rng, can_pass=lambda n: lv.tile(*n) in GRAZING + (T.ROAD,))
            if nxt and lv.free(*nxt):
                lv.move_actor(a, *nxt)
        return
    if game.rng.random() < 0.18:                                        # graze: drift about
        dx, dy = game.rng.choice(DIRS8)
        n = (a.x + dx, a.y + dy)
        if lv.free(*n) and lv.tile(*n) in GRAZING:
            lv.move_actor(a, *n)


def _hurt(game, dmg: int) -> None:
    p = game.player
    p.hp -= dmg
    if p.hp <= 0:
        game.end("dead", "gored by a boar")


# ------------------------------------------------------------------ the hunt
def attack(game, a: Animal, unaware: bool, acc: float, dmg: float) -> bool:
    """The player strikes ``a``; ``acc`` is hit chance in percent and ``dmg`` the damage of an ordinary blow."""
    if not unaware and game.rng.random() * 100 >= acc:
        game.msg(f"You swing at the {a.name.lower()} and miss.", "combat")
        a.alert, a.state = True, ("charge" if a.species == "boar" else "flee")
        return True
    hurt = max(1, int(dmg * (SNEAK_BLOW if unaware else 1.0)))
    a.hp -= hurt
    if a.hp <= 0:
        kill(game, a)
        return True
    a.alert = True
    a.state = "charge" if a.species == "boar" else "flee"
    game.msg(f"You hit the {a.name.lower()} for {hurt}.", "combat")
    return True


def kill(game, a: Animal) -> None:
    lv = game.level
    lv.remove_actor(a)
    lo, hi = SPECIES[a.species][2]
    n = game.rng.randint(lo, hi)
    lv.drop(a.pos, Item("raw_meat", n))
    game.player.gain_xp(3)
    game.player.bump("game")
    game.msg(f"The {a.name.lower()} drops. {n} cut{'s' if n != 1 else ''} of meat lie there: pick it up, and cook it.", "good")


# ------------------------------------------------------------------ foraging
def can_forage(game) -> str:
    """Why you cannot forage here, or an empty string."""
    p, lv = game.player, game.level
    if lv.kind != "overworld":
        return "There is nothing to gather indoors."
    if lv.tile(*p.pos) not in GRAZING:
        return "Nothing edible grows on this. Try grass or brush."
    if game.visible_hostiles():
        return "Not with something hunting you."
    return ""


def forage(game) -> bool:
    """Gather what is edible round you.  Returns True if time passed."""
    if not game._begin_action():
        return False
    why = can_forage(game)
    if why:
        game.msg(why, "info")
        return False
    p, lv, t = game.player, game.level, game.clock.turn
    patches = getattr(game, "foraged", None)
    if patches is None:
        patches = game.foraged = {}
    if any(cheb(pos, p.pos) <= 2 and t - when < PATCH_TURNS for pos, when in patches.items()):
        game.msg("This patch is already picked over. Move on.", "info")
        return False
    for _ in range(FORAGE_TURNS):
        game._spend(1)
        if game.over:
            return True
        if game.visible_hostiles():
            game.msg("You stop gathering: something is coming.", "warn")
            return True
    game.emit_noise(p.pos, 2, "player")
    patches[p.pos] = t
    chance = FORAGE_CHANCE.get(lv.tile(*p.pos), 0.4)
    if game.weather in ("rain", "fog"):
        chance += 0.1
    if not game.clock.is_day:
        chance -= 0.25
    if game.rng.random() < chance:
        n = game.rng.randint(1, 3)
        game.give_item(Item("forage", n))
        game.msg(f"You gather wild greens and berries ({n}).", "good")
    else:
        game.msg("You find nothing worth eating here.", "info")
    return True
