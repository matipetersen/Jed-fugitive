"""
Tomb identities: every tomb is the resting place of a specific Dark Lord.

A tomb is no longer an anonymous stack of rooms. When the player first enters a
tomb entrance it is bound to one Sith Lord, which decides:

  * the trial      - a rule that shapes the descent (illusions, crushing
                     presence, possession, duelists, sorrow);
  * the garrison   - which enemies guard the halls;
  * the guardian   - a named boss waiting beside the corrupted Jedi relic;
  * the lore       - three holocron fragments, one on each of the first three
                     floors, telling the Lord's story in their own voice.

Lore is progression: recovering all three fragments of a Lord teaches the
player what that Lord knew (a Force power, a lightsaber form, a permanent
edge). The guardian's fall and the relic's history close the tomb's story.

Historical notes in the fragments follow Legends continuity (Old Republic era).
"""
import random

FRAGMENT_GLYPH = '◊'

LORDS = {
    'ajunta_pall': {
        'name': 'Ajunta Pall',
        'epithet': 'First Dark Lord of the Sith',
        'trial': 'sorrow',
        'trial_text': "A grief older than the Republic hangs in the air. It weighs on the angry and eases the calm.",
        'garrison': ('tukata', 'acolyte', 'acolyte'),
        'boss': ('sith_lord', "Shade of Ajunta Pall"),
        'fragments': (
            "We were Jedi once. After the Hundred-Year Darkness the Council cast us out, "
            "and we fled past the edge of every chart until we reached Korriban.",
            "The Sith species knelt before exiles with the Force in their hands. They named me "
            "their Dark Lord, the first to bear the title. I called it conquest. It was flight.",
            "I am bound to this place and I remember what I was. Hear the only lesson I have left: "
            "what you guard, you keep. What you take, you lose.",
        ),
        'reward': {'ability': 'Protect', 'defense': 1,
                   'text': "Ajunta Pall's regret becomes your discipline: you learn to guard instead of strike."},
        'relic': "a Jedi Shadow's focusing crystal, brought here to seal the exiles' tomb and turned against its bearer",
    },
    'tulak_hord': {
        'name': 'Tulak Hord',
        'epithet': 'Dark Lord of the Sith, master of the blade',
        'trial': 'duelists',
        'trial_text': "Every hall is a dueling ring. The guardians here were chosen for their blades, not their numbers.",
        'garrison': ('warrior', 'assassin', 'warrior'),
        'boss': ('sith_lord', "Echo of Tulak Hord"),
        'fragments': (
            "Power that cannot be held in the hand is a rumour. I held mine in a blade, "
            "and the galaxy learned the difference.",
            "Form is a cage until it is mastered. Then it is a key. I broke every form I was "
            "taught and kept only what drew blood.",
            "Juyo is not fury. It is fury that has been given orders. Learn that, and you will "
            "fight as I fought, whatever side you serve.",
        ),
        'reward': {'form': 'Juyo / Vaapad', 'attack': 1,
                   'text': "Tulak Hord's last lesson settles into your wrists: you know Juyo / Vaapad."},
        'relic': "a Jedi Weapon Master's hilt, taken in a duel and kept as a trophy until the dark side soaked into it",
    },
    'marka_ragnos': {
        'name': 'Marka Ragnos',
        'epithet': 'Dark Lord of the Sith for a century',
        'trial': 'strength',
        'trial_text': "The tomb presses down on you like a hand. Only strength is respected here: the guardians are hardier.",
        'garrison': ('warrior', 'trooper', 'warrior'),
        'boss': ('sith_lord', "Spirit of Marka Ragnos"),
        'fragments': (
            "For a hundred years I held the Sith together by strength alone. "
            "No law, no council: only the certainty that I could not be beaten.",
            "When I died, Ludo Kressh and Naga Sadow drew blades over my bier. I rose to tell them "
            "the truth they already knew: the strongest must rule.",
            "Sadow was the stronger, and his strength led the Empire to ruin. Strength is the right "
            "to rule. It is not the wisdom to rule well.",
        ),
        'reward': {'ability': 'Force Rage', 'max_hp': 15,
                   'text': "Marka Ragnos' endurance becomes yours: +15 max HP, and you learn Force Rage."},
        'relic': "a Republic envoy's peace-holocron, whose message Ragnos' acolytes rewrote into a declaration of war",
    },
    'naga_sadow': {
        'name': 'Naga Sadow',
        'epithet': 'Dark Lord who led the Great Hyperspace War',
        'trial': 'illusions',
        'trial_text': "Shapes move at the edge of your sight. Some of the guardians are real. Some are Sadow's illusions.",
        'garrison': ('acolyte', 'warrior', 'acolyte'),
        'boss': ('sorcerer', "Phantom of Naga Sadow"),
        'fragments': (
            "Kressh wanted the Sith to hide. I showed them the Republic's worlds and led them "
            "out of hiding, into the Great Hyperspace War.",
            "Half of my armies were never there. An illusion that terrifies does the work of a "
            "fleet, and costs nothing when it dies.",
            "Defeated, I fled to Yavin's moon and slept in my temple among the Massassi. "
            "Sleep is patience. Patience is the last illusion.",
        ),
        'reward': {'ability': 'Force Phantom', 'accuracy': 3,
                   'text': "Naga Sadow's art is yours: you can see through illusions (+3 accuracy) and cast your own Force Phantom."},
        'relic': "a Jedi Seer's meditation stone, which Sadow's alchemists taught to show false visions",
    },
    'freedon_nadd': {
        'name': 'Freedon Nadd',
        'epithet': 'Fallen Jedi, King of Onderon',
        'trial': 'possession',
        'trial_text': "A voice speaks inside your thoughts as if it had always lived there. Do not let it stay too long.",
        'garrison': ('acolyte', 'assassin', 'trooper'),
        'boss': ('inquisitor', "Spirit of Freedon Nadd"),
        'fragments': (
            "My masters would not teach me what I was owed, so I left the Jedi and found a teacher "
            "who would: Naga Sadow, asleep beneath the jungles of Yavin's moon.",
            "When he had taught me everything, I killed him. A student's last lesson is that the "
            "master is no longer needed.",
            "On Onderon they made me king. When I died my spirit remained, and the kings who came after "
            "me listened. So will you. Everyone listens, in the end.",
        ),
        'reward': {'ability': 'Drain', 'max_force': 15,
                   'text': "You silenced Freedon Nadd and kept his secret: you learn Drain (+15 max Force energy)."},
        'relic': "the saber crystal of a Jedi Knight who hunted Nadd's spirit and was possessed by it",
    },
}


# ---------------------------------------------------------------- identity
def _say(game, msg):
    try:
        game.add_message(msg)
    except Exception:
        try:
            game.ui.messages.add(msg)
        except Exception:
            pass


def lord_for(game, entrance):
    """Bind an entrance to a Sith Lord (once). Distinct Lords until all five are used."""
    records = getattr(game, 'tomb_records', None)
    if records is None:
        records = game.tomb_records = {}
    rec = records.get(entrance)
    if rec is None:
        used = [r['lord'] for r in records.values()]
        unused = [k for k in LORDS if k not in used]
        lord = random.choice(unused or list(LORDS))
        rec = records[entrance] = {'lord': lord, 'fragments': {}, 'boss_defeated': False,
                                   'relic_recovered': False}
    return rec


def current_record(game):
    entrance = getattr(game, 'current_tomb', None)
    if entrance is None:
        return None
    return (getattr(game, 'tomb_records', None) or {}).get(entrance)


def current_lord(game):
    rec = current_record(game)
    return LORDS.get(rec['lord']) if rec else None


def in_tomb(game):
    return bool(getattr(game, 'tomb_levels', None)) and hasattr(game, 'tomb_floor') \
        and getattr(game, 'current_tomb', None) is not None


# ------------------------------------------------------------- generation
def _make(kind, level):
    from jedi_fugitive.game import enemies_sith as sith
    makers = {
        'trooper': sith.create_sith_trooper,
        'acolyte': sith.create_sith_acolyte,
        'warrior': sith.create_sith_warrior,
        'assassin': sith.create_sith_assassin,
        'tukata': sith.create_tukata,
        'sorcerer': sith.create_sith_sorcerer,
        'sith_lord': sith.create_sith_lord,
        'inquisitor': sith.create_dread_inquisitor,
    }
    return makers.get(kind, sith.create_sith_warrior)(level=level)


def garrison_enemy(lord_id, depth, player_level):
    """One guardian for floor `depth` (1-based) of a Lord's tomb."""
    lord = LORDS[lord_id]
    kinds = lord['garrison']
    kind = kinds[min(depth - 1, len(kinds) - 1)] if random.random() < 0.7 else random.choice(kinds)
    level = max(1, player_level + max(0, depth - 2))
    e = _make(kind, level)
    trial = lord['trial']
    if trial == 'strength':
        e.max_hp = e.hp = int(getattr(e, 'max_hp', getattr(e, 'hp', 10)) * 1.25)
    elif trial == 'duelists':
        e.attack = int(getattr(e, 'attack', 5)) + 2
        e.accuracy = int(getattr(e, 'accuracy', 70) or 70) + 5
    elif trial == 'illusions' and random.random() < 0.3:
        make_illusion(e)
    return e


def make_illusion(e):
    """Turn an enemy into one of Naga Sadow's phantoms: it looks real, but cannot truly harm you."""
    e.illusion = True
    e.max_hp = e.hp = 1
    e.attack = 0
    e.xp_value = 0
    return e


def spawn_guardian(game, lord_id, x, y, player_level):
    lord = LORDS[lord_id]
    kind, name = lord['boss']
    e = _make(kind, max(3, player_level + 2))
    e.name = name
    e.x, e.y = x, y
    e.is_boss = True          # boss behaviour and legendary drop
    e.tomb_boss = True        # ...but not the story's final boss
    e.max_hp = e.hp = int(getattr(e, 'max_hp', 80)) + 10 * player_level
    e.symbol = e.char = 'L'
    return e


def place_fragments(game, rec, levels, rooms):
    """One holocron fragment on each of the first three floors (or fewer, if shallow)."""
    from jedi_fugitive.game.level import Display
    lord = LORDS[rec['lord']]
    for idx in range(min(len(lord['fragments']), len(levels))):
        level_map, floor_rooms = levels[idx], rooms[idx]
        candidates = list(floor_rooms[1:] or floor_rooms)
        random.shuffle(candidates)
        placed = False
        for room in candidates:
            for _ in range(30):
                x = random.randint(room[0] + 1, room[0] + room[2] - 2)
                y = random.randint(room[1] + 1, room[1] + room[3] - 2)
                if level_map[y][x] == Display.FLOOR:
                    level_map[y][x] = FRAGMENT_GLYPH
                    rec['fragments'][(idx, x, y)] = idx
                    placed = True
                    break
            if placed:
                break


def announce_entry(game, rec, first_time):
    lord = LORDS[rec['lord']]
    if first_time:
        _say(game, f"#1#This is the tomb of {lord['name']}, {lord['epithet']}.#0#")
        _say(game, f"#3#{lord['trial_text']}#0#")
        _say(game, f"Three holocron fragments ({FRAGMENT_GLYPH}) lie in these halls. {lord['name']}'s guardian waits at the bottom.")
        try:
            game.player.add_to_travel_log(f"[TOMB] I entered the tomb of {lord['name']}. {lord['trial_text']}")
        except Exception:
            pass
    else:
        found = sum(1 for i in range(len(lord['fragments'])) if i in _known(game.player, rec['lord']))
        _say(game, f"#3#You return to the tomb of {lord['name']}.#0# Fragments recovered: {found}/{len(lord['fragments'])}.")


# ------------------------------------------------------------ lore as progression
def _known(player, lord_id):
    known = getattr(player, 'lord_fragments', None)
    if known is None:
        known = player.lord_fragments = {}
    return known.setdefault(lord_id, set())


def _ensure_codex(game):
    codex = getattr(game, 'sith_codex', None)
    if codex is None:
        return None
    if 'tomb_lords' not in codex.categories or not codex.categories['tomb_lords']:
        for lord_id, lord in LORDS.items():
            for i, text in enumerate(lord['fragments']):
                codex.add_entry('tomb_lords', f"{lord_id}_{i}",
                                f"{lord['name']}, fragment {i + 1}/{len(lord['fragments'])}", text,
                                force_echo=(i == len(lord['fragments']) - 1))
    return codex


def on_step(game):
    """Called after the player moves: recover a holocron fragment underfoot."""
    if not in_tomb(game):
        return False
    rec = current_record(game)
    if not rec:
        return False
    key = (game.tomb_floor, game.player.x, game.player.y)
    idx = rec['fragments'].pop(key, None)
    if idx is None:
        return False
    from jedi_fugitive.game.level import Display
    try:
        game.game_map[key[2]][key[1]] = Display.FLOOR
    except Exception:
        pass
    lord_id = rec['lord']
    lord = LORDS[lord_id]
    known = _known(game.player, lord_id)
    known.add(idx)
    _say(game, f"#7#A holocron fragment flickers to life. {lord['name']} speaks:#0#")
    _say(game, f"\"{lord['fragments'][idx]}\"")
    try:
        if _ensure_codex(game) is not None and hasattr(game, '_register_codex_discovery'):
            game._register_codex_discovery(game.player, 'tomb_lords', f"{lord_id}_{idx}")
    except Exception:
        pass
    try:
        game.player.add_to_travel_log(f"[HOLOCRON] {lord['name']}: \"{lord['fragments'][idx]}\"")
    except Exception:
        pass
    if len(known) >= len(lord['fragments']):
        grant_mastery(game, lord_id)
    else:
        _say(game, f"Fragments of {lord['name']}: {len(known)}/{len(lord['fragments'])}.")
    return True


def grant_mastery(game, lord_id):
    """All fragments of a Lord recovered: learn what they knew. Granted once per Lord."""
    p = game.player
    mastered = getattr(p, 'lord_masteries', None)
    if mastered is None:
        mastered = p.lord_masteries = set()
    if lord_id in mastered:
        return False
    mastered.add(lord_id)
    reward = LORDS[lord_id]['reward']
    if reward.get('ability'):
        try:
            from jedi_fugitive.game.equipment import _grant_ability
            _grant_ability(game, reward['ability'])
        except Exception:
            pass
    if reward.get('form'):
        forms = getattr(p, 'known_forms', None)
        if forms is None:
            forms = p.known_forms = ["Shii-Cho"]
        if reward['form'] not in forms:
            forms.append(reward['form'])
    base = getattr(p, '_base_stats', None)
    for stat in ('attack', 'defense', 'accuracy'):
        if reward.get(stat):
            setattr(p, stat, int(getattr(p, stat, 0) or 0) + reward[stat])
            if isinstance(base, dict) and stat in base:
                base[stat] += reward[stat]
    if reward.get('max_hp'):
        p.max_hp = int(getattr(p, 'max_hp', 100)) + reward['max_hp']
        p.hp = min(p.max_hp, int(getattr(p, 'hp', 0)) + reward['max_hp'])
    if reward.get('max_force'):
        p.max_force_energy = int(getattr(p, 'max_force_energy', 100)) + reward['max_force']
    _say(game, f"#2#LEGACY OF {LORDS[lord_id]['name'].upper()}:#0# {reward['text']}")
    try:
        p.add_to_travel_log(f"[LEGACY] {reward['text']}")
    except Exception:
        pass
    return True


# ------------------------------------------------------------------ trials
def dispel_illusion(game, enemy):
    """Striking an illusion dispels it. Returns True if the target was an illusion."""
    if not getattr(enemy, 'illusion', False):
        return False
    try:
        game.enemies.remove(enemy)
    except Exception:
        pass
    _say(game, f"#5#Your blade passes through {getattr(enemy, 'name', 'the figure')}. It was never there.#0#")
    try:
        game.player.add_stress(3)
    except Exception:
        pass
    return True


def tick(game):
    """Once per world tick while inside a tomb: trial pressure and the guardian's fate."""
    if not in_tomb(game):
        return
    rec = current_record(game)
    if not rec:
        return
    lord = LORDS[rec['lord']]
    turn = getattr(game, 'turn_count', 0)
    p = game.player
    trial = lord['trial']
    # a recent meditation keeps the whispers out
    meditating = turn - getattr(game, 'last_meditation_turn', -999) < 40
    if trial == 'strength' and turn % 25 == 0:
        try:
            p.add_stress(1)
        except Exception:
            pass
    elif trial == 'sorrow' and turn % 30 == 0:
        dark = int(getattr(p, 'dark_corruption', 0) or 0)
        try:
            if dark < 40:
                p.reduce_stress(2)
            else:
                p.add_stress(2)
                _say(game, "#5#Ajunta Pall's grief finds the anger in you and feeds on it.#0#")
        except Exception:
            pass
    elif trial == 'possession' and turn % 40 == 0 and not meditating:
        p.dark_corruption = min(100, int(getattr(p, 'dark_corruption', 0) or 0) + 1)
        _say(game, "#5#\"You want this,\" Freedon Nadd whispers. Your corruption deepens. (Meditate to shut him out.)#0#")

    boss = getattr(game, 'tomb_guardian', None)
    if boss is not None and not rec['boss_defeated'] and getattr(boss, 'hp', 1) <= 0:
        on_guardian_defeated(game, rec, boss)


def on_guardian_defeated(game, rec, boss):
    rec['boss_defeated'] = True
    game.tomb_guardian = None
    lord = LORDS[rec['lord']]
    _say(game, f"#2#{getattr(boss, 'name', 'The guardian')} dissolves into ash. {lord['name']}'s hold on this tomb is broken.#0#")
    try:
        p = game.player
        p.reduce_stress(10)
        p.add_to_travel_log(f"[TOMB] I defeated {getattr(boss, 'name', 'the guardian')} in the tomb of {lord['name']}.")
    except Exception:
        pass


def on_relic_recovered(game):
    """The corrupted Jedi relic was picked up: tell its story."""
    rec = current_record(game)
    if not rec or rec.get('relic_recovered'):
        return False
    rec['relic_recovered'] = True
    lord = LORDS[rec['lord']]
    _say(game, f"#6#The relic was {lord['relic']}.#0#")
    try:
        game.player.add_to_travel_log(f"[RELIC] From the tomb of {lord['name']}: {lord['relic']}.")
    except Exception:
        pass
    return True
