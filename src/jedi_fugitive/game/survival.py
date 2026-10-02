"""
Survival: wounds that the Force cannot mend, and camps that cost exposure.

Wounds
  A heavy hit (a loss of 20%+ of max HP within one world tick) may leave a
  wound; a brutal one (35%+) always does. One wound per location:

    leg    evasion -6, and moving can make you stumble (the world gets a free tick)
    arm    accuracy -8, damage -1
    torso  bleeding: -1 HP every 12 ticks (never below 1)
    head   concussion: accuracy -4, +1 stress every 20 ticks

  Force Heal restores HP but not wounds. A medkit treats one wound; so does a
  full night in camp.

Camping (K)
  Spend 40 ticks resting. If nothing interrupts you: one wound treated, +35% HP,
  -20 stress, full Force energy. The risk of being found grows with your Heat
  (Force signature), with every wound you carry, at night, and in a tomb.
  An ambush or an enemy wandering close ends the camp early with only partial
  rest.
"""
import random

WOUNDS = {
    'leg':   {'name': 'Wounded leg',       'evasion': -6,
              'text': "Your leg buckles under you. (evasion -6, you may stumble while moving)"},
    'arm':   {'name': 'Wounded sword arm', 'accuracy': -8, 'damage': -1,
              'text': "Your sword arm is torn open. (accuracy -8, damage -1)"},
    'torso': {'name': 'Bleeding wound',    'bleed': True,
              'text': "A deep gash across your ribs. You are bleeding. (-1 HP every 12 ticks)"},
    'head':  {'name': 'Concussion',        'accuracy': -4, 'stress': True,
              'text': "Your skull rings from the blow. (accuracy -4, stress builds)"},
}
WOUND_ORDER = ('torso', 'leg', 'arm', 'head')  # treated first -> last

HEAVY_HIT = 0.20
BRUTAL_HIT = 0.35
STUMBLE_CHANCE = 0.30
CAMP_TICKS = 40


def _say(game, msg):
    try:
        game.add_message(msg)
    except Exception:
        try:
            game.ui.messages.add(msg)
        except Exception:
            pass


def wounds(player):
    w = getattr(player, 'wounds', None)
    if w is None:
        w = player.wounds = {}
    return w


def damage_penalty(player):
    return sum(-WOUNDS[k].get('damage', 0) for k in wounds(player))


def _apply(player, loc, sign):
    spec = WOUNDS[loc]
    for stat in ('evasion', 'accuracy'):
        if spec.get(stat):
            setattr(player, stat, int(getattr(player, stat, 0) or 0) + sign * spec[stat])


def inflict(game, loc=None):
    """Give the player a wound (random untaken location if loc is None). Returns the location."""
    p = game.player
    w = wounds(p)
    free = [k for k in WOUNDS if k not in w]
    if not free:
        return None
    loc = loc if loc in free else random.choice(free)
    w[loc] = getattr(game, 'turn_count', 0)
    _apply(p, loc, +1)
    _say(game, f"#1#WOUNDED: {WOUNDS[loc]['name']}.#0# {WOUNDS[loc]['text']}")
    try:
        p.add_to_travel_log(f"[WOUND] {WOUNDS[loc]['name']}. The Force can close a cut, not this.")
    except Exception:
        pass
    return loc


def treat(game, loc=None, source="You"):
    """Treat one wound (the most dangerous first). Returns the treated location or None."""
    p = game.player
    w = wounds(p)
    if not w:
        return None
    if loc not in w:
        loc = next(k for k in WOUND_ORDER if k in w)
    del w[loc]
    _apply(p, loc, -1)
    _say(game, f"#2#{source} treat the {WOUNDS[loc]['name'].lower()}.#0#")
    return loc


def on_hp_change(game):
    """Once per world tick: turn heavy damage into wounds, and let wounds act."""
    p = game.player
    hp = int(getattr(p, 'hp', 0) or 0)
    max_hp = max(1, int(getattr(p, 'max_hp', 1) or 1))
    last = getattr(game, '_last_hp_seen', None)
    if last is not None and hp > 0:
        loss = last - hp
        if loss >= BRUTAL_HIT * max_hp or (loss >= HEAVY_HIT * max_hp and random.random() < 0.5):
            inflict(game)
    turn = getattr(game, 'turn_count', 0)
    w = wounds(p)
    if 'torso' in w and turn % 12 == 0 and hp > 1:
        p.hp = hp = hp - 1
    if 'head' in w and turn % 20 == 0:
        try:
            p.add_stress(1)
        except Exception:
            pass
    game._last_hp_seen = hp


def on_player_moved(game):
    """A wounded leg can give way: the world gets a free tick (see pop_stumble)."""
    if 'leg' in wounds(game.player) and random.random() < STUMBLE_CHANCE:
        game._stumbles = getattr(game, '_stumbles', 0) + 1
        _say(game, "#3#Your wounded leg gives way. You stumble.#0#")


def pop_stumble(game):
    n = getattr(game, '_stumbles', 0)
    game._stumbles = 0
    return n


def is_medkit(item):
    try:
        name = (item.get('name') if isinstance(item, dict) else getattr(item, 'name', '')) or ''
        eff = (item.get('effect') if isinstance(item, dict) else getattr(item, 'effect', {})) or {}
    except Exception:
        return False
    return 'medkit' in name.lower() or (isinstance(eff, dict) and (eff.get('treat_wound') or eff.get('cure')))


# ------------------------------------------------------------------ camping
def camp_risk(game):
    """Chance that something finds you during a full camp."""
    heat = 0
    try:
        heat = int(game.pursuit_system.detection_level)
    except Exception:
        pass
    risk = 0.10 + heat / 200.0 + 0.05 * len(wounds(game.player))
    if getattr(game, 'tomb_levels', None) and hasattr(game, 'tomb_floor'):
        risk += 0.15
    try:
        from jedi_fugitive.game import daynight
        risk += daynight.camp_risk_modifier(game)  # a fire at night is a beacon
    except Exception:
        pass
    return max(0.0, min(0.85, risk))


def _ambush(game):
    from jedi_fugitive.game import enemies_sith as sith
    try:
        spot = game.pursuit_system._spawn_spot(game, 6, 10)
    except Exception:
        spot = None
    if spot is None:
        return []
    lvl = max(1, int(getattr(game.player, 'level', 1) or 1))
    in_tomb = bool(getattr(game, 'tomb_levels', None)) and hasattr(game, 'tomb_floor')
    if in_tomb:
        try:
            from jedi_fugitive.game import tomb_lords
            rec = tomb_lords.current_record(game)
            group = [tomb_lords.garrison_enemy(rec['lord'], game.tomb_floor + 1, lvl) for _ in range(2)]
            text = "Footsteps in the dark. The tomb's guardians have found your camp!"
        except Exception:
            group = [sith.create_sith_acolyte(level=lvl) for _ in range(2)]
            text = "Footsteps in the dark. Something has found your camp!"
    elif random.random() < 0.5:
        group = [sith.create_sith_trooper(level=lvl), sith.create_sith_trooper(level=lvl)]
        text = "Boots crunch nearby. A Sith patrol has spotted your fire!"
    else:
        group = [sith.create_tukata(level=lvl)]
        text = "A low growl. Something hungry followed the smell of your camp!"
    out = []
    for i, e in enumerate(group):
        e.x, e.y = spot[0] + i, spot[1]
        try:
            if game.game_map[e.y][e.x] != game.game_map[spot[1]][spot[0]]:
                e.x, e.y = spot
        except Exception:
            e.x, e.y = spot
        e._has_spotted = True
        e.patrol_points = [(game.player.x, game.player.y)]
        e._patrol_index = 0
        game.enemies.append(e)
        out.append(e)
    _say(game, f"#1#{text}#0#")
    return out


def make_camp(game):
    """Rest for CAMP_TICKS world ticks. Returns True if time passed."""
    p = game.player
    try:
        if game._in_combat(radius=10):
            _say(game, "You can't make camp with enemies this close.")
            return False
    except Exception:
        pass
    risk = camp_risk(game)
    ambush_at = random.randint(8, CAMP_TICKS - 5) if random.random() < risk else None
    _say(game, f"You make camp. (risk of being found: {int(risk * 100)}%)")
    rested = 0
    interrupted = None
    for i in range(CAMP_TICKS):
        if i == ambush_at:
            if _ambush(game):
                interrupted = "ambush"
                break
        try:
            if game._world_tick() is False:
                return True
        except Exception:
            pass
        rested += 1
        if getattr(p, 'hp', 1) <= 0:
            return True
        try:
            if game._in_combat(radius=6):
                interrupted = "enemy"
                break
        except Exception:
            pass
    frac = rested / CAMP_TICKS
    max_hp = int(getattr(p, 'max_hp', 100) or 100)
    p.hp = min(max_hp, int(p.hp) + int(max_hp * 0.35 * frac))
    try:
        p.reduce_stress(int(20 * frac))
    except Exception:
        pass
    if interrupted is None:
        p.force_energy = getattr(p, 'max_force_energy', getattr(p, 'force_energy', 100))
        treat(game, source="Rested and bandaged, you")
        _say(game, "#2#You break camp rested. (+35% HP, -20 stress, Force restored)#0#")
        try:
            p.add_to_travel_log("[CAMP] A few hours of rest. For once, no one came.")
        except Exception:
            pass
    else:
        if interrupted == "enemy":
            _say(game, "#3#Your rest is cut short: enemies are close.#0#")
        try:
            p.add_to_travel_log("[CAMP] I tried to rest. They found me anyway.")
        except Exception:
            pass
    game._last_hp_seen = int(p.hp)
    return True
