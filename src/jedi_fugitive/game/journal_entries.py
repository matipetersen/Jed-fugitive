"""
Enhanced Journal Entry System - Immersive, lore-rich travel log entries.

This module provides contextual, Star Wars themed journal entries that respond to:
- Player alignment (Light/Dark/Balanced)
- Current biome/location
- Event type (combat, discovery, milestone)
- Corruption level and stress state
"""

import random

# ═══════════════════════════════════════════════════════════════════════════
# COMBAT JOURNAL ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def get_combat_victory_entry(enemy_name, player_alignment, biome="wasteland", weapon_type=None):
    """Generate immersive combat victory journal entry."""
    
    # Light Side entries - defensive, reluctant combat
    light_entries = {
        'lightsaber': [
            f"Defended myself against {enemy_name}. My blade found its mark, but I take no joy in this necessity.",
            f"The {enemy_name} left me no choice. My lightsaber hummed in defense of life, not in anger.",
            f"Struck down {enemy_name} in the {biome}. The Force guided my blade to end this threat swiftly.",
            f"Another life extinguished. {enemy_name} fell to my saber. I pray this violence ends soon.",
        ],
        'blaster': [
            f"Fired on {enemy_name} only as a last resort. Precision over brutality - one clean shot.",
            f"My blaster spoke when words could not. {enemy_name} dropped in the {biome}. I feel the weight of it.",
            f"Shot {enemy_name} in self-defense. Each discharge dims my spirit a little more.",
        ],
        'force': [
            f"Used the Force against {enemy_name}. A defensive push, nothing more. The Light Side remains strong.",
            f"The Living Force flowed through me, neutralizing {enemy_name} without hatred.",
            f"Channeled the Force to overcome {enemy_name}. Discipline over anger. Peace over violence.",
        ],
        'melee': [
            f"Close quarters with {enemy_name} in the {biome}. Fought with restraint, ended it cleanly.",
            f"Hand-to-hand with {enemy_name}. Survival, not vengeance, guided my strikes.",
        ]
    }
    
    # Dark Side entries - aggressive, reveling in power
    dark_entries = {
        'lightsaber': [
            f"Cut down {enemy_name} with ruthless efficiency. Their fear fed my power!",
            f"My blade sang through {enemy_name}'s defenses. The thrill of combat courses through me!",
            f"Slaughtered {enemy_name} in the {biome}. Each kill makes me stronger. The dark side rewards strength!",
            f"Destroyed {enemy_name} with barely an effort. They were insects before my power!",
            f"{enemy_name} fell screaming. The sound of their defeat is... satisfying.",
        ],
        'blaster': [
            f"Gunned down {enemy_name} without hesitation. No mercy for the weak!",
            f"Blasted {enemy_name} to oblivion. The smoking corpse serves as warning to others.",
            f"One precise shot through {enemy_name}'s center mass. Efficiency is its own art form.",
        ],
        'force': [
            f"Crushed {enemy_name} with raw dark side power! The Force bends to my will!",
            f"Unleashed Force lightning on {enemy_name}. Their agony was... educational.",
            f"Dominated {enemy_name} completely. They never stood a chance against true power!",
        ],
        'melee': [
            f"Beat {enemy_name} into submission. Felt every bone break. This is strength!",
            f"Tore through {enemy_name} with savage fury. The dark side flows freely in combat!",
        ]
    }
    
    # Balanced/Neutral entries - practical, tactical
    balanced_entries = {
        'lightsaber': [
            f"Engaged {enemy_name} in combat. Swift strikes ended the threat efficiently.",
            f"Dueled {enemy_name} in the {biome}. Victory through superior technique.",
            f"Faced {enemy_name} blade-to-blade. Experience won the day.",
        ],
        'blaster': [
            f"Took down {enemy_name} with ranged fire. Tactical advantage secured.",
            f"Shot {enemy_name} from cover. Combat is about survival, not honor.",
        ],
        'force': [
            f"Used Force abilities against {enemy_name}. Pragmatic application of power.",
            f"The Force gave me the edge over {enemy_name}. Tool, not master.",
        ],
        'melee': [
            f"Close combat with {enemy_name}. Training and instinct carried me through.",
            f"Brawled with {enemy_name} in the {biome}. Messy but effective.",
        ]
    }
    
    # Determine weapon category
    weapon_cat = 'melee'  # default
    if weapon_type:
        wt_lower = weapon_type.lower()
        if 'saber' in wt_lower or 'blade' in wt_lower:
            weapon_cat = 'lightsaber'
        elif 'blast' in wt_lower or 'rifle' in wt_lower or 'pistol' in wt_lower:
            weapon_cat = 'blaster'
        elif 'force' in wt_lower or 'push' in wt_lower or 'lightning' in wt_lower:
            weapon_cat = 'force'
    
    # Select entry pool based on alignment
    if player_alignment in ['pure_light', 'light']:
        pool = light_entries.get(weapon_cat, light_entries['melee'])
    elif player_alignment in ['pure_dark', 'dark']:
        pool = dark_entries.get(weapon_cat, dark_entries['melee'])
    else:
        pool = balanced_entries.get(weapon_cat, balanced_entries['melee'])
    
    return random.choice(pool)


def get_combat_death_entry(enemy_name, player_alignment, cause="combat"):
    """Generate immersive death journal entry."""
    
    light_deaths = [
        f"My journey ends at the hands of {enemy_name}. I tried to stay true to the Light... I hope I succeeded.",
        f"{enemy_name} struck me down. May the Force accept me, flawed as I was.",
        f"Fell in combat against {enemy_name}. I die as I lived - seeking the Light, even in darkness.",
        f"The {enemy_name} was too strong. At least I fought with honor. The Force will guide me now.",
    ]
    
    dark_deaths = [
        f"Defeated by {enemy_name}... impossible! The dark side has FAILED me!",
        f"{enemy_name} struck the killing blow. I underestimated them... a fatal weakness...",
        f"Brought down by {enemy_name}. The power I sought... wasn't enough...",
        f"My ambition led me here, broken by {enemy_name}. The dark side... consumes all...",
    ]
    
    balanced_deaths = [
        f"Fell to {enemy_name}. My path ends here, for better or worse.",
        f"{enemy_name} proved superior in the end. Such is the way of survival.",
        f"My luck ran out against {enemy_name}. The galaxy is indifferent to my fate.",
        f"Struck down by {enemy_name}. Another story cut short in this endless war.",
    ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light_deaths)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark_deaths)
    else:
        return random.choice(balanced_deaths)


# ═══════════════════════════════════════════════════════════════════════════
# DISCOVERY & EXPLORATION ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def get_discovery_entry(item_name, item_type, player_alignment, biome="wasteland"):
    """Generate entry for finding items."""
    
    if item_type in ['weapon', 'lightsaber', 'blade']:
        light = [
            f"Discovered {item_name} among the ruins of the {biome}. A tool, not a trophy.",
            f"Found {item_name}. Another relic of war. I'll use it only in defense.",
            f"Recovered {item_name} from the {biome}. May it serve the Light if called upon.",
        ]
        dark = [
            f"Claimed {item_name} from the {biome}! This weapon will serve my power well!",
            f"Found {item_name}. A fitting instrument for my purposes!",
            f"Seized {item_name}! The stronger I become, the better!",
        ]
        balanced = [
            f"Acquired {item_name} in the {biome}. A useful addition to my arsenal.",
            f"Found {item_name}. Better equipped means better odds.",
            f"Picked up {item_name}. Every advantage counts out here.",
        ]
    elif item_type in ['armor', 'protection']:
        light = [
            f"Found {item_name}. Protection allows me to help others without falling.",
            f"Recovered {item_name} in the {biome}. Survival means I can do more good.",
        ]
        dark = [
            f"Donned {item_name}. I will be unstoppable now!",
            f"Claimed {item_name}. Let them try to harm me now!",
        ]
        balanced = [
            f"Equipped {item_name}. Practical defense for what's ahead.",
            f"Found {item_name}. Better protection means better survival.",
        ]
    else:  # consumables, artifacts, etc
        light = [
            f"Discovered {item_name} in the {biome}. Resources are scarce - I'm grateful for this find.",
            f"Found {item_name}. Small mercies in this harsh place.",
        ]
        dark = [
            f"Acquired {item_name}. Mine by right of conquest!",
            f"Claimed {item_name} from the {biome}. Everything here belongs to the strong!",
        ]
        balanced = [
            f"Found {item_name}. Useful find in the {biome}.",
            f"Picked up {item_name}. Practical addition to my supplies.",
        ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark)
    else:
        return random.choice(balanced)


def get_landmark_entry(landmark_name, landmark_type, player_alignment, biome="wasteland"):
    """Generate entry for discovering landmarks."""
    
    light_entries = [
        f"Reached {landmark_name}. Even in desolation, there's wonder in these ancient places.",
        f"Discovered {landmark_name} in the {biome}. The Force whispers stories of those who came before.",
        f"Found {landmark_name}. So much history, so much loss. I must remember this.",
        f"Arrived at {landmark_name}. These ruins stand as testament to the cycle of light and darkness.",
    ]
    
    dark_entries = [
        f"Claimed {landmark_name}! The power in this place... I can FEEL it!",
        f"Discovered {landmark_name} in the {biome}. What secrets does it hold? What power can I take?",
        f"Found {landmark_name}. The dark side thrums here. This place knows true strength!",
        f"Reached {landmark_name}. Ancient power lingers here. It will be mine!",
    ]
    
    balanced_entries = [
        f"Discovered {landmark_name} in the {biome}. Interesting find.",
        f"Reached {landmark_name}. Another waypoint on this strange journey.",
        f"Found {landmark_name}. Worth noting for future reference.",
        f"Arrived at {landmark_name}. The past leaves many marks on this world.",
    ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light_entries)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark_entries)
    else:
        return random.choice(balanced_entries)


# ═══════════════════════════════════════════════════════════════════════════
# ARTIFACT & FORCE ABILITY ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def get_artifact_choice_entry(choice, player_alignment, artifact_name="Sith artifact"):
    """Generate entry for artifact decisions."""
    
    if choice == 'destroy':
        light = [
            f"Destroyed the {artifact_name}. The corruption ends with me. The Light prevails.",
            f"Shattered the {artifact_name}. Its dark whispers are silenced forever. I am strengthened by this choice.",
            f"Purified the {artifact_name} through destruction. The Force flows cleaner now.",
        ]
        balanced = [
            f"Destroyed the {artifact_name}. Seemed like the safer choice.",
            f"Broke the {artifact_name}. No point in keeping that kind of power around.",
        ]
        # Dark players shouldn't destroy, but if they do:
        dark = [
            f"Destroyed the {artifact_name}... why did I do that? Such waste...",
        ]
        
        if player_alignment in ['pure_light', 'light']:
            return random.choice(light)
        elif player_alignment in ['pure_dark', 'dark']:
            return random.choice(dark)
        else:
            return random.choice(balanced)
    
    elif choice == 'absorb':
        dark = [
            f"Absorbed the {artifact_name}'s power! The dark side surges within me! I am LIMITLESS!",
            f"Consumed the {artifact_name}. Its essence flows through me now. More... I NEED MORE!",
            f"Drained the {artifact_name} completely. This is what true power feels like!",
        ]
        balanced = [
            f"Absorbed the {artifact_name}. Power is power - I'll use it as needed.",
            f"Took the energy from the {artifact_name}. Practical boost, whatever the source.",
        ]
        # Light players doing dark deed:
        light = [
            f"I... I absorbed the {artifact_name}. The power was too tempting. What am I becoming?",
            f"Consumed the {artifact_name}. The darkness seeps in. Have I made a terrible mistake?",
        ]
        
        if player_alignment in ['pure_dark', 'dark']:
            return random.choice(dark)
        elif player_alignment in ['pure_light', 'light']:
            return random.choice(light)
        else:
            return random.choice(balanced)
    
    else:  # leave
        light = [
            f"Left the {artifact_name} untouched. Some things should not be disturbed.",
            f"Walked away from the {artifact_name}. Restraint is wisdom.",
        ]
        balanced = [
            f"Left the {artifact_name} alone. Not worth the risk.",
        ]
        dark = [
            f"Ignored the {artifact_name}... for now. I may return when I'm stronger.",
        ]
        
        if player_alignment in ['pure_light', 'light']:
            return random.choice(light)
        elif player_alignment in ['pure_dark', 'dark']:
            return random.choice(dark)
        else:
            return random.choice(balanced)


def get_ability_learned_entry(ability_name, player_alignment):
    """Generate entry for learning new Force abilities."""
    
    light_entries = [
        f"Learned {ability_name} through meditation and study. The Force reveals itself to the patient.",
        f"Mastered {ability_name}. Each step deepens my connection to the Living Force.",
        f"The Force granted me insight into {ability_name}. I will use it wisely.",
    ]
    
    dark_entries = [
        f"Seized mastery of {ability_name}! My power grows beyond limits!",
        f"Conquered {ability_name} through sheer will! The Force BENDS to me!",
        f"Claimed {ability_name} as my own. With each ability, I become unstoppable!",
    ]
    
    balanced_entries = [
        f"Learned {ability_name}. Expanding my capabilities.",
        f"Gained proficiency in {ability_name}. Another tool in the kit.",
        f"Mastered {ability_name}. Knowledge is survival.",
    ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light_entries)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark_entries)
    else:
        return random.choice(balanced_entries)


# ═══════════════════════════════════════════════════════════════════════════
# BIOME-SPECIFIC ATMOSPHERIC ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def get_biome_atmosphere_entry(biome, player_alignment, corruption_level=50):
    """Generate biome-specific atmospheric observations."""
    
    biome_entries = {
        'wasteland': {
            'light': [
                "The wasteland stretches endlessly. Yet even here, tiny flowers push through cracks in the stone. Life persists.",
                "Desolate winds sweep the wasteland. The Force whispers that nothing is truly barren.",
                "Walking through endless wastes. I must remember: despair is as dangerous as any enemy.",
            ],
            'dark': [
                "The wasteland mirrors my soul - harsh, unforgiving, powerful. I am HOME here!",
                "These wastes bow to no one. Perfect. Neither do I.",
                "The wasteland strips away weakness. Only the strong survive here. Only ME.",
            ],
            'balanced': [
                "Endless wasteland. One foot forward, then another. That's all there is.",
                "The wastes are indifferent. So am I. We understand each other.",
            ]
        },
        'ruins': {
            'light': [
                "Ancient ruins surround me. Civilizations rise and fall, but the Force endures.",
                "Walking through crumbling monuments. Pride before a fall, always.",
                "These ruins were once grand. A reminder that nothing lasts but the Force itself.",
            ],
            'dark': [
                "These ruins speak of failure! Of WEAKNESS! I will not end like this!",
                "Empires fall, but legends endure. I will be LEGENDARY!",
                "The ruins are lessons: crush enemies COMPLETELY or they rise again!",
            ],
            'balanced': [
                "Ancient ruins everywhere. History has a way of repeating.",
                "Crumbling architecture tells stories. None of them end well.",
            ]
        },
        'tomb': {
            'light': [
                "Tombs line these passages. So much death, so much suffering. I pray for their peace.",
                "The tomb air is heavy with old sorrows. May the Force grant them rest at last.",
                "Walking among the dead. Each was someone. Each had hopes. Now just echoes.",
            ],
            'dark': [
                "These tombs REEK of power! The dead have much to teach the ambitious!",
                "Death surrounds me. Fear surrounds me. I feed on BOTH!",
                "The tombs hold secrets, and I will PRY them all free!",
            ],
            'balanced': [
                "Tomb passages. The dead don't care about the living. Why should I care about them?",
                "Ancient tombs. Full of dust, bones, and occasionally useful artifacts.",
            ]
        },
        'volcanic': {
            'light': [
                "The volcanic heat is oppressive. Like anger - must stay cool, stay centered.",
                "Flames and lava everywhere. Destruction is easy. Creation takes discipline.",
                "The volcano's fury reminds me: rage consumes everything, including itself.",
            ],
            'dark': [
                "The volcanic fires match my passion! Burn it ALL down!",
                "Heat, fury, POWER! This place understands strength!",
                "The volcano doesn't apologize for its nature. Neither will I!",
            ],
            'balanced': [
                "Volcanic region. Hot, dangerous, unstable. Business as usual.",
                "Lava flows. Fire storms. Just another day surviving.",
            ]
        },
    }
    
    biome_key = biome.lower()
    if biome_key not in biome_entries:
        biome_key = 'wasteland'  # fallback
    
    if player_alignment in ['pure_light', 'light']:
        pool = biome_entries[biome_key]['light']
    elif player_alignment in ['pure_dark', 'dark']:
        pool = biome_entries[biome_key]['dark']
    else:
        pool = biome_entries[biome_key]['balanced']
    
    return random.choice(pool)


# ═══════════════════════════════════════════════════════════════════════════
# LEVEL UP & MILESTONE ENTRIES
# ═══════════════════════════════════════════════════════════════════════════

def get_level_up_entry(new_level, player_alignment):
    """Generate entry for gaining a level."""
    
    light_entries = [
        f"Advanced to level {new_level}. Growth through adversity. The Force guides my path.",
        f"Reached level {new_level}. Each challenge teaches. Each lesson strengthens the Light within.",
        f"Level {new_level} achieved. I'm becoming who the Force needs me to be.",
    ]
    
    dark_entries = [
        f"Level {new_level}! With each ascension, I grow CLOSER to absolute power!",
        f"Attained level {new_level}! The weak fall away. Only I rise!",
        f"Level {new_level}! NOTHING can stop my ascent now!",
    ]
    
    balanced_entries = [
        f"Level {new_level}. Experience counts for something.",
        f"Reached level {new_level}. Survival breeds competence.",
        f"Advanced to level {new_level}. Progress, however slow.",
    ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light_entries)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark_entries)
    else:
        return random.choice(balanced_entries)


def get_form_learned_entry(form_name, player_alignment):
    """Generate entry for learning a lightsaber form."""
    
    light_entries = [
        f"Studied {form_name}. Ancient techniques flow through me. Knowledge honors those who came before.",
        f"Mastered {form_name} through discipline. The Old Ways still teach.",
        f"Learned {form_name}. Each form is a philosophy. Each stance tells a story.",
    ]
    
    dark_entries = [
        f"Conquered {form_name}! One more weapon in my arsenal of DOMINATION!",
        f"Seized mastery of {form_name}! The old masters would TREMBLE at my skill!",
        f"Claimed {form_name} as my own! Each form makes me more LETHAL!",
    ]
    
    balanced_entries = [
        f"Learned {form_name}. Different situations call for different approaches.",
        f"Added {form_name} to my repertoire. Versatility equals survival.",
        f"Mastered {form_name}. More options means better odds.",
    ]
    
    if player_alignment in ['pure_light', 'light']:
        return random.choice(light_entries)
    elif player_alignment in ['pure_dark', 'dark']:
        return random.choice(dark_entries)
    else:
        return random.choice(balanced_entries)
