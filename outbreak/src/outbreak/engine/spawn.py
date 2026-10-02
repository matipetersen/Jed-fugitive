"""Creating zombies (and raiders) with stats derived from the preset, the special
type and how far the outbreak has progressed."""
from __future__ import annotations

import random
from typing import Optional

from outbreak.content.zombies import SPECIALS, ZombieProfile
from outbreak.engine.model import Human, Level, Zombie
from outbreak.util import weighted_choice


def pick_special(rng: random.Random, profile: ZombieProfile, day: int) -> str:
    phase = profile.phase(day)
    pairs = [("walker", 10.0)]
    for sid, weight, first_day in profile.specials:
        if day >= first_day:
            pairs.append((sid, weight * phase.special))
    return weighted_choice(rng, pairs)


def make_zombie(game, special_id: str, x: int, y: int, fresh: bool = False) -> Zombie:
    profile: ZombieProfile = game.profile
    sp = SPECIALS[special_id]
    day = game.clock.day
    phase = profile.phase(day)
    age = 0 if fresh else game.rng.randint(0, max(0, day - 1))
    decay = max(0.4, 1.0 - profile.decay * age)
    hp = max(1, int(sp.hp * profile.hp_mult * phase.hp * decay))
    z = Zombie(
        uid=game.next_uid(), name=profile.name_of(special_id), glyph=sp.glyph, x=x, y=y, hp=hp, max_hp=hp,
        special=special_id, dmg=sp.dmg, acc=sp.acc,
        speed=profile.speed * sp.speed * phase.speed * (0.85 if decay < 1 else 1.0),
        sight=profile.sight * sp.sight, hearing=profile.hearing * sp.hearing, xp=sp.xp, flags=sp.flags,
        birth_day=day - age)
    if "boss" in sp.flags or "relentless" in sp.flags:
        z.speed = max(z.speed, 1.0)
    return z


def spawn_zombie(game, level: Level, pos, special: Optional[str] = None, dormant: bool = True,
                 fresh: bool = False) -> Zombie:
    sid = special or pick_special(game.rng, game.profile, game.clock.day)
    z = make_zombie(game, sid, pos[0], pos[1], fresh)
    z.state = "dormant" if (dormant and level.kind != "overworld") else "idle"
    level.add_actor(z)
    return z


def make_raider(game, x: int, y: int) -> Human:
    era = game.era
    reach = 6 if (era.firearms or era.tech == 0) else 1          # guns, or bows in the old world
    hp = int(18 * (1.0 + 0.04 * game.player.level))
    h = Human(uid=game.next_uid(), name="Raider", glyph="R", x=x, y=y, hp=hp, max_hp=hp, role="raider",
              faction="raiders", hostile=True, dmg=(3, 6), acc=48, reach=reach)
    if game.rng.random() < 0.7:
        from outbreak.engine import loot
        h.loot = loot.roll_items(game.rng, era, "camp", 1.6, game.diff.loot)
    return h
