"""Combat rules: player attacks, zombie and human attacks, injuries, infection.

Every function takes the running ``game`` and mutates it; they return whether a
turn was spent where that matters.  Nothing here knows about eras: weapons are
:class:`ItemDef` records and zombies are parameterised by the preset.
"""
from __future__ import annotations

from typing import Optional

from outbreak.content.items import ItemDef
from outbreak.content.zombies import SPECIALS
from outbreak.engine import tiles as T
from outbreak.engine.fov import has_los
from outbreak.engine.model import Actor, Hazard, Human, Item, Zombie
from outbreak.util import cheb, clamp, dist

FISTS = ItemDef("fists", "Fists", "weapon", style="unarmed", dmg=(1, 3), noise=2)
LIMBS = (("arm", 35), ("leg", 35), ("torso", 25), ("neck", 5))
STAMINA_PER_ATTACK = 4


# ------------------------------------------------------------------ helpers
def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def weapon_def(game) -> ItemDef:
    w = game.player.weapon
    return game.item_def(w.id) if w is not None else FISTS


def player_lit(game) -> bool:
    p = game.player
    return p.light is not None and p.light_on and (p.light.dur or 0) > 0 and game.is_dark()


def _accuracy(game, w: ItemDef, evade: float, distance: int = 1) -> float:
    p = game.player
    acc = 72 + w.accuracy + 3 * p.style_rank(w.style)
    if w.is_ranged:
        acc += p.mod("ranged_acc") - max(0, distance - 2) * 2.5
    elif p.fracture:
        acc -= 4
    if p.panic >= 75:
        acc -= 16
    elif p.panic >= 50:
        acc -= 8
    if p.stamina < STAMINA_PER_ATTACK + 1:
        acc -= 12
    if p.amputated == "arm":
        acc -= 8
    if game.is_dark() and not player_lit(game):
        acc -= 8
    return clamp(acc - evade, 12, 96)


def _head_chance(game, w: ItemDef) -> float:
    p = game.player
    base = 0.15 + w.head + 0.02 * p.style_rank(w.style)
    base += p.mod("head_ranged") if w.is_ranged else p.mod("head_melee")
    if w.style == "blunt":
        base += 0.08
    return clamp(base, 0.0, 0.85)


def _damage(game, w: ItemDef, item: Optional[Item], sneak: bool) -> float:
    p = game.player
    raw = game.rng.randint(*w.dmg)
    mult = 1.0 + 0.04 * p.style_rank(w.style)
    if not w.is_ranged:
        mult += p.mod("melee_dmg")
    if item is not None and w.durability and (item.dur or 0) < w.durability * 0.25:
        mult *= 0.8
    if p.stamina < STAMINA_PER_ATTACK + 1:
        mult *= 0.75
    if p.hunger >= 75:
        mult *= 0.85
    if sneak and not w.is_ranged:
        mult *= 2.0
    return raw * mult


def _wear_weapon(game, item: Optional[Item], w: ItemDef) -> None:
    if item is None or not w.durability:
        return
    if game.rng.random() < game.player.mod("dur_save"):
        return
    item.dur = (item.dur or 1) - 1
    if item.dur <= 0:
        game.player.weapon = None
        game.msg(f"Your {w.name} breaks!", "bad")


def _train(game, w: ItemDef, amount: int = 1) -> None:
    p = game.player
    before = p.style_rank(w.style)
    p.style_xp[w.style] = p.style_xp.get(w.style, 0) + amount
    if p.style_rank(w.style) > before:
        game.msg(f"Your skill with {w.style} weapons improves.", "good")


# ------------------------------------------------------------------ player attacks
def hurt_zombie(game, z: Zombie, raw: float, head: bool, style: str = "", fire: bool = False) -> int:
    """Apply damage honouring the preset's kill rule.  Returns the damage dealt."""
    profile = game.profile
    dmg = raw
    if head:
        dmg *= 3.0 if profile.kill_rule == "head" else 2.0
    else:
        if profile.kill_rule == "head":
            dmg *= 0.5
        if "tough" in z.flags:
            dmg *= 0.6
    if fire and profile.weakness in ("fire", "light"):
        dmg *= 2.0
    elif style == "energy" and profile.weakness == "light":
        dmg *= 1.3
    dealt = max(1, int(round(dmg)))
    z.hp -= dealt
    if z.hp <= 0:
        kill_zombie(game, z, head=head)
    else:
        z.state = "hunt"
        z.target = game.player.pos
        z.stimulus_turn = game.clock.turn
    return dealt


def kill_zombie(game, z: Zombie, head: bool = False, by_player: bool = True) -> None:
    level = game.level
    level.remove_actor(z)
    level.corpses[z.pos] = (game.clock.turn, z.fresh_human)
    for item in z.carries:
        level.drop(z.pos, item)
    if by_player:
        p = game.player
        p.kills += 1
        p.bump("zombies")
        levels = p.gain_xp(z.xp)
        p.panic = max(0.0, p.panic - 1.0)
        if levels:
            game.msg(f"You reach level {p.level}! (+1 perk point)", "good")
    if "explodes" in z.flags:
        burst(game, z.pos)
    if "boss" in z.flags and z.special == "stalker":
        game.on_stalker_killed()
    game.msg(f"The {z.name.lower()} {'collapses' if head else 'goes down'}.", "combat")


def burst(game, pos) -> None:
    """A bloater pops: a cloud of spores that infects the careless."""
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            p = (pos[0] + dx, pos[1] + dy)
            if game.level.walkable(*p) and dx * dx + dy * dy <= 5:
                game.level.hazards[p] = Hazard("spore", 9)
    game.msg("The bloater bursts in a cloud of spores!", "warn")
    game.emit_noise(pos, 6, "zombie")


def _sneak_ok(game, z: Zombie) -> bool:
    """True when the zombie has not noticed the player."""
    return z.state in ("idle", "dormant") or (z.state == "investigate" and not game.zombie_sees_player(z))


def player_attack(game, target: Actor) -> bool:
    """Melee (or polearm) attack.  Returns True if a turn was spent."""
    p = game.player
    w = weapon_def(game)
    if w.is_ranged:                                         # bashing with a gun
        w = FISTS
        item = None
        game.msg("You club it with the butt of your weapon.", "info")
    else:
        item = p.weapon
    d = cheb(p.pos, target.pos)
    if d > w.reach or (d > 1 and not has_los(game.level, p.pos, target.pos)):
        return False
    p.stamina = max(0.0, p.stamina - STAMINA_PER_ATTACK)
    noise = max(1, w.noise + (p.armor and game.item_def(p.armor.id).stealth or 0))
    game.emit_noise(p.pos, noise, "player")
    if isinstance(target, Human):
        return _attack_human(game, target, w, item)
    z: Zombie = target
    sneak = _sneak_ok(game, z)
    if sneak:
        hit = True
    else:
        hit = game.rng.random() * 100 < _accuracy(game, w, 0)
    if not hit:
        game.msg(f"You swing at the {z.name.lower()} and miss.", "combat")
        z.state, z.target, z.stimulus_turn = "hunt", p.pos, game.clock.turn
        return True
    head = sneak or game.rng.random() < _head_chance(game, w)
    dmg = hurt_zombie(game, z, _damage(game, w, item, sneak), head, w.style)
    _wear_weapon(game, item, w)
    _train(game, w)
    if z.hp > 0:
        verb = "stab" if w.style in ("blade", "polearm") else "smash" if w.style == "blunt" else "hit"
        game.msg(f"You {verb} the {z.name.lower()}{' in the head' if head else ''} for {dmg}.", "combat")
    elif sneak:
        game.msg("A silent kill.", "good")
    return True


def _attack_human(game, h: Human, w: ItemDef, item: Optional[Item]) -> bool:
    p = game.player
    if not h.hostile:
        game.make_hostile(h)
    if game.rng.random() * 100 >= _accuracy(game, w, 8):
        game.msg("You miss.", "combat")
        return True
    dmg = max(1, int(_damage(game, w, item, False)))
    h.hp -= dmg
    _wear_weapon(game, item, w)
    _train(game, w)
    if h.hp <= 0:
        kill_human(game, h)
    else:
        game.msg(f"You hit the {h.name.lower()} for {dmg}.", "combat")
    return True


def kill_human(game, h: Human) -> None:
    level = game.level
    level.remove_actor(h)
    level.corpses[h.pos] = (game.clock.turn, True)
    for item in h.loot:
        level.drop(h.pos, item)
    game.player.gain_xp(12)
    game.player.bump("humans")
    game.msg(f"The {h.name.lower()} falls.", "combat")
    if not h.hostile or h.role != "raider":
        game.adjust_humanity(-12, "You killed someone who was not trying to kill you.")


def player_fire(game, target: Actor) -> bool:
    """Ranged attack with the equipped weapon.  Returns True if a turn was spent."""
    p = game.player
    w = weapon_def(game)
    item = p.weapon
    if not w.is_ranged:
        game.msg("You have no ranged weapon equipped.", "warn")
        return False
    d = cheb(p.pos, target.pos)
    if d > w.reach:
        game.msg("Out of range.", "warn")
        return False
    if not has_los(game.level, p.pos, target.pos):
        game.msg("No clear line of fire.", "warn")
        return False
    if w.ammo and p.count(w.ammo) < 1:
        game.msg(f"Out of {game.item_def(w.ammo).name.lower()}.", "warn")
        return False
    if w.ammo and game.rng.random() >= p.mod("ammo_save"):
        p.take(w.ammo, 1)
    p.stamina = max(0.0, p.stamina - 2)
    noise = max(1, int(w.noise * (1.0 + p.mod("ranged_noise"))))
    game.emit_noise(p.pos, noise, "player")
    if isinstance(target, Human):
        if not target.hostile:
            game.make_hostile(target)
        evade, sneak = 8, False
    else:
        evade, sneak = 0, _sneak_ok(game, target)
    hit = game.rng.random() * 100 < _accuracy(game, w, evade, d) + (12 if sneak else 0)
    _wear_weapon(game, item, w)
    _train(game, w)
    if not hit:
        game.msg(f"Your shot misses the {target.name.lower()}.", "combat")
        if isinstance(target, Zombie):
            target.state, target.target, target.stimulus_turn = "hunt", p.pos, game.clock.turn
        return True
    if isinstance(target, Human):
        dmg = max(1, int(_damage(game, w, item, False)))
        target.hp -= dmg
        if target.hp <= 0:
            kill_human(game, target)
        else:
            game.msg(f"You hit the {target.name.lower()} for {dmg}.", "combat")
        return True
    head = game.rng.random() < _head_chance(game, w) + (0.2 if sneak else 0.0)
    dmg = hurt_zombie(game, target, _damage(game, w, item, False), head, w.style)
    if target.hp > 0:
        game.msg(f"You shoot the {target.name.lower()}{' in the head' if head else ''} for {dmg}.", "combat")
    return True


# ------------------------------------------------------------------ throwables
def throw(game, item_id: str, pos) -> bool:
    p = game.player
    d = game.item_def(item_id)
    reach = 8
    if cheb(p.pos, pos) > reach or not has_los(game.level, p.pos, pos):
        game.msg("You cannot throw it there.", "warn")
        return False
    p.take(item_id, 1)
    eff = d.effect
    if eff.get("fire"):
        game.msg(f"The {d.name.lower()} bursts into flames!", "info")
        radius = int(eff.get("radius", 1))
        lo, hi = eff.get("damage", (8, 14))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                q = (pos[0] + dx, pos[1] + dy)
                if not game.level.walkable(*q) or game.level.tile(*q) in (T.PORTAL, T.STAIRS_UP, T.STAIRS_DOWN):
                    continue
                game.level.hazards[q] = Hazard("fire", 8)
                victim = game.level.actor_at(*q)
                if isinstance(victim, Zombie):
                    hurt_zombie(game, victim, game.rng.randint(lo, hi), False, "fire", fire=True)
                elif isinstance(victim, Human):
                    victim.hp -= game.rng.randint(lo, hi)
                    if victim.hp <= 0:
                        kill_human(game, victim)
        game.emit_noise(pos, 8, "player")
    elif eff.get("noise"):
        game.msg(f"The {d.name.lower()} clatters and screams where it lands.", "info")
        game.emit_noise(pos, int(eff["noise"]), "decoy")
    return True


# ------------------------------------------------------------------ enemy attacks
def damage_player(game, amount: int, cause: str) -> None:
    p = game.player
    p.hp -= amount
    game.add_panic(3 + amount * 0.4)
    if p.hp <= 0:
        game.end("dead", cause)


def pick_limb(rng) -> str:
    roll = rng.random() * sum(w for _, w in LIMBS)
    for limb, weight in LIMBS:
        roll -= weight
        if roll <= 0:
            return limb
    return "arm"


def infect(game, source: str = "bite") -> None:
    """The infection takes hold (or progresses if you already carry it)."""
    p = game.player
    profile = game.profile
    if p.infected:
        p.infection_timer = max(1, p.infection_timer - 100)
        game.msg("Another wound feeds the infection. The clock runs faster.", "bad")
        return
    p.infected = True
    p.infection_timer = max(10, int(profile.incubation * game.diff.timer))
    p.bite_limb = "lungs" if source == "spore" else pick_limb(game.rng)
    window = max(8, min(30, profile.incubation // 3)) + int(p.mod("surgeon"))
    p.bite_window = window if p.bite_limb in ("arm", "leg") else 0
    if source == "spore":
        game.msg("You breathe in the spores. You are infected.", "bad")
    else:
        game.msg(f"You have been bitten ({p.bite_limb})! You are infected.", "bad")
        if p.bite_window:
            game.msg(f"Cutting it off might save you - but only for the next {p.bite_window} turns (X).", "warn")
    game.add_panic(25)


def zombie_attack(game, z: Zombie) -> None:
    p = game.player
    profile = game.profile
    if game.rng.random() * 100 >= clamp(z.acc - p.evade, 15, 92):
        game.msg(f"The {z.name.lower()} lunges and misses.", "combat")
        return
    armor = game.item_def(p.armor.id) if p.armor else None
    raw = game.rng.randint(*z.dmg) * game.diff.damage
    dmg = max(1, int(round(raw - (armor.defense if armor else 0))))
    if armor and p.armor.dur is not None:
        p.armor.dur -= 1
        if p.armor.dur <= 0:
            game.msg(f"Your {armor.name.lower()} falls apart!", "bad")
            p.armor = None
    game.msg(f"The {z.name.lower()} hits you for {dmg}.", "bad")
    damage_player(game, dmg, f"torn apart by {article(z.name)} {z.name.lower()}")
    if not p.alive:
        return
    guard = armor.bite_guard if armor else 0.0
    chance = profile.infect * (1.0 - guard) * (1.0 - p.mod("infect_resist"))
    if profile.vector == "spore":
        chance *= 0.5
    if game.rng.random() < chance:
        infect(game, "bite")
    if dmg >= 4 and game.rng.random() < 0.2 * (1.0 - p.mod("bleed_resist")):
        p.bleeding = min(3, p.bleeding + 1)
        game.msg("You are bleeding.", "bad")
    if ("breaker" in z.flags or "cripples" in z.flags) and not p.fracture and game.rng.random() < 0.2:
        p.fracture = True
        game.msg("Something snaps. Your leg is broken!", "bad")


def human_attack(game, h: Human) -> None:
    p = game.player
    d = cheb(h.pos, p.pos)
    if d > 1:
        if game.era.firearms:
            game.emit_noise(h.pos, 18, "zombie")
        else:
            game.emit_noise(h.pos, 4, "zombie")
    if game.rng.random() * 100 >= clamp(h.acc - p.evade - (d - 1) * 2, 12, 90):
        game.msg(f"The {h.name.lower()} {'shoots' if d > 1 else 'swings'} and misses.", "combat")
        return
    armor = game.item_def(p.armor.id) if p.armor else None
    dmg = max(1, int(round(game.rng.randint(*h.dmg) * game.diff.damage - (armor.defense if armor else 0))))
    game.msg(f"The {h.name.lower()} hits you for {dmg}.", "bad")
    damage_player(game, dmg, f"killed by {article(h.name)} {h.name.lower()}")


# ------------------------------------------------------------------ surgery
def can_amputate(game) -> Optional[str]:
    """Reason you cannot amputate, or None if you can."""
    p = game.player
    if not p.infected:
        return "You are not infected."
    if p.bite_limb not in ("arm", "leg"):
        return "The infection is not in a limb you can remove."
    if p.bite_window <= 0:
        return "Too late: it has already spread."
    carried = ([p.weapon] if p.weapon else []) + p.inventory
    has_blade = any(game.item_def(i.id).kind == "weapon" and game.item_def(i.id).style == "blade" for i in carried)
    if not has_blade:
        return "You need a blade."
    return None


def amputate(game) -> bool:
    reason = can_amputate(game)
    if reason:
        game.msg(reason, "warn")
        return False
    p = game.player
    limb = p.bite_limb
    p.infected = False
    p.infection_timer = 0
    p.bite_window = 0
    p.amputated = limb
    p.bleeding = 2
    p.hp = max(1, p.hp - 8)
    game.add_panic(max(5.0, 30.0 - 4.0 * p.mod("surgeon") / 8))
    game.emit_noise(p.pos, 7, "player")
    game.msg(f"You cut off your {limb}. The infection goes with it. You are bleeding badly.", "good")
    p.bump("amputations")
    return True
