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
            "Many were once Jedi Padawans who fell during Order 66.",
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
            "Veterans of the Clone Wars, they hunt surviving Jedi with brutal efficiency.",
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
            "Many fell during Order 66, choosing survival over principle.",
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
        'lore': "Standard Republic issue. These supplies have saved countless lives during the Clone Wars.",
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
}

# Environmental inspection text
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
            "Your ship was shot down during Order 66's chaos.",
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
