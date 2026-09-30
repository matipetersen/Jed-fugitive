"""
Rituals and Ceremonies system for Dark Meridian.
Handles lightsaber attunement, Force rituals, burial ceremonies, and meditation rites.
"""
import random

# Lightsaber crystal attunement rituals
CRYSTAL_ATTUNEMENT_RITUALS = {
    'light_attunement': {
        'name': 'Crystal Purification Rite',
        'corruption_required': (0, 40),
        'duration': 'Takes several hours of deep meditation',
        'description': [
            "You sit in meditation, your kyber crystal resting in your palm.",
            "Reaching into the Force, you pour your Light side energy into the crystal.",
            "Memories of your Jedi training surface - lessons of peace, compassion, and selflessness.",
            "The crystal resonates with your essence, glowing with a pure blue light.",
            "When you open your eyes, the crystal hums with renewed clarity.",
        ],
        'effects': {
            'corruption_change': -15,
            'force_boost': 10,
            'message': 'Your lightsaber feels more attuned to the Light side of the Force.'
        },
        'requirements': 'Requires a kyber crystal and time for meditation.'
    },
    'balanced_attunement': {
        'name': 'Crystal Harmony Meditation',
        'corruption_required': (30, 70),
        'duration': 'Requires deep concentration and balance',
        'description': [
            "You hold the crystal, seeking neither light nor dark, but equilibrium.",
            "The Force flows through you - both the calm and the storm.",
            "You accept all aspects of yourself: compassion and anger, peace and passion.",
            "The crystal shifts between colors, settling on a unique hue that is purely yours.",
            "Balance achieved. The crystal reflects your gray path.",
        ],
        'effects': {
            'corruption_change': 0,  # Maintains balance
            'hybrid_boost': 15,
            'message': 'Your crystal now channels both light and dark in perfect balance.'
        },
        'requirements': 'Requires maintaining balance between light and dark.'
    },
    'dark_bleeding': {
        'name': 'Crystal Bleeding Ritual',
        'corruption_required': (60, 100),
        'duration': 'A painful process fueled by dark emotions',
        'description': [
            "You grip the crystal tightly, channeling your rage and pain into it.",
            "The Sith way: bend the kyber to your will through the dark side.",
            "You recall every loss, every betrayal. The crystal resists, but you are stronger.",
            "Cracks of crimson spread through the once-pure crystal as it bleeds.",
            "When finished, the crystal glows red - a testament to your dark power.",
        ],
        'effects': {
            'corruption_change': 20,
            'attack_boost': 15,
            'message': 'Your lightsaber now burns with the crimson of the dark side.'
        },
        'requirements': 'Requires embracing dark emotions and Sith techniques.'
    },
    'crystal_healing': {
        'name': 'Crystal Redemption Rite',
        'corruption_required': (40, 80),
        'duration': 'A lengthy process requiring genuine remorse',
        'description': [
            "You hold your corrupted crystal, feeling its pain - and your own.",
            "To heal it, you must heal yourself. To purify it, you must seek redemption.",
            "You meditate on your dark deeds, accepting responsibility without self-hatred.",
            "Slowly, painfully, the crimson fades. The crystal returns to its natural state.",
            "It is not the same as before, but neither are you. Both are redeemed.",
        ],
        'effects': {
            'corruption_change': -25,
            'force_regen_boost': 20,
            'message': 'Your crystal is healed. The darkness recedes. Redemption is possible.'
        },
        'requirements': 'Requires a bled crystal and genuine desire for redemption.'
    }
}

# Jedi meditation rites (Light side ceremonies)
JEDI_RITES = {
    'temple_meditation': {
        'name': 'Temple Meditation Ritual',
        'corruption_required': (0, 50),
        'location_required': 'meditation_shrine',
        'description': [
            "You kneel at the ancient shrine, feeling the Force converge here.",
            "The Jedi of old meditated in places like this, seeking guidance.",
            "You empty your mind of fear and anger, focusing on peace and serenity.",
            "The Force flows through you, cleansing, healing, restoring.",
            "You rise refreshed, your connection to the Light strengthened.",
        ],
        'effects': {
            'corruption_change': -10,
            'hp_restore': 50,
            'force_restore': 100,
            'message': 'The shrine\'s energy rejuvenates body and spirit.'
        }
    },
    'jedi_code_reaffirmation': {
        'name': 'Recitation of the Jedi Code',
        'corruption_required': (0, 40),
        'description': [
            "You speak the words your master taught you:",
            "'There is no emotion, there is peace.'",
            "'There is no ignorance, there is knowledge.'",
            "'There is no passion, there is serenity.'",
            "'There is no chaos, there is harmony.'",
            "'There is no death, there is the Force.'",
            "The Code grounds you, reminding you who you are.",
        ],
        'effects': {
            'corruption_change': -8,
            'resolve_boost': 10,
            'message': 'The Jedi Code strengthens your resolve against the dark side.'
        }
    },
    'force_cleansing': {
        'name': 'Force Cleansing Meditation',
        'corruption_required': (20, 60),
        'description': [
            "You sit in stillness, examining the darkness that has crept into your heart.",
            "Without judgment, you acknowledge each dark thought, each temptation.",
            "Then, gently, you release them into the Force.",
            "Like water washing away dirt, the Force cleanses your spirit.",
            "You emerge lighter, though the battle is never truly won.",
        ],
        'effects': {
            'corruption_change': -12,
            'clarity_boost': 15,
            'message': 'You feel clearer, more centered. The dark side\'s hold weakens.'
        }
    }
}

# Sith rituals (Dark side ceremonies)
SITH_RITES = {
    'dark_meditation': {
        'name': 'Dark Side Meditation',
        'corruption_required': (50, 100),
        'location_required': 'tomb',
        'description': [
            "You sit within the Sith tomb, letting its dark energy wash over you.",
            "You do not resist - you embrace it, draw it in, make it yours.",
            "Your anger, your hatred, your ambition - these are your power.",
            "The ancient Sith would approve. You are becoming what you were meant to be.",
            "You rise, the dark side flowing through you like never before.",
        ],
        'effects': {
            'corruption_change': 15,
            'force_boost': 30,
            'attack_boost': 20,
            'message': 'Dark power surges through you. You feel invincible.'
        }
    },
    'sith_code_proclamation': {
        'name': 'Proclamation of the Sith Code',
        'corruption_required': (60, 100),
        'description': [
            "You speak the words of the ancient Sith:",
            "'Peace is a lie, there is only passion.'",
            "'Through passion, I gain strength.'",
            "'Through strength, I gain power.'",
            "'Through power, I gain victory.'",
            "'Through victory, my chains are broken.'",
            "'The Force shall free me.'",
            "The Code resonates with your dark heart.",
        ],
        'effects': {
            'corruption_change': 12,
            'willpower_boost': 15,
            'message': 'The Sith Code fills you with dark conviction.'
        }
    },
    'ritual_of_consumption': {
        'name': 'Ritual of Dark Consumption',
        'corruption_required': (70, 100),
        'location_required': 'tomb',
        'description': [
            "You perform the ancient Sith ritual, drawing on the ambient dark energy.",
            "Life force from the tomb's victims, pain from centuries past - all of it flows into you.",
            "The Jedi would call this an abomination. You call it survival.",
            "Your body repairs itself as you consume the lingering essence of the dead.",
            "This is the Sith way - take what you need, without mercy or hesitation.",
        ],
        'effects': {
            'corruption_change': 18,
            'hp_restore': 100,
            'force_restore': 50,
            'max_hp_boost': 10,
            'message': 'You drain the tomb\'s dark energy. Death has made you stronger.'
        }
    },
    'artifact_consecration': {
        'name': 'Dark Artifact Consecration',
        'corruption_required': (65, 100),
        'description': [
            "You hold a Sith artifact, preparing to bind it to your will.",
            "Through the dark side, you channel your essence into the object.",
            "It will serve you, amplify your power, become an extension of yourself.",
            "The ritual is complete. The artifact is yours, body and soul.",
        ],
        'effects': {
            'corruption_change': 10,
            'artifact_power': 25,
            'message': 'The artifact is bound to you, its dark power at your command.'
        }
    }
}

# Burial and memorial ceremonies
BURIAL_CEREMONIES = {
    'jedi_funeral': {
        'name': 'Jedi Funeral Rite',
        'corruption_required': (0, 50),
        'description': [
            "You arrange the fallen's body with reverence and care.",
            "Speaking the traditional words, you commit them to the Force:",
            "'In life, you served the Light. In death, you become one with the Force.'",
            "'May you find peace in the cosmic Force, free from suffering.'",
            "You mark the grave with stones, a small memorial in this forgotten place.",
            "Even in darkness, some traditions must be honored.",
        ],
        'effects': {
            'corruption_change': -5,
            'respect_gained': True,
            'message': 'Honoring the dead brings you peace. The Force approves.'
        }
    },
    'enemy_burial': {
        'name': 'Enemy Burial',
        'corruption_required': (20, 80),
        'description': [
            "You defeated this foe, but they deserve better than to rot in the wilderness.",
            "Whether out of respect or merely tradition, you dig a simple grave.",
            "'You were my enemy, but you were brave. The Force will judge you now.'",
            "You cover the body and move on. Perhaps this is what separates you from them.",
        ],
        'effects': {
            'corruption_change': -3,
            'karma_boost': 5,
            'message': 'Even enemies deserve dignity in death. You honor that.'
        }
    },
    'desecration': {
        'name': 'Dark Desecration',
        'corruption_required': (70, 100),
        'description': [
            "The fallen enemy holds power even in death. You will take it.",
            "Using dark side techniques, you drain the remaining life essence.",
            "The body withers as you consume its Force signature.",
            "This is the Sith way - victory through domination, even over death.",
            "You leave the corpse where it fell. Let it serve as a warning.",
        ],
        'effects': {
            'corruption_change': 15,
            'force_restore': 30,
            'dark_essence': 10,
            'message': 'You desecrate the corpse, consuming its essence. Power at any cost.'
        }
    },
    'mass_grave': {
        'name': 'Memorial for the Fallen',
        'corruption_required': (0, 60),
        'description': [
            "So many dead. The Great Purge claimed countless lives.",
            "You cannot bury them all, but you can remember them.",
            "Creating a simple cairn, you speak their names to the Force.",
            "Masters, Padawans, even civilians caught in the Sith War.",
            "'May the Force remember what the galaxy has forgotten.'",
        ],
        'effects': {
            'corruption_change': -8,
            'remembrance_bonus': True,
            'message': 'You honor the memory of the fallen. Their sacrifice will not be forgotten.'
        }
    }
}

# Combat stance/form rituals
FORM_MEDITATION_RITUALS = {
    'form_i_meditation': {
        'name': 'Form I: Shii-Cho Kata',
        'corruption_required': (0, 100),  # Available to all
        'duration': 'Practice the ancient forms',
        'description': [
            "You practice the fundamental strikes of Form I - the Way of the Sarlacc.",
            "Wide sweeping motions, basic but effective against multiple opponents.",
            "This is where all Jedi begin. The foundation of lightsaber combat.",
            "Through repetition, the form becomes part of you.",
        ],
        'effects': {
            'form_learned': 'Shii-Cho',
            'message': 'Form I: Shii-Cho mastered. The foundation of all forms.'
        }
    },
    'form_iii_meditation': {
        'name': 'Form III: Soresu Meditation',
        'corruption_required': (0, 50),
        'level_required': 3,
        'duration': 'Master defensive techniques',
        'description': [
            "You focus on defense, letting attacks flow past you harmlessly.",
            "Form III - the Way of the Mynock. Patient, immovable, unbreakable.",
            "You visualize deflecting countless blaster bolts, outlasting any foe.",
            "Like Obi-Wan Kenobi, you become a fortress of the Light.",
        ],
        'effects': {
            'form_learned': 'Soresu',
            'defense_bonus': 5,
            'message': 'Form III: Soresu learned. You are now a master of defense.'
        }
    },
    'form_v_meditation': {
        'name': 'Form V: Shien/Djem So Practice',
        'corruption_required': (30, 80),
        'level_required': 5,
        'duration': 'Channel power through aggression',
        'description': [
            "You practice powerful strikes, each one devastating and direct.",
            "Form V - turning defense into overwhelming offense.",
            "Like the ancient Jedi battlemaster Kao Cen Darach, you dominate the battlefield with raw strength.",
            "Power, aggression, victory. The form of champions.",
        ],
        'effects': {
            'form_learned': 'Shien',
            'attack_bonus': 5,
            'message': 'Form V: Shien mastered. Your strikes are now devastating.'
        }
    },
    'form_vii_meditation': {
        'name': 'Form VII: Juyo Ritual',
        'corruption_required': (60, 100),
        'level_required': 8,
        'duration': 'Embrace controlled chaos',
        'description': [
            "You move without thought, channeling raw emotion into combat.",
            "Form VII - the Ferocity Form. Unpredictable, overwhelming, dangerous.",
            "Only the strongest can use this without falling to darkness.",
            "You dance on the edge between control and chaos.",
        ],
        'effects': {
            'form_learned': 'Juyo',
            'attack_bonus': 8,
            'corruption_change': 5,
            'message': 'Form VII: Juyo learned. Beware - this form is perilous.'
        }
    },
    'stance_change_ritual': {
        'name': 'Combat Stance Meditation',
        'corruption_required': (0, 100),
        'duration': 'Attune to a different fighting style',
        'description': [
            "You meditate on your combat style, seeking to adapt.",
            "The Force guides your movements, showing you new techniques.",
            "Each stance has strengths - you must choose wisely.",
            "Your form is part of who you are as a warrior.",
        ],
        'effects': {
            'stance_selection': True,
            'message': 'Meditation complete. You may now switch combat stances.'
        }
    }
}

# Special ceremonies for milestones
MILESTONE_CEREMONIES = {
    'knighthood': {
        'name': 'Self-Knighting Ceremony',
        'corruption_required': (0, 40),
        'level_required': 10,
        'description': [
            "There is no Council to knight you. No master to speak the ancient words.",
            "But you have proven yourself worthy through trial and survival.",
            "You draw your lightsaber and speak the oath yourself:",
            "'I am a Jedi, like my masters before me.'",
            "'I will protect those who cannot protect themselves.'",
            "'I will seek knowledge and peace, not glory or power.'",
            "The Force itself bears witness. You are a Jedi Knight.",
        ],
        'effects': {
            'corruption_change': -10,
            'title_gained': 'Jedi Knight',
            'skill_boost': 20,
            'message': 'You have knighted yourself. May you prove worthy of the title.'
        }
    },
    'dark_ascension': {
        'name': 'Sith Ascension Rite',
        'corruption_required': (70, 100),
        'level_required': 10,
        'description': [
            "You have walked the dark path long enough. It is time to claim your title.",
            "Kneeling before an ancient Sith statue, you proclaim your new identity:",
            "'I am no longer a Jedi. I am Sith.'",
            "'Through the dark side, I am free. Through power, I am victorious.'",
            "You rise, choosing your Darth name. The transformation is complete.",
        ],
        'effects': {
            'corruption_change': 20,
            'title_gained': 'Sith Lord',
            'dark_powers_unlocked': True,
            'message': 'You have embraced the Sith legacy. The dark side flows through you.'
        }
    },
    'gray_oath': {
        'name': 'Gray Jedi Vow',
        'corruption_required': (35, 65),
        'level_required': 10,
        'description': [
            "You walk between light and dark, beholden to neither.",
            "The Jedi would call you fallen. The Sith would call you weak.",
            "You reject both labels. You are something different.",
            "'I will use both light and dark, but be ruled by neither.'",
            "'I will seek balance, not extremes. Wisdom, not dogma.'",
            "The Gray Jedi way is lonely, but it is yours.",
        ],
        'effects': {
            'corruption_change': 0,
            'title_gained': 'Gray Jedi',
            'hybrid_mastery': True,
            'message': 'You forge your own path between light and dark.'
        }
    },
    'first_tomb': {
        'name': 'Tomb Survivor\'s Rite',
        'corruption_required': (0, 100),
        'tombs_completed': 1,
        'description': [
            "You have emerged from a Sith tomb alive. Few can claim that.",
            "Taking a moment to center yourself, you reflect on what you faced.",
            "The dark side tested you. You survived. But at what cost?",
            "You mark this milestone, knowing more tombs await.",
        ],
        'effects': {
            'title_gained': 'Tomb Delver',
            'xp_bonus': 500,
            'message': 'You survived your first Sith tomb. Many more await.'
        }
    }
}

def get_available_rituals(corruption_level, location=None, level=1, tombs_completed=0):
    """
    Get list of rituals available to the player based on their state.
    
    Args:
        corruption_level: Player's corruption (0-100)
        location: Current location type (optional)
        level: Player's level (for milestone rituals)
        tombs_completed: Number of tombs completed (for milestone rituals)
        
    Returns:
        List of (ritual_category, ritual_id, ritual_data) tuples
    """
    # Validate corruption level
    if corruption_level is None:
        corruption_level = 50  # Default to neutral
    
    # Ensure corruption level is within valid range
    corruption_level = max(0, min(100, corruption_level))
    
    available = []
    
    # Check crystal attunement rituals
    for ritual_id, ritual_data in CRYSTAL_ATTUNEMENT_RITUALS.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            available.append(('crystal', ritual_id, ritual_data))
    
    # Check Jedi rites
    for ritual_id, ritual_data in JEDI_RITES.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            # Check location requirement if present
            if 'location_required' in ritual_data:
                if location == ritual_data['location_required']:
                    available.append(('jedi', ritual_id, ritual_data))
            else:
                available.append(('jedi', ritual_id, ritual_data))
    
    # Check Sith rites
    for ritual_id, ritual_data in SITH_RITES.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            # Check location requirement if present
            if 'location_required' in ritual_data:
                if location == ritual_data['location_required']:
                    available.append(('sith', ritual_id, ritual_data))
            else:
                available.append(('sith', ritual_id, ritual_data))
    
    # Check burial ceremonies (always available)
    for ritual_id, ritual_data in BURIAL_CEREMONIES.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            available.append(('burial', ritual_id, ritual_data))
    
    # Check milestone ceremonies
    for ritual_id, ritual_data in MILESTONE_CEREMONIES.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            # Check additional requirements
            can_perform = True
            if 'level_required' in ritual_data and level < ritual_data['level_required']:
                can_perform = False
            if 'tombs_completed' in ritual_data and tombs_completed < ritual_data['tombs_completed']:
                can_perform = False
            
            if can_perform:
                available.append(('milestone', ritual_id, ritual_data))
    
    # Check form meditation rituals
    for ritual_id, ritual_data in FORM_MEDITATION_RITUALS.items():
        min_corrupt, max_corrupt = ritual_data['corruption_required']
        if min_corrupt <= corruption_level <= max_corrupt:
            # Check level requirement if present
            if 'level_required' in ritual_data:
                if level >= ritual_data['level_required']:
                    available.append(('form', ritual_id, ritual_data))
            else:
                available.append(('form', ritual_id, ritual_data))
    
    return available

def perform_ritual(ritual_category, ritual_id, player, game_state):
    """
    Perform a ritual and apply its effects to the player.
    
    Args:
        ritual_category: Category of ritual ('crystal', 'jedi', 'sith', 'burial', 'milestone')
        ritual_id: ID of the specific ritual
        player: Player object
        game_state: Game state object for applying effects
        
    Returns:
        Success message and effects applied
    """
    # Get ritual data
    ritual_sets = {
        'crystal': CRYSTAL_ATTUNEMENT_RITUALS,
        'jedi': JEDI_RITES,
        'sith': SITH_RITES,
        'burial': BURIAL_CEREMONIES,
        'milestone': MILESTONE_CEREMONIES,
        'form': FORM_MEDITATION_RITUALS
    }
    
    ritual_data = ritual_sets[ritual_category].get(ritual_id)
    if not ritual_data:
        return "Ritual not found.", {}
    
    # Return ritual description and effects
    return ritual_data['description'], ritual_data['effects']

def format_ritual_display(ritual_category, ritual_id, ritual_data):
    """
    Format ritual information for display to player.
    
    Args:
        ritual_category: Category of ritual
        ritual_id: Ritual ID
        ritual_data: Ritual data dictionary
        
    Returns:
        List of formatted text lines
    """
    lines = []
    lines.append(f"═══ {ritual_data['name']} ═══")
    lines.append("")
    
    if 'duration' in ritual_data:
        lines.append(f"Duration: {ritual_data['duration']}")
        lines.append("")
    
    if 'requirements' in ritual_data:
        lines.append(f"Requirements: {ritual_data['requirements']}")
        lines.append("")
    
    # Show corruption requirement range
    min_c, max_c = ritual_data['corruption_required']
    if min_c == 0 and max_c <= 40:
        alignment = "Light Side"
    elif min_c >= 60:
        alignment = "Dark Side"
    else:
        alignment = "Balanced"
    lines.append(f"Alignment: {alignment} (Corruption {min_c}-{max_c})")
    lines.append("")
    
    # Show effects preview
    effects = ritual_data['effects']
    lines.append("Effects:")
    if 'corruption_change' in effects and effects['corruption_change'] != 0:
        change = effects['corruption_change']
        direction = "darker" if change > 0 else "lighter"
        lines.append(f"  • Shifts your alignment {direction}")
    if 'hp_restore' in effects:
        lines.append(f"  • Restores {effects['hp_restore']} HP")
    if 'force_restore' in effects:
        lines.append(f"  • Restores {effects['force_restore']} Force points")
    if 'attack_boost' in effects:
        lines.append(f"  • Increases combat power")
    if 'defense_boost' in effects:
        lines.append(f"  • Enhances defense")
    if 'title_gained' in effects:
        lines.append(f"  • Grants title: {effects['title_gained']}")
    
    return lines
