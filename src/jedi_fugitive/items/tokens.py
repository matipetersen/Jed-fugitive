"""Token registry: map single-char map tokens to rich item metadata.

This allows map placement, pickup and inspection to refer to the same canonical
metadata as full ITEM_DEFS / WEAPONS / ARMORS without duplicating logic.
"""
from copy import deepcopy
TOKEN_MAP = {}

try:
    from jedi_fugitive.items import consumables as consumables_mod
except Exception:
    consumables_mod = None

try:
    from jedi_fugitive.items import weapons as weapons_mod
except Exception:
    weapons_mod = None

try:
    from jedi_fugitive.items import armor as armor_mod
except Exception:
    armor_mod = None

# consumable tokens (take directly from ITEM_DEFS)
try:
    if consumables_mod is not None:
        for it in getattr(consumables_mod, 'ITEM_DEFS', []):
            try:
                tk = it.get('token')
                if not tk:
                    continue
                TOKEN_MAP[tk] = {
                    'id': it.get('id'),
                    'name': it.get('name'),
                    'token': tk,
                    'type': it.get('type', 'consumable'),
                    'description': it.get('description', ''),
                    'effect': deepcopy(it.get('effect', {})),
                }
            except Exception:
                continue
except Exception:
    pass

# weapons: map 'v' -> vibroblade, 'b' -> blaster pistol if available
try:
    if weapons_mod is not None:
        for w in getattr(weapons_mod, 'WEAPONS', []):
            try:
                nm = getattr(w, 'name', '') or ''
                ln = nm.lower()
                if 'vibroblade' in ln and 'v' not in TOKEN_MAP:
                    TOKEN_MAP['v'] = {'id': 'vibroblade', 'name': nm, 'token': 'v', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm}
                if 'blaster pistol' in ln and 'b' not in TOKEN_MAP:
                    TOKEN_MAP['b'] = {'id': 'blaster_pistol', 'name': nm, 'token': 'b', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm}
                # lightsaber token mapping (use 'L' if available)
                if 'lightsaber' in ln and 'L' not in TOKEN_MAP:
                    TOKEN_MAP['L'] = {'id': 'lightsaber', 'name': nm, 'token': 'L', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm}
            except Exception:
                continue
except Exception:
    pass

# armor/shield token 's' (fallback to a simple energy shield entry if no armor prototype)
try:
    if 's' not in TOKEN_MAP:
        found_shield = None
        if armor_mod is not None:
            for a in getattr(armor_mod, 'ARMORS', []):
                try:
                    if 'shield' in getattr(a, 'name', '').lower():
                        found_shield = a; break
                except Exception:
                    continue
        if found_shield is not None:
            TOKEN_MAP['s'] = {'id': getattr(found_shield, 'name', 'shield').lower().replace(' ', '_'), 'name': getattr(found_shield, 'name', 'Shield'), 'token': 's', 'type': 'armor', 'description': getattr(found_shield, 'description', '')}
        else:
            TOKEN_MAP['s'] = {'id': 'energy_shield', 'name': 'Energy Shield', 'token': 's', 'type': 'armor', 'defense': 2, 'description': 'A compact energy shield that provides +2 defense.'}
except Exception:
    pass

# Crafting materials tokens
try:
    from jedi_fugitive.items import crafting as crafting_mod
    if crafting_mod is not None:
        materials = getattr(crafting_mod, 'MATERIALS', [])
        material_tokens = {
            'm': 'Scrap Metal',
            'M': 'Durasteel Plate',
            'w': 'Fused Wire',
            'P': 'Power Cell',
            'p': 'Plasteel Composite',
            'l': 'Focusing Lens',
            'C': 'Advanced Circuitry',
            'o': 'Cortosis Ore',
            'K': 'Kyber Crystal',
        }
        
        for token, mat_name in material_tokens.items():
            if token not in TOKEN_MAP:
                # Find material in MATERIALS list
                found_mat = None
                for mat in materials:
                    if getattr(mat, 'name', '') == mat_name:
                        found_mat = mat
                        break
                
                if found_mat:
                    TOKEN_MAP[token] = {
                        'id': mat_name.lower().replace(' ', '_'),
                        'name': mat_name,
                        'token': token,
                        'type': 'material',
                        'description': getattr(found_mat, 'description', f'{mat_name} crafting material')
                    }
except Exception:
    pass

# Jedi Artifact - quest item for victory condition
if 'Q' not in TOKEN_MAP:
    TOKEN_MAP['Q'] = {
        'id': 'jedi_artifact',
        'name': 'Jedi Artifact',
        'token': 'Q',
        'type': 'quest_item',
        'description': 'An ancient Jedi relic corrupted by Sith magic. The artifact pulses with dark energy - you must recover it to cleanse the tomb and restore balance.',
        'quest': True,
        'unique': True
    }

# provide a convenience list
TOKEN_DEFS = list(TOKEN_MAP.values())

# fill missing descriptions with generic fallbacks so UI/inspect always shows something
try:
    for tk, info in list(TOKEN_MAP.items()):
        try:
            name = info.get('name', '') if isinstance(info, dict) else str(info)
            if isinstance(info, dict) and not info.get('description'):
                t = info.get('type', 'item')
                info['description'] = f"{name} ({t})"
                TOKEN_MAP[tk] = info
        except Exception:
            continue
except Exception:
    pass

__all__ = ['TOKEN_MAP', 'TOKEN_DEFS']
