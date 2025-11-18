"""
NPC Encounter system for Jedi Fugitive.
Handles survivor camps, hermit Jedi/Sith, moral choices, and dialogue.
"""
import random

# NPC types and their properties
NPC_TYPES = {
    'survivor_camp': {
        'symbol': '@',
        'color': 'yellow',
        'name': 'Survivor Camp',
        'description': 'A small group of refugees from Order 66.',
        'spawn_chance': 0.15,  # 15% chance per biome
        'biomes': ['forest', 'plains', 'river', 'crash_site'],
    },
    'hermit_jedi': {
        'symbol': 'J',
        'color': 'cyan',
        'name': 'Hermit Jedi',
        'description': 'A Jedi Master in hiding.',
        'spawn_chance': 0.10,  # 10% chance per biome
        'biomes': ['forest', 'mountain_pass', 'rocky'],
    },
    'fallen_jedi': {
        'symbol': 'F',
        'color': 'magenta',
        'name': 'Fallen Jedi',
        'description': 'A Jedi who turned to the dark side.',
        'spawn_chance': 0.08,  # 8% chance per biome
        'biomes': ['desert', 'rocky', 'tomb'],
    },
    'dark_hermit': {
        'symbol': 'D',
        'color': 'red',
        'name': 'Dark Side Hermit',
        'description': 'A Sith cultist studying forbidden knowledge.',
        'spawn_chance': 0.12,  # 12% chance per biome
        'biomes': ['tomb', 'desert', 'rocky'],
    },
}

# Survivor camp dialogues and interactions
SURVIVOR_DIALOGUES = {
    'greeting': [
        "You there! Please, we mean no harm. Are you... are you a Jedi?",
        "By the Force, another survivor! We thought we were alone.",
        "Stay back! Wait... you're not with the Empire, are you?",
        "Please help us. We've been running for weeks.",
    ],
    'light_response': [
        "Your presence brings us hope. Thank you for not abandoning us.",
        "A true Jedi! We knew some would survive the purge.",
        "The Force is still with us. Will you help protect our camp?",
    ],
    'dark_response': [
        "Your eyes... they're different. What have you become?",
        "You carry darkness with you. Perhaps we should keep our distance.",
        "We've heard rumors of Jedi turning dark. Is it true?",
    ],
    'trade_offer': [
        "We salvaged supplies from crashed ships. Perhaps we can trade?",
        "We don't have much, but we'd be grateful to share what we have.",
        "Take what you need. We owe you our lives.",
    ],
    'moral_choice_setup': [
        "The Empire's scouts were here yesterday. They're looking for Force users.",
        "We have wounded. The Empire took our medical supplies.",
        "We're planning to flee deeper into the wilderness. It's dangerous.",
    ]
}

# Hermit Jedi dialogues (Light Side mentors)
HERMIT_JEDI_DIALOGUES = {
    'greeting': [
        "Peace, young one. I sensed your presence through the Force.",
        "Another survivor of Order 66. The Force guided you here.",
        "I've been waiting. The Force told me you would come.",
    ],
    'light_path': [
        "I see the light still burns within you. Good. Hold onto it.",
        "The dark times test us all, but you resist temptation. Admirable.",
        "Your crystal glows pure. You walk the path of the Jedi.",
    ],
    'balanced_path': [
        "You walk a dangerous line between light and dark.",
        "Balance is wise, but be cautious. Many who sought balance fell to darkness.",
        "You seek to understand both sides. A perilous, but perhaps necessary, path.",
    ],
    'dark_warning': [
        "I sense the darkness growing in you. Turn back before it's too late!",
        "The dark side clouds your judgment. You can still choose redemption.",
        "You're on the path that leads to suffering. I've seen it before.",
    ],
    'teaching_offer': [
        "I can teach you an old technique, if you're willing to learn.",
        "The ancient Jedi knew secrets lost to the modern Order. I can share them.",
        "Meditation and patience - let me show you what I've learned.",
    ],
    'philosophy': [
        "The Jedi Order fell because it became rigid. We must adapt to survive.",
        "Attachment led to our downfall, but complete detachment made us blind.",
        "The Force flows through all living things. Never forget that.",
    ]
}

# Fallen Jedi dialogues (temptation to dark side)
FALLEN_JEDI_DIALOGUES = {
    'greeting': [
        "Another Jedi? No... you're more than that. I can sense your potential.",
        "The Order abandoned us. The Empire hunts us. What choice did we have?",
        "You survived too. Have you embraced your anger yet?",
    ],
    'light_rejection': [
        "Still clinging to the old ways? The Jedi Code failed us!",
        "Your restraint will get you killed. The dark side offers power.",
        "You're weak, just like the Council. They're all dead now.",
    ],
    'balanced_interest': [
        "You understand, don't you? Neither fully light nor dark.",
        "The middle path... interesting. But will it be enough to survive?",
        "You seek power without losing yourself. I tried that too.",
    ],
    'dark_kinship': [
        "Yes! You've embraced what we truly are. The strong survive.",
        "Together we could be unstoppable. The Empire would fear us.",
        "I see the hunger in your eyes. Good. Use it.",
    ],
    'temptation_offer': [
        "I know a Sith technique. Dark, yes, but powerful. Want to learn?",
        "There's a tomb nearby. The power inside could make you invincible.",
        "Join me. Together we can take what we deserve.",
    ],
    'warning': [
        "The Inquisitors are coming. They'll find you eventually.",
        "The Empire doesn't distinguish between light and dark Jedi. We're all targets.",
        "Survival is all that matters now. Morality is a luxury.",
    ]
}

# Dark Hermit dialogues (Sith cultists)
DARK_HERMIT_DIALOGUES = {
    'greeting': [
        "Welcome, seeker. Do you hunger for true power?",
        "The dark side called you here. Do not resist it.",
        "Another Force user drawn to this place. Curious.",
    ],
    'light_hostility': [
        "A Jedi! Your kind are relics of a failed Order.",
        "The light makes you weak. You'll die clinging to your principles.",
        "Turn back, Jedi. This place is not for you.",
    ],
    'balanced_curiosity': [
        "You flirt with darkness but don't commit. Cowardice or wisdom?",
        "The dark side beckons you, yet you resist. Why?",
        "You could be powerful if you'd only let go of your reservations.",
    ],
    'dark_welcome': [
        "Ah, one who understands! The dark side has blessed you.",
        "I sense great power in you. You've embraced your true nature.",
        "Welcome, apprentice of darkness. Let me show you secrets.",
    ],
    'knowledge_offer': [
        "I possess knowledge from ancient Sith holocrons. It can be yours.",
        "Forbidden techniques, lost to time. Would you like to learn?",
        "Power comes at a price. Are you willing to pay it?",
    ],
    'corruption_tempt': [
        "Feel the dark side flowing through this place. Embrace it!",
        "Your anger, your fear - they are weapons. Wield them!",
        "The Jedi lied to you. Passion is strength, not weakness.",
    ]
}

# Moral choices that NPCs can present
MORAL_CHOICES = {
    'imperial_scouts': {
        'setup': "Imperial scouts are tracking this camp. We could ambush them, but...",
        'option_light': {
            'text': "Help them escape quietly (Light)",
            'corruption_change': -10,
            'message': "You help the survivors slip away under cover. The scouts find only an abandoned camp.",
            'reward': None
        },
        'option_dark': {
            'text': "Ambush and kill the scouts (Dark)",
            'corruption_change': 15,
            'message': "You strike from the shadows. The scouts never see it coming. The survivors are safe, but at what cost?",
            'reward': 'imperial_commlink'
        }
    },
    'wounded_civilian': {
        'setup': "This person is dying. I have a Force technique that could save them, but it draws on the dark side.",
        'option_light': {
            'text': "Use traditional healing, knowing it may not be enough (Light)",
            'corruption_change': -5,
            'message': "You do what you can with Jedi healing techniques. Their fate is in the Force's hands now.",
            'reward': None
        },
        'option_dark': {
            'text': "Use dark side healing to guarantee survival (Dark)",
            'corruption_change': 12,
            'message': "You channel the dark side. Life Force flows from you into them. They live, but you feel changed.",
            'reward': 'force_essence'
        }
    },
    'stolen_supplies': {
        'setup': "Raiders stole our supplies. We know where they're camped. We need someone to get them back.",
        'option_light': {
            'text': "Negotiate or intimidate the raiders into returning supplies (Light)",
            'corruption_change': -3,
            'message': "You confront the raiders. Your presence alone is enough - they return what they took.",
            'reward': 'extra_rations'
        },
        'option_dark': {
            'text': "Take the supplies back by force (Dark)",
            'corruption_change': 8,
            'message': "You don't give them a choice. The supplies are yours now. So is everything else they had.",
            'reward': 'raider_cache'
        }
    },
    'information_torture': {
        'setup': "We captured an Imperial. He knows where other survivors are hiding. He won't talk.",
        'option_light': {
            'text': "Let him go or convince him through compassion (Light)",
            'corruption_change': -8,
            'message': "You show mercy. He's just a soldier following orders. Perhaps he'll remember this kindness.",
            'reward': None
        },
        'option_dark': {
            'text': "Use Force interrogation to extract the information (Dark)",
            'corruption_change': 18,
            'message': "You tear through his mental defenses. You get the information, but the man is broken. Was it worth it?",
            'reward': 'intelligence_data'
        }
    },
    'artifact_choice': {
        'setup': "This Sith artifact pulses with dark power. It could make you stronger, or corrupt you further.",
        'option_light': {
            'text': "Destroy the artifact to prevent its evil from spreading (Light)",
            'corruption_change': -12,
            'message': "You shatter the artifact. The dark presence dissipates. You feel lighter.",
            'reward': None
        },
        'option_dark': {
            'text': "Absorb the artifact's power into yourself (Dark)",
            'corruption_change': 20,
            'message': "Power floods through you. Ancient Sith knowledge fills your mind. You are changed forever.",
            'reward': 'sith_knowledge'
        }
    }
}

# Training offers from NPCs (can grant abilities or stat boosts)
TRAINING_OFFERS = {
    'jedi_meditation': {
        'name': 'Jedi Meditation Technique',
        'teacher': 'hermit_jedi',
        'corruption_required': (0, 40),  # Only if corruption is low
        'description': 'An ancient meditation technique that enhances Force regeneration.',
        'effect': 'force_regen_boost',
        'corruption_cost': -5
    },
    'defensive_forms': {
        'name': 'Defensive Lightsaber Forms',
        'teacher': 'hermit_jedi',
        'corruption_required': (0, 50),
        'description': 'Master Soresu and Shien, defensive forms emphasizing protection.',
        'effect': 'defense_boost',
        'corruption_cost': 0
    },
    'gray_balance': {
        'name': 'Gray Force Technique',
        'teacher': 'fallen_jedi',
        'corruption_required': (35, 65),  # Only if balanced
        'description': 'Use both light and dark without fully committing to either.',
        'effect': 'hybrid_power',
        'corruption_cost': 0
    },
    'aggressive_forms': {
        'name': 'Aggressive Combat Forms',
        'teacher': 'fallen_jedi',
        'corruption_required': (40, 100),
        'description': 'Learn Juyo and Djem So, forms focused on overwhelming offense.',
        'effect': 'attack_boost',
        'corruption_cost': 5
    },
    'sith_alchemy': {
        'name': 'Sith Alchemy Basics',
        'teacher': 'dark_hermit',
        'corruption_required': (60, 100),  # Only if corrupted
        'description': 'Dark side techniques to enhance weapons and armor.',
        'effect': 'item_enhancement',
        'corruption_cost': 10
    },
    'force_drain': {
        'name': 'Force Drain',
        'teacher': 'dark_hermit',
        'corruption_required': (50, 100),
        'description': 'Drain life force from enemies to restore your own.',
        'effect': 'life_drain_ability',
        'corruption_cost': 15
    }
}

def select_npc_for_biome(biome_type, existing_npcs):
    """
    Determine if an NPC should spawn in a biome and which type.
    
    Args:
        biome_type: The type of biome ('forest', 'desert', etc.)
        existing_npcs: List of NPCs already spawned on the map
        
    Returns:
        NPC type string or None if no NPC should spawn
    """
    # Limit total NPCs per map
    if len(existing_npcs) >= 5:
        return None
    
    # Get valid NPC types for this biome
    valid_types = []
    for npc_type, data in NPC_TYPES.items():
        if biome_type in data['biomes']:
            valid_types.append((npc_type, data['spawn_chance']))
    
    if not valid_types:
        return None
    
    # Roll for each valid type
    for npc_type, chance in valid_types:
        if random.random() < chance:
            return npc_type
    
    return None

def get_npc_dialogue(npc_type, player_corruption, interaction_type='greeting'):
    """
    Get appropriate dialogue for an NPC based on type and player corruption.
    
    Args:
        npc_type: Type of NPC
        player_corruption: Player's corruption level (0-100)
        interaction_type: Type of interaction (greeting, teaching, etc.)
        
    Returns:
        Dialogue string
    """
    # Determine alignment for corruption-specific dialogue
    if player_corruption <= 35:
        alignment = 'light'
    elif player_corruption <= 65:
        alignment = 'balanced'
    else:
        alignment = 'dark'
    
    # Select dialogue set
    dialogue_sets = {
        'survivor_camp': SURVIVOR_DIALOGUES,
        'hermit_jedi': HERMIT_JEDI_DIALOGUES,
        'fallen_jedi': FALLEN_JEDI_DIALOGUES,
        'dark_hermit': DARK_HERMIT_DIALOGUES
    }
    
    dialogues = dialogue_sets.get(npc_type, {})
    
    # Get appropriate dialogue
    if interaction_type == 'greeting':
        return random.choice(dialogues.get('greeting', ['...']))
    
    # Get corruption-specific response
    if alignment == 'light':
        key = f'{alignment}_response' if npc_type == 'survivor_camp' else f'{alignment}_path'
        if 'hermit' in npc_type and npc_type == 'hermit_jedi':
            key = f'{alignment}_path'
        elif npc_type == 'fallen_jedi':
            key = f'{alignment}_rejection'
        elif npc_type == 'dark_hermit':
            key = f'{alignment}_hostility'
    elif alignment == 'balanced':
        if npc_type == 'hermit_jedi':
            key = 'balanced_path'
        elif npc_type == 'fallen_jedi':
            key = 'balanced_interest'
        elif npc_type == 'dark_hermit':
            key = 'balanced_curiosity'
        else:
            key = 'dark_response'
    else:  # dark
        if npc_type == 'hermit_jedi':
            key = 'dark_warning'
        elif npc_type == 'fallen_jedi':
            key = 'dark_kinship'
        elif npc_type == 'dark_hermit':
            key = 'dark_welcome'
        else:
            key = 'dark_response'
    
    return random.choice(dialogues.get(key, ['...']))

def get_available_training(npc_type, player_corruption):
    """
    Get training offers available from this NPC type based on player corruption.
    
    Args:
        npc_type: Type of NPC
        player_corruption: Player's corruption level (0-100)
        
    Returns:
        List of available training offers
    """
    available = []
    
    for training_id, training_data in TRAINING_OFFERS.items():
        # Check if this NPC can teach this
        if training_data['teacher'] != npc_type:
            continue
        
        # Check corruption requirements
        min_corrupt, max_corrupt = training_data['corruption_required']
        if min_corrupt <= player_corruption <= max_corrupt:
            available.append((training_id, training_data))
    
    return available

def get_moral_choice(npc_type, player_corruption):
    """
    Get a moral choice appropriate for this NPC and player state.
    
    Args:
        npc_type: Type of NPC
        player_corruption: Player's corruption level (0-100)
        
    Returns:
        Moral choice dictionary or None
    """
    # Survivor camps offer specific moral choices
    if npc_type == 'survivor_camp':
        choices = ['imperial_scouts', 'wounded_civilian', 'stolen_supplies', 'information_torture']
        choice_id = random.choice(choices)
        return choice_id, MORAL_CHOICES[choice_id]
    
    # Fallen Jedi and Dark Hermits can offer artifact temptations
    if npc_type in ['fallen_jedi', 'dark_hermit']:
        if random.random() < 0.3:  # 30% chance
            return 'artifact_choice', MORAL_CHOICES['artifact_choice']
    
    return None, None

def create_npc_entity(npc_type, x, y):
    """
    Create an NPC entity dictionary for placement on the map.
    
    Args:
        npc_type: Type of NPC to create
        x, y: Coordinates for placement
        
    Returns:
        NPC entity dictionary
    """
    data = NPC_TYPES[npc_type]
    
    return {
        'type': npc_type,
        'x': x,
        'y': y,
        'symbol': data['symbol'],
        'color': data['color'],
        'name': data['name'],
        'description': data['description'],
        'interacted': False,  # Track if player has talked to this NPC
        'quest_given': False,  # Track if this NPC gave a quest/choice
    }
