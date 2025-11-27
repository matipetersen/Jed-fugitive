"""
Enhanced inspection system with detailed lore for enemies, items, and environment.
Provides rich descriptions and storytelling through the inspect command.
"""
import random

# Enemy lore by type
ENEMY_LORE = {
    'sith_acolyte': {
        'title': 'Sith Acolyte',
        'description': 'A dark side apprentice consumed by ambition and hatred.',
        'lore': [
            "Sith Acolytes are the lowest rank in the Sith hierarchy, hungry for power.",
            "They've abandoned the Jedi teachings in pursuit of strength through passion.",
            "Many were once Jedi who fell during the Great Jedi Purge of the Old Republic.",
            "Their rage makes them dangerous, but their inexperience is their weakness.",
        ],
        'tactics': 'Aggressive and reckless. Exploit their overconfidence.',
        'corruption_notes': {
            'light': "You sense the person they once were, before the darkness consumed them.",
            'dark': "You recognize their hunger for power - it mirrors your own.",
            'balanced': "They chose one extreme. You've chosen to walk between."
        }
    },
    'sith_warrior': {
        'title': 'Sith Warrior',
        'description': 'A battle-hardened servant of the dark side.',
        'lore': [
            "Sith Warriors have proven themselves through countless battles.",
            "They embody the dark side philosophy: power through passion and victory.",
            "Veterans of the Great Galactic War, they hunt Jedi with brutal efficiency.",
            "Their lightsaber forms emphasize aggression over defense.",
        ],
        'tactics': 'Experienced combatant. Match their aggression or outmaneuver them.',
        'corruption_notes': {
            'light': "The darkness radiating from them fills you with sadness for what they've become.",
            'dark': "A worthy opponent. Defeating them will prove your superiority.",
            'balanced': "They've mastered one aspect of the Force. You seek to master both."
        }
    },
    'dark_jedi': {
        'title': 'Dark Jedi',
        'description': 'A former Jedi who has fallen to the dark side.',
        'lore': [
            "Dark Jedi retain their training but have embraced forbidden powers.",
            "Unlike true Sith, they haven't fully committed to the Sith philosophy.",
            "Many fell during the Jedi Civil War, choosing power over principle.",
            "They walk a path of inner conflict between their past and present.",
        ],
        'tactics': 'Combines Jedi technique with dark side powers. Stay adaptable.',
        'corruption_notes': {
            'light': "There's still conflict in them. Perhaps redemption is possible?",
            'dark': "They're weak, clinging to their Jedi past. You've surpassed such limitations.",
            'balanced': "They understand both sides but lack balance. A cautionary tale."
        }
    },
    'sith_lord': {
        'title': 'Sith Lord',
        'description': 'A master of the dark side wielding immense power.',
        'lore': [
            "Sith Lords have spent decades perfecting their mastery of the dark side.",
            "Each bears a Darth title, earned through treachery and triumph.",
            "They've studied ancient Sith holocrons and learned forbidden techniques.",
            "Many survived the Rule of Two by hiding in the Unknown Regions.",
        ],
        'tactics': 'Extremely dangerous. Use every advantage. Retreat is not cowardice.',
        'corruption_notes': {
            'light': "The corruption is overwhelming. This is what you're fighting against.",
            'dark': "This is your future if you continue down the dark path. Power incarnate.",
            'balanced': "They've achieved mastery through extremity. Can balance achieve the same?"
        }
    },
}

# Item descriptions and lore
ITEM_LORE = {
    'lightsaber': {
        'description': 'An elegant weapon for a more civilized age.',
        'lore': "The lightsaber is not just a weapon - it's a Jedi's life. Each crystal attunes to its wielder through the Force.",
        'condition_text': {
            'light': "Your crystal glows with a steady blue light, pure and true.",
            'dark': "Your crystal pulses with crimson energy, reflecting your inner turmoil.",
            'balanced': "Your crystal shimmers between colors, mirroring your balanced path."
        }
    },
    'force_crystal': {
        'description': 'A kyber crystal attuned to the Force.',
        'lore': "Kyber crystals are living Force conduits. They choose their Jedi as much as the Jedi chooses them.",
    },
    'medkit': {
        'description': 'Emergency medical supplies from your crashed ship.',
        'lore': "Standard Republic issue. These supplies saved countless lives during the Great Galactic War.",
    },
    'ration': {
        'description': 'Preserved food, tasteless but nourishing.',
        'lore': "Military rations designed for extended campaigns. You've eaten better, but you've eaten worse.",
    },
    'stimpack': {
        'description': 'A combat stimulant that temporarily enhances abilities.',
        'lore': "Used by clone troopers for extreme situations. The Jedi Council frowned upon their use.",
    },
    'ancient_artifact': {
        'description': 'A mysterious relic radiating Force energy.',
        'lore': "These artifacts predate the Republic. Each one holds the essence of its creator - for good or ill.",
        'corruption_choice': "Absorb its power (dark) or Destroy it (light) - your choice shapes your destiny.",
    },
    # Weapons
    'training_saber': {
        'description': 'A practice lightsaber with reduced power output.',
        'lore': "Younglings train with these before constructing their true lightsaber. The Force guided you to salvage this from the wreckage.",
    },
    'vibroblade': {
        'description': 'A vibrating blade that can cut through armor.',
        'lore': "Mandalorian design, perfected over centuries of warfare. It hums with deadly efficiency in your hand.",
    },
    'blaster': {
        'description': 'Standard issue energy weapon.',
        'lore': "An uncivilized weapon, but effective. Sometimes a Jedi must adapt to survive.",
    },
    'grenade': {
        'description': 'Thermal detonator with adjustable yield.',
        'lore': "Banned by the Jedi Council for their indiscriminate destruction. Desperate times call for desperate measures.",
    },
    # Armor
    'jedi_robes': {
        'description': 'Traditional Jedi garments worn for centuries.',
        'lore': "These robes mark you as a guardian of peace. Now they make you a target for those who hunt Jedi.",
    },
    'combat_armor': {
        'description': 'Reinforced plating designed for battlefield survival.',
        'lore': "Clone trooper armor, modified for mobility. It has protected countless Republic soldiers.",
    },
    'energy_shield': {
        'description': 'Personal deflector shield generator.',
        'lore': "Ancient Sith technology repurposed by the Republic. It draws power from your Force connection.",
    },
    # Consumables
    'bacta_tank': {
        'description': 'Concentrated healing agent.',
        'lore': "Bacta saved thousands during the Great Galactic War. This small supply is precious.",
    },
    'force_crystal_shard': {
        'description': 'A fragment of a broken kyber crystal.',
        'lore': "Even shattered, the Force resonates within. Perhaps it can be reforged with skill and meditation.",
    },
    'nutrient_paste': {
        'description': 'Compressed food designed for deep space missions.',
        'lore': "It tastes like despair and survival. Every fugitive's constant companion.",
    },
    # Materials
    'durasteel': {
        'description': 'High-strength alloy used in starship hulls.',
        'lore': "Salvaged from your crashed vessel. With proper crafting, it could reinforce equipment.",
    },
    'cortosis_ore': {
        'description': 'Rare mineral that disrupts lightsaber blades.',
        'lore': "Sith assassins weave this into their armor. Its presence here suggests ancient battles were fought on this world.",
    },
}

# Environmental inspection text - ENHANCED with eerie descriptions for all tile types
ENVIRONMENT_LORE = {
    'tomb_entrance': {
        'description': 'An ancient entrance carved with Sith runes.',
        'lore': [
            "Sith tombs were designed to test those who seek their knowledge.",
            "The runes warn of trials ahead - combat, sacrifice, and temptation.",
            "Many enter seeking power. Few leave with their sanity intact.",
        ]
    },
    'ancient_statue': {
        'description': 'A weathered statue of a hooded Sith Lord.',
        'lore': [
            "This statue depicts a Sith Lord from the Old Republic era.",
            "Their eyes seem to follow you, judging your worthiness.",
            "Sith culture glorified the powerful and despised the weak.",
        ]
    },
    'crash_wreckage': {
        'description': 'The twisted remains of your Republic vessel.',
        'lore': [
            "Your ship was shot down during the Great Sith War's chaos.",
            "The crash killed most of the crew. You survived by chance - or destiny.",
            "This wreckage marks both an ending and a beginning.",
        ]
    },
    'meditation_shrine': {
        'description': 'A small shrine marked by carved stones.',
        'lore': [
            "Ancient Force users built these shrines at points of Force convergence.",
            "The Force flows strongly here, offering clarity to those who seek it.",
            "Both Jedi and Sith have meditated here over the millennia.",
        ]
    },
    # NEW: Tile-specific eerie descriptions
    'floor': {
        'description': 'Barren ground, worn smooth by forgotten footsteps.',
        'lore': [
            "How many have walked this path before you? Their bones now dust, their names erased.",
            "The ground remembers violence. Blood soaked into soil millennia ago still whispers of betrayal.",
            "Empty space is never truly empty. The Force echoes with the screams of the fallen.",
        ]
    },
    'wall': {
        'description': 'Ancient stone walls, cold and unyielding.',
        'lore': [
            "These walls have witnessed unspeakable horrors. They remember. They always remember.",
            "Stone holds memory better than flesh. What terrors did these walls observe?",
            "The walls seem to press inward when you're not looking. The tomb does not want you here.",
        ]
    },
    'stairs_down': {
        'description': 'Stairs descending into suffocating darkness.',
        'lore': [
            "Each step down takes you further from the light. Closer to something ancient. Something hungry.",
            "The stairs groan under your weight, as if the tomb itself warns you away.",
            "Darkness waits below. It has been patient for thousands of years.",
        ]
    },
    'stairs_up': {
        'description': 'Stairs ascending toward distant light.',
        'lore': [
            "Escape beckons above, but you know you'll return. The darkness calls to something within you.",
            "The way up is never as easy as the way down. The tomb holds you with invisible chains.",
            "Light promises safety, but you've tasted power. Which will you choose?",
        ]
    },
    'forest': {
        'description': 'Dense, twisted trees claw at the perpetual twilight.',
        'lore': [
            "The trees grew gnarled and wrong, warped by dark side energy seeping from the tombs.",
            "Birds don't sing here. Nothing living makes sound in these cursed woods.",
            "The forest watches you with a thousand unseen eyes. You are the intruder.",
        ]
    },
    'desert': {
        'description': 'Endless dunes of bone-white sand stretch toward oblivion.',
        'lore': [
            "The sand whispers names of the dead. Sometimes, it whispers yours.",
            "Nothing should survive here, yet you do. The Force has plans for you.",
            "Heat shimmers reveal shapes that vanish when you look directly. Ghosts, or madness?",
        ]
    },
    'rocky': {
        'description': 'Jagged rocks jut from the earth like broken teeth.',
        'lore': [
            "The stones are sharp enough to draw blood. The planet wants your sacrifice.",
            "Ancient battles shattered the bedrock. You can still feel the violence in the air.",
            "The rocks form patterns. Runes? Or do you see meaning where there is none?",
        ]
    },
    'plains': {
        'description': 'Desolate grassland stretches beneath a blood-red sky.',
        'lore': [
            "The grass grows pale and lifeless, drained by the dark side's presence.",
            "Wind carries sounds that might be voices. Or might be your imagination.",
            "You stand exposed under the uncaring sky. Nowhere to hide. Nowhere to run.",
        ]
    },
    'darkness': {
        'description': 'Oppressive darkness that devours light.',
        'lore': [
            "The shadows here are alive. They hunger for warmth, for life, for you.",
            "Your eyes adjust, but understanding never comes. The darkness hides truths you cannot comprehend.",
            "In darkness, all fears take form. What shape will yours assume?",
        ]
    },
    'wreckage': {
        'description': 'Twisted metal and shattered dreams.',
        'lore': [
            "Your ship died screaming. You can still hear it in the howling wind.",
            "Every piece of debris is a reminder: you should be dead. Why aren't you?",
            "The wreckage attracts scavengers. Some walk on two legs. Some don't.",
        ]
    },
}

def get_enemy_inspection(enemy_name, player_corruption):
    """Get detailed inspection text for an enemy."""
    # Try to match enemy type from name
    enemy_type = None
    name_lower = enemy_name.lower()
    
    if 'acolyte' in name_lower:
        enemy_type = 'sith_acolyte'
    elif 'warrior' in name_lower:
        enemy_type = 'sith_warrior'
    elif 'dark jedi' in name_lower or 'fallen jedi' in name_lower:
        enemy_type = 'dark_jedi'
    elif 'sith' in name_lower or 'darth' in name_lower or 'lord' in name_lower:
        enemy_type = 'sith_lord'
    
    if not enemy_type or enemy_type not in ENEMY_LORE:
        return {
            'title': enemy_name,
            'description': 'A dark side warrior who hunts you.',
            'lore': ['This enemy wields the dark side of the Force.'],
            'tactics': 'Approach with caution.',
            'personal_note': "You sense their connection to the dark side."
        }
    
    enemy_data = ENEMY_LORE[enemy_type]
    
    # Get corruption-specific note
    if player_corruption <= 35:
        alignment = 'light'
    elif player_corruption <= 65:
        alignment = 'balanced'
    else:
        alignment = 'dark'
    
    personal_note = enemy_data['corruption_notes'].get(alignment, "")
    
    return {
        'title': enemy_data['title'],
        'description': enemy_data['description'],
        'lore': random.choice(enemy_data['lore']),
        'tactics': enemy_data['tactics'],
        'personal_note': personal_note
    }

def get_item_inspection(item_token, item_name, player_corruption):
    """Get detailed inspection text for an item."""
    # Try to match item type
    item_key = None
    name_lower = item_name.lower() if item_name else ''
    token_lower = item_token.lower() if item_token else ''
    
    for key in ITEM_LORE.keys():
        if key in name_lower or key.replace('_', ' ') in name_lower:
            item_key = key
            break
        if key in token_lower or key.replace('_', ' ') in token_lower:
            item_key = key
            break
    
    if not item_key:
        # Generic item description
        return {
            'name': item_name or item_token,
            'description': f'A {item_name or "mysterious item"} lying on the ground.',
            'lore': "Every item has a story, though this one's history is lost to time."
        }
    
    item_data = ITEM_LORE[item_key]
    result = {
        'name': item_name or item_token,
        'description': item_data['description'],
        'lore': item_data.get('lore', '')
    }
    
    # Add condition text for lightsaber
    if item_key == 'lightsaber' and 'condition_text' in item_data:
        if player_corruption <= 35:
            result['condition'] = item_data['condition_text']['light']
        elif player_corruption <= 65:
            result['condition'] = item_data['condition_text']['balanced']
        else:
            result['condition'] = item_data['condition_text']['dark']
    
    # Add corruption choice for artifacts
    if 'corruption_choice' in item_data:
        result['choice'] = item_data['corruption_choice']
    
    return result

def get_tile_description(tile_char, biome=None, in_tomb=False):
    """Get eerie description for a specific tile based on character and context."""
    # Map tile characters to environment types
    tile_map = {
        '.': 'floor',
        '#': 'wall',
        '>': 'stairs_down',
        '<': 'stairs_up',
        'D': 'tomb_entrance',
        'W': 'wreckage',
    }
    
    # Use biome for floor tiles if available
    if tile_char == '.' and biome:
        location_type = biome
    else:
        location_type = tile_map.get(tile_char, 'floor')
    
    # If in tomb, use more oppressive description
    if in_tomb and location_type == 'floor':
        location_type = 'darkness'
    
    return get_environment_inspection(location_type)

def get_environment_inspection(location_type):
    """Get detailed inspection text for environmental features."""
    if location_type not in ENVIRONMENT_LORE:
        return None
    
    env_data = ENVIRONMENT_LORE[location_type]
    return {
        'description': env_data['description'],
        'lore': random.choice(env_data['lore']) if isinstance(env_data['lore'], list) else env_data['lore']
    }

def format_inspection_text(inspection_data, data_type='enemy'):
    """Format inspection data into display lines."""
    lines = []
    
    if data_type == 'enemy':
        lines.append(f"═══ {inspection_data['title']} ═══")
        lines.append("")
        lines.append(inspection_data['description'])
        lines.append("")
        lines.append(f"Lore: {inspection_data['lore']}")
        lines.append("")
        lines.append(f"Tactics: {inspection_data['tactics']}")
        if inspection_data.get('personal_note'):
            lines.append("")
            lines.append(f"[{inspection_data['personal_note']}]")
    
    elif data_type == 'item':
        lines.append(f"═══ {inspection_data['name']} ═══")
        lines.append("")
        lines.append(inspection_data['description'])
        if inspection_data.get('lore'):
            lines.append("")
            lines.append(inspection_data['lore'])
        if inspection_data.get('condition'):
            lines.append("")
            lines.append(inspection_data['condition'])
        if inspection_data.get('choice'):
            lines.append("")
            lines.append(inspection_data['choice'])
    
    elif data_type == 'environment':
        lines.append("═══ Point of Interest ═══")
        lines.append("")
        lines.append(inspection_data['description'])
        lines.append("")
        lines.append(inspection_data['lore'])
    
    return lines
