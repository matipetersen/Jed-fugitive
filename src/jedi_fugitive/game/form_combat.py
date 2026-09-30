"""Combat mechanics for lightsaber forms.

lightsaber_forms.py defines the stances and their numbers; this module makes them
matter in a fight. Stance bonuses only apply while a lightsaber is wielded.

* every form: attack / defense / evasion / crit chance from the stance
* Shii-Cho: sweeping cut, half damage to one other adjacent enemy
* Makashi: +25% against a lone opponent, -20% when surrounded, crits hit harder
* Soresu / Shien / Niman: better blaster deflection (see enemy.py), Shien counters
  a missed melee attack
* Ataru: acrobatic and quick, but tiring - stress builds up in long fights
* Juyo / Vaapad: bonus damage from corruption, every critical feeds the dark side
"""
import random

from jedi_fugitive.game.lightsaber_forms import FORMS_BY_NAME

BASE_CRIT = 0.05


def form_key(player):
    """Short stable name of the active stance ('Shien / Djem So' -> 'Shien')."""
    name = str(getattr(player, "active_form", "") or "")
    if name.startswith("Shien"):
        return "Shien"
    if name.startswith("Juyo"):
        return "Juyo"
    return name


def has_lightsaber(player):
    w = getattr(player, "equipped_weapon", None)
    if not w:
        return False
    name = w.get("name", "") if isinstance(w, dict) else getattr(w, "name", "")
    return "lightsaber" in str(name).lower()


def _form(player):
    return FORMS_BY_NAME.get(getattr(player, "active_form", None))


def _stat(player, attr):
    f = _form(player)
    if f is None or not has_lightsaber(player):
        return 0
    return getattr(f, attr, 0)


def defense_bonus(player):
    return _stat(player, "defense_bonus")


def evasion_bonus(target):
    """Evasion bonus for any target: 0 unless it is a saber-wielding player."""
    if not hasattr(target, "active_form"):
        return 0
    return _stat(target, "evasion_bonus")


def total_defense(player):
    return int(getattr(player, "defense", 0) or 0) + defense_bonus(player)


def force_cost_multiplier(player):
    red = _stat(player, "force_cost_reduction")
    return max(0.5, 1.0 - red / 100.0)


def crit_chance(player):
    c = BASE_CRIT + _stat(player, "crit_chance_bonus") / 100.0
    try:
        from jedi_fugitive.game import jedi_skills
        c += jedi_skills.bonus(player, "crit")
    except Exception:
        pass
    return min(0.6, c)


def adjacent_enemies(game, enemy, exclude=None):
    out = []
    for e in list(getattr(game, "enemies", []) or []):
        if e is enemy or e is exclude or getattr(e, "hp", 1) <= 0:
            continue
        if max(abs(e.x - enemy.x), abs(e.y - enemy.y)) <= 1:
            out.append(e)
    return out


def _player_adjacent(game, enemy_list):
    px, py = game.player.x, game.player.y
    return [e for e in enemy_list if max(abs(e.x - px), abs(e.y - py)) <= 1]


def modify_player_attack(player, enemy, dmg, game=None, rng=None):
    """Apply stance effects to a landed hit. Returns (damage, [notes])."""
    rng = rng or random
    notes = []
    f = _form(player)
    if f is None or not has_lightsaber(player):
        return dmg, notes
    key = form_key(player)
    dmg = dmg + getattr(f, "attack_bonus", 0)

    near = []
    if game is not None:
        near = _player_adjacent(game, [e for e in getattr(game, "enemies", []) or [] if getattr(e, "hp", 1) > 0])
    if key == "Makashi":
        if len(near) <= 1:
            dmg = int(dmg * 1.25)
            notes.append("Makashi: a clean duelist's thrust.")
        elif len(near) >= 3:
            dmg = int(dmg * 0.8)
    if key == "Juyo":
        dmg += int((getattr(player, "dark_corruption", 0) or 0) // 10)

    crit = rng.random() < crit_chance(player)
    if crit:
        mult = 2.0 if key == "Makashi" else 1.5
        dmg = int(dmg * mult)
        notes.append("CRITICAL! You find the opening.")
        if key == "Juyo":
            player.dark_corruption = min(100, (getattr(player, "dark_corruption", 0) or 0) + 1)
            notes.append("The fury feeds something dark inside you.")
        if key == "Shii-Cho":
            notes.append("Your sweep knocks the enemy's guard aside.")
    if key == "Ataru":
        n = getattr(player, "_ataru_streak", 0) + 1
        player._ataru_streak = n
        if n % 6 == 0:
            try:
                player.add_stress(2, source="acrobatic exertion")
                notes.append("Ataru's acrobatics wear you down.")
            except Exception:
                pass
    else:
        player._ataru_streak = 0
    return max(1, int(dmg)), notes


def cleave(player, enemy, dmg, game, messages=None):
    """Shii-Cho's wide sweep: half damage to one other adjacent enemy."""
    if game is None or form_key(player) != "Shii-Cho" or not has_lightsaber(player):
        return None
    others = adjacent_enemies(game, enemy)
    others = _player_adjacent(game, others)
    if not others:
        return None
    victim = others[0]
    part = max(1, int(dmg) // 2)
    victim.hp -= part
    if messages is not None:
        try:
            messages.add(f"Your sweeping cut also clips {getattr(victim, 'name', 'another enemy')} for {part}.")
        except Exception:
            pass
    return victim


def counter_chance(player):
    c = 0.30 if form_key(player) == "Shien" else 0.0
    try:
        from jedi_fugitive.game import jedi_skills
        c += jedi_skills.bonus(player, "counter")
    except Exception:
        pass
    return c if has_lightsaber(player) else 0.0


def on_enemy_miss(game, attacker, rng=None):
    """An enemy's melee attack missed the player: Shien / Riposte may counter."""
    rng = rng or random
    p = game.player
    ch = counter_chance(p)
    if ch <= 0 or rng.random() >= ch:
        return False
    dmg = max(1, int(getattr(p, "attack", 1) // 2) + _stat(p, "attack_bonus"))
    try:
        attacker.hp -= dmg
        game.ui.messages.add(f"You turn the blow aside and counter {getattr(attacker, 'name', 'the enemy')} for {dmg}!")
    except Exception:
        pass
    return True
