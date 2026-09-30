"""The opening escape: Sith squads land around the crash site and close in.

Story beat: your ship went down with Sith fighters on its tail. Before the
dust settles, dropships put squads in a ring around the wreck. The ring
tightens every tick; troopers that spot you break formation and chase. Get
past the ring and you are free (for now: the Fanatic picks up your trail later).

Design constraints kept from the rest of the game:
* squads are ordinary Sith enemies (same stats/AI once they spot you);
* the ring leaves gaps between squads, so escaping is about reading the
  formation and moving, not a forced fight;
* everything is tick based, so it plays the same in turn-based and real-time.
"""
import math
import random

from jedi_fugitive.game.level import Display

BLOCKING = frozenset(('#', '~', 'r', 'T'))


class Cordon:
    def __init__(self, center, radius, start_turn):
        self.center = center
        self.radius0 = float(radius)
        self.radius = float(radius)
        self.start_turn = start_turn
        self.active = True
        self.escaped = False
        self.units = []
        self.landings = []       # (x, y) where dropships touched down (for the renderer)
        self.grace = 5           # ticks before the ring starts to tighten
        self.shrink = 0.4        # tiles per tick
        self.min_radius = 2.5
        self.escape_margin = 6

    @property
    def escape_radius(self):
        return self.radius0 + self.escape_margin


def _free_tile(game, x, y, max_r=5):
    gm = game.game_map
    mh = len(gm)
    mw = len(gm[0]) if mh else 0
    occupied = {(getattr(e, 'x', None), getattr(e, 'y', None)) for e in getattr(game, 'enemies', []) or []}
    for r in range(0, max_r + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                tx, ty = x + dx, y + dy
                if 2 <= tx < mw - 2 and 2 <= ty < mh - 2 and gm[ty][tx] == getattr(Display, 'FLOOR', '.') \
                        and (tx, ty) not in occupied and (tx, ty) != (game.player.x, game.player.y):
                    return tx, ty
    return None


def start_cordon(game, squads=6, radius=24, rng=random):
    """Land the squads around the crash site. Returns the Cordon (also stored on game.cordon)."""
    from jedi_fugitive.game import enemies_sith as sith
    gm = game.game_map
    mh = len(gm)
    mw = len(gm[0]) if mh else 0
    radius = max(10, min(radius, min(mw, mh) // 4))
    cx, cy = int(game.player.x), int(game.player.y)
    cordon = Cordon((cx, cy), radius, getattr(game, 'turn_count', 0))
    lvl = max(1, getattr(game.player, 'level', 1))
    base = rng.random() * math.tau
    for i in range(squads):
        ang = base + i * math.tau / squads + rng.uniform(-0.25, 0.25)
        sx = int(round(cx + math.cos(ang) * radius))
        sy = int(round(cy + math.sin(ang) * radius))
        landing = _free_tile(game, sx, sy, max_r=6)
        if landing is None:
            continue
        cordon.landings.append(landing)
        # a trooper pair; one squad is led by a Sith warrior
        makers = [sith.create_sith_warrior if i == 0 else sith.create_sith_trooper, sith.create_sith_trooper]
        for j, make in enumerate(makers):
            spot = _free_tile(game, landing[0], landing[1], max_r=3)
            if spot is None:
                continue
            e = make(level=lvl)
            e.x, e.y = spot
            e.cordon = True
            e.cordon_angle = ang + (j - 0.5) * 0.16
            e.alert_range = 5
            e.patrol_points = None
            game.enemies.append(e)
            cordon.units.append(e)
    game.cordon = cordon
    try:
        game.add_message("Sith dropships scream down around the wreck. Squads are sealing off the crash site!")
        game.add_message("Break through the ring before it closes. Look for the gaps between squads.")
    except Exception:
        pass
    try:
        game.player.add_to_travel_log(
            "[CRASH] My ship tore through the sky and died in the dust. Before I could stand, "
            "Sith dropships were already landing around me.")
    except Exception:
        pass
    return cordon


def _step_towards(game, e, tx, ty):
    gm = game.game_map
    ex, ey = int(e.x), int(e.y)
    sx = (tx > ex) - (tx < ex)
    sy = (ty > ey) - (ty < ey)
    occupied = {(getattr(o, 'x', None), getattr(o, 'y', None)) for o in game.enemies if o is not e}
    for dx, dy in ((sx, sy), (sx, 0), (0, sy)):
        if dx == 0 and dy == 0:
            continue
        nx, ny = ex + dx, ey + dy
        if not (0 <= ny < len(gm) and 0 <= nx < len(gm[0])):
            continue
        if gm[ny][nx] in BLOCKING or (nx, ny) in occupied or (nx, ny) == (game.player.x, game.player.y):
            continue
        e.x, e.y = nx, ny
        return True
    return False


def update_cordon(game):
    """Advance the cordon by one world tick."""
    cordon = getattr(game, 'cordon', None)
    if cordon is None or not cordon.active:
        return
    if getattr(game, 'tomb_levels', None) and game.game_map is not getattr(game, 'surface_map', game.game_map):
        return  # underground: the surface squads keep waiting
    elapsed = getattr(game, 'turn_count', 0) - cordon.start_turn
    cordon.radius = max(cordon.min_radius, cordon.radius0 - cordon.shrink * max(0, elapsed - cordon.grace))
    cx, cy = cordon.center
    px, py = int(game.player.x), int(game.player.y)
    alive = [u for u in cordon.units if getattr(u, 'hp', 0) > 0 and u in game.enemies]
    player_d = math.hypot(px - cx, py - cy)
    if player_d > cordon.escape_radius or not alive:
        _end_cordon(game, cordon, broke_through=not alive and player_d <= cordon.escape_radius)
        return
    vis = getattr(game, 'visible', set()) or set()
    for u in alive:
        if getattr(u, '_has_spotted', False):
            continue  # regular AI is chasing
        d = abs(u.x - px) + abs(u.y - py)
        if d <= int(getattr(u, 'alert_range', 4)) and (u.x, u.y) in vis:
            u._has_spotted = True
            try:
                added = game.player.add_stress(5, source='spotted')
                game.add_message(f"{getattr(u, 'name', 'A trooper')} spots you and breaks formation! (+{added} stress)")
            except Exception:
                pass
            continue
        a = getattr(u, 'cordon_angle', 0.0)
        tx = int(round(cx + math.cos(a) * cordon.radius))
        ty = int(round(cy + math.sin(a) * cordon.radius))
        if (u.x, u.y) != (tx, ty):
            _step_towards(game, u, tx, ty)


def _end_cordon(game, cordon, broke_through=False):
    cordon.active = False
    cordon.escaped = True
    for u in cordon.units:
        u.cordon = False
        u._has_spotted = False
        # scatter into ordinary patrols around where they stood
        try:
            u.patrol_points = [(u.x + random.randint(-6, 6), u.y + random.randint(-6, 6)) for _ in range(3)]
            u._patrol_index = 0
        except Exception:
            pass
    try:
        if broke_through:
            game.add_message("The last squad falls. The cordon is broken!")
        else:
            game.add_message("You slip through the Sith cordon and vanish into the wilds.")
        game.player.gain_xp(60)
        game.player.reduce_stress(10)
        game.add_message("(+60 XP, -10 stress)")
    except Exception:
        pass
    try:
        game.player.add_to_travel_log(
            "[ESCAPE] I broke through the Sith cordon around the crash site. They will not stop looking.")
    except Exception:
        pass
    # the hunt goes on: a fanatic picks up the trail some time later
    try:
        game._fanatic_turn = getattr(game, 'turn_count', 0) + random.randint(40, 90)
    except Exception:
        pass
