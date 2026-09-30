"""
NPC Encounter system for Dark Meridian.
Handles survivor camps, hermit Jedi/Sith, moral choices, and dialogue.
"""
import random

# NPC types and their properties
NPC_TYPES = {
    'survivor_camp': {
        'symbol': '@',
        'color': 'yellow',
        'name': 'Survivor Camp',
        'description': 'A small group of refugees from the Jedi Purge.',
        'spawn_chance': 0.15,  # 15% chance per biome
        'biomes': ['forest', 'plains', 'river', 'crash_site'],
    },
    'hermit_jedi': {
        'symbol': 'Y',  # Changed from J to avoid conflict with Jedi Hunter enemy
        'color': 'cyan',
        'name': 'Hermit Jedi',
        'description': 'A Jedi Master in hiding.',
        'spawn_chance': 0.10,  # 10% chance per biome
        'biomes': ['forest', 'mountain_pass', 'rocky'],
    },
    'fallen_jedi': {
        'symbol': 'f',
        'color': 'magenta',
        'name': 'Fallen Jedi',
        'description': 'A Jedi who turned to the dark side.',
        'spawn_chance': 0.08,  # 8% chance per biome
        'biomes': ['desert', 'rocky', 'tomb'],
    },
    'archivist': {
        'symbol': 'a',
        'color': 'cyan',
        'name': 'Wandering Archivist',
        'description': 'A scholar who has memorised the speech of dying civilisations.',
        'spawn_chance': 0.60,
        'biomes': ['forest', 'plains', 'river', 'rocky', 'mountain_pass'],
    },
    'rakatan_tinker': {
        'symbol': 'R',
        'color': 'yellow',
        'name': 'Rakatan Tinker',
        'description': 'A salvager who reads Infinite Empire machine-script and builds with it.',
        'spawn_chance': 0.50,
        'biomes': ['desert', 'rocky', 'plains'],
    },
    'dark_hermit': {
        'symbol': 'N',  # Changed from D to avoid conflict with Dewback enemy
        'color': 'red',
        'name': 'Dark Side Hermit',
        'description': 'A Sith cultist studying forbidden knowledge.',
        'spawn_chance': 0.12,  # 12% chance per biome
        'biomes': ['tomb', 'desert', 'rocky'],
    },
}

# Expanded survivor camp dialogues and interactions
SURVIVOR_DIALOGUES = {
    'greeting': [
        "You there! Please, we mean no harm. Are you... are you a Jedi?",
        "By the Force, another survivor! We thought we were alone.",
        "Stay back! Wait... you're not with the Sith Empire, are you?",
        "Please help us. We've been running for weeks.",
        "We lost so many... Are you here to help or to finish what the Sith started?",
        "The galaxy is a cruel place now. Any friend is welcome.",
        "We saw your lightsaber. Does that mean hope, or more danger?"
    ],
    'light_response': [
        "Your presence brings us hope. Thank you for not abandoning us.",
        "A true Jedi! We knew some would survive the purge.",
        "The Force is still with us. Will you help protect our camp?",
        "You remind us of the old stories. Maybe the Jedi aren't all gone.",
        "We can sleep easier knowing someone like you is out there."
    ],
    'dark_response': [
        "Your eyes... they're different. What have you become?",
        "You carry darkness with you. Perhaps we should keep our distance.",
        "We've heard rumors of Jedi turning dark. Is it true?",
        "We fear you almost as much as the Sith. Please, just let us be.",
        "The children are afraid. Please don't hurt us."
    ],
    'trade_offer': [
        "We salvaged supplies from crashed ships. Perhaps we can trade?",
        "We don't have much, but we'd be grateful to share what we have.",
        "Take what you need. We owe you our lives.",
        "If you have medicine, we'll trade anything for it.",
        "Some of us were mechanics. Maybe we can fix something for you."
    ],
    'moral_choice_setup': [
        "The Sith scouts were here yesterday. They're looking for Force users.",
        "We have wounded. The Sith took our medical supplies.",
        "We're planning to flee deeper into the wilderness. It's dangerous.",
        "A child is missing. We think she wandered toward the ruins.",
        "Food is running low. Some want to steal from the next camp we find."
    ]
}

# Expanded Hermit Jedi dialogues (Light Side mentors)
HERMIT_JEDI_DIALOGUES = {
    'greeting': [
        "Peace, young one. I sensed your presence through the Force.",
        "Another survivor of the Purge. The Force guided you here.",
        "I've been waiting. The Force told me you would come.",
        "You carry the weight of many losses. Sit, rest, and let the Force ease your mind.",
        "The galaxy is darker now, but the light endures in those who remember."
    ],
    'light_path': [
        "I see the light still burns within you. Good. Hold onto it.",
        "The dark times test us all, but you resist temptation. Admirable.",
        "Your crystal glows pure. You walk the path of the Jedi.",
        "You have not let anger rule you. That is rare, and precious.",
        "The Force is strong with you, and so is your compassion."
    ],
    'balanced_path': [
        "You walk a dangerous line between light and dark.",
        "Balance is wise, but be cautious. Many who sought balance fell to darkness.",
        "You seek to understand both sides. A perilous, but perhaps necessary, path.",
        "The Living Force is not always light or dark. Sometimes, it is simply survival.",
        "I once thought balance was impossible. Now, I am not so sure."
    ],
    'dark_warning': [
        "I sense the darkness growing in you. Turn back before it's too late!",
        "The dark side clouds your judgment. You can still choose redemption.",
        "You're on the path that leads to suffering. I've seen it before.",
        "Anger is easy. Forgiveness is harder. But it is not too late.",
        "I have seen what the dark side does to good people. Please, do not follow that path."
    ],
    'teaching_offer': [
        "I can teach you an old technique, if you're willing to learn.",
        "The ancient Jedi knew secrets lost to the modern Order. I can share them.",
        "Meditation and patience - let me show you what I've learned.",
        "There is a cave nearby, strong in the Force. Meditate there, and you may find answers.",
        "If you listen, the Force will teach you more than any master."
    ],
    'philosophy': [
        "The Jedi Order fell because it became rigid. We must adapt to survive.",
        "Attachment led to our downfall, but complete detachment made us blind.",
        "The Force flows through all living things. Never forget that.",
        "Wisdom is not the same as knowledge. Sometimes, it is knowing when to let go.",
        "The galaxy is full of pain, but also hope. We must be both strong and kind."
    ]
}

# Fallen Jedi dialogues (temptation to dark side)
FALLEN_JEDI_DIALOGUES = {
    'greeting': [
        "Another Jedi? No... you're more than that. I can sense your potential.",
        "The Order abandoned us. The Sith hunt us. What choice did we have?",
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
        "Together we could be unstoppable. The Sith Empire would fear us.",
        "I see the hunger in your eyes. Good. Use it.",
    ],
    'temptation_offer': [
        "I know a Sith technique. Dark, yes, but powerful. Want to learn?",
        "There's a tomb nearby. The power inside could make you invincible.",
        "Join me. Together we can take what we deserve.",
    ],
    'warning': [
        "The Sith Assassins are coming. They'll find you eventually.",
        "The Sith Empire doesn't distinguish between light and dark Jedi. We're all targets.",
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
    'sith_scouts': {
        'setup': "Sith scouts are tracking this camp. We could ambush them, but...",
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
            'reward': 'sith_commlink'
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
        'setup': "We captured a Sith trooper. He knows where other survivors are hiding. He won't talk.",
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
        choices = ['sith_scouts', 'wounded_civilian', 'stolen_supplies', 'information_torture']
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


class NPC:
    """Individual NPC instance"""
    def __init__(self, npc_type, x, y):
        self.npc_type = npc_type
        self.x = x
        self.y = y
        self.data = NPC_TYPES[npc_type]
        self.name = self.data['name']
        self.description = self.data['description']
        self.symbol = self.data['symbol']
        self.interacted = False
        self.quest_given = False
        self.lessons = 0  # language lessons given so far (teachers only)
        self.teaches = self._pick_language()

    def _pick_language(self):
        if self.npc_type == 'rakatan_tinker':
            return 'rakatan'
        if self.npc_type == 'archivist':
            import hashlib
            h = int(hashlib.sha256(f"{self.x},{self.y}".encode()).hexdigest(), 16)
            return ('sith', 'tythonian', 'mando')[h % 3]
        return None

    def get_greeting(self):
        """Get initial greeting based on NPC type"""
        if self.npc_type == 'survivor_camp':
            return random.choice(SURVIVOR_DIALOGUES['greeting'])
        elif self.npc_type == 'hermit_jedi':
            return random.choice(HERMIT_JEDI_DIALOGUES['greeting'])
        elif self.npc_type == 'fallen_jedi':
            return random.choice(FALLEN_JEDI_DIALOGUES['greeting'])
        elif self.npc_type == 'dark_hermit':
            return random.choice(DARK_HERMIT_DIALOGUES['greeting'])
        elif self.npc_type == 'archivist':
            return "Ah, a reader! Few care for the old scripts any more. Sit, sit."
        elif self.npc_type == 'rakatan_tinker':
            return "Hah! You've got that look - salvage and questions. Show me what you've got."
        else:
            return "Hello, traveler."
    
    def get_available_interactions(self, player):
        """Get list of available interaction options"""
        options = []
        
        if self.npc_type == 'survivor_camp':
            options = ["Ask for supplies", "Share news", "Offer protection"]
            if not self.quest_given:
                options.append("Listen to their story")
        elif self.npc_type == 'hermit_jedi':
            options = ["Ask about the Force", "Request training"]
            if player.corruption < 50:  # Only available to light-side players
                options.append("Seek guidance")
        elif self.npc_type == 'fallen_jedi':
            options = ["Challenge their choices", "Ask about the dark side"]
            if player.corruption > 50:  # Only available to dark-side players
                options.append("Join their cause")
        elif self.npc_type == 'dark_hermit':
            options = ["Ask about Sith knowledge", "Inquire about artifacts"]
            if player.corruption > 30:
                options.append("Request dark training")
        elif self.npc_type in ('archivist', 'rakatan_tinker'):
            from jedi_fugitive.game import languages
            lname = languages.LANGUAGES[self.teaches]['name']
            options = [f"Ask to be taught {lname}", "Show them your inscriptions"]
            if self.npc_type == 'rakatan_tinker':
                options.append("Barter salvage for lessons")
                options.append("Ask what you could build")
        
        return options
    
    def handle_interaction(self, choice_index, player, action_type=None):
        """Handle player's interaction choice, with suspicion/faction logic."""
        options = self.get_available_interactions(player)
        if choice_index >= len(options):
            return "Invalid choice."
        chosen_option = options[choice_index]

        # Suspicion logic: suspicious actions near hostile factions or while disguised
        suspicious_actions = ["force", "sneak", "steal"]
        if action_type in suspicious_actions:
            # If disguised or faction is hostile, increase suspicion
            hostile_factions = getattr(player, 'faction_manager', None)
            rep = None
            if hostile_factions:
                # Assume NPC has a faction (for now, map by type)
                npc_faction = None
                if self.npc_type == 'survivor_camp':
                    npc_faction = 'Settlers'
                elif self.npc_type == 'hermit_jedi':
                    npc_faction = 'Republic'
                elif self.npc_type == 'fallen_jedi' or self.npc_type == 'dark_hermit':
                    npc_faction = 'Sith Empire'
                if npc_faction:
                    rep = hostile_factions.get_reputation(npc_faction)
            # If disguised or reputation is low, increase suspicion
            if player.disguise or (rep is not None and rep < 0):
                player.suspicion = min(100, player.suspicion + 25)
                if player.suspicion >= 100:
                    return "NPCs become alarmed! Your suspicious actions have triggered an alarm."
        # Faction logic: friendly factions may help
        if getattr(player, 'faction_manager', None):
            npc_faction = None
            if self.npc_type == 'survivor_camp':
                npc_faction = 'Settlers'
            elif self.npc_type == 'hermit_jedi':
                npc_faction = 'Republic'
            elif self.npc_type == 'fallen_jedi' or self.npc_type == 'dark_hermit':
                npc_faction = 'Sith Empire'
            if npc_faction:
                rep = player.faction_manager.get_reputation(npc_faction)
                if rep is not None and rep > 50:
                    return f"{self.name} recognizes your reputation and offers help!"

        if self.npc_type == 'survivor_camp':
            return self._handle_survivor_interaction(chosen_option, player)
        elif self.npc_type == 'hermit_jedi':
            return self._handle_hermit_jedi_interaction(chosen_option, player)
        elif self.npc_type == 'fallen_jedi':
            return self._handle_fallen_jedi_interaction(chosen_option, player)
        elif self.npc_type == 'dark_hermit':
            return self._handle_dark_hermit_interaction(chosen_option, player)
        elif self.npc_type in ('archivist', 'rakatan_tinker'):
            return self._handle_teacher_interaction(chosen_option, player)

    def _handle_teacher_interaction(self, option, player):
        """Language teachers: lessons, archive consultations, bartering, tech advice."""
        from jedi_fugitive.game import languages
        lang = self.teaches
        lname = languages.LANGUAGES[lang]['name']
        if option.startswith("Ask to be taught"):
            if self.lessons >= 2:
                return f"{self.name}: 'I have taught you all I can in one sitting. Read the stones - practice will do the rest.'"
            self.lessons += 1
            got = languages.grant_words(player, lang, 4)
            if not got:
                return f"{self.name}: 'You already know everything I could teach you of {lname}.'"
            words = ", ".join(f"{languages.native_word(lang, w)}='{w}'" for w in got)
            return f"{self.name} teaches you {lname}: {words}."
        if option.startswith("Show them"):
            got = languages.consult_archive(player, lang, 3)
            if not got:
                return f"{self.name} studies your notes but finds nothing new to explain in {lname}."
            words = ", ".join(f"{languages.native_word(lang, w)}='{w}'" for w in got)
            return f"{self.name} reads your inscriptions aloud and explains: {words}."
        if option.startswith("Barter"):
            from jedi_fugitive.items.crafting import check_materials, consume_materials
            price = {"Scrap Metal": 1, "Fused Wire": 1}
            if not check_materials(getattr(player, "inventory", []) or [], price):
                return f"{self.name}: 'Bring me a Scrap Metal and a Fused Wire and we'll talk.'"
            player.inventory = consume_materials(player.inventory, price)
            got = languages.grant_words(player, lang, 3)
            if not got:
                return f"{self.name} keeps the salvage anyway: 'Nothing left to teach you, friend.'"
            words = ", ".join(f"{languages.native_word(lang, w)}='{w}'" for w in got)
            return f"{self.name} trades lessons for salvage: {words}."
        if option.startswith("Ask what you could build"):
            from jedi_fugitive.game import tech
            for did, name, t, desc, status in tech.device_rows(player):
                if status != "MAX":
                    return f"{self.name}: 'Next, the {name}. {status}. Press I to build.'"
            return f"{self.name}: 'You have built everything I know how to build.'"
        return f"{self.name} nods."
    
    def _handle_survivor_interaction(self, option, player):
        """Handle survivor camp interactions"""
        if "supplies" in option:
            # Give random supply
            supplies = ["medpack", "ration", "power_cell"]
            item = random.choice(supplies)
            player.inventory.append({'name': item, 'id': item})
            return f"The survivors share a {item} with you."
        elif "news" in option:
            return "You share news of the outside world. The survivors look both hopeful and afraid."
        elif "protection" in option:
            return "You offer to protect them. They are grateful for your kindness."
        elif "story" in option:
            self.quest_given = True
            return "They tell you of Sith patrols nearby. You gain insight into the local situation."
        return "The survivors nod respectfully."
    
    def _handle_hermit_jedi_interaction(self, option, player):
        """Handle hermit Jedi interactions"""  
        if "Force" in option:
            player.force_energy = min(player.max_force_energy, player.force_energy + 20)
            return "The hermit shares wisdom about the Force. You feel refreshed."
        elif "training" in option:
            player.gain_xp(50)
            return "The hermit teaches you advanced techniques. You gain experience."
        elif "guidance" in option:
            if player.corruption > 0:
                player.corruption = max(0, player.corruption - 5)
                return "The hermit's wisdom helps center you in the light."
            return "The hermit nods approvingly at your dedication to the light side."
        return "The hermit Jedi watches you with wise eyes."
    
    def _handle_fallen_jedi_interaction(self, option, player):
        """Handle fallen Jedi interactions"""
        if "Challenge" in option:
            return "The fallen Jedi sneers at your righteousness but respects your conviction."
        elif "dark side" in option:
            player.corruption = min(100, player.corruption + 3)
            return "The fallen Jedi speaks of power through passion. You feel the dark side's allure."
        elif "cause" in option:
            player.corruption = min(100, player.corruption + 10)
            return "The fallen Jedi welcomes you to the path of power. Darkness flows through you."
        return "The fallen Jedi watches you with calculating eyes."
    
    def _handle_dark_hermit_interaction(self, option, player):
        """Handle dark hermit interactions"""
        if "knowledge" in option:
            return "The dark hermit whispers forbidden secrets. Knowledge is power."
        elif "artifacts" in option:
            return "The hermit speaks of ancient Sith artifacts hidden in the tombs."
        elif "training" in option:
            player.corruption = min(100, player.corruption + 5)
            return "The hermit teaches you to embrace your anger. Power flows through hatred."
        return "The dark hermit's eyes gleam with malevolent knowledge."


class NPCEncounters:
    """Manager for NPC encounter system"""
    def __init__(self):
        self.active_npcs = {}  # (x, y) -> NPC instance
        
    def spawn_npc(self, npc_type, x, y):
        """Spawn an NPC at the specified location"""
        npc = NPC(npc_type, x, y)
        self.active_npcs[(x, y)] = npc
        return npc
    
    def get_npc_at_position(self, x, y):
        """Get NPC at specified position"""
        return self.active_npcs.get((x, y))
    
    def remove_npc(self, x, y):
        """Remove NPC from specified position"""
        if (x, y) in self.active_npcs:
            del self.active_npcs[(x, y)]


def select_npc_for_biome(biome_type):
    """Select appropriate NPC type for the given biome"""
    suitable_npcs = []
    for npc_type, data in NPC_TYPES.items():
        if biome_type in data['biomes']:
            suitable_npcs.extend([npc_type] * int(data['spawn_chance'] * 100))
    
    if suitable_npcs:
        return random.choice(suitable_npcs)
    return None
