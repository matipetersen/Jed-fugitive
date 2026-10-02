"""
The game, driven one key at a time from a web page (Pyodide).

The desktop game reads keys in blocking loops (menus, dialogs, "press any
key"). In a browser nothing may block, so each key the page sends is run as
one action:

* the action runs with ``curses`` replaced by cursesstub;
* when the game asks for a key the page has not given yet, the action stops
  (``NeedKey``), its RNG and new messages are rolled back, and the modal
  screen the game drew is returned to the page as a *prompt*;
* the page answers with a key, and the action is replayed from the start
  with the keys chosen so far, so every existing menu works unchanged.

All public functions return JSON strings for the page.
"""
import json
import os
import random
import sys

from jedi_fugitive.web import cursesstub

sys.modules['curses'] = cursesstub
os.environ.setdefault('JEDI_FUGITIVE_SAVE_DIR', '/saves')

import time as _time  # noqa: E402

_time.sleep = lambda *_a, **_k: None   # animations must not stall the page

_game = None
_outbox = []
_pending = None   # (key, answers, rng_state, messages_len)
_KEY_ESC = 27
_view = [41, 27]


def set_view(w, h):
    """How many map tiles the page shows (odd numbers keep the player centred)."""
    _view[0] = max(11, int(w) | 1)
    _view[1] = max(9, int(h) | 1)
    return state()


def _install_message_tap(game):
    buf = game.ui.messages
    original = buf.add

    def add(text, color=0):
        before = len(buf.messages)
        last = buf.messages[-1] if buf.messages else None
        original(text, color)
        if len(buf.messages) != before or (buf.messages and buf.messages[-1] is not last):
            m = buf.messages[-1]
            _outbox.append({'text': m.get('text', ''), 'color': m.get('color', 0)})
    buf.add = add


def _new_manager():
    from jedi_fugitive.game.game_manager import GameManager
    gm = GameManager(cursesstub.initscr())
    gm.animate_projectile = lambda *a, **k: None
    return gm


def start(size='small', seed=None, resume=False):
    """New game (or the latest save when resume is true). Returns the state."""
    global _game, _pending
    _outbox.clear()
    _pending = None
    cursesstub.keys.mode = 'cancel'
    cursesstub.keys.queue = []
    gm = _new_manager()
    gm.world_size = size
    loaded = False
    if resume:
        from jedi_fugitive.game import save_system
        try:
            loaded = save_system.continue_game(gm)
        except Exception:
            loaded = False
        if not loaded:
            gm = _new_manager()
            gm.world_size = size
    if not loaded:
        if seed is not None:
            gm.world_seed = int(seed)
        gm.initialize()
        _install_message_tap(gm)
        gm.generate_world()
    else:
        _install_message_tap(gm)
        gm.add_message("Game loaded. Welcome back, wanderer.")
    # messages written before the tap was installed
    if not _outbox:
        for m in gm.ui.messages.messages[-14:]:
            _outbox.append({'text': m.get('text', ''), 'color': m.get('color', 0)})
    gm.running = True
    try:
        gm.compute_visibility()
    except Exception:
        pass
    _game = gm
    return state()


def has_save():
    from jedi_fugitive.game import save_system
    return json.dumps(save_system.latest_save_path() is not None)


def _run(key, answers, rng):
    """Run one action. Returns a prompt (lines, runs) if the game needs a key."""
    gm = _game
    k = cursesstub.keys
    k.queue, k.mode, k.asked, k.calls = list(answers), 'ask', False, 0
    cursesstub.reset_capture()
    random.setstate(rng)
    msgs_before = len(gm.ui.messages.messages)
    outbox_before = len(_outbox)
    from jedi_fugitive.game import input_handler
    stopped = False
    try:
        input_handler.handle_input(gm, key)
    except cursesstub.NeedKey:
        stopped = True
    stopped = stopped or k.asked
    if stopped:
        screen = cursesstub.capture()
        # roll the aborted attempt back: it will be replayed with the answer
        del gm.ui.messages.messages[msgs_before:]
        del _outbox[outbox_before:]
        k.mode = 'cancel'
        return screen or ([" (choose)"], [[]])
    k.mode = 'cancel'
    return None


def press(key):
    """The player pressed `key` (a curses key code) outside any prompt."""
    global _pending
    if _game is None:
        return state()
    if _pending is not None:
        return answer(key)
    rng = random.getstate()
    prompt = _run(int(key), [], rng)
    if prompt is not None:
        _pending = (int(key), [], rng)
        return state(prompt=prompt)
    _after_action(int(key))
    return state()


def answer(key):
    """The player answered the open prompt with `key`."""
    global _pending
    if _pending is None:
        return press(key)
    first, answers, rng = _pending
    answers = answers + [int(key)]
    if len(answers) > 60:  # a menu that never closes: give up on it
        _pending = None
        return state()
    prompt = _run(first, answers, rng)
    if prompt is not None:
        _pending = (first, answers, rng)
        return state(prompt=prompt)
    _pending = None
    if answers[-1] != _KEY_ESC:   # a menu closed with Esc costs no time
        _after_action(first)
    return state()


def cancel():
    """Close the open prompt (Esc, a few times if the menu nests)."""
    global _pending
    for _ in range(4):
        if _pending is None:
            break
        out = answer(_KEY_ESC)
    _pending = None
    return state()


def _after_action(key):
    gm = _game
    if not gm.running:
        return
    try:
        free = gm._is_free_key(key)
    except Exception:
        free = False
    if free:
        return
    cursesstub.keys.mode = 'cancel'
    try:
        gm._world_tick()
        from jedi_fugitive.game import survival
        for _ in range(survival.pop_stumble(gm)):
            if not gm._world_tick():
                break
    except cursesstub.NeedKey:
        pass
    try:
        gm.compute_visibility()
    except Exception:
        pass


# ------------------------------------------------------------------ state
_BIOME_CODE = {'forest': 'f', 'plains': 'p', 'desert': 'd', 'rocky': 'r', 'mountains': 'm',
               'swamp': 's', 'river': 'w', 'crash_site': 'c', 'mountain_pass': 'm', 'ruins': 'u'}


def state(view_w=None, view_h=None, prompt=None):
    view_w = view_w or _view[0]
    view_h = view_h or _view[1]
    gm = _game
    if gm is None:
        return json.dumps({'ready': False})
    p = gm.player
    mh = len(gm.game_map)
    mw = len(gm.game_map[0]) if mh else 0
    x0 = max(0, min(mw - view_w, p.x - view_w // 2)) if mw > view_w else 0
    y0 = max(0, min(mh - view_h, p.y - view_h // 2)) if mh > view_h else 0
    vis = getattr(gm, 'visible', set()) or set()
    explored = getattr(gm, 'explored', set()) or set()
    fog = bool(getattr(gm, 'fog_of_war', True))
    biomes = getattr(gm, 'map_biomes', None)
    in_tomb = bool(getattr(gm, 'tomb_levels', None)) and hasattr(gm, 'tomb_floor')
    rows, seen, bio = [], [], []
    for y in range(y0, min(mh, y0 + view_h)):
        row = gm.game_map[y]
        rows.append(''.join(row[x0:x0 + view_w]))
        seen.append(''.join('2' if (x, y) in vis else ('1' if (x, y) in explored or not fog else '0')
                            for x in range(x0, min(mw, x0 + view_w))))
        if biomes is not None and not in_tomb:
            try:
                bio.append(''.join(_BIOME_CODE.get(biomes[y][x], 'p') for x in range(x0, min(mw, x0 + view_w))))
            except Exception:
                bio.append('p' * len(rows[-1]))
    ents = []
    for e in getattr(gm, 'enemies', []) or []:
        ex, ey = getattr(e, 'x', -1), getattr(e, 'y', -1)
        if (ex, ey) in vis and x0 <= ex < x0 + view_w and y0 <= ey < y0 + view_h and getattr(e, 'hp', 0) > 0:
            ents.append({'x': ex - x0, 'y': ey - y0, 'ch': str(getattr(e, 'symbol', None) or getattr(e, 'char', 'E'))[:1],
                         'name': getattr(e, 'name', 'Enemy'), 'hp': int(getattr(e, 'hp', 0)),
                         'max': int(getattr(e, 'max_hp', 1) or 1), 'boss': bool(getattr(e, 'is_boss', False)),
                         'beast': bool(getattr(e, 'is_fauna', False) or getattr(e, 'faction', '') == 'Wildlife'),
                         'illusion': bool(getattr(e, 'illusion', False))})
    npcs = []
    for (nx, ny), npc in (getattr(gm, 'npcs_on_map', {}) or {}).items():
        if (nx, ny) in vis and x0 <= nx < x0 + view_w and y0 <= ny < y0 + view_h:
            npcs.append({'x': nx - x0, 'y': ny - y0, 'name': getattr(npc, 'name', 'Survivor')})
    from jedi_fugitive.game import daynight, survival
    ps = getattr(gm, 'pursuit_system', None)
    heat = int(getattr(ps, 'detection_level', 0) or 0)
    try:
        from jedi_fugitive.game.pursuit import tier_name
        tier = tier_name(heat)
    except Exception:
        tier = ''
    if in_tomb:
        try:
            from jedi_fugitive.game import tomb_lords
            lord = tomb_lords.current_lord(gm)
            where = f"Tomb of {lord['name']}" if lord else "Sith tomb"
        except Exception:
            where = "Sith tomb"
        where += f" · level {int(getattr(gm, 'tomb_floor', 0)) + 1}"
    else:
        where = str(getattr(gm, 'current_biome', 'surface') or 'surface').replace('_', ' ').title()
    cordon = getattr(gm, 'cordon', None)
    banner = None
    if cordon is not None and getattr(cordon, 'active', False) and not in_tomb:
        import math
        d = math.hypot(p.x - cordon.center[0], p.y - cordon.center[1])
        banner = f"Escape the cordon: ring {cordon.radius:.0f} m, you are {d:.0f}/{cordon.escape_radius:.0f} m out"
    targeting = (getattr(gm, 'pending_force_ability', None) is not None or getattr(gm, 'pending_gun_shot', False)
                 or getattr(gm, 'pending_grenade_throw', False))
    reticle = None
    if targeting:
        reticle = {'x': int(getattr(gm, 'target_x', p.x)) - x0, 'y': int(getattr(gm, 'target_y', p.y)) - y0}
    out = {
        'ready': True,
        'map': rows, 'seen': seen, 'biome': bio, 'tomb': in_tomb,
        'player': {'x': p.x - x0, 'y': p.y - y0},
        'enemies': ents, 'npcs': npcs, 'reticle': reticle,
        'hud': {
            'hp': int(getattr(p, 'hp', 0)), 'maxHp': int(getattr(p, 'max_hp', 1)),
            'force': int(getattr(p, 'force_energy', 0)), 'maxForce': int(getattr(p, 'max_force_energy', 100)),
            'stress': int(getattr(p, 'stress', 0)), 'maxStress': int(getattr(p, 'max_stress', 100)),
            'stressOn': bool(getattr(p, '_stress_system_active', False)),
            'heat': heat, 'tier': tier, 'level': int(getattr(p, 'level', 1)),
            'corruption': int(getattr(p, 'dark_corruption', 0) or 0),
            'wounds': [survival.WOUNDS[k]['name'] for k in survival.wounds(p)],
            'time': None if in_tomb else daynight.clock_label(gm),
            'dark': daynight.darkness(gm),
            'where': where, 'turn': int(getattr(gm, 'turn_count', 0)),
            'artifacts': int(getattr(gm, 'artifacts_collected', 0) or 0),
            'artifactsNeeded': int(getattr(gm, 'artifacts_needed', 3) or 3),
        },
        'banner': banner, 'targeting': bool(targeting),
        'messages': list(_outbox),
        'prompt': {'lines': prompt[0], 'runs': prompt[1]} if prompt else None,
        'dead': bool(getattr(gm, 'death', False) or getattr(p, 'hp', 1) <= 0),
        'victory': bool(getattr(gm, 'victory', False)),
    }
    _outbox.clear()
    return json.dumps(out)
