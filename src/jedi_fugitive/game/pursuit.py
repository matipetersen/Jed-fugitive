"""
Pursuit & Detection System ("Heat" / Force signature)

A Jedi fugitive's core dilemma: every use of the Force and every fight leaves a
trace the Empire can follow. ``detection_level`` (0-100) is that trace.

Sources (see update_detection):
  force powers  energy cost / 2 (dark powers x1.5), e.g. Heal +15, Lightning +30
  melee         +3 per swing        ranged shot +4        grenade +8
Decay per world tick:
  -1 baseline, -3 when no enemy is aware of you, extra when meditating/stealthy.

Escalation tiers:
  0-29  Quiet     nothing hunts you
  30-59 Noticed   a two-trooper patrol is sent towards you every ~45 ticks
  60-89 Hunted    patrols every ~25 ticks with a Sith warrior; nearby Sith are alerted
  90+   Predator  a Sith Predator is dispatched (once, again 300 ticks after it dies)
"""
import math
import random

TIERS = ((90, "PREDATOR"), (60, "HUNTED"), (30, "NOTICED"), (0, "QUIET"))

SOURCE_HEAT = {'combat': 3, 'ranged': 4, 'grenade': 8, 'force': 20}


def _say(game, msg):
    try:
        game.add_message(msg)
    except Exception:
        try:
            game.ui.messages.add(msg)
        except Exception:
            pass


def tier_name(level):
    for threshold, name in TIERS:
        if level >= threshold:
            return name
    return "QUIET"


class PursuitSystem:
    def __init__(self, player):
        self.player = player
        self.detection_level = 0  # 0-100
        self.last_force_use_turn = None
        self.last_combat_turn = None
        self.sith_predator_active = False
        self.predator = None
        self.predator_cooldown_until = 0
        self.next_patrol_turn = 0
        self._last_tier = "QUIET"

    def update_detection(self, action_type, stealth=False, disguise_bonus=0, amount=None, turn=None):
        """Raise (or lower, for 'stealth') the Heat from a player action."""
        turn = turn if turn is not None else getattr(self.player, 'turn_count', 0)
        if action_type == 'stealth':
            self.detection_level = max(0, self.detection_level - (amount or 10))
        else:
            gain = SOURCE_HEAT.get(action_type, 5) if amount is None else amount
            if action_type == 'force':
                self.last_force_use_turn = turn
            elif action_type in ('combat', 'ranged', 'grenade'):
                self.last_combat_turn = turn
            self.detection_level += gain
        self.detection_level = max(0, min(100, self.detection_level - disguise_bonus))

    # ------------------------------------------------------------------ tick
    def tick(self, game):
        """Once per world tick: decay, escalation messages, patrols, predator."""
        aware = False
        try:
            aware = bool(game._in_combat(radius=10))
        except Exception:
            pass
        decay = 1 if aware else 3
        if getattr(game, 'in_tomb', False) or getattr(game, 'tomb_levels', None):
            decay += 1  # underground the Empire loses your trail faster
        self.detection_level = max(0, self.detection_level - decay)

        tier = tier_name(self.detection_level)
        if tier != self._last_tier:
            self._announce(game, tier, rising=self._rank(tier) > self._rank(self._last_tier))
            self._last_tier = tier

        on_surface = not getattr(game, 'tomb_levels', None) or game.game_map is getattr(game, 'surface_map', None)
        if not on_surface:
            return
        turn = getattr(game, 'turn_count', 0)
        if tier in ("NOTICED", "HUNTED", "PREDATOR") and turn >= self.next_patrol_turn:
            self._dispatch_patrol(game, heavy=tier != "NOTICED")
            self.next_patrol_turn = turn + (45 if tier == "NOTICED" else 25)
            if tier != "NOTICED":
                self._alert_nearby(game, radius=30)
        if self.predator is not None and (getattr(self.predator, 'hp', 0) <= 0 or self.predator not in game.enemies):
            self.predator = None
            self.sith_predator_active = False
            self.predator_cooldown_until = turn + 300
        if tier == "PREDATOR":
            self.check_predator_spawn(game)

    @staticmethod
    def _rank(tier):
        return {"QUIET": 0, "NOTICED": 1, "HUNTED": 2, "PREDATOR": 3}.get(tier, 0)

    def _announce(self, game, tier, rising):
        msgs = {
            "NOTICED": "#3#Your Force signature ripples outward. Sith listening posts take notice.#0#",
            "HUNTED": "#1#The Empire has your scent. Patrols are converging on your position.#0#",
            "PREDATOR": "#1#Something ancient and hungry turns its attention towards you.#0#",
            "QUIET": "#6#Your presence fades back into the noise of the world.#0#",
        }
        turn = getattr(game, 'turn_count', 0)
        recent = getattr(self, '_announced', {})
        self._announced = recent
        # hysteresis: hovering around a threshold should not repeat the same warning
        if (rising or tier == "QUIET") and turn - recent.get(tier, -999) >= 30:
            recent[tier] = turn
            _say(game, msgs[tier])

    def _spawn_spot(self, game, rmin, rmax):
        from jedi_fugitive.game.level import Display
        gm = game.game_map
        mh, mw = len(gm), len(gm[0]) if gm else 0
        px, py = game.player.x, game.player.y
        vis = getattr(game, 'visible', set()) or set()
        floor = getattr(Display, 'FLOOR', '.')
        for _ in range(300):
            a = random.random() * math.tau
            r = random.randint(rmin, rmax)
            x, y = int(px + math.cos(a) * r), int(py + math.sin(a) * r)
            if 2 <= x < mw - 2 and 2 <= y < mh - 2 and gm[y][x] == floor and (x, y) not in vis \
                    and not any(getattr(e, 'x', None) == x and getattr(e, 'y', None) == y for e in game.enemies):
                return x, y
        return None

    def _dispatch_patrol(self, game, heavy=False):
        from jedi_fugitive.game import enemies_sith as sith
        spot = self._spawn_spot(game, 18, 26)
        if spot is None:
            return
        lvl = max(1, int(getattr(game.player, 'level', 1) or 1))
        makers = [sith.create_sith_trooper, sith.create_sith_trooper]
        if heavy:
            makers.append(sith.create_sith_warrior)
        px, py = game.player.x, game.player.y
        for i, make in enumerate(makers):
            e = make(level=lvl)
            e.x, e.y = spot[0] + (i % 2), spot[1] + (i // 2)
            if game.game_map[e.y][e.x] != game.game_map[spot[1]][spot[0]]:
                e.x, e.y = spot
            # they march to where you were last sensed, then sweep around it
            e.patrol_points = [(px, py), (px + random.randint(-4, 4), py + random.randint(-4, 4))]
            e._patrol_index = 0
            e.heat_patrol = True
            game.enemies.append(e)
        _say(game, "You sense a Sith patrol moving towards where you were.")

    def _alert_nearby(self, game, radius=30):
        px, py = game.player.x, game.player.y
        for e in game.enemies:
            if abs(getattr(e, 'x', 0) - px) + abs(getattr(e, 'y', 0) - py) <= radius:
                e.patrol_points = [(px, py)]
                e._patrol_index = 0

    def check_predator_spawn(self, game):
        """Dispatch the Sith Predator (out of sight, not on top of the player)."""
        turn = getattr(game, 'turn_count', 0)
        if self.detection_level < 90 or self.sith_predator_active or turn < self.predator_cooldown_until:
            return False
        try:
            from jedi_fugitive.game import enemies_sith
            spot = self._spawn_spot(game, 12, 20)
            if spot is None:
                return False
            level = max(1, int(getattr(game.player, 'level', 1) or 1))
            predator = enemies_sith.create_sith_warrior(level=level, x=spot[0], y=spot[1])
            predator.x, predator.y = spot
            predator.name = "Sith Predator"
            predator.char = "S"
            predator.symbol = "S"
            predator.max_hp = predator.hp = 60 + 15 * level
            predator.attack = 14 + 2 * level
            predator.defense = 6 + level // 2
            predator.xp_value = 300
            predator.is_hunter = True
            predator._has_spotted = True
            game.enemies.append(predator)
            self.predator = predator
            self.sith_predator_active = True
            _say(game, "#1#⚠ A SITH PREDATOR HAS FOUND YOUR TRAIL! Break line of sight and go quiet.#0#")
            try:
                game.player.add_to_travel_log("[HUNTED] I used the Force too freely. Something followed the echo: a Sith Predator.")
            except Exception:
                pass
            return True
        except Exception:
            return False

    def decay_detection(self):
        # kept for compatibility; tick() handles decay with context
        if self.detection_level > 0:
            self.detection_level -= 1
