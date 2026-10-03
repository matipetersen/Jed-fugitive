"""Behaviour of the living and the dead.

Only actors within ``ACTIVE_RADIUS`` of the player are simulated.  Zombies run
a small state machine: ``dormant`` (still until disturbed) -> ``idle`` (wanders)
-> ``investigate`` (heard something) -> ``hunt`` (knows where you are).
"""
from __future__ import annotations

from outbreak.engine import combat
from outbreak.engine import tiles as T
from outbreak.engine.fov import has_los
from outbreak.engine.model import Human, Zombie
from outbreak.engine.pathing import descend, greedy_step
from outbreak.util import DIRS8, cheb, dist

ACTIVE_RADIUS = 45
FOE_SIGHT = 5                 # how far a zombie notices a living person that is not the player
HUMAN_SIGHT = 8
FIGHTERS = ("raider", "scout", "soldier")
FIELD_RADIUS = 28
NO_ENTRY = (T.PORTAL, T.STAIRS_UP, T.STAIRS_DOWN)
DOOR_HP = 8
LOST_AFTER = 14               # turns a hunter keeps looking after losing you
TRAIL_LENGTH = 60


# ------------------------------------------------------------------ perception
def sight_range(game, z: Zombie) -> float:
    if "blind" in z.flags:
        return 0.0
    prof, p = game.profile, game.player
    r = z.sight
    if game.is_dark():
        r *= 0.6 * prof.night_sight
        if combat.player_lit(game):
            r = max(r, 6.0) * 1.7
    if p.sneaking:
        r *= 0.5
    if game.level.tile(*p.pos) == T.BRUSH:
        r *= 0.5
    if p.disguise_turns > 0 and prof.intel < 2 and (z.uid * 37) % 100 < prof.disguise * 100:
        r = min(r, 1.5)
    return r


def sees_player(game, z: Zombie) -> bool:
    p = game.player
    r = sight_range(game, z)
    if r <= 0 or dist(z.pos, p.pos) > r:
        return False
    return has_los(game.level, z.pos, p.pos)


def speed_now(game, z: Zombie) -> float:
    s = z.speed
    if game.is_dark():
        s *= game.profile.night_speed
    elif game.clock.is_day:
        s *= game.profile.day_speed
    if z.state == "idle":
        s *= 0.5
    return s


# ------------------------------------------------------------------ main loop
def run(game) -> None:
    level, p = game.level, game.player
    humans = [a for a in level.actors if isinstance(a, Human) and a.hp > 0 and a.role in FIGHTERS]
    for a in list(level.actors):
        if a.hp <= 0 or level.occ.get(a.pos) is not a or cheb(a.pos, p.pos) > ACTIVE_RADIUS:
            continue
        if isinstance(a, Zombie):
            _zombie(game, a, humans)
        elif isinstance(a, Human):
            _human(game, a, humans)


def _zombie(game, z: Zombie, humans) -> None:
    prof, level = game.profile, game.level
    if z.cooldown > 0:
        z.cooldown -= 1
    if prof.sun_burn and level.kind == "overworld" and game.clock.is_day:
        z.hp -= 2
        if z.hp <= 0:
            combat.kill_zombie(game, z, by_player=False)
            return
    z.energy += speed_now(game, z)
    steps = 0
    while z.energy >= 1.0 and steps < 3 and z.hp > 0 and level.occ.get(z.pos) is z:
        z.energy -= 1.0
        steps += 1
        _zombie_step(game, z, humans)


def nearest_foe(game, a, foes, limit: float):
    """The closest living foe of ``a`` within ``limit`` that it can see, or None."""
    level, best, best_d = game.level, None, limit + 1
    for f in foes:
        if f is a or f.hp <= 0:
            continue
        d = cheb(a.pos, f.pos)
        if d < best_d and has_los(level, a.pos, f.pos):
            best, best_d = f, d
    return best


def _zombie_fight(game, z: Zombie, foe: Human) -> None:
    z.state, z.target, z.stimulus_turn = "hunt", foe.pos, game.clock.turn
    if cheb(z.pos, foe.pos) == 1:
        combat.attack_actor(game, z, foe)
        return
    nxt = greedy_step(game.level, z.pos, foe.pos, game.rng, can_pass=lambda n: _passable(game, z, n))
    if nxt is not None:
        _move_or_bash(game, z, nxt)


def _zombie_step(game, z: Zombie, humans=()) -> None:
    p, prof = game.player, game.profile
    turn = game.clock.turn
    d = cheb(z.pos, p.pos)
    seen = sees_player(game, z)
    if humans and z.state != "dormant":
        foe = nearest_foe(game, z, humans, FOE_SIGHT)
        if foe is not None and (not seen or cheb(z.pos, foe.pos) < d):
            _zombie_fight(game, z, foe)
            return
    if z.state == "dormant":
        if seen and d <= max(2.0, sight_range(game, z) * 0.5):
            z.state = "hunt"
        else:
            return
    if seen:
        if z.state != "hunt":
            _spotted(game, z)
        z.state, z.target, z.stimulus_turn = "hunt", p.pos, turn
    elif z.state == "hunt":
        _lost_sight(game, z, d)
    if prof.dormant_after and z.state in ("hunt", "investigate") and turn - z.stimulus_turn > prof.dormant_after:
        z.state, z.target = "dormant", None
        return
    if z.state in ("hunt", "investigate") and z.target is not None:
        _pursue(game, z, d, seen)
    elif z.state == "idle" and game.level.kind == "overworld" and game.rng.random() < 0.35:
        _wander(game, z)


def _spotted(game, z: Zombie) -> None:
    if "screams" in z.flags and z.cooldown <= 0:
        z.cooldown = 40
        game.msg(f"The {z.name.lower()} screams!", "warn")
        game.emit_noise(z.pos, 22, "zombie")
        game.add_heat(6)


def _lost_sight(game, z: Zombie, d: int) -> None:
    p, prof = game.player, game.profile
    if "relentless" in z.flags and d <= 45:
        z.target = p.pos                                  # nothing shakes a stalker
        return
    if prof.smell and game.clock.turn - z.stimulus_turn < 25:
        spot = game.scent_near(z.pos, prof.smell)
        if spot:
            z.target = spot
            return
    if game.clock.turn - z.stimulus_turn > LOST_AFTER:
        z.state, z.target = "idle", None


def _pursue(game, z: Zombie, d: int, seen: bool) -> None:
    p, level = game.player, game.level
    if d == 1 and (seen or z.target == p.pos):
        combat.zombie_attack(game, z)
        return
    if "leaps" in z.flags and seen and 2 <= d <= 4 and z.cooldown <= 0:
        spot = level.free_spot_near(p.x, p.y, 1)
        if spot and cheb(spot, z.pos) <= 4:
            level.move_actor(z, *spot)
            z.cooldown = 8
            game.msg(f"The {z.name.lower()} leaps at you!", "bad")
            combat.zombie_attack(game, z)
            return
    if z.target is not None and cheb(z.pos, z.target) == 0:
        if z.state == "investigate":
            z.state, z.target = "idle", None
        return
    nxt = None
    if z.target == p.pos:
        field = game.get_field()
        if z.pos in field:
            nxt = descend(level, field, z.pos, game.rng, blocked=_hazard_tiles(game, z))
    if nxt is None and z.target is not None:
        nxt = greedy_step(level, z.pos, z.target, game.rng, can_pass=lambda n: _passable(game, z, n))
    if nxt is None:
        if z.state == "investigate":
            z.state, z.target = "idle", None
        return
    _move_or_bash(game, z, nxt)


def _passable(game, z: Zombie, pos) -> bool:
    t = game.level.tile(*pos)
    if t in NO_ENTRY:
        return False
    if t == T.FENCE:
        return game.profile.swarm
    hz = game.level.hazards.get(pos)
    return not (hz and hz.kind == "fire" and game.profile.intel >= 1)


def _hazard_tiles(game, z: Zombie):
    if game.profile.intel < 1:
        return None
    return {pos for pos, hz in game.level.hazards.items() if hz.kind == "fire"}


def _move_or_bash(game, z: Zombie, nxt) -> None:
    level = game.level
    t = level.tile(*nxt)
    if t in NO_ENTRY:
        return
    if t == T.DOOR:
        if game.profile.intel >= 1:
            level.set_tile(nxt[0], nxt[1], T.DOOR_OPEN)
            return
        _bash_door(game, z, nxt)
        return
    if nxt in level.occ:
        return
    level.move_actor(z, *nxt)


def _bash_door(game, z: Zombie, pos) -> None:
    level = game.level
    power = 6 if "breaker" in z.flags else 2
    if game.profile.swarm:
        power *= 1 + sum(1 for dx, dy in DIRS8 if isinstance(level.occ.get((pos[0] + dx, pos[1] + dy)), Zombie))
    hp = level.door_hp.get(pos, DOOR_HP) - power
    level.door_hp[pos] = hp
    game.emit_noise(pos, 6, "zombie")
    if hp <= 0:
        level.set_tile(pos[0], pos[1], T.FLOOR)
        level.door_hp.pop(pos, None)
        if cheb(pos, game.player.pos) <= 12:
            game.msg("A door splinters and gives way.", "warn")


def _wander(game, z: Zombie) -> None:
    dx, dy = game.rng.choice(DIRS8)
    n = (z.x + dx, z.y + dy)
    if game.level.walkable(*n) and _passable(game, z, n) and n not in game.level.occ \
            and game.level.tile(*n) != T.DOOR:
        game.level.move_actor(z, *n)


# ------------------------------------------------------------------ humans
def _foes_of(h: Human, game, humans):
    """Everything this human will shoot at that is not the player: the dead, and the other side."""
    out = list(z for z in game.level.actors if isinstance(z, Zombie) and z.hp > 0)
    mine = h.faction == "raiders"
    out += [o for o in humans if o is not h and (o.faction == "raiders") != mine]
    return out


def _human(game, h: Human, humans) -> None:
    if h.role not in FIGHTERS:
        return                                                    # shopkeepers and healers keep out of it
    p, level = game.player, game.level
    d = cheb(h.pos, p.pos)
    seen = h.hostile and d <= 11 and has_los(level, h.pos, p.pos)
    foe = nearest_foe(game, h, _foes_of(h, game, humans), HUMAN_SIGHT if h.reach > 1 else FOE_SIGHT)
    if h.state == "follow" and d > 10:
        foe = None                                                # a companion does not chase far from you
    if foe is not None and not (seen and d < cheb(h.pos, foe.pos)):
        _human_fight(game, h, foe)
        return
    if seen:
        h.state, h.target = "hunt", p.pos
    if h.state == "follow":
        _follow_step(game, h)
        return
    if h.state == "patrol":
        _patrol_step(game, h)
        return
    if h.state != "hunt" or not h.hostile:
        return
    if h.hp < h.max_hp * 0.3 and seen:
        _flee(game, h, p.pos)
        return
    if h.reach > 1 and seen and 2 <= d <= h.reach:
        combat.human_attack(game, h)
        return
    if d == 1:
        combat.human_attack(game, h)
        return
    field = game.get_field()
    nxt = descend(level, field, h.pos, game.rng) if h.pos in field else None
    if nxt is None:
        nxt = greedy_step(level, h.pos, p.pos, game.rng, can_pass=lambda n: level.tile(*n) not in NO_ENTRY)
    _human_move(game, h, nxt)


def _human_move(game, h: Human, nxt) -> bool:
    level = game.level
    if nxt and nxt not in level.occ and level.tile(*nxt) not in NO_ENTRY:
        if level.tile(*nxt) == T.DOOR:
            level.set_tile(nxt[0], nxt[1], T.DOOR_OPEN)
        else:
            level.move_actor(h, *nxt)
        return True
    return False


def _human_fight(game, h: Human, foe) -> None:
    level = game.level
    d = cheb(h.pos, foe.pos)
    if h.hp < h.max_hp * 0.3 and isinstance(foe, Zombie) and d <= 2:
        _flee(game, h, foe.pos)
        return
    ranged = h.reach > 1
    if ranged and 2 <= d <= h.reach:
        combat.attack_actor(game, h, foe, ranged=True)
    elif d == 1:
        combat.attack_actor(game, h, foe)
    else:                                                         # close the distance
        nxt = greedy_step(level, h.pos, foe.pos, game.rng, can_pass=lambda n: level.tile(*n) not in NO_ENTRY)
        _human_move(game, h, nxt)


def _patrol_step(game, h: Human) -> None:
    """Walk to the group's current waypoint, every other tick; pick a new one on arrival."""
    if game.clock.turn % 2:
        return
    goals = game.patrol_goals
    goal = goals.get(h.group)
    if goal is None or cheb(h.pos, goal) <= 2 or h.stuck > 8:
        nodes = game.patrol_nodes
        if not nodes:
            return
        goal = game.rng.choice(nodes)
        goals[h.group] = goal
        h.stuck = 0
    nxt = greedy_step(game.level, h.pos, goal, game.rng, can_pass=lambda n: game.level.tile(*n) not in NO_ENTRY)
    if nxt is None or not _human_move(game, h, nxt):
        h.stuck += 1


def _follow_step(game, h: Human) -> None:
    """A companion stays close to the player."""
    p, level = game.player, game.level
    if p.humanity < 20:
        h.state = "patrol"
        game.msg(f"The {h.name.lower()} looks at what you have become, and walks away.", "warn")
        return
    if cheb(h.pos, p.pos) <= 2:
        return
    field = game.get_field()
    nxt = descend(level, field, h.pos, game.rng) if h.pos in field else None
    if nxt is None:
        nxt = greedy_step(level, h.pos, p.pos, game.rng, can_pass=lambda n: level.tile(*n) not in NO_ENTRY)
    _human_move(game, h, nxt)


# ------------------------------------------------------------------ far away, in the abstract
ABSTRACT_EVERY = 20
ABSTRACT_STEPS = 5
ABSTRACT_RANGE = 10


def abstract_run(game) -> None:
    """Patrols beyond the simulated radius still walk and still fight, in coarse strokes."""
    if game.level is not game.world.level or game.clock.turn % ABSTRACT_EVERY:
        return
    lv, p = game.world.level, game.player
    groups = {}
    for a in lv.actors:
        if isinstance(a, Human) and a.role in ("scout", "soldier") and a.state == "patrol" and a.hp > 0 \
                and cheb(a.pos, p.pos) > ACTIVE_RADIUS:
            groups.setdefault(a.group, []).append(a)
    for gid, members in groups.items():
        _abstract_fight(game, members)
        members = [m for m in members if m.hp > 0]
        if members:
            _abstract_move(game, gid, members)


def _abstract_move(game, gid: int, members) -> None:
    lv = game.world.level
    goal = game.patrol_goals.get(gid)
    if goal is None or any(cheb(m.pos, goal) <= 2 for m in members):
        if not game.patrol_nodes:
            return
        goal = game.rng.choice(game.patrol_nodes)
        game.patrol_goals[gid] = goal
    for m in members:
        for _ in range(ABSTRACT_STEPS):
            nxt = greedy_step(lv, m.pos, goal, game.rng, can_pass=lambda n: lv.tile(*n) not in NO_ENTRY)
            if nxt is None or not _human_move(game, m, nxt):
                break


def _abstract_fight(game, members) -> int:
    """Resolve a skirmish between a far-off patrol and whatever is near it.  Returns foes killed."""
    lv, p, rng = game.world.level, game.player, game.rng
    lead = members[0]
    foes = [a for a in lv.actors if a.hp > 0 and cheb(a.pos, lead.pos) <= ABSTRACT_RANGE and cheb(a.pos, p.pos) > ACTIVE_RADIUS
            and (isinstance(a, Zombie) or (isinstance(a, Human) and a.faction == "raiders"))]
    hordes = [h for h in game.hordes if cheb(h.pos, lead.pos) <= ABSTRACT_RANGE]
    if not foes and not hordes:
        return 0
    foe_power = sum(1.8 if isinstance(a, Human) else 0.8 for a in foes) + sum(0.7 * h.size for h in hordes)
    power = sum(1.6 if m.role == "soldier" else 1.2 for m in members) * (0.6 + rng.random() * 0.8)
    killed = 0
    foes.sort(key=lambda a: cheb(a.pos, lead.pos))
    for a in foes:
        cost = 1.8 if isinstance(a, Human) else 0.9
        if power < cost:
            break
        power -= cost
        killed += 1
        if isinstance(a, Zombie):
            combat.kill_zombie(game, a, by_player=False)
        else:
            lv.remove_actor(a)
            lv.corpses[a.pos] = (game.clock.turn, True)
    for h in hordes:
        n = min(h.size, int(power / 0.9))
        power -= n * 0.9
        h.size -= n
        killed += n
        if h.size <= 1 and h in game.hordes:
            game.hordes.remove(h)
    damage = foe_power * (0.5 + rng.random()) * 3.0
    killer = foes[0] if foes else lead
    for m in sorted(members, key=lambda _m: rng.random()):
        if damage <= 0:
            break
        hit = min(damage, rng.randint(6, 14))
        damage -= hit
        m.hp -= int(hit)
        if m.hp <= 0:
            combat.kill_human_other(game, m, killer)
    return killed


def _flee(game, h: Human, away_from) -> None:
    level = game.level
    best, best_d = None, cheb(h.pos, away_from)
    for dx, dy in DIRS8:
        n = (h.x + dx, h.y + dy)
        if level.free(*n) and level.tile(*n) not in NO_ENTRY and cheb(n, away_from) > best_d:
            best, best_d = n, cheb(n, away_from)
    if best:
        level.move_actor(h, *best)
