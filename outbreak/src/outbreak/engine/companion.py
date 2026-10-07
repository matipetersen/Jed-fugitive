"""One companion at a time: someone with a name, a strength, a flaw, a bond with you, and a death that sticks.

Anyone who is not hostile can become your companion (``recruit``).  The profile they get comes from who they are (a healer
is a medic) and from their id.  Strengths and flaws are small, regular effects applied from ``tick``; the bond between you
grows when you spend time together and win, and shrinks when you do things they cannot stand.  When the bond breaks they
leave; when they die, they stay dead, and the log says so.
"""
from __future__ import annotations

import random
from typing import Optional

from outbreak.content.companions import (ARCHETYPES, BY_ID, FLAWS, NAMES, ROLE_ARCHETYPE, SITUATION_LINES, STRENGTHS)
from outbreak.engine import tiles as T
from outbreak.engine.model import Human, Item
from outbreak.util import cheb, compass

BOND_START_STRANGER = 10
BOND_START_ALLY = 25
BOND_LEAVES = 5
STORY_AT = (35, 60, 85)                       # bond at which each part of their story comes out
SAY_EVERY = (110, 230)
WANDER_NOISE = 6
MEDIC_EVERY, TINKER_EVERY, HUNGRY_EVERY, LOUD_EVERY, CALM_EVERY, SCOUT_EVERY = 60, 60, 160, 25, 8, 4


# ------------------------------------------------------------------ who they are
def person_rng(game, uid: int) -> random.Random:
    return random.Random(f"{game.seed}:person:{uid}")        # their own stream: it never disturbs the world's


def ensure_person(game, h: Human, archetype: Optional[str] = None) -> None:
    """Give someone a personal name and a profile (once), fixed by who they are."""
    if h.trait:
        return
    rng = person_rng(game, h.uid)
    pick = archetype or (ROLE_ARCHETYPE.get(h.role) if h.role in ("healer", "trader", "scholar") or h.uid % 3 else None)
    arch = BY_ID.get(pick) if pick else rng.choice(ARCHETYPES)
    taken = {n for n, _ in getattr(game, "fallen_allies", [])} | {a.name for a in game.world.level.actors if isinstance(a, Human) and a.trait}
    names = [n for n in NAMES if n not in taken] or list(NAMES)
    h.name = rng.choice(names)
    h.trait = arch.id
    h.glyph = h.name[0].upper()
    h.max_hp = h.hp = arch.hp
    h.dmg, h.acc = arch.dmg, arch.acc
    if (game.era.firearms or game.era.tech == 0) and arch.id in ("veteran", "hunter"):
        h.reach = 6
        h.mag = h.ammo = 8 if game.era.firearms else 0
    elif h.reach > 1:
        h.reach = 1


def arch_of(h: Human):
    return BY_ID.get(h.trait)


def current(game) -> Optional[Human]:
    """The companion, if you have one and they are alive and with you (on the open map)."""
    uid = getattr(game, "companion_uid", 0)
    if not uid:
        return None
    for a in game.world.level.actors:
        if isinstance(a, Human) and a.uid == uid and a.hp > 0 and a.state in ("follow", "wait"):
            return a
    return None


def say(game, c: Human, text: str) -> None:
    game.msg(f"{c.name}: {text}", "ally")


def note(game, text: str, key: bool = False) -> None:
    game.msg(text, "ally", key=key)


def add_bond(c: Human, n: int) -> None:
    c.bond = max(0, min(100, c.bond + n))


def describe(c: Human) -> str:
    a = arch_of(c)
    if a is None:
        return c.name
    return f"{c.name}, {a.label}. Good at it: {STRENGTHS[a.strength]}. Trouble: {FLAWS[a.flaw]}."


def bond_word(c: Human) -> str:
    return ("a stranger", "wary of you", "getting used to you", "a friend", "someone who would die for you")[min(4, c.bond // 22)]


# ------------------------------------------------------------------ joining and leaving
def refusal(game, npc: Human) -> str:
    if npc.hostile:
        return "They would sooner shoot you."
    if game.player.humanity < 20:
        return "They will not follow what you have become."
    if current(game) is not None:
        return "You already travel with someone. Only one can keep up with you."
    if npc.role in ("scout", "soldier"):
        trusted = game.rep.get(npc.faction, 0) >= 15 or game.aided.get(npc.group) is True
        if not trusted:
            return "They do not know you well enough to follow you. Earn their trust: answer a call for help, or do them a favour."
    elif npc.role in ("trader", "healer", "scholar"):
        if game.rep.get("enclave", 0) < 20 and game.player.humanity < 50:
            return "They have a place here, and you have not given them a reason to leave it. Be better known, or better liked."
    return ""


def recruit(game, npc: Human, archetype: Optional[str] = None, bond: int = BOND_START_STRANGER) -> None:
    """Bring ``npc`` into your life.  They may have to be brought out of the building they live in."""
    ensure_person(game, npc, archetype)
    world = game.world.level
    if npc not in world.actors:
        for lv in game.levels.values():
            if npc in lv.actors:
                lv.remove_actor(npc)
        spot = world.free_spot_near(game.player.x, game.player.y, 3) if game.level is world else None
        if spot is None:
            site = next((p for p in game.pois.values() if p.kind == "refuge"), None)
            spot = world.free_spot_near(site.x, site.y + 1, 4) if site else world.free_spot_near(*game.world.start, 4)
        if spot is None:
            return
        npc.x, npc.y = spot
        world.add_actor(npc)
    npc.state, npc.hostile, npc.talked = "follow", False, True
    npc.bond = max(npc.bond, bond)
    npc.since = game.clock.turn
    npc.nextsay = game.clock.turn + 80
    game.companion_uid = npc.uid
    a = arch_of(npc)
    note(game, f"{npc.name} the {a.label} joins you.", key=True)
    say(game, npc, a.intro)
    note(game, f"  Good at it: {STRENGTHS[a.strength]}. Trouble: {FLAWS[a.flaw]}.")


def release(game, c: Human, why: str, state: str = "patrol") -> None:
    c.state = state
    game.companion_uid = 0
    if c.group and game.patrol_nodes:
        game.patrol_goals[c.group] = game.rng.choice(game.patrol_nodes)
    note(game, why, key=True)


def dismiss(game, c: Human) -> str:
    release(game, c, f"{c.name} goes their own way.")
    return f"{c.name} nods and goes their own way."


def toggle_wait(game, c: Human) -> str:
    if c.state == "follow":
        c.state = "wait"
        return f"{c.name} stays where they are and keeps watch."
    c.state = "follow"
    return f"{c.name} falls in beside you again."


# ------------------------------------------------------------------ the effects, every turn
def tick(game) -> None:
    c = current(game)
    if c is None or game.level is not game.world.level or arch_of(c) is None:
        return
    t, p, a = game.clock.turn, game.player, arch_of(c)
    near = cheb(c.pos, p.pos) <= 10
    if t % 100 == 0:
        add_bond(c, 1)
    if t % 15 == 0 and c.hp < c.max_hp and not any(True for z in game.visible_hostiles() if cheb(z.pos, c.pos) <= 6):
        c.hp += 1
    if p.humanity < 20:
        release(game, c, f"{c.name} looks at what you have become, and walks away.")
        return
    if c.bond <= BOND_LEAVES:
        say(game, c, "\"I am done. I cannot do this with you.\"")
        release(game, c, f"{c.name} leaves you.")
        return
    if near:
        _strength(game, c, a.strength, t)
        _flaw(game, c, a.flaw, t)
    _chatter(game, c, t)
    _watch(game, c, t)


def _strength(game, c: Human, s: str, t: int) -> None:
    p = game.player
    if s == "medic" and t >= c.nextfx and cheb(c.pos, p.pos) <= 6 and (p.hp < p.max_hp * 0.6 or p.bleeding):
        c.nextfx = t + MEDIC_EVERY
        p.hp = min(p.max_hp, p.hp + 8)
        p.bleeding = 0
        add_bond(c, 1)
        say(game, c, "\"Hold still.\"")
        note(game, f"{c.name} dresses your wounds. (+8)")
    elif s == "calm" and t % CALM_EVERY == 0 and p.panic > 20:
        game.add_panic(-3, raw=True)
    elif s == "tinker" and t % TINKER_EVERY == 0 and p.weapon is not None and p.weapon.dur is not None:
        d = game.item_def(p.weapon.id)
        if d.durability and p.weapon.dur < d.durability:
            p.weapon.dur = min(d.durability, p.weapon.dur + 2)
            if t % (TINKER_EVERY * 3) == 0:
                say(game, c, "\"Your grip was loose. Better now.\"")
    elif s == "scout" and t % SCOUT_EVERY == 0:
        _spot(game, c)


def _spot(game, c: Human) -> None:
    """A scout sees what lies in wait before you walk into it."""
    lv = game.level
    for h in lv.actors:
        if isinstance(h, Human) and h.hidden and cheb(h.pos, c.pos) <= 8:
            h.hidden = False
            h.state = "idle"
            say(game, c, "\"Down! There, in the cover. They are waiting for us.\"")
            note(game, f"{c.name} spots an ambush.")
            add_bond(c, 2)
            return
    for pos, hz in lv.hazards.items():
        if hz.kind == "snare" and hz.hidden and cheb(pos, c.pos) <= 6:
            hz.hidden = False
            say(game, c, "\"Wire. Do not step there.\"")
            return


def _flaw(game, c: Human, f: str, t: int) -> None:
    p = game.player
    if f == "loud" and t % LOUD_EVERY == 0 and game.rng.random() < 0.3:
        game.emit_noise(c.pos, WANDER_NOISE, "player")
        note(game, f"{c.name} knocks something over. That was loud.")
    elif f == "hungry" and t >= c.nextfx2 and t - c.since >= HUNGRY_EVERY:
        c.nextfx2 = t + HUNGRY_EVERY
        food = next((i for i in p.inventory if game.item_def(i.id).kind == "food"), None)
        if food is not None:
            p.take(food.id, 1)
            note(game, f"{c.name} takes {game.item_def(food.id).name.lower()} from your pack without asking.")
        else:
            add_bond(c, -2)
            say(game, c, "\"I have not eaten in a day. Are we going to do something about that?\"")


def _chatter(game, c: Human, t: int) -> None:
    if t < c.nextsay or game.visible_hostiles():
        return
    rng = game.rng
    c.nextsay = t + rng.randint(*SAY_EVERY)
    p, a = game.player, arch_of(c)
    pool = []
    if p.hp < p.max_hp * 0.4:
        pool += SITUATION_LINES["hurt"]
    if game.is_dark():
        pool += SITUATION_LINES["night"]
    if game.weather in SITUATION_LINES and game.weather != "clear":
        pool += SITUATION_LINES[game.weather]
    from outbreak.engine import wild
    if wild.forest_here(game):
        pool += SITUATION_LINES["forest"]
    if getattr(game.cfg, "needs", False) and p.hunger > 60:
        pool += SITUATION_LINES["hungry"]
    pool += list(a.idle) * 2
    say(game, c, rng.choice(pool))


def _watch(game, c: Human, t: int) -> None:
    """Warn of what they see before you do."""
    if t % 6 or t < c.nextwarn:
        return
    for z in game.level.actors:
        if z.hp > 0 and getattr(z, "special", None) and cheb(z.pos, c.pos) <= 9 and z.pos not in game.visible \
                and z.state not in ("dormant",):
            c.nextwarn = t + 60
            say(game, c, f"\"{compass(z.x - c.x, z.y - c.y).capitalize()}! Something is moving.\"")
            return


# ------------------------------------------------------------------ moments
def on_enter(game, target) -> None:
    c = current(game)
    if c is None or arch_of(c) is None:
        return
    poi = game.poi_of_level(target)
    if poi is not None and poi.kind == "cave":
        say(game, c, SITUATION_LINES["cave"][0])
    else:
        say(game, c, "\"I will keep watch out here.\"")
    add_bond(c, 0)


def on_return(game) -> None:
    """You come out of a building: whoever waited outside has been busy."""
    c = current(game)
    if c is None or arch_of(c) is None:
        return
    s = arch_of(c).strength
    rng = game.rng
    if s in ("scavenger", "lucky") and rng.random() < (0.45 if s == "scavenger" else 0.35):
        item = rng.choice(["scrap", "cloth", "wood", "food", "bandage"] + (["chem"] if s == "lucky" else []))
        if item in game.items:
            game.give_item(Item(item, rng.randint(1, 2)))
            say(game, c, f"\"While you were in there I found this. {game.item_def(item).name}. You are welcome.\"")
            add_bond(c, 1)
            if s == "lucky" and rng.random() < 0.5:
                game.player.coins += rng.randint(1, 4)
    elif rng.random() < 0.3:
        say(game, c, "\"Nothing out here. Good. Let us keep it that way.\"")


def on_ally_kill(game, c: Human, victim) -> None:
    c.kills += 1
    add_bond(c, 1)
    a = arch_of(c)
    if a and game.rng.random() < 0.35:
        say(game, c, game.rng.choice(a.kill))


def on_player_kills_human(game, victim: Human) -> None:
    """You killed a person who was not trying to kill you: it is not forgotten."""
    c = current(game)
    if c is None or arch_of(c) is None or victim is c:
        return
    if victim.hostile:
        return
    a = arch_of(c)
    if a.flaw == "pacifist":
        add_bond(c, -15)
        say(game, c, "\"No. No, no. That was a person.\"")
    else:
        add_bond(c, -4)
        say(game, c, "\"Did they have to die?\"")


def on_hurt(game, c: Human) -> None:
    a = arch_of(c)
    if a and game.rng.random() < 0.3:
        say(game, c, game.rng.choice(a.hurt))


def on_death(game, h: Human, killer=None) -> None:
    if h.uid != getattr(game, "companion_uid", 0):
        return
    a = arch_of(h)
    days = max(0, (game.clock.turn - h.since) // 240)
    by = f" at the hands of {killer.name.lower()}" if killer is not None and not isinstance(killer, str) else ""
    note(game, f"{h.name} is dead{by}. {days} day{'s' if days != 1 else ''} together, {h.kills} kill{'s' if h.kills != 1 else ''}. "
               f"Gone for good.", key=True)
    if a:
        note(game, f"You remember what {h.name} said: {a.farewell}")
    fallen = getattr(game, "fallen_allies", None)
    if fallen is None:
        fallen = game.fallen_allies = []
    fallen.append((h.name, f"{a.label if a else 'survivor'}, {days}d, {h.kills} kills"))
    game.companion_uid = 0
    game.add_panic(12 + h.bond / 5, raw=True)
    if h.bond >= 50:
        game.adjust_humanity(-3, "")


# ------------------------------------------------------------------ talking
def talk(game, c: Human) -> str:
    a = arch_of(c)
    t = game.clock.turn
    if c.story < 3 and c.bond >= STORY_AT[c.story]:
        line = a.backstory[c.story]
        c.story += 1
        reward = _reward(game, c)
        say(game, c, line)
        return f"{c.name}: {line}\n{reward}"
    line = game.rng.choice(list(a.idle) + [l for l in SITUATION_LINES["night" if game.is_dark() else "warning"]][:1])
    if t - c.lasttalk > 200:
        add_bond(c, 1)
    c.lasttalk = t
    game._spend(1)
    return f"{c.name}: {line}"


def _reward(game, c: Human) -> str:
    n = c.story
    if n == 1:
        add_bond(c, 2)
        if game.reveal_random_lead():
            return f"{c.name} shares something they know: a lead is on your map."
        return f"{c.name} seems lighter for having said it."
    if n == 2:
        game.give_item(Item("medkit" if "medkit" in game.items else "bandage", 1))
        add_bond(c, 2)
        return f"{c.name} hands you a medkit they had been saving."
    c.max_hp += 6
    c.hp = c.max_hp
    game.player.max_hp += 3
    game.player.hp = min(game.player.max_hp, game.player.hp + 3)
    return f"You would trust {c.name} with your life. Something in you steadies. (+3 max health; {c.name} +6)"


def give(game, c: Human, index: int) -> str:
    p = game.player
    if not 0 <= index < len(p.inventory):
        return ""
    it = p.inventory[index]
    d = game.item_def(it.id)
    if d.kind == "food":
        p.take(it.id, 1)
        add_bond(c, 4)
        c.nextfx2 = game.clock.turn + HUNGRY_EVERY
        say(game, c, "\"Thank you. I mean it.\"")
        return f"{c.name} eats gratefully."
    if d.kind == "med":
        if c.hp >= c.max_hp:
            return f"{c.name} is not hurt."
        p.take(it.id, 1)
        c.hp = min(c.max_hp, c.hp + int(d.effect.get("heal", 6)))
        add_bond(c, 3)
        say(game, c, "\"You did not have to.\"")
        return f"You patch {c.name} up."
    return f"{c.name} has no use for the {d.name.lower()}."


def advice(game) -> str:
    """Their read on what to do next, in their own voice."""
    c = current(game)
    p = game.player
    todo = next((text for text, done in game.objectives() if not done), None)
    bits = []
    if p.hp < p.max_hp * 0.5:
        bits.append("You are hurt: patch yourself up first.")
    if getattr(game.cfg, "needs", False) and p.hunger > 60:
        bits.append("You need to eat.")
    if todo:
        bits.append(f"What we came for: {todo}.")
    site = game.pois.get(game.final_site_id)
    if site is not None and site.revealed:
        bits.append(f"{site.name} is {compass(site.x - p.x, site.y - p.y)}, {cheb(site.pos, p.pos)} tiles.")
    lead = next((q for q in game.pois.values() if q.lead and not q.done and q.component), None)
    if lead is not None:
        bits.append(f"A lead: {lead.name}, {compass(lead.x - p.x, lead.y - p.y)}, {cheb(lead.pos, p.pos)} tiles.")
    return f"{c.name}: " + " ".join(bits or ["Keep moving and keep quiet."])


# ------------------------------------------------------------------ the AI's questions
def flee_below(h: Human) -> float:
    a = arch_of(h)
    return 0.6 if a and a.flaw == "coward" else 0.3


def refuses_to_fight(h: Human, foe) -> bool:
    a = arch_of(h)
    return bool(a and a.flaw == "pacifist" and isinstance(foe, Human))


def is_reckless(h: Human) -> bool:
    a = arch_of(h)
    return bool(a and a.flaw == "reckless")


# ------------------------------------------------------------------ the start
def spawn_start(game) -> None:
    """You do not begin alone: someone is already with you."""
    rng = random.Random(f"{game.seed}:companion")
    arch = rng.choice(ARCHETYPES)
    lv, p = game.world.level, game.player
    spot = lv.free_spot_near(p.x, p.y, 3)
    if spot is None:
        return
    h = Human(game.next_uid(), "Survivor", "S", spot[0], spot[1], 30, 30, role="survivor", faction="enclave", hostile=False,
              state="follow")
    ensure_person(game, h, arch.id)
    lv.add_actor(h)
    h.bond, h.since, h.nextsay = BOND_START_ALLY, 0, 90
    game.companion_uid = h.uid
    a = arch_of(h)
    note(game, f"{h.name} the {a.label} is with you.", key=True)
    say(game, h, a.intro)
    note(game, f"  Good at it: {STRENGTHS[a.strength]}. Trouble: {FLAWS[a.flaw]}.")


def offer_stranger(game, chance: float) -> None:
    """Someone you helped asks to come along (if you travel alone), or thanks you and goes."""
    if game.rng.random() >= chance:
        return
    lv, p = game.world.level, game.player
    if game.level is not lv or current(game) is not None:
        return
    spot = lv.free_spot_near(p.x, p.y, 3)
    if spot is None:
        return
    h = Human(game.next_uid(), "Survivor", "S", spot[0], spot[1], 30, 30, role="survivor", faction="enclave", hostile=False,
              state="follow")
    lv.add_actor(h)
    recruit(game, h, None, bond=15)
