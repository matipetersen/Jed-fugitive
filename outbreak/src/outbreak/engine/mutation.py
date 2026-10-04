"""The strain changes: how much depends on the plague *and* on the world it spreads in.

A plague that mutates (the engineered ones above all) changes faster where there is science to feed it: a lab-grade
age turns Resident Evil into a nightmare, while the same shambling dead in a medieval world barely change from the
first day to the last.  Each change is a trait the whole population gains at once, announced when it happens.
"""
from __future__ import annotations

MAX_TRAITS = 5
RAMP_DAYS = 12                      # the strain needs this long to reach its full pace
TRAITS = {                          # id: (what you are told, stat, factor)
    "fleet": ("They move faster than they did.", "speed", 1.12),
    "tough": ("They take more killing: the hides are tougher.", "hp", 1.2),
    "keen": ("They hear and see more than they did.", "senses", 1.2),
    "frenzied": ("They hit harder.", "dmg", 1.2),
    "swift": ("They close the distance faster still.", "speed", 1.1),
}


def strength(game) -> float:
    """0 (never changes) .. about 1.4 (an engineered plague in a world of labs, at full pace)."""
    day = game.clock.day
    return game.profile.mutates * game.era.rules.lab * min(1.0, max(0, day - 1) / RAMP_DAYS)


def special_boost(game) -> float:
    """More of the strange ones as the strain runs ahead."""
    return 1.0 + 0.6 * strength(game)


def _apply(z, trait: str) -> None:
    _, stat, k = TRAITS[trait]
    if stat == "speed":
        z.speed *= k
    elif stat == "hp":
        z.hp = int(z.hp * k)
        z.max_hp = int(z.max_hp * k)
    elif stat == "senses":
        z.hearing *= k
        z.sight *= 1.1
    elif stat == "dmg":
        z.dmg = (int(z.dmg[0] * k), max(int(z.dmg[0] * k), int(z.dmg[1] * k)))


def apply(game, z) -> None:
    """A new zombie is born with every change the strain has made so far."""
    for trait in game.mutations:
        _apply(z, trait)


def daily(game) -> None:
    """Once a day the strain may change; the dead that already walk change with it."""
    s = strength(game)
    if s <= 0 or len(game.mutations) >= MAX_TRAITS:
        return
    if game.rng.random() >= min(0.8, 0.5 * s):
        return
    left = [t for t in TRAITS if t not in game.mutations]
    trait = game.rng.choice(left)
    game.mutations.append(trait)
    for lv in game.levels.values():
        for a in lv.actors:
            if getattr(a, "special", None) is not None and hasattr(a, "hearing"):
                _apply(a, trait)
    game.msg(f"Day {game.clock.day}: the strain has changed. {TRAITS[trait][0]}", "lore")


def matchup(era, profile) -> str:
    """One honest sentence for the briefing about how this plague plays in this era."""
    m = profile.mutates * era.rules.lab
    if m < 0.1:
        how = "The strain hardly changes here: the dead of the last day are the dead of the first."
    elif m < 0.4:
        how = "The strain changes slowly. Expect a new trait now and then."
    elif m < 0.8:
        how = "The strain changes steadily; after a couple of weeks it is not what it was."
    else:
        how = "The strain mutates fast here: expect a new trait every few days, and the strange ones to multiply."
    return f"{era.rules.feel} {how}".strip()
