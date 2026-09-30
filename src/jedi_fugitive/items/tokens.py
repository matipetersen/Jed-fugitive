"""Token registry: map single-char map tokens to rich item metadata.

This allows map placement, pickup and inspection to refer to the same canonical
metadata as full ITEM_DEFS / WEAPONS / ARMORS without duplicating logic.

Enhanced token organization with visual grouping:
- Weapons (Red): Combat items, blasters, lightsabers
- Armor (Blue): Defensive equipment, shields, robes
- Consumables (Green): Healing, energy, temporary effects
- Tools (Yellow): Utility items, devices, equipment
- Materials (White/Magenta): Crafting components by rarity
- Quest Items (Cyan): Special story/progression items
- Rare Items (Bright colors): Unique/legendary equipment
"""
from copy import deepcopy

# Enhanced token categories for better organization
TOKEN_CATEGORIES = {
    'weapons': {'symbols': 'vb/L_', 'color': 'red', 'description': 'Combat weapons and tools'},
    'armor': {'symbols': 's;,', 'color': 'blue', 'description': 'Defensive equipment'},
    'consumables': {'symbols': 'ht*!', 'color': 'green', 'description': 'Healing and energy items'},
    'tools': {'symbols': 'TPF+?', 'color': 'yellow', 'description': 'Utility and equipment'},
    'common_materials': {'symbols': 'mwpl', 'color': 'white', 'description': 'Basic crafting materials'},
    'rare_materials': {'symbols': 'iKk', 'color': 'magenta', 'description': 'Rare crafting components'},
    'quest_items': {'symbols': 'DJC', 'color': 'cyan', 'description': 'Special story items'}
}

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
                    'color': 'green',  # Consumables in green
                }
            except Exception:
                continue
except Exception:
    pass

# weapons: map common weapon types to tokens
try:
    if weapons_mod is not None:
        for w in getattr(weapons_mod, 'WEAPONS', []):
            try:
                nm = getattr(w, 'name', '') or ''
                ln = nm.lower()
                if 'vibroblade' in ln and 'v' not in TOKEN_MAP:
                    TOKEN_MAP['v'] = {'id': 'vibroblade', 'name': nm, 'token': 'v', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm, 'color': 'red'}
                if 'blaster pistol' in ln and 'b' not in TOKEN_MAP:
                    TOKEN_MAP['b'] = {'id': 'blaster_pistol', 'name': nm, 'token': 'b', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm, 'color': 'red'}
                # lightsaber token mapping (use 'L' if available)
                if 'lightsaber' in ln and '/' not in TOKEN_MAP:
                    TOKEN_MAP['/'] = {'id': 'lightsaber', 'name': nm, 'token': '/', 'type': 'weapon', 'description': getattr(w, 'description', ''), 'prototype_name': nm}
            except Exception:
                continue
except Exception:
    pass

# armor/shield tokens
try:
    if armor_mod is not None:
        for a in getattr(armor_mod, 'ARMORS', []):
            try:
                nm = getattr(a, 'name', '').lower()
                if 'shield' in nm and 's' not in TOKEN_MAP:
                    TOKEN_MAP['s'] = {'id': getattr(a, 'name', 'shield').lower().replace(' ', '_'), 'name': getattr(a, 'name', 'Shield'), 'token': 's', 'type': 'armor', 'description': getattr(a, 'description', ''), 'color': 'blue'}
                elif 'robes' in nm and ';' not in TOKEN_MAP:
                    TOKEN_MAP[';'] = {'id': 'jedi_robes', 'name': getattr(a, 'name', 'Robes'), 'token': ';', 'type': 'armor', 'description': getattr(a, 'description', ''), 'color': 'blue'}
                elif 'armor' in nm and ',' not in TOKEN_MAP:
                    TOKEN_MAP[','] = {'id': 'combat_armor', 'name': getattr(a, 'name', 'Armor'), 'token': ',', 'type': 'armor', 'description': getattr(a, 'description', ''), 'color': 'blue'}
            except Exception:
                continue
    # Fallback shield if none found
    if 's' not in TOKEN_MAP:
        TOKEN_MAP['s'] = {'id': 'energy_shield', 'name': 'Energy Shield', 'token': 's', 'type': 'armor', 'defense': 2, 'description': 'A compact energy shield that provides +2 defense.', 'color': 'blue'}
except Exception:
    pass

# Crafting materials tokens
try:
    from jedi_fugitive.items import crafting as crafting_mod
    if crafting_mod is not None:
        materials = getattr(crafting_mod, 'MATERIALS', [])
        # lowercase glyphs that do not collide with terrain/landmarks (M/P/C/o used to)
        material_tokens = {
            'm': 'Scrap Metal',
            'h': 'Durasteel Plate',
            'w': 'Fused Wire',
            'e': 'Power Cell',
            'p': 'Plasteel Composite',
            'l': 'Focusing Lens',
            'i': 'Advanced Circuitry',
            'k': 'Cortosis Ore',
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
                    # Enhanced material categorization with better visual grouping
                    rarity = getattr(found_mat, 'rarity', 'Common').lower()
                    
                    # Assign to appropriate category based on rarity and token
                    if token in TOKEN_CATEGORIES['common_materials']['symbols']:
                        color = TOKEN_CATEGORIES['common_materials']['color']
                        category = 'common_material'
                    elif token in TOKEN_CATEGORIES['rare_materials']['symbols']:
                        color = TOKEN_CATEGORIES['rare_materials']['color']
                        category = 'rare_material'
                    else:
                        # Fallback color by rarity
                        color = 'white' if rarity == 'common' else 'yellow' if rarity == 'uncommon' else 'magenta' if rarity == 'rare' else 'cyan'
                        category = 'material'
                    
                    TOKEN_MAP[token] = {
                        'id': mat_name.lower().replace(' ', '_'),
                        'name': mat_name,
                        'token': token,
                        'type': 'material',
                        'category': category,
                        'description': getattr(found_mat, 'description', f'{mat_name} crafting material'),
                        'color': color,
                        'rarity': rarity
                    }
except Exception:
    pass

def get_tokens_by_category(category):
    """Get all tokens belonging to a specific category for organized display."""
    return {token: data for token, data in TOKEN_MAP.items() 
            if data.get('category') == category or 
            (category == 'weapon' and data.get('type') == 'weapon') or
            (category == 'armor' and data.get('type') == 'armor') or
            (category == 'consumable' and data.get('type') == 'consumable')}

def get_token_color_legend():
    """Generate a color legend for token categories."""
    legend = []
    for cat_name, cat_data in TOKEN_CATEGORIES.items():
        color = cat_data['color']
        symbols = cat_data['symbols'][:5] + ('...' if len(cat_data['symbols']) > 5 else '')
        desc = cat_data['description']
        legend.append(f"#{color}#{symbols} - {desc}#0#")
    return legend

def enhance_token_with_category(token_data):
    """Auto-assign category and enhanced color to token based on type."""
    token_type = token_data.get('type', 'misc')
    token_char = token_data.get('token', '?')
    
    # Auto-categorize based on type and symbol
    if token_type == 'weapon':
        if token_char in TOKEN_CATEGORIES['weapons']['symbols']:
            token_data['category'] = 'weapon'
            token_data['color'] = TOKEN_CATEGORIES['weapons']['color']
    elif token_type == 'armor':
        if token_char in TOKEN_CATEGORIES['armor']['symbols']:
            token_data['category'] = 'armor'  
            token_data['color'] = TOKEN_CATEGORIES['armor']['color']
    elif token_type == 'consumable':
        if token_char in TOKEN_CATEGORIES['consumables']['symbols']:
            token_data['category'] = 'consumable'
            token_data['color'] = TOKEN_CATEGORIES['consumables']['color']
    elif token_type == 'tool':
        if token_char in TOKEN_CATEGORIES['tools']['symbols']:
            token_data['category'] = 'tool'
            token_data['color'] = TOKEN_CATEGORIES['tools']['color']
    
    return token_data

# Jedi Artifact - quest item for victory condition
if 'Q' not in TOKEN_MAP:
    TOKEN_MAP['Q'] = {
        'id': 'jedi_artifact',
        'name': 'Jedi Artifact',
        'token': 'Q',
        'type': 'quest_item',
        'description': 'An ancient Jedi relic corrupted by Sith magic. The artifact pulses with dark energy - you must recover it to cleanse the tomb and restore balance.',
        'quest': True,
        'unique': True,
        'color': 'magenta'
    }

# provide a convenience list
TOKEN_DEFS = list(TOKEN_MAP.values())

# fill missing descriptions and colors with generic fallbacks so UI/inspect always shows something
try:
    for tk, info in list(TOKEN_MAP.items()):
        try:
            name = info.get('name', '') if isinstance(info, dict) else str(info)
            if isinstance(info, dict):
                # Add default color if missing
                if not info.get('color'):
                    item_type = info.get('type', 'item')
                    default_colors = {
                        'weapon': 'red', 'armor': 'blue', 'consumable': 'green',
                        'material': 'white', 'quest_item': 'magenta', 'ammo': 'yellow'
                    }
                    info['color'] = default_colors.get(item_type, 'white')
                # Add default description if missing
                if not info.get('description'):
                    t = info.get('type', 'item')
                    info['description'] = f"{name} ({t})"
                TOKEN_MAP[tk] = info
        except Exception:
            continue
except Exception:
    pass

__all__ = ['TOKEN_MAP', 'TOKEN_DEFS']
