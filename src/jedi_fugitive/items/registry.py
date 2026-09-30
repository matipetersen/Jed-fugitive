"""Single source of truth for turning map tokens / map entries into inventory items.

Before this module the same item could exist as a bare token string, a token
dict, a map entry with x/y, or a real Weapon/Shield object, and each system
(pickup, equip, use, drop, craft) handled a different subset. Items picked up
from the map are now materialized once, here:

* weapons   -> a copy of the matching ``Weapon`` from ``WEAPONS`` (real stats, hands)
* shields   -> a copy of a ``Shield`` from ``SHIELDS`` (equippable in the offhand)
* armor     -> a copy of the matching ``Armor``
* consumables / materials / quest items -> plain dicts without map coordinates
"""
from copy import deepcopy
import random

# Map glyphs that belong to items. Chosen so they never collide with terrain,
# landmarks or quest objects ('T' used to be both Calming Tea and a tree, 'C'
# both the Compass and the comms terminal, 'M' Meditation Focus and Monolith...).
ITEM_GLYPHS = set('+!0cftn:;z' 'vb/s' 'mhwepliKk' 'Q' 'E' '$' '&')

_MAP_ONLY_KEYS = ('x', 'y', 'guarded')

# glyphs items used before the collision fix (old scripts/saves may still carry them)
LEGACY_TOKENS = {'M': 'f', 'T': 't', 'C': 'n', '*': '0', 'L': '/', 'P': 'e', 'o': 'k'}


def _find(seq, pred):
    for it in seq:
        try:
            if pred(it):
                return it
        except Exception:
            continue
    return None


def weapon_by_name(name):
    try:
        from jedi_fugitive.items.weapons import WEAPONS
    except Exception:
        return None
    if not name:
        return None
    low = str(name).lower()
    w = _find(WEAPONS, lambda w: w.name.lower() == low) or _find(WEAPONS, lambda w: low in w.name.lower())
    return deepcopy(w) if w is not None else None


def shield_by_name(name=None):
    try:
        from jedi_fugitive.items.shields import SHIELDS
    except Exception:
        return None
    if name:
        low = str(name).lower()
        s = _find(SHIELDS, lambda s: s.name.lower() == low)
        if s is not None:
            return deepcopy(s)
    s = _find(SHIELDS, lambda s: 'energy' in s.name.lower()) or (SHIELDS[0] if SHIELDS else None)
    return deepcopy(s) if s is not None else None


def armor_by_name(name):
    try:
        from jedi_fugitive.items.armor import ARMORS
    except Exception:
        return None
    low = str(name or '').lower()
    a = _find(ARMORS, lambda a: a.name.lower() == low)
    return deepcopy(a) if a is not None else None


def materialize(entry):
    """Return the inventory form of a map entry, token dict or token string."""
    if entry is None:
        return None
    if not isinstance(entry, (dict, str)):
        return entry  # already a real object (Weapon, Shield, Armor, Material)
    if isinstance(entry, str):
        from jedi_fugitive.items.tokens import TOKEN_MAP
        info = TOKEN_MAP.get(entry)
        if info is None:
            return {'name': entry, 'token': entry}
        entry = info
    # dropped real objects travel inside the map entry
    if entry.get('object') is not None:
        return entry['object']
    # bare token entries ({'token': 'v'}) get the canonical metadata filled in
    if not entry.get('type') or not entry.get('name') or (entry.get('type') in ('consumable', 'ammo') and not entry.get('effect')):
        from jedi_fugitive.items.tokens import TOKEN_MAP
        tok = entry.get('token')
        base = TOKEN_MAP.get(tok) or TOKEN_MAP.get(LEGACY_TOKENS.get(tok, ''))
        if base:
            merged = dict(base)
            merged.update({k: v for k, v in entry.items() if v not in (None, '', {}) and k != 'token'})
            entry = merged
    itype = entry.get('type')
    name = entry.get('prototype_name') or entry.get('name')
    if itype == 'weapon':
        w = weapon_by_name(name)
        if w is not None:
            return w
    if itype in ('armor', 'shield'):
        if 'shield' in str(name).lower() or entry.get('token') == 's':
            s = shield_by_name(name)
            if s is not None:
                return s
        a = armor_by_name(name)
        if a is not None:
            return a
    item = {k: deepcopy(v) for k, v in entry.items() if k not in _MAP_ONLY_KEYS}
    if item.get('effect') is None and itype in ('consumable', 'ammo'):
        item['effect'] = {}
    return item


def map_entry(item, x, y, token=None):
    """Build an items_on_map entry for an inventory item (keeps real objects intact)."""
    if isinstance(item, dict):
        e = dict(item)
        e['x'], e['y'] = x, y
        if token:
            e['token'] = token
        e.setdefault('token', e.get('token') or '?')
        return e
    name = getattr(item, 'name', str(item))
    itype = getattr(item, 'type', 'item')
    glyph = token or {'weapon': 'v', 'shield': 's', 'material': 'm'}.get(itype, 'E')
    if itype == 'weapon' and 'saber' in name.lower():
        glyph = token or '/'
    return {'x': x, 'y': y, 'token': glyph, 'name': name, 'type': itype,
            'description': getattr(item, 'description', ''), 'object': item}


def item_name(item):
    if isinstance(item, dict):
        return item.get('name') or item.get('token') or 'item'
    return getattr(item, 'name', str(item))


def cache_loot(rng=random):
    """Contents of a guarded Sith supply cache: supplies plus a chance of gear."""
    from jedi_fugitive.items.tokens import TOKEN_MAP
    loot = [materialize(TOKEN_MAP[rng.choice(['+', '!', ':', 'c'])])]
    roll = rng.random()
    if roll < 0.45:
        loot.append(materialize(TOKEN_MAP[rng.choice(['v', 'b', 's'])]))
    elif roll < 0.8:
        loot.append(materialize(TOKEN_MAP[rng.choice(['0', 'f', 'n'])]))
    else:
        loot.append(materialize(TOKEN_MAP[rng.choice(['h', 'e', 'i', 'l'])]))
    return [it for it in loot if it is not None]
